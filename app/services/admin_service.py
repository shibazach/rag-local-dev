"""
管理サービス - Prototype統合版
システム管理・統計・設定管理サービス
"""

import asyncio
import psutil
import platform
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.config import config, logger

class AdminService:
    """管理機能サービス"""
    
    def __init__(self, db_session: AsyncSession = None):
        """
        Args:
            db_session: データベースセッション（オプショナル）
        """
        self.db = db_session
    
    async def get_system_info(self) -> Dict[str, Any]:
        """
        システム情報取得
        
        Returns:
            システム情報
        """
        try:
            # CPU情報
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            
            # メモリ情報
            memory = psutil.virtual_memory()
            
            # ディスク情報
            disk = psutil.disk_usage('/')
            
            # Python情報
            python_version = platform.python_version()
            
            # CUDA情報
            cuda_available = config.CUDA_AVAILABLE
            cuda_version = "N/A"
            if cuda_available:
                try:
                    import torch
                    cuda_version = torch.version.cuda
                except:
                    pass
            
            return {
                "system": {
                    "platform": platform.system(),
                    "platform_version": platform.version(),
                    "architecture": platform.machine(),
                    "hostname": platform.node(),
                    "python_version": python_version
                },
                "cpu": {
                    "percent": cpu_percent,
                    "count": cpu_count,
                    "count_logical": psutil.cpu_count(logical=True)
                },
                "memory": {
                    "total": memory.total,
                    "available": memory.available,
                    "percent": memory.percent,
                    "used": memory.used
                },
                "disk": {
                    "total": disk.total,
                    "used": disk.used,
                    "free": disk.free,
                    "percent": disk.percent
                },
                "gpu": {
                    "cuda_available": cuda_available,
                    "cuda_version": cuda_version
                },
                "app": {
                    "version": config.APP_VERSION,
                    "environment": config.ENVIRONMENT,
                    "debug": config.DEBUG
                }
            }
            
        except Exception as e:
            logger.error(f"システム情報取得エラー: {e}")
            raise
    
    async def get_statistics(self) -> Dict[str, Any]:
        """
        統計情報取得
        
        Returns:
            統計情報
        """
        # TODO: データベースから統計取得（Phase 2で実装）
        # 現在はモックデータを返す
        return {
            "files": {
                "total": 150,
                "today": 5,
                "this_week": 23,
                "this_month": 87
            },
            "storage": {
                "total_size": 1024 * 1024 * 1024,  # 1GB
                "files_by_type": {
                    "pdf": 80,
                    "docx": 40,
                    "txt": 20,
                    "csv": 10
                }
            },
            "processing": {
                "total_jobs": 200,
                "completed": 180,
                "failed": 15,
                "in_progress": 5
            },
            "users": {
                "total": 25,
                "active_today": 8,
                "active_this_week": 15
            }
        }
    
    async def get_recent_activities(
        self,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        最近のアクティビティ取得
        
        Args:
            limit: 取得数上限
            
        Returns:
            アクティビティリスト
        """
        # TODO: データベースから取得（Phase 2で実装）
        # 現在はモックデータを返す
        activities = []
        base_time = datetime.utcnow()
        
        for i in range(min(limit, 10)):
            activity_time = base_time - timedelta(minutes=i*10)
            activities.append({
                "id": str(i + 1),
                "type": ["upload", "search", "process", "login"][i % 4],
                "user": f"user{i % 3 + 1}",
                "description": f"アクティビティ {i + 1}",
                "timestamp": activity_time.isoformat()
            })
        
        return activities
    
    async def get_configuration(self) -> Dict[str, Any]:
        """
        現在の設定取得
        
        Returns:
            設定情報
        """
        return {
            "app": {
                "name": config.APP_NAME,
                "version": config.APP_VERSION,
                "environment": config.ENVIRONMENT,
                "debug": config.DEBUG
            },
            "server": {
                "host": config.HOST,
                "port": config.PORT
            },
            "database": {
                "url": config.DATABASE_URL.split("@")[-1] if "@" in config.DATABASE_URL else config.DATABASE_URL
            },
            "ollama": {
                "base_url": config.OLLAMA_BASE_URL,
                "model": config.OLLAMA_MODEL,
                "timeout": config.OLLAMA_TIMEOUT
            },
            "embedding": {
                "default_option": config.DEFAULT_EMBEDDING_OPTION,
                "options": list(config.EMBEDDING_OPTIONS.keys())
            },
            "upload": {
                "max_size_mb": config.MAX_UPLOAD_SIZE // 1024 // 1024,
                "allowed_extensions": config.ALLOWED_EXTENSIONS
            }
        }
    
    async def update_configuration(
        self,
        section: str,
        settings: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        設定更新
        
        Args:
            section: 設定セクション
            settings: 更新する設定
            
        Returns:
            更新結果
        """
        # TODO: 実際の設定更新実装（Phase 2）
        logger.info(f"設定更新リクエスト: {section} = {settings}")
        
        return {
            "status": "success",
            "message": "設定を更新しました（開発中のため実際には反映されません）"
        }
    
    async def get_logs(
        self,
        level: str = "INFO",
        limit: int = 100,
        search: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        ログ取得
        
        Args:
            level: ログレベル
            limit: 取得数上限
            search: 検索文字列
            
        Returns:
            ログエントリーリスト
        """
        # TODO: 実際のログファイル読み込み（Phase 2）
        logs = []
        base_time = datetime.utcnow()
        
        for i in range(min(limit, 20)):
            log_time = base_time - timedelta(seconds=i*30)
            logs.append({
                "timestamp": log_time.isoformat(),
                "level": ["INFO", "WARNING", "ERROR", "DEBUG"][i % 4],
                "logger": "prototypes.services",
                "message": f"ログメッセージ {i + 1}"
            })
        
        return logs
    
    async def export_data(
        self,
        export_type: str = "statistics"
    ) -> Dict[str, Any]:
        """
        データエクスポート
        
        Args:
            export_type: エクスポートタイプ
            
        Returns:
            エクスポート結果
        """
        if export_type == "statistics":
            data = await self.get_statistics()
        elif export_type == "configuration":
            data = await self.get_configuration()
        elif export_type == "system_info":
            data = await self.get_system_info()
        else:
            raise ValueError(f"未対応のエクスポートタイプ: {export_type}")
        
        return {
            "status": "success",
            "export_type": export_type,
            "timestamp": datetime.utcnow().isoformat(),
            "data": data
        }

# サービスインスタンス作成ヘルパー
def get_admin_service(db_session: AsyncSession = None) -> AdminService:
    """管理サービスインスタンス取得"""
    return AdminService(db_session)