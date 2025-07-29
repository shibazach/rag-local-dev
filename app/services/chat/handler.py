# app/services/chat/handler.py
# チャット検索ハンドラー

import asyncio
import logging
from typing import Dict, List

from src.config import LLM_ENGINE
from app.services.chat.query_embedder import fetch_top_chunks, fetch_top_files
from app.services.chat.query_handler import llm_summarize_with_score_async
from llm.prompt_loader import get_chat_prompt

LOGGER = logging.getLogger("chat_handler")

# 新しい高度化されたプロンプトファイルのパス
ADVANCED_CHAT_PROMPT_FILE = "bin/chat_prompts_advanced.txt"

def get_advanced_chat_prompt(section: str) -> str:
    """高度化されたチャットプロンプトから指定セクションのプロンプトを取得する"""
    try:
        import os
        if not os.path.exists(ADVANCED_CHAT_PROMPT_FILE):
            # フォールバック: 既存のプロンプトを使用
            return get_chat_prompt(section)
        
        with open(ADVANCED_CHAT_PROMPT_FILE, encoding="utf-8") as f:
            content = f.read()
        
        # <section>...</section> 形式のセクションを抽出
        import re
        pattern = f"<{section}>(.*?)</{section}>"
        match = re.search(pattern, content, re.DOTALL)
        
        if match:
            return match.group(1).strip()
        else:
            # フォールバック: 既存のプロンプトを使用
            return get_chat_prompt(section)
            
    except Exception as e:
        LOGGER.warning(f"高度化プロンプト読み込みエラー: {e}")
        # フォールバック: 既存のプロンプトを使用
        return get_chat_prompt(section)

async def handle_query(query: str, model_key: str, mode: str = "チャンク統合", search_limit: int = 10, min_score: float = 0.0) -> Dict:

    # 埋め込みテーブル名の決定（モデルキーに基づく）
    tablename = f"embeddings_{model_key}"

    # ── A. チャンク統合 ────────────────────────
    if mode == "チャンク統合":
         # 2) 上位Kチャンクを取得（ユーザー指定の件数）
        rows = fetch_top_chunks(query, model_key, tablename, limit=search_limit)

         # 3) 統合回答用にスニペットを抽出＋LLM呼び出し
        snippets = [r["snippet"] for r in rows]
        # 高度化されたプロンプトを使用
        prompt_template = get_advanced_chat_prompt("chunk_integration")
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
    rows = fetch_top_files(query, model_key, tablename, limit=search_limit)

    # 並列でLLM処理を実行
    tasks = []
    for row in rows:
        task = llm_summarize_with_score_async(query, row["refined_text"], row["blob_id"], row["file_name"])
        tasks.append(task)
    
    # 全てのタスクを並列実行
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    summaries: List[Dict] = []
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            LOGGER.warning(f"ファイル {rows[i]['file_name']} の要約でエラー: {result}")
            summaries.append({
                "file_id": rows[i]["blob_id"],
                "file_name": rows[i]["file_name"],
                "score": 0.0,
                "summary": f"要約エラー: {str(result)}"
            })
        else:
            summaries.append(result)

    return {
        "mode": mode, 
        "summaries": summaries,
        "results": rows
    }