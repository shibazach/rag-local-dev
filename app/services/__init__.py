"""
サービスレイヤー - Prototype統合版
各種ビジネスロジックサービス
"""

from .stats_service import get_system_stats
from .multimodal_service import MultimodalLLMService
from .file_service import FileService, get_file_service
# from .chat_service import ChatService, get_chat_service  # SQLAlchemy依存のため一時的にコメントアウト
# from .processing_service import ProcessingService, get_processing_service  # SQLAlchemy依存のため一時的にコメントアウト
from .admin_service import AdminService, get_admin_service

__all__ = [
    # 既存サービス
    'get_system_stats',
    'MultimodalLLMService',
    # 新規統合サービス
    'FileService',
    'get_file_service',
    # 'ChatService',   # SQLAlchemy依存のため一時的にコメントアウト
    # 'get_chat_service',  # SQLAlchemy依存のため一時的にコメントアウト
    # 'ProcessingService',  # SQLAlchemy依存のため一時的にコメントアウト
    # 'get_processing_service',  # SQLAlchemy依存のため一時的にコメントアウト
    'AdminService',
    'get_admin_service'
]