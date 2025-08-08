"""
コア機能モジュール - Prototype統合版
データベース・モデル・共通機能
"""

from .database import (
    Base,
    engine,
    # async_engine,  # 非同期版は将来実装
    SessionLocal,
    # AsyncSessionLocal,  # 非同期版は将来実装
    get_db,
    # get_async_db,  # 非同期版は将来実装
    get_db_session,
    # get_async_db_session,  # 非同期版は将来実装
    init_database,
    health_check,
    # async_health_check,  # 非同期版は将来実装
    get_database_info
)

from .models import (
    # ファイル管理モデル（Files3兄弟）
    FilesBlob,
    FilesMeta,
    FilesText,
    # 埋め込みモデル
    FileEmbedding,
    # 画像管理モデル
    FilesImage
)

from .db_handler import FileDBHandler

from .schemas import (
    UploadResponse,
    BatchUploadResponse,
    UploadStatusResponse,
    FileInfoResponse,
    FileListResponse,
    SuccessResponse,
    ErrorResponse
)

__all__ = [
    # データベース関連
    'Base',
    'engine',
    'SessionLocal',
    'get_db',
    'get_db_session',
    'init_database',
    'health_check',
    'get_database_info',
    # モデル
    'FilesBlob',
    'FilesMeta',
    'FilesText',
    'FileEmbedding',
    'FilesImage',
    # ハンドラ
    'FileDBHandler',
    # スキーマ
    'UploadResponse',
    'BatchUploadResponse',
    'UploadStatusResponse',
    'FileInfoResponse',
    'FileListResponse',
    'SuccessResponse',
    'ErrorResponse'
]
