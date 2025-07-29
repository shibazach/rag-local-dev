# app/services/chat/query_handler.py
# クエリ処理とLLM要約機能

import asyncio
import logging
from typing import Dict, Any
from src.config import LLM_ENGINE

LOGGER = logging.getLogger("query_handler")

async def llm_summarize_with_score_async(
    query: str, 
    text_content: str, 
    blob_id: str, 
    file_name: str
) -> Dict[str, Any]:
    """非同期でLLM要約を実行"""
    try:
        # 要約プロンプトの構築
        prompt = f"""
以下のテキストを、質問「{query}」に関連する内容に基づいて要約してください。

テキスト内容:
{text_content[:2000]}  # 長すぎる場合は切り詰め

要約のポイント:
1. 質問に関連する重要な情報を抽出
2. 簡潔で分かりやすい日本語で記述
3. 具体的な数値や事実があれば含める
4. 最大200文字程度で要約

要約:
"""
        
        # 非同期でLLM処理を実行
        loop = asyncio.get_event_loop()
        summary = await loop.run_in_executor(
            None, 
            lambda: LLM_ENGINE.invoke(prompt).strip()
        )
        
        # 簡易的なスコア計算（要約の長さと内容の充実度）
        score = min(1.0, len(summary) / 100.0)
        
        return {
            "file_id": blob_id,
            "file_name": file_name,
            "summary": summary,
            "score": score
        }
        
    except Exception as e:
        LOGGER.exception(f"LLM要約エラー: {e}")
        return {
            "file_id": blob_id,
            "file_name": file_name,
            "summary": f"要約エラー: {str(e)}",
            "score": 0.0
        } 