# app/services/chat/handler.py（更新日時: 2025-07-18 18:00 JST）
"""
チャット検索リクエストハンドラ
  ・チャンク統合
  ・ファイル別（要約＋一致度）
"""

# ── 標準ライブラリ ───────────────────────────
import re
import asyncio
from typing import List, Dict

# ── サードパーティ ───────────────────────────
import numpy as np
from langchain_community.embeddings import OllamaEmbeddings
from sentence_transformers import SentenceTransformer

# ── プロジェクト共通 ──────────────────────────
from src.config import EMBEDDING_OPTIONS, LLM_ENGINE, OLLAMA_BASE
from src.utils import to_pgvector_literal
from db.handler import (
    fetch_top_chunks,
    fetch_top_files,
    get_file_text
)
from llm.prompt_loader import get_chat_prompt

# ═════════════════════════════════════════════

# ═════════════════════════════════════════════
async def handle_query(query: str, model_key: str, mode: str = "チャンク統合", search_limit: int = 10, min_score: float = 0.0) -> Dict:
    selected_model = EMBEDDING_OPTIONS[model_key]
    tablename = (
        f"{selected_model['model_name'].replace('/', '_').replace('-', '_')}"
        f"_{selected_model['dimension']}"
    )

    # 1) クエリ埋め込み
    if selected_model["embedder"] == "OllamaEmbeddings":
        embedder = OllamaEmbeddings(
            model=selected_model["model_name"],
            base_url=OLLAMA_BASE
        )
        query_embedding = embedder.embed_query(query)
    else:
        embedder = SentenceTransformer(selected_model["model_name"])
        query_embedding = embedder.encode([query], convert_to_numpy=True)[0]

    embedding_str = to_pgvector_literal(query_embedding)

    # ── A. チャンク統合 ────────────────────────
    if mode == "チャンク統合":
         # 2) 上位Kチャンクを取得（ユーザー指定の件数）
        rows = fetch_top_chunks(embedding_str, tablename, limit=search_limit)

         # 3) 統合回答用にスニペットを抽出＋LLM呼び出し
        snippets = [r["snippet"] for r in rows]
        prompt_template = get_chat_prompt("chunk_integration")
        prompt = prompt_template.replace("{QUERY}", query).replace("{SNIPPETS}", "\n---\n".join(snippets))
        # キャンセルチェック
        from app.routes.chat import _search_cancelled
        if _search_cancelled:
            raise asyncio.CancelledError("検索処理がキャンセルされました")
            
        # 非同期でLLM呼び出し
        loop = asyncio.get_event_loop()
        answer = await loop.run_in_executor(None, lambda: LLM_ENGINE.invoke(prompt).strip())

        # 4) 使用されたファイルをユニーク抽出
        seen = {r["blob_id"]: r["file_name"] for r in rows}
        sources = [{"file_id": blob_id, "file_name": fn} for blob_id, fn in seen.items()]

        return {
            "mode": mode,
            "answer": answer,
            "sources": sources,
            "results": rows
        }

    # ── B. ファイル別（要約＋一致度）──────────────
    rows = fetch_top_files(embedding_str, tablename, limit=search_limit)

    # 並列でLLM処理を実行
    tasks = []
    for row in rows:
        task = llm_summarize_with_score_async(query, row["refined_text"], row["blob_id"], row["file_name"])
        tasks.append(task)
    
    # 全てのタスクを並列実行
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    summaries: List[Dict] = []
    for result in results:
        if isinstance(result, Exception):
            continue  # エラーの場合はスキップ
        summary, score, file_id, file_name = result
        # 最小一致度フィルタリング
        if score >= min_score:
            summaries.append({
                "file_id": file_id,
                "file_name": file_name,
                "score": score,
                "summary": summary
            })
    summaries.sort(key=lambda x: x["score"], reverse=True)

    return {
        "mode": mode, 
        "results": summaries,
        "total_found": len(rows),
        "filtered_count": len(summaries),
        "min_score_threshold": min_score
    }

# ═════════════════════════════════════════════
def get_file_content(file_id: str) -> str:
    meta = get_file_text(file_id)
    return meta["refined_text"] if meta else ""

# ═════════════════════════════════════════════
def llm_summarize_with_score(query: str, content: str):
    prompt_template = get_chat_prompt("file_summary_score")
    prompt = prompt_template.replace("{QUERY}", query).replace("{CONTENT}", content[:3000])
    result = LLM_ENGINE.invoke(prompt)
    m = re.search(
        r"一致度[:：]\s*([0-9.]+).*?要約[:：]\s*(.+)", result, re.DOTALL
    )
    if m:
        return m.group(2).strip(), float(m.group(1))
    return result.strip(), 0.0

# ═════════════════════════════════════════════
async def llm_summarize_with_score_async(query: str, content: str, file_id: str, file_name: str):
    """非同期版のLLM要約・評価関数"""
    # キャンセルチェック
    from app.routes.chat import _search_cancelled
    if _search_cancelled:
        raise asyncio.CancelledError("検索処理がキャンセルされました")
        
    prompt_template = get_chat_prompt("file_summary_score")
    prompt = prompt_template.replace("{QUERY}", query).replace("{CONTENT}", content[:3000])
    # 非同期でLLM呼び出し
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, lambda: LLM_ENGINE.invoke(prompt))
    
    m = re.search(
        r"一致度[:：]\s*([0-9.]+).*?要約[:：]\s*(.+)", result, re.DOTALL
    )
    if m:
        summary = m.group(2).strip()
        score = float(m.group(1))
    else:
        summary = result.strip()
        score = 0.0
    
    return summary, score, file_id, file_name