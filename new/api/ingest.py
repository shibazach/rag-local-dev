# new/api/ingest.py
# データ登録処理・SSE進捗表示API

import asyncio
import json
import logging
import time
from typing import Dict, List, Optional, AsyncGenerator
from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.responses import StreamingResponse, JSONResponse
from sqlalchemy.engine import Connection

from new.database.connection import get_db_connection
from new.services.ocr import OCREngineFactory
from new.services.processing.pipeline import ProcessingPipeline
from new.config import LOGGER

router = APIRouter(prefix="/ingest", tags=["ingest"])

# グローバル状態管理
current_job: Optional[Dict] = None
cancel_event: Optional[asyncio.Event] = None
processing_pipeline: Optional[ProcessingPipeline] = None

@router.post("/start")
async def start_processing(
    request_data: Dict,
    connection: Connection = Depends(get_db_connection)
) -> JSONResponse:
    """データ登録処理を開始"""
    global current_job, cancel_event
    
    try:
        # 既存ジョブチェック
        if current_job and current_job.get("status") == "running":
            raise HTTPException(status_code=409, detail="処理が既に実行中です")
        
        # リクエストデータ検証
        selected_files = request_data.get("selected_files", [])
        if not selected_files:
            raise HTTPException(status_code=400, detail="処理対象ファイルが選択されていません")
        
        # 処理設定
        settings = request_data.get("settings", {})
        ocr_engine = settings.get("ocr_engine", "ocrmypdf")
        embedding_models = settings.get("embedding_models", ["intfloat-e5-large-v2"])
        overwrite_existing = settings.get("overwrite_existing", True)
        quality_threshold = settings.get("quality_threshold", 0.0)
        llm_timeout = settings.get("llm_timeout", 300)
        
        # ファイル情報を取得
        from sqlalchemy import text
        placeholders = ",".join([f":file_id_{i}" for i in range(len(selected_files))])
        params = {f"file_id_{i}": file_id for i, file_id in enumerate(selected_files)}
        
        query = text(f"""
            SELECT 
                fb.id as file_id,
                fm.file_name,
                CONCAT('/workspace/INPUT/', fm.file_name) as file_path,
                fm.size as file_size
            FROM files_blob fb
            JOIN files_meta fm ON fb.id = fm.blob_id
            WHERE fb.id IN ({placeholders})
            ORDER BY fb.stored_at DESC
        """)
        
        files = connection.execute(query, params).fetchall()
        
        if not files:
            raise HTTPException(status_code=404, detail="指定されたファイルが見つかりません")
        
        # ジョブ初期化
        current_job = {
            "id": f"job_{int(time.time())}",
            "status": "running",
            "files": files,
            "settings": {
                "ocr_engine": ocr_engine,
                "embedding_models": embedding_models,
                "overwrite_existing": overwrite_existing,
                "quality_threshold": quality_threshold,
                "llm_timeout": llm_timeout
            },
            "progress": {
                "total_files": len(files),
                "processed_files": 0,
                "current_file": None,
                "start_time": time.time()
            },
            "results": []
        }
        
        # キャンセルイベントリセット
        cancel_event = asyncio.Event()
        
        LOGGER.info(f"処理開始: {len(files)}ファイル, エンジン={ocr_engine}")
        
        return JSONResponse({
            "success": True,
            "data": {
                "job_id": current_job["id"],
                "total_files": len(files),
                "message": f"{len(files)}件のファイル処理を開始しました"
            }
        })
        
    except HTTPException:
        raise
    except Exception as e:
        LOGGER.error(f"処理開始エラー: {e}")
        raise HTTPException(status_code=500, detail=f"処理開始エラー: {str(e)}")

