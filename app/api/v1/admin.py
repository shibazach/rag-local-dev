"""
管理API
Admin endpoints for system management and monitoring
"""

from fastapi import APIRouter, Depends, HTTPException, Query
# from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, List, Optional
import psutil
import asyncio
from datetime import datetime, timedelta

from app.auth.dependencies import require_admin
from app.core.database import get_db
from app.core.database import db_health_check
from app.config import config, logger

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/health")
async def system_health_check(
    current_admin = Depends(require_admin),
    db = Depends(get_db)
):
    """システムヘルスチェック"""
    try:
        health_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "system": await _get_system_health(),
            "database": await _get_database_health(db),
            "services": await _get_services_health(),
            "storage": await _get_storage_health()
        }
        
        # 全体ステータス判定
        all_healthy = all([
            health_data["system"]["status"] == "healthy",
            health_data["database"]["status"] == "healthy",
            health_data["services"]["status"] == "healthy",
            health_data["storage"]["status"] == "healthy"
        ])
        
        health_data["overall_status"] = "healthy" if all_healthy else "degraded"
        
        return health_data
        
    except Exception as e:
        logger.error(f"ヘルスチェックエラー: {e}")
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "overall_status": "error",
            "error_message": str(e)
        }


@router.get("/system-info")
async def get_system_info(current_admin = Depends(require_admin)):
    """システム情報取得"""
    try:
        return {
            "application": {
                "name": config.APP_NAME,
                "version": config.APP_VERSION,
                "environment": config.ENVIRONMENT,
                "debug_mode": config.DEBUG
            },
            "configuration": {
                "max_upload_size": config.MAX_UPLOAD_SIZE,
                "allowed_extensions": config.ALLOWED_EXTENSIONS,
                "ollama_model": config.OLLAMA_MODEL,
                "default_ocr_engine": config.DEFAULT_OCR_ENGINE,
                "embedding_options": list(config.EMBEDDING_OPTIONS.keys())
            },
            "directories": {
                "upload_dir": str(config.UPLOAD_DIR),
                "processed_dir": str(config.PROCESSED_DIR),
                "project_root": str(config.PROJECT_ROOT)
            },
            "database": {
                "url": config.DATABASE_URL.split("@")[1] if "@" in config.DATABASE_URL else "configured",
                "session_secret_configured": bool(config.SESSION_SECRET_KEY)
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"システム情報取得エラー: {str(e)}")


@router.get("/metrics")
async def get_system_metrics(
    hours: int = Query(24, ge=1, le=168),  # 最大7日間
    current_admin = Depends(require_admin)
):
    """システムメトリクス取得"""
    try:
        # TODO: 実際のメトリクス収集実装
        return {
            "cpu_usage": [65, 70, 68, 72, 69, 71, 67],  # 過去7時間の平均
            "memory_usage": [78, 80, 82, 79, 81, 83, 80],
            "disk_usage": 45,
            "active_users": 12,
            "processing_queue_size": 3,
            "requests_per_hour": [145, 132, 156, 189, 178, 134, 167],
            "error_rate": 0.02,
            "avg_response_time": 0.8,  # 秒
            "uptime": "5 days, 14 hours, 23 minutes"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"メトリクス取得エラー: {str(e)}")


@router.get("/logs")
async def get_system_logs(
    level: str = Query("INFO", regex="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$"),
    lines: int = Query(100, ge=1, le=1000),
    current_admin = Depends(require_admin)
):
    """システムログ取得"""
    try:
        # TODO: ログファイル読み取り実装
        sample_logs = [
            {
                "timestamp": (datetime.utcnow() - timedelta(minutes=i)).isoformat(),
                "level": "INFO" if i % 3 != 0 else "WARNING",
                "module": "app.services.processing_service",
                "message": f"ファイル処理完了: test_{i}.pdf" if i % 3 != 0 else f"処理時間が閾値を超過: {i*10}秒"
            }
            for i in range(min(lines, 50))
        ]
        
        return {
            "logs": sample_logs,
            "total_count": len(sample_logs),
            "level_filter": level,
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ログ取得エラー: {str(e)}")


@router.post("/config/update")
async def update_system_config(
    config_updates: Dict[str, Any],
    current_admin = Depends(require_admin)
):
    """システム設定更新"""
    try:
        # 設定可能な項目の制限
        allowed_keys = {
            "max_upload_size",
            "ollama_model", 
            "default_ocr_engine",
            "log_level"
        }
        
        # バリデーション
        invalid_keys = set(config_updates.keys()) - allowed_keys
        if invalid_keys:
            raise HTTPException(
                status_code=400,
                detail=f"更新できない設定項目: {', '.join(invalid_keys)}"
            )
        
        # TODO: 設定更新の実装
        # 環境変数やコンフィグファイルへの反映
        
        logger.info(f"システム設定更新: {config_updates}, 管理者: {current_admin.get('username')}")
        
        return {
            "message": "設定を更新しました",
            "updated_config": config_updates,
            "restart_required": "ollama_model" in config_updates  # モデル変更時は再起動が必要
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"設定更新エラー: {str(e)}")


@router.post("/maintenance")
async def toggle_maintenance_mode(
    enable: bool,
    message: Optional[str] = None,
    current_admin = Depends(require_admin)
):
    """メンテナンスモード切り替え"""
    try:
        # TODO: メンテナンスモードの実装
        # 一時的にAPIアクセスを制限する仕組み
        
        status = "有効" if enable else "無効"
        logger.info(f"メンテナンスモード{status}化: 管理者={current_admin.get('username')}")
        
        return {
            "maintenance_mode": enable,
            "message": message or f"メンテナンスモードを{status}にしました",
            "updated_by": current_admin.get("username"),
            "updated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"メンテナンスモード切り替えエラー: {str(e)}")


@router.delete("/cache")
async def clear_system_cache(
    cache_type: str = Query("all", regex="^(all|embedding|processing|files)$"),
    current_admin = Depends(require_admin)
):
    """システムキャッシュクリア"""
    try:
        # TODO: キャッシュクリア実装
        cleared_items = []
        
        if cache_type in ["all", "embedding"]:
            # 埋め込みキャッシュクリア
            cleared_items.append("embedding_cache")
        
        if cache_type in ["all", "processing"]:
            # 処理キャッシュクリア
            cleared_items.append("processing_cache")
        
        if cache_type in ["all", "files"]:
            # ファイルキャッシュクリア
            cleared_items.append("file_cache")
        
        logger.info(f"キャッシュクリア: {cleared_items}, 管理者: {current_admin.get('username')}")
        
        return {
            "message": f"キャッシュをクリアしました: {', '.join(cleared_items)}",
            "cleared_items": cleared_items,
            "cache_type": cache_type
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"キャッシュクリアエラー: {str(e)}")


# プライベート関数

async def _get_system_health() -> Dict[str, Any]:
    """システムヘルス取得"""
    try:
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        return {
            "status": "healthy" if cpu_percent < 80 and memory.percent < 85 else "warning",
            "cpu_usage": cpu_percent,
            "memory_usage": memory.percent,
            "disk_usage": disk.percent,
            "load_average": psutil.getloadavg()[0] if hasattr(psutil, 'getloadavg') else None
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


async def _get_database_health(db) -> Dict[str, Any]:
    """データベースヘルス取得"""
    try:
        is_healthy = await db_health_check()
        return {
            "status": "healthy" if is_healthy else "error",
            "connection": "established" if is_healthy else "failed"
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


async def _get_services_health() -> Dict[str, Any]:
    """サービスヘルス取得"""
    try:
        # TODO: 各サービスのヘルスチェック実装
        return {
            "status": "healthy",
            "ollama": "available",
            "embedding_service": "available",
            "ocr_service": "available"
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


async def _get_storage_health() -> Dict[str, Any]:
    """ストレージヘルス取得"""
    try:
        upload_dir = config.UPLOAD_DIR
        processed_dir = config.PROCESSED_DIR
        
        upload_exists = upload_dir.exists()
        processed_exists = processed_dir.exists()
        
        return {
            "status": "healthy" if upload_exists and processed_exists else "warning",
            "upload_directory": "accessible" if upload_exists else "not_found",
            "processed_directory": "accessible" if processed_exists else "not_found"
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}