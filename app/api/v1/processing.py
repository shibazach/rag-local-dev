"""
処理API
Document processing endpoints with real-time progress
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Form
from fastapi.responses import StreamingResponse
# from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict, Any
import json

from app.auth.dependencies import get_current_user_required, get_current_user_optional
from app.core.database import get_db
from app.core.schemas import ProcessingConfig, ProcessingResponse
from app.services.processing_service import get_processing_service, ProcessingService

router = APIRouter(prefix="/processing", tags=["processing"])


@router.post("/start", response_model=ProcessingResponse)
async def start_processing(
    file_ids: List[str] = Form(...),
    config = Depends(),
    processing_service = Depends(get_processing_service),
    db = Depends(get_db),
    current_user = Depends(get_current_user_required)
):
    """処理開始"""
    try:
        # ファイルIDバリデーション
        if not file_ids:
            raise HTTPException(status_code=400, detail="処理対象ファイルが選択されていません")
        
        if len(file_ids) > 100:  # 一度に処理できるファイル数制限
            raise HTTPException(status_code=400, detail="一度に処理できるファイル数は100件までです")
        
        # 処理開始
        job_id = await processing_service.start_processing(
            file_ids=file_ids,
            processing_config=config.dict(),
            user_id=current_user.get("id")
        )
        
        return ProcessingResponse(
            success=True,
            job_id=job_id,
            message=f"{len(file_ids)}件のファイル処理を開始しました"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"処理開始エラー: {str(e)}")


@router.get("/status/{job_id}")
async def get_processing_status(
    job_id: str,
    processing_service = Depends(get_processing_service),
    current_user = Depends(get_current_user_optional)
):
    """処理状況取得"""
    try:
        status = await processing_service.get_job_status(job_id)
        
        if not status:
            raise HTTPException(status_code=404, detail="ジョブが見つかりません")
        
        # ユーザー権限チェック（必要に応じて）
        if current_user and status.get("user_id") != current_user.get("id"):
            # 管理者権限がない場合はアクセス拒否
            if not current_user.get("is_admin", False):
                raise HTTPException(status_code=403, detail="アクセス権限がありません")
        
        return status
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"状況取得エラー: {str(e)}")


@router.post("/cancel/{job_id}")
async def cancel_processing(
    job_id: str,
    processing_service = Depends(get_processing_service),
    current_user = Depends(get_current_user_required)
):
    """処理キャンセル"""
    try:
        # ジョブ存在確認
        status = await processing_service.get_job_status(job_id)
        if not status:
            raise HTTPException(status_code=404, detail="ジョブが見つかりません")
        
        # ユーザー権限チェック
        if status.get("user_id") != current_user.get("id"):
            if not current_user.get("is_admin", False):
                raise HTTPException(status_code=403, detail="キャンセル権限がありません")
        
        # キャンセル実行
        success = await processing_service.cancel_job(job_id)
        
        if success:
            return {"message": "処理をキャンセルしました", "job_id": job_id}
        else:
            raise HTTPException(status_code=400, detail="キャンセルできませんでした")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"キャンセルエラー: {str(e)}")


@router.get("/stream/{job_id}")
async def stream_processing_progress(
    job_id: str,
    processing_service = Depends(get_processing_service),
    current_user = Depends(get_current_user_optional)
):
    """処理進捗ストリーミング"""
    try:
        # ジョブ存在確認
        status = await processing_service.get_job_status(job_id)
        if not status:
            raise HTTPException(status_code=404, detail="ジョブが見つかりません")
        
        # ユーザー権限チェック
        if current_user and status.get("user_id") != current_user.get("id"):
            if not current_user.get("is_admin", False):
                raise HTTPException(status_code=403, detail="アクセス権限がありません")
        
        # 進捗ストリーミング
        async def generate_progress():
            try:
                async for progress_data in processing_service.stream_progress(job_id):
                    yield f"data: {json.dumps(progress_data, ensure_ascii=False, default=str)}\n\n"
            except Exception as e:
                yield f"data: {json.dumps({'type': 'error', 'message': str(e)}, ensure_ascii=False)}\n\n"
        
        return StreamingResponse(
            generate_progress(),
            media_type="text/plain; charset=utf-8",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Content-Type": "text/event-stream; charset=utf-8"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"進捗ストリーミングエラー: {str(e)}")


@router.get("/queue")
async def get_processing_queue(
    current_user = Depends(get_current_user_required)
):
    """処理キュー状況取得"""
    try:
        # 管理者権限チェック
        if not current_user.get("is_admin", False):
            raise HTTPException(status_code=403, detail="管理者権限が必要です")
        
        # TODO: キュー状況の実装
        return {
            "queued_jobs": 2,
            "active_jobs": 1,
            "completed_jobs_today": 15,
            "avg_processing_time": 180,  # 秒
            "system_load": 0.65
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"キュー状況取得エラー: {str(e)}")


@router.get("/stats")
async def get_processing_stats(
    days: int = Query(7, ge=1, le=30),
    current_user = Depends(get_current_user_optional)
):
    """処理統計取得"""
    try:
        if not current_user:
            return {"total_processed": 0, "success_rate": 0}
        
        # TODO: 統計情報の実装
        return {
            "total_processed": 156,
            "success_rate": 0.94,
            "avg_processing_time": 145,  # 秒
            "most_processed_formats": ["PDF", "DOCX", "TXT"],
            "daily_processing_count": [12, 8, 15, 9, 18, 14, 11],  # 過去7日間
            "error_rate_by_format": {
                "PDF": 0.03,
                "DOCX": 0.08,
                "TXT": 0.01
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"統計取得エラー: {str(e)}")


@router.post("/retry/{job_id}")
async def retry_processing(
    job_id: str,
    processing_service = Depends(get_processing_service),
    current_user = Depends(get_current_user_required)
):
    """処理再試行"""
    try:
        # 元のジョブ情報取得
        original_status = await processing_service.get_job_status(job_id)
        if not original_status:
            raise HTTPException(status_code=404, detail="元のジョブが見つかりません")
        
        # ユーザー権限チェック
        if original_status.get("user_id") != current_user.get("id"):
            if not current_user.get("is_admin", False):
                raise HTTPException(status_code=403, detail="再試行権限がありません")
        
        # 失敗したファイルのみ再処理
        failed_files = []  # TODO: 失敗ファイル抽出ロジック
        
        if not failed_files:
            return {"message": "再試行が必要なファイルがありません"}
        
        # 新しいジョブとして再処理開始
        new_job_id = await processing_service.start_processing(
            file_ids=failed_files,
            processing_config=original_status.get("config", {}),
            user_id=current_user.get("id")
        )
        
        return {
            "message": f"{len(failed_files)}件のファイルを再処理します",
            "new_job_id": new_job_id,
            "original_job_id": job_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"再試行エラー: {str(e)}")