"""
データベースモデル定義
SQLAlchemy models for the RAG system
"""

import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Boolean, JSON, LargeBinary, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
# from sqlalchemy.dialects.postgresql import ARRAY  # SQLite非対応のため削除
try:
    from sqlalchemy.dialects.postgresql import UUID
except ImportError:
    from sqlalchemy import String
    UUID = lambda as_uuid=True: String(36)

from .database import Base

# ========== メインファイル管理モデル ==========

class FilesBlob(Base):
    """
    ファイルバイナリ格納テーブル（主テーブル）
    Stores actual file binary data with checksum for deduplication
    """
    __tablename__ = "files_blob"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    checksum = Column(String, nullable=False, unique=True, index=True)
    blob_data = Column(LargeBinary, nullable=False)
    stored_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # リレーション
    meta = relationship("FilesMeta", back_populates="blob", uselist=False, cascade="all, delete-orphan")
    text = relationship("FilesText", back_populates="blob", uselist=False, cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<FilesBlob(id={self.id}, checksum={self.checksum[:8]}...)>"

class FilesMeta(Base):
    """
    ファイルメタ情報テーブル（1:1対応）
    Stores file metadata and processing status
    """
    __tablename__ = "files_meta"
    
    blob_id = Column(UUID(as_uuid=True), ForeignKey("files_blob.id", ondelete="CASCADE"), primary_key=True)
    file_name = Column(String, nullable=False, index=True)
    original_filename = Column(String, nullable=False)
    mime_type = Column(String, nullable=False)
    file_size = Column(Integer, nullable=False)
    
    # 処理ステータス
    processing_status = Column(String, default="uploaded", index=True)  # uploaded, processing, completed, failed
    processing_stage = Column(String, default="uploaded")  # uploaded, ocr, llm, embedding, indexed
    
    # メタデータ
    file_metadata = Column(JSON)  # ページ数、言語、作成者等
    processing_metadata = Column(JSON)  # 処理時間、エラー情報等
    
    # タイムスタンプ
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    processed_at = Column(DateTime(timezone=True))
    
    # リレーション
    blob = relationship("FilesBlob", back_populates="meta")
    
    @property
    def page_count(self) -> Optional[int]:
        """ファイルのページ数を取得"""
        if self.file_metadata and isinstance(self.file_metadata, dict):
            return self.file_metadata.get('page_count')
        return None
    
    @property
    def is_processed(self) -> bool:
        """処理完了フラグ"""
        return self.processing_status == "completed"
    
    def __repr__(self):
        return f"<FilesMeta(id={self.blob_id}, name={self.file_name}, status={self.processing_status})>"

class FilesText(Base):
    """
    ファイルテキスト格納テーブル（1:1対応）
    Stores extracted and refined text content
    """
    __tablename__ = "files_text"
    
    blob_id = Column(UUID(as_uuid=True), ForeignKey("files_blob.id", ondelete="CASCADE"), primary_key=True)
    
    # テキストデータ
    raw_text = Column(Text)  # OCR抽出生テキスト
    refined_text = Column(Text)  # LLM精緻化テキスト
    
    # 品質情報
    quality_score = Column(Float, default=0.0)  # テキスト品質スコア
    confidence_score = Column(Float, default=0.0)  # OCR信頼度
    
    # 分析情報
    language = Column(String, default="ja")
    word_count = Column(Integer, default=0)
    character_count = Column(Integer, default=0)
    
    # 構造化データ
    text_chunks = Column(JSON)  # チャンク分割されたテキスト
    extracted_entities = Column(JSON)  # 抽出エンティティ
    tags = Column(JSON, server_default='[]')  # タグ情報（JSON配列）
    
    # タイムスタンプ
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # リレーション
    blob = relationship("FilesBlob", back_populates="text")
    
    def __repr__(self):
        return f"<FilesText(id={self.blob_id}, quality={self.quality_score}, words={self.word_count})>"

# ========== ベクトル検索モデル ==========

class FileEmbedding(Base):
    """
    ファイル埋め込みベクトルテーブル
    Stores embeddings for semantic search
    """
    __tablename__ = "file_embeddings"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    blob_id = Column(UUID(as_uuid=True), ForeignKey("files_blob.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # 埋め込み情報
    chunk_index = Column(Integer, nullable=False)  # チャンクインデックス
    chunk_text = Column(Text, nullable=False)  # チャンクテキスト
    embedding_vector = Column(JSON, nullable=False)  # 埋め込みベクトル
    
    # メタデータ
    model_name = Column(String, nullable=False)  # 埋め込みモデル名
    vector_dimension = Column(Integer, nullable=False)  # ベクトル次元
    
    # タイムスタンプ
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<FileEmbedding(id={self.id}, blob_id={self.blob_id}, chunk={self.chunk_index})>"

# ========== ユーザー・認証モデル ==========

class User(Base):
    """
    ユーザーテーブル
    User management with SAML preparation
    """
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String, unique=True, nullable=False, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    
    # 認証情報
    password_hash = Column(String)  # ローカル認証用
    password_salt = Column(String)  # ソルト
    
    # SAML準備
    saml_id = Column(String, unique=True, index=True)  # SAML識別子
    external_id = Column(String, unique=True, index=True)  # 外部システムID
    
    # プロフィール
    display_name = Column(String)
    department = Column(String)
    role = Column(String, default="user")  # user, admin, readonly
    
    # フラグ
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    is_verified = Column(Boolean, default=False)
    
    # タイムスタンプ
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_login_at = Column(DateTime(timezone=True))
    
    def __repr__(self):
        return f"<User(id={self.id}, username={self.username}, role={self.role})>"

class UserSession(Base):
    """
    ユーザーセッションテーブル
    Session management for security
    """
    __tablename__ = "user_sessions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    session_token = Column(String, unique=True, nullable=False, index=True)
    
    # セッション情報
    ip_address = Column(String)
    user_agent = Column(String)
    device_info = Column(JSON)
    
    # タイムスタンプ
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False)
    last_activity = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<UserSession(id={self.id}, user_id={self.user_id}, expires={self.expires_at})>"

# ========== 運用・監視モデル ==========

class SystemLog(Base):
    """
    システムログテーブル
    System operation logs
    """
    __tablename__ = "system_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # ログ情報
    level = Column(String, nullable=False, index=True)  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    message = Column(Text, nullable=False)
    category = Column(String, nullable=False, index=True)  # auth, file, search, processing, etc.
    
    # コンテキスト
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)
    session_id = Column(String, index=True)
    request_id = Column(String, index=True)
    
    # 詳細情報
    log_metadata = Column(JSON)  # 追加メタデータ
    stack_trace = Column(Text)  # エラースタックトレース
    
    # タイムスタンプ
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    def __repr__(self):
        return f"<SystemLog(id={self.id}, level={self.level}, category={self.category})>"

class SystemMetrics(Base):
    """
    システムメトリクステーブル
    Performance and usage metrics
    """
    __tablename__ = "system_metrics"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # メトリクス情報
    metric_name = Column(String, nullable=False, index=True)
    metric_value = Column(Float, nullable=False)
    metric_unit = Column(String)  # seconds, bytes, count, etc.
    
    # ディメンション
    dimensions = Column(JSON)  # メトリクス分析用次元
    
    # タイムスタンプ
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    def __repr__(self):
        return f"<SystemMetrics(name={self.metric_name}, value={self.metric_value}, time={self.timestamp})>"