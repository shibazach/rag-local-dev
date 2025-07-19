# REM: app/services/chat_handler.py（更新日時: 2025-07-18 18:00 JST）
"""
チャット検索リクエストハンドラ
  ・チャンク統合
  ・ファイル別（要約＋一致度）
"""

# ── 標準ライブラリ ───────────────────────────
import re
from typing import List, Dict

# ── サードパーティ ───────────────────────────
import numpy as np
from langchain_community.embeddings import OllamaEmbeddings
from sentence_transformers import SentenceTransformer

# ── プロジェクト共通 ──────────────────────────
from src.config import EMBEDDING_OPTIONS, LLM_ENGINE, OLLAMA_BASE
from db.handler import (
    fetch_top_chunks,
    fetch_top_files,
    get_file_text
)

# ═════════════════════════════════════════════
def to_pgvector_literal(vec) -> str:
    if isinstance(vec, np.ndarray):
        vec = vec.tolist()
    return "[" + ",".join(f"{float(x):.6f}" for x in vec) + "]"

# ═════════════════════════════════════════════
def handle_query(query: str, model_key: str, mode: str = "チャンク統合") -> Dict:
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
         # 2) 上位Kチャンクを取得
        rows = fetch_top_chunks(embedding_str, tablename, limit=5)

         # 3) 統合回答用にスニペットを抽出＋LLM呼び出し
        snippets = [r["snippet"] for r in rows]
        prompt = (
            f"質問：{query}\n"
            "以下の文書スニペットを参照し、一つの回答を出力してください：\n\n"
            + "\n---\n".join(snippets)
        )
        answer = LLM_ENGINE.invoke(prompt).strip()

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
    rows = fetch_top_files(embedding_str, tablename, limit=10)

    summaries: List[Dict] = []
    for row in rows:
        summary, score = llm_summarize_with_score(query, row["refined_text"])
        summaries.append({
            "file_id":   row["blob_id"],  # 新しいテーブル構造に対応
            "file_name": row["file_name"],
            "score": score,
            "summary": summary
        })
    summaries.sort(key=lambda x: x["score"], reverse=True)

    return {"mode": mode, "results": summaries}

# ═════════════════════════════════════════════
def get_file_content(file_id: str) -> str:
    meta = get_file_text(file_id)
    return meta["refined_text"] if meta else ""

# ═════════════════════════════════════════════
def llm_summarize_with_score(query: str, content: str):
    prompt = f"""
以下はユーザーの質問と文書の内容です。

【質問】
{query}

【文書】
{content[:3000]}

この文書が質問にどの程度一致しているか（0.0〜1.0）で評価し、次の形式で出力してください：

一致度: <score>
要約: <summary>
"""
    result = LLM_ENGINE.invoke(prompt)
    m = re.search(
        r"一致度[:：]\s*([0-9.]+).*?要約[:：]\s*(.+)", result, re.DOTALL
    )
    if m:
        return m.group(2).strip(), float(m.group(1))
    return result.strip(), 0.0
