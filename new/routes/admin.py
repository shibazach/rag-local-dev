# new/routes/admin.py
# 管理画面API（システム監視・ログ機能追加）

import os
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
from pathlib import Path
from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse

from ..auth import User, require_admin
from ..config import LOGGER
from ..services.queue_service import QueueService
from ..services.search_service import SearchService
from ..main import templates

router = APIRouter(prefix="/admin", tags=["admin"])

# メモリ内ログストレージ（簡易実装）
class LogManager:
    def __init__(self, max_logs=1000):
        self.logs = []
        self.max_logs = max_logs
        self.error_count = 0
        self.warning_count = 0
    
    def add_log(self, level: str, message: str, timestamp: datetime = None):
        """ログエントリを追加"""
        if timestamp is None:
            timestamp = datetime.now()
        
        log_entry = {
            "timestamp": timestamp.isoformat(),
            "level": level,
            "message": message
        }
        
        self.logs.append(log_entry)
        
        # カウンタ更新
        if level == "ERROR":
            self.error_count += 1
        elif level == "WARNING":
            self.warning_count += 1
        
        # 最大数を超えたら古いものを削除
        if len(self.logs) > self.max_logs:
            removed = self.logs.pop(0)
            if removed["level"] == "ERROR":
                self.error_count = max(0, self.error_count - 1)
            elif removed["level"] == "WARNING":
                self.warning_count = max(0, self.warning_count - 1)
    
    def get_recent_logs(self, limit: int = 100, level_filter: str = None) -> List[Dict]:
        """最新ログを取得"""
        logs = self.logs
        if level_filter:
            logs = [log for log in logs if log["level"] == level_filter]
        return logs[-limit:]
    
    def get_error_summary(self) -> Dict[str, Any]:
        """エラーサマリー取得"""
        recent_errors = [log for log in self.logs[-50:] if log["level"] == "ERROR"]
        recent_warnings = [log for log in self.logs[-50:] if log["level"] == "WARNING"]
        
        return {
            "total_errors": self.error_count,
            "total_warnings": self.warning_count,
            "recent_errors": len(recent_errors),
            "recent_warnings": len(recent_warnings),
            "last_error": recent_errors[-1] if recent_errors else None,
            "last_warning": recent_warnings[-1] if recent_warnings else None
        }

# グローバルログマネージャー
log_manager = LogManager()

# カスタムログハンドラーでメモリに保存
class MemoryLogHandler(logging.Handler):
    def emit(self, record):
        try:
            log_manager.add_log(
                level=record.levelname,
                message=self.format(record),
                timestamp=datetime.fromtimestamp(record.created)
            )
        except Exception:
            pass

# ログハンドラーを設定
memory_handler = MemoryLogHandler()
memory_handler.setLevel(logging.INFO)  # INFOレベルから記録
formatter = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
memory_handler.setFormatter(formatter)
LOGGER.addHandler(memory_handler)

# 初期ログ追加
log_manager.add_log("INFO", "システム起動完了")
log_manager.add_log("INFO", "ログ監視機能が有効になりました")
LOGGER.info("管理画面ログ機能が初期化されました")

@router.get("", response_class=HTMLResponse)
async def admin_dashboard(
    request: Request,
    current_user: User = Depends(require_admin)
):
    """管理画面ダッシュボード"""
    try:
        queue_service = QueueService()
        search_service = SearchService()
        
        # システム統計情報
        pending_count = queue_service.get_pending_count()
        search_stats = search_service.get_stats()
        error_summary = log_manager.get_error_summary()
        
        return templates.TemplateResponse("admin.html", {
            "request": request,
            "user": current_user,
            "pending_count": pending_count,
            "search_stats": search_stats,
            "error_summary": error_summary
        })
    except Exception as e:
        LOGGER.error(f"管理画面エラー: {e}")
        raise HTTPException(status_code=500, detail="管理画面の読み込みに失敗しました")

@router.get("/logs")
async def get_system_logs(
    limit: int = 100,
    level: str = None,
    current_user: User = Depends(require_admin)
):
    """システムログ取得API"""
    try:
        logs = log_manager.get_recent_logs(limit=limit, level_filter=level)
        return {
            "logs": logs,
            "summary": log_manager.get_error_summary()
        }
    except Exception as e:
        LOGGER.error(f"ログ取得エラー: {e}")
        raise HTTPException(status_code=500, detail="ログの取得に失敗しました")

@router.get("/system/status")
async def get_system_status(
    current_user: User = Depends(require_admin)
):
    """システム状態監視API"""
    try:
        import psutil
        import platform
        
        # システム情報
        system_info = {
            "platform": platform.platform(),
            "python_version": platform.python_version(),
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage('/').percent,
            "uptime": datetime.now().isoformat()
        }
        
        # アプリケーション統計
        queue_service = QueueService()
        app_stats = {
            "pending_queue": queue_service.get_pending_count(),
            "error_count": log_manager.error_count,
            "warning_count": log_manager.warning_count
        }
        
        return {
            "system": system_info,
            "application": app_stats,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        LOGGER.error(f"システム状態取得エラー: {e}")
        # psutilが無い場合の基本情報
        return {
            "system": {
                "platform": "Linux",
                "status": "running"
            },
            "application": {
                "pending_queue": 0,
                "error_count": log_manager.error_count,
                "warning_count": log_manager.warning_count
            },
            "timestamp": datetime.now().isoformat()
        }

@router.post("/logs/clear")
async def clear_logs(
    current_user: User = Depends(require_admin)
):
    """ログクリアAPI"""
    try:
        log_manager.logs.clear()
        log_manager.error_count = 0
        log_manager.warning_count = 0
        
        LOGGER.info(f"管理者 {current_user.username} がログをクリアしました")
        return {"success": True, "message": "ログをクリアしました"}
    except Exception as e:
        LOGGER.error(f"ログクリアエラー: {e}")
        raise HTTPException(status_code=500, detail="ログのクリアに失敗しました") 