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
import os

router = APIRouter(prefix="/ingest", tags=["ingest"])

# グローバル状態管理
current_job: Optional[Dict] = None

def _cleanup_temp_files(files: List[Dict]):
    """一時ファイルをクリーンアップ"""
    if not files:
        return
        
    for file_info in files:
        if not file_info:  # None チェック追加
            continue
            
        if file_info.get('temp_file') and file_info.get('file_path'):  # より安全なチェック
            temp_path = file_info['file_path']
            try:
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
                    LOGGER.debug(f"一時ファイル削除: {temp_path}")
            except Exception as e:
                LOGGER.error(f"一時ファイル削除エラー [{temp_path}]: {e}")
cancel_event: Optional[asyncio.Event] = None
processing_pipeline: Optional[ProcessingPipeline] = None

@router.get("/status")
async def get_processing_status() -> JSONResponse:
    """現在の処理状況を取得"""
    global current_job
    
    if current_job:
        return JSONResponse({
            "status": current_job.get("status", "unknown"),
            "files_total": current_job.get("files_total", 0),
            "files_completed": current_job.get("files_completed", 0),
            "current_file": current_job.get("current_file", None),
            "start_time": current_job.get("start_time", None)
        })
    else:
        return JSONResponse({
            "status": "idle",
            "files_total": 0,
            "files_completed": 0,
            "current_file": None,
            "start_time": None
        })

@router.post("/reset")
async def reset_processing_state() -> JSONResponse:
    """処理状態を強制リセット"""
    global current_job, cancel_event, processing_pipeline
    
    # 処理状態を強制リセット（ログ削除）
    current_job = None
    cancel_event = None
    
    if processing_pipeline:
        processing_pipeline.abort_flag = {'flag': True}
        processing_pipeline = None
    
    return JSONResponse({
        "message": "処理状態をリセットしました",
        "status": "reset_complete"
    })

@router.post("/cancel")
async def cancel_processing() -> JSONResponse:
    """処理をキャンセル"""
    global current_job, cancel_event, processing_pipeline
    
    if not current_job or current_job.get("status") != "running":
        return JSONResponse({
            "message": "キャンセル対象の処理がありません",
            "status": "no_active_job"
        })
    
    # キャンセルフラグを設定
    if cancel_event:
        cancel_event.set()
    
    if processing_pipeline:
        processing_pipeline.abort_flag = {'flag': True}
    
    current_job["status"] = "cancelled"
    
    return JSONResponse({
        "message": "処理のキャンセルを要求しました",
        "status": "cancel_requested"
    })

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
        # デバッグログを削除（うざいため）
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
                fm.size as file_size,
                fb.blob_data
            FROM files_blob fb
            JOIN files_meta fm ON fb.id = fm.blob_id
            WHERE fb.id IN ({placeholders})
            ORDER BY fb.stored_at DESC
        """)
        
        files_raw = connection.execute(query, params).fetchall()
        # DB取得ファイル数ログを削除（うざいため）
        
        # DB blobから一時ファイルを作成
        files = []
        import tempfile
        import os
        from pathlib import Path
        
        for file_row in files_raw:
            # 一時ファイル作成
            file_ext = Path(file_row.file_name).suffix
            temp_fd, temp_path = tempfile.mkstemp(suffix=file_ext, prefix=f"ingest_{file_row.file_id}_")
            
            try:
                # blobデータを一時ファイルに書き込み
                with os.fdopen(temp_fd, 'wb') as temp_file:
                    temp_file.write(file_row.blob_data)
                
                files.append({
                    'file_id': file_row.file_id,
                    'file_name': file_row.file_name,
                    'file_path': temp_path,
                    'file_size': file_row.file_size,
                    'temp_file': True  # 一時ファイルマーク
                })
                
                # 一時ファイル作成（ログ削除）
                
            except Exception as e:
                # エラー時はファイルを閉じる
                try:
                    os.close(temp_fd)
                except:
                    pass
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
                raise e
        
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
        
        # 処理開始（ログ削除）
        
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
        return JSONResponse(content={"message": "実行中の処理がありません", "status": "no_running_job"})
    
    if cancel_event:
        cancel_event.set()
        # 処理キャンセル要求（ログ削除）
    
    # パイプラインキャンセル
    if processing_pipeline:
        processing_pipeline.cancel_processing()
    
    # 状態をリセット
    current_job = None
    cancel_event = None
    processing_pipeline = None
    # 処理状態リセット完了（ログ削除）
    
    return JSONResponse(content={"message": "処理をキャンセルしました", "status": "cancelled"})



@router.get("/stream")
async def progress_stream(request: Request) -> StreamingResponse:
    """SSEで進捗をストリーミング（実際の処理エンジン使用）"""
    global current_job, cancel_event, processing_pipeline
    
    # ジョブがない場合は待機（SSE接続維持）
    # フロントエンドは処理開始前に接続するため
    
    # SSE接続開始（ログ削除）
    
    async def event_generator() -> AsyncGenerator[str, None]:
        global processing_pipeline
        
        try:
            # SSE接続確立通知
            yield f"data: {json.dumps({'type': 'connected', 'message': 'SSE接続確立'})}\n\n"
            
            # ジョブが開始されるまで待機
            while not current_job:
                if await request.is_disconnected():
                    return
                await asyncio.sleep(0.5)
            
            # 処理パイプライン初期化
            processing_pipeline = ProcessingPipeline()
            # 処理パイプライン初期化完了（ログ削除）
            
            # クライアント切断監視
            async def monitor_disconnect():
                while current_job and current_job.get("status") == "running":
                    if await request.is_disconnected():
                        # クライアント切断検知（ログ削除）
                        if processing_pipeline:
                            processing_pipeline.cancel_processing()
                        break
                    await asyncio.sleep(0.5)
            
            # キャンセル監視
            async def monitor_cancellation():
                while current_job and current_job.get("status") == "running":
                    if cancel_event and cancel_event.is_set():
                        # キャンセル要求検知（ログ削除）
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
            
            # ファイル処理開始（ログ削除）
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
                # DEBUG-SSE イベント送信（ログ削除）
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
                    
                # 一時ファイルクリーンアップ
                _cleanup_temp_files(current_job.get("files", []))
            
        except Exception as e:
            LOGGER.error(f"SSE処理エラー: {e}")
            yield f"data: {json.dumps({'type': 'error', 'message': f'処理エラー: {str(e)}'})}\n\n"
            
            if current_job:
                current_job["status"] = "error"
                # エラー時も一時ファイルクリーンアップ
                _cleanup_temp_files(current_job.get("files", []))
    
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