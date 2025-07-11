# /workspace/app/routes/query.py
"""
/query 用ルーター
"""

from fastapi import APIRouter, Form
from fastapi.responses import JSONResponse
from app.fastapi.services.query_handler import handle_query

router = APIRouter()

@router.post("/query")
async def query_api(
    query: str     = Form(...),
    model_key: str = Form(...),
    mode: str      = Form("チャンク統合")
):
    try:
        return handle_query(query, model_key, mode)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)
