# REM: app/routes/chat_edit.py（更新日時: 2025-07-18 18:00 JST）
"""
チャット検索結果からのファイル編集機能
"""

from fastapi import APIRouter, Form, HTTPException
from fastapi.responses import JSONResponse
from OLD.db.handler import get_file_text, update_file_text
from OLD.fileio.file_embedder import embed_and_insert
from OLD.llm.chunker import split_into_chunks

router = APIRouter()

@router.get("/api/content/{blob_id}")
async def get_file_content(blob_id: str):
    """ファイル内容を取得（編集用）"""
    try:
        text_data = get_file_text(blob_id)
        if not text_data:
            raise HTTPException(404, "File not found")
        
        return {
            "content": text_data.get("refined_text", ""),
            "quality_score": text_data.get("quality_score", 0.0)
        }
    except Exception as e:
        raise HTTPException(500, f"Error retrieving content: {str(e)}")

@router.post("/api/save/{blob_id}")
async def save_file_content(blob_id: str, content: str = Form(...)):
    """ファイル内容を保存して再ベクトル化"""
    try:
        # 1. ファイル内容を更新
        update_file_text(blob_id, refined_text=content)
        
        # 2. 再ベクトル化
        chunks = split_into_chunks(content, chunk_size=500, overlap=50)
        
        # 3. 全ての埋め込みモデルで再ベクトル化
        from src.config import EMBEDDING_OPTIONS
        model_keys = list(EMBEDDING_OPTIONS.keys())
        
        embed_and_insert(
            texts=chunks,
            file_name="",  # ダミー（blob_id指定時は不要）
            model_keys=model_keys,
            overwrite=True,
            file_id=blob_id
        )
        
        return JSONResponse({"status": "success", "message": "再ベクトル化完了"})
        
    except Exception as e:
        raise HTTPException(500, f"Error saving content: {str(e)}")