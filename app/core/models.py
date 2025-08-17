"""
アップロードログモデル定義
"""
from sqlalchemy import Column, String, Text, Integer, DateTime, JSON, Enum
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declarative_base
import uuid
import enum

Base = declarative_base()

class UploadStatus(str, enum.Enum):
    """アップロードステータス"""
    PENDING = "pending"
    UPLOADING = "uploading"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    DUPLICATE = "duplicate"

class UploadLog(Base):
    """アップロードログテーブル"""
    __tablename__ = "upload_logs"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String(36), nullable=False, index=True)  # セッションID（バッチアップロードのグループ化）
    file_name = Column(String(255), nullable=False)
    file_size = Column(Integer, nullable=False)
    status = Column(Enum(UploadStatus), nullable=False, default=UploadStatus.PENDING)
    progress = Column(Integer, default=0)  # アップロード進捗（0-100）
    message = Column(Text)  # 詳細メッセージ
    error_detail = Column(Text)  # エラー詳細
    metadata = Column(JSON, default={})  # 追加メタデータ
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # インデックス
    __table_args__ = (
        {"mysql_charset": "utf8mb4"},
    )