@router.post("/cancel")
async def cancel_processing() -> JSONResponse:
    """処理をキャンセル"""
    global current_job, cancel_event, processing_pipeline
    
    if not current_job or current_job.get("status") != "running":
        raise HTTPException(status_code=404, detail="実行中の処理がありません")
    
    if cancel_event:
        cancel_event.set()
        LOGGER.info("処理キャンセル要求")
    
    # パイプラインキャンセル
    if processing_pipeline:
        processing_pipeline.cancel_processing()
    
    # 状態をリセット
    current_job = None
    cancel_event = None
    processing_pipeline = None
    LOGGER.info("処理状態リセット完了")
    
    return JSONResponse({
        "success": True,
        "message": "処理をキャンセルし、状態をリセットしました"
    })

@router.post("/reset")
async def reset_processing_state() -> JSONResponse:
    """処理状態を強制リセット"""
    global current_job, cancel_event, processing_pipeline
    
    current_job = None
    cancel_event = None
    processing_pipeline = None
    
    LOGGER.info("処理状態を強制リセット")
    
    return JSONResponse({
        "success": True,
        "message": "処理状態をリセットしました"
    })

@router.get("/status")
async def get_processing_status() -> JSONResponse:
    """処理状況を取得"""
    global current_job
    
    if not current_job:
        raise HTTPException(status_code=404, detail="処理ジョブが見つかりません")
    
    return JSONResponse({
        "success": True,
        "data": {
            "job_id": current_job["id"],
            "status": current_job["status"],
            "progress": current_job["progress"],
            "results": current_job.get("results", [])
        }
    })

@router.get("/stream")
async def progress_stream(request: Request) -> StreamingResponse:
    """SSEで進捗をストリーミング（実際の処理エンジン使用）"""
    global current_job, cancel_event, processing_pipeline
    
    if not current_job:
        raise HTTPException(status_code=404, detail="処理ジョブが見つかりません")
    
    LOGGER.info(f"SSE接続開始: {request.client.host}")
    
    async def event_generator() -> AsyncGenerator[str, None]:
        nonlocal processing_pipeline
        
        try:
            # 処理パイプライン初期化
            processing_pipeline = ProcessingPipeline()
            LOGGER.info("処理パイプライン初期化完了")
            
            # クライアント切断監視
            async def monitor_disconnect():
                while current_job and current_job.get("status") == "running":
                    if await request.is_disconnected():
                        LOGGER.info("クライアント切断検知")
                        if processing_pipeline:
                            processing_pipeline.cancel_processing()
                        break
                    await asyncio.sleep(0.5)
            
            # キャンセル監視
            async def monitor_cancellation():
                while current_job and current_job.get("status") == "running":
                    if cancel_event and cancel_event.is_set():
                        LOGGER.info("キャンセル要求検知")
                        if processing_pipeline:
                            processing_pipeline.cancel_processing()
                        break
                    await asyncio.sleep(0.5)
            
            # 監視タスク開始
            asyncio.create_task(monitor_disconnect())
            asyncio.create_task(monitor_cancellation())
            
            # 実際のファイル処理実行
            files = current_job["files"]
            settings = current_job["settings"]
            current_job["results"] = []
            
            LOGGER.info(f"ファイル処理開始: {len(files)}件")
            async for event in processing_pipeline.process_files(files, settings):
                # キャンセル・切断チェック
                if (cancel_event and cancel_event.is_set()) or \
                   (await request.is_disconnected()):
                    break
                
                # 結果保存
                if event.get('type') == 'file_complete':
                    result = event.get('data', {}).get('result', {})
                    if result:
                        current_job["results"].append(result)
                
                # SSEイベント送信
                yield f"data: {json.dumps(event)}\n\n"
                
                # 完了チェック
                if event.get('type') in ['complete', 'error', 'cancelled']:
                    break
            
            # ジョブ状態更新
            if current_job:
                if cancel_event and cancel_event.is_set():
                    current_job["status"] = "cancelled"
                else:
                    current_job["status"] = "completed"
            
        except Exception as e:
            LOGGER.error(f"SSE処理エラー: {e}")
            yield f"data: {json.dumps({'type': 'error', 'message': f'処理エラー: {str(e)}'})}\n\n"
            
            if current_job:
                current_job["status"] = "error"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Cache-Control"
        }
    )