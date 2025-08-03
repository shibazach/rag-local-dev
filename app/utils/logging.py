"""
ログ管理
Centralized logging configuration and utilities
"""

import logging
import logging.handlers
import sys
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
import traceback

from app.config import config


class JSONFormatter(logging.Formatter):
    """JSON形式ログフォーマッター"""
    
    def format(self, record: logging.LogRecord) -> str:
        """ログをJSON形式でフォーマット"""
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # 追加フィールド
        if hasattr(record, 'user_id'):
            log_data["user_id"] = record.user_id
        
        if hasattr(record, 'request_id'):
            log_data["request_id"] = record.request_id
        
        if hasattr(record, 'processing_job_id'):
            log_data["processing_job_id"] = record.processing_job_id
        
        # 例外情報
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": traceback.format_exception(*record.exc_info)
            }
        
        # パフォーマンス情報
        if hasattr(record, 'duration'):
            log_data["duration_ms"] = record.duration
        
        if hasattr(record, 'status_code'):
            log_data["status_code"] = record.status_code
        
        return json.dumps(log_data, ensure_ascii=False)


class StructuredLogger:
    """構造化ログ出力"""
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        
    def info(self, message: str, **kwargs):
        """情報ログ"""
        self._log(logging.INFO, message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """警告ログ"""
        self._log(logging.WARNING, message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """エラーログ"""
        self._log(logging.ERROR, message, **kwargs)
    
    def debug(self, message: str, **kwargs):
        """デバッグログ"""
        self._log(logging.DEBUG, message, **kwargs)
    
    def critical(self, message: str, **kwargs):
        """重要ログ"""
        self._log(logging.CRITICAL, message, **kwargs)
    
    def _log(self, level: int, message: str, **kwargs):
        """ログ出力実行"""
        record = self.logger.makeRecord(
            name=self.logger.name,
            level=level,
            fn="",
            lno=0,
            msg=message,
            args=(),
            exc_info=None
        )
        
        # 追加属性設定
        for key, value in kwargs.items():
            setattr(record, key, value)
        
        self.logger.handle(record)


class SecurityLogger:
    """セキュリティ関連ログ"""
    
    def __init__(self):
        self.logger = StructuredLogger("security")
    
    def login_attempt(self, username: str, success: bool, ip_address: str, user_agent: str = None):
        """ログイン試行ログ"""
        self.logger.info(
            f"ログイン{'成功' if success else '失敗'}: {username}",
            event_type="login_attempt",
            username=username,
            success=success,
            ip_address=ip_address,
            user_agent=user_agent
        )
    
    def permission_denied(self, user_id: str, resource: str, action: str, ip_address: str):
        """権限拒否ログ"""
        self.logger.warning(
            f"権限拒否: ユーザー{user_id}が{resource}への{action}を試行",
            event_type="permission_denied",
            user_id=user_id,
            resource=resource,
            action=action,
            ip_address=ip_address
        )
    
    def suspicious_activity(self, description: str, user_id: str = None, ip_address: str = None):
        """不審な活動ログ"""
        self.logger.warning(
            f"不審な活動: {description}",
            event_type="suspicious_activity",
            user_id=user_id,
            ip_address=ip_address
        )
    
    def data_access(self, user_id: str, resource_type: str, resource_id: str, action: str):
        """データアクセスログ"""
        self.logger.info(
            f"データアクセス: {user_id}が{resource_type}#{resource_id}に{action}",
            event_type="data_access",
            user_id=user_id,
            resource_type=resource_type,
            resource_id=resource_id,
            action=action
        )


class PerformanceLogger:
    """パフォーマンス関連ログ"""
    
    def __init__(self):
        self.logger = StructuredLogger("performance")
    
    def api_request(
        self,
        method: str,
        path: str,
        status_code: int,
        duration: float,
        user_id: str = None,
        request_id: str = None
    ):
        """APIリクエストログ"""
        self.logger.info(
            f"API {method} {path} - {status_code} ({duration:.3f}s)",
            event_type="api_request",
            method=method,
            path=path,
            status_code=status_code,
            duration=duration * 1000,  # ミリ秒
            user_id=user_id,
            request_id=request_id
        )
    
    def processing_job(
        self,
        job_id: str,
        file_count: int,
        duration: float,
        success_count: int,
        error_count: int,
        user_id: str = None
    ):
        """処理ジョブログ"""
        self.logger.info(
            f"処理ジョブ完了: {job_id} - {success_count}/{file_count}成功 ({duration:.1f}s)",
            event_type="processing_job",
            processing_job_id=job_id,
            file_count=file_count,
            duration=duration * 1000,
            success_count=success_count,
            error_count=error_count,
            success_rate=success_count / file_count if file_count > 0 else 0,
            user_id=user_id
        )
    
    def database_query(self, query: str, duration: float, rows: int = None):
        """データベースクエリログ"""
        # デバッグレベルでのみ出力（本番では無効化）
        if config.DEBUG:
            self.logger.debug(
                f"DB クエリ実行 ({duration:.3f}s)",
                event_type="database_query",
                query=query[:200] + "..." if len(query) > 200 else query,
                duration=duration * 1000,
                rows=rows
            )


class AuditLogger:
    """監査ログ"""
    
    def __init__(self):
        self.logger = StructuredLogger("audit")
    
    def user_action(
        self,
        user_id: str,
        action: str,
        resource_type: str,
        resource_id: str = None,
        details: Dict[str, Any] = None,
        ip_address: str = None
    ):
        """ユーザーアクション監査"""
        message = f"ユーザーアクション: {user_id} - {action}"
        if resource_type:
            message += f" ({resource_type}"
            if resource_id:
                message += f"#{resource_id}"
            message += ")"
        
        self.logger.info(
            message,
            event_type="user_action",
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
            ip_address=ip_address
        )
    
    def system_change(
        self,
        admin_user_id: str,
        change_type: str,
        before_value: Any = None,
        after_value: Any = None,
        description: str = None
    ):
        """システム変更監査"""
        self.logger.info(
            f"システム変更: {change_type} by {admin_user_id}",
            event_type="system_change",
            admin_user_id=admin_user_id,
            change_type=change_type,
            before_value=before_value,
            after_value=after_value,
            description=description
        )
    
    def file_operation(
        self,
        user_id: str,
        operation: str,
        file_id: str,
        filename: str,
        file_size: int = None,
        checksum: str = None
    ):
        """ファイル操作監査"""
        self.logger.info(
            f"ファイル操作: {operation} - {filename}",
            event_type="file_operation",
            user_id=user_id,
            operation=operation,
            file_id=file_id,
            filename=filename,
            file_size=file_size,
            checksum=checksum
        )


def setup_logging():
    """ログ設定初期化"""
    # ログディレクトリ作成
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # ルートロガー設定
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, config.LOG_LEVEL.upper()))
    
    # 既存ハンドラー削除
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # コンソールハンドラー
    console_handler = logging.StreamHandler(sys.stdout)
    if config.DEBUG:
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(console_formatter)
    else:
        console_handler.setFormatter(JSONFormatter())
    
    root_logger.addHandler(console_handler)
    
    # ファイルハンドラー（ローテーション）
    file_handler = logging.handlers.RotatingFileHandler(
        log_dir / "app.log",
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setFormatter(JSONFormatter())
    root_logger.addHandler(file_handler)
    
    # セキュリティログ専用ハンドラー
    security_logger = logging.getLogger("security")
    security_handler = logging.handlers.RotatingFileHandler(
        log_dir / "security.log",
        maxBytes=10 * 1024 * 1024,
        backupCount=10,
        encoding='utf-8'
    )
    security_handler.setFormatter(JSONFormatter())
    security_logger.addHandler(security_handler)
    
    # 監査ログ専用ハンドラー
    audit_logger = logging.getLogger("audit")
    audit_handler = logging.handlers.RotatingFileHandler(
        log_dir / "audit.log",
        maxBytes=10 * 1024 * 1024,
        backupCount=20,  # 長期保存
        encoding='utf-8'
    )
    audit_handler.setFormatter(JSONFormatter())
    audit_logger.addHandler(audit_handler)
    
    # サードパーティライブラリのログレベル調整
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)


# グローバルロガーインスタンス
security_log = SecurityLogger()
performance_log = PerformanceLogger()
audit_log = AuditLogger()


# ログ初期化実行
setup_logging()