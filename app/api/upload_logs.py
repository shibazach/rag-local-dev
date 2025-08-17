"""
アップロードログAPI
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any
from app.services.upload_log_service import upload_log_service
from app.config import logger

router = APIRouter()

@router.get("/logs/recent")
async def get_recent_logs(
    limit: int = Query(100, description="取得する件数"),
    offset: int = Query(0, description="オフセット")
) -> List[Dict[str, Any]]:
    """
    最近のアップロードログを取得（最新順）
    """
    try:
        logs = upload_log_service.get_recent_logs(limit=limit, offset=offset)
        return logs
    except Exception as e:
        logger.error(f"Failed to get recent logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/logs/session/{session_id}")
async def get_session_logs(session_id: str) -> List[Dict[str, Any]]:
    """
    特定セッションのログを取得
    """
    try:
        logs = upload_log_service.get_session_logs(session_id)
        return logs
    except Exception as e:
        logger.error(f"Failed to get session logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/logs/in_progress")
async def get_in_progress_logs(limit: int = Query(200, description="取得件数")) -> List[Dict[str, Any]]:
    """未完了ログ（pending/uploading/processing）を取得"""
    try:
        logs = upload_log_service.get_in_progress_logs(limit=limit)
        return logs
    except Exception as e:
        logger.error(f"Failed to get in-progress logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


