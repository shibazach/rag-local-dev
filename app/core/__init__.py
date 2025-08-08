"""
コア機能モジュール - Prototype統合版
データベース・共通機能（SQLAlchemy削除済み）
"""

# db_simpleを使用する新しい実装のみ残す
# from .db_handler import FileDBHandler  # SQLAlchemy依存のため削除

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
    # スキーマ
    'UploadResponse',
    'BatchUploadResponse',
    'UploadStatusResponse',
    'FileInfoResponse',
    'FileListResponse',
    'SuccessResponse',
    'ErrorResponse'
]
