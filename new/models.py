# new/models.py
# データベースモデル定義

import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Boolean, JSON
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID

from .database import Base

class File(Base):
    """ファイル管理テーブル"""
    __tablename__ = "files"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    file_path = Column(String, unique=True, nullable=False, index=True)
    file_name = Column(String, nullable=False)
    file_size = Column(Integer)
    file_type = Column(String)
    user_id = Column(Integer, nullable=False, index=True)
    status = Column(String, default="pending")  # pending, text_extracted, processing, completed, failed
    processing_stage = Column(String, default="uploaded")  # uploaded, text_extracted, vectorized, indexed
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    note = Column(Text)
    file_metadata = Column(JSON)  # ファイルのメタデータ（ページ数、言語等）

class FileText(Base):
    """ファイルテキスト管理テーブル"""
    __tablename__ = "file_texts"
    
    id = Column(Integer, primary_key=True, index=True)
    file_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    raw_text = Column(Text)
    refined_text = Column(Text)
    text_chunks = Column(JSON)  # チャンク分割されたテキスト
    quality_score = Column(Float, default=0.0)
    language = Column(String, default="ja")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class FileImage(Base):
    """ファイル画像管理テーブル"""
    __tablename__ = "file_images"
    
    # 複合主キー: file_id + page_number + image_number
    file_id = Column(UUID(as_uuid=True), primary_key=True, index=True)
    page_number = Column(Integer, primary_key=True)
    image_number = Column(Integer, primary_key=True)  # 同一ページ内の画像番号
    
    # 画像情報
    image_path = Column(String)  # 画像ファイルのパス（必要に応じて）
    image_size = Column(JSON)  # {"width": 800, "height": 600}
    image_format = Column(String)  # "png", "jpg" 等
    
    # 認識結果
    ocr_text = Column(Text)  # OCRで抽出されたテキスト
    llm_description = Column(Text)  # LLMによる画像の説明
    llm_analysis = Column(JSON)  # LLMによる詳細分析結果
    
    # ベクトル化
    embedding_vector = Column(Text)  # JSON形式で保存
    embedding_model = Column(String)
    
    # メタデータ
    confidence_score = Column(Float, default=0.0)  # OCR信頼度
    processing_status = Column(String, default="pending")  # pending, ocr_completed, llm_analyzed, vectorized
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class Embedding(Base):
    """埋め込みベクトル管理テーブル"""
    __tablename__ = "embeddings"
    
    id = Column(Integer, primary_key=True, index=True)
    file_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    chunk_id = Column(String, nullable=False)  # チャンクの一意識別子
    text_chunk = Column(Text, nullable=False)
    embedding_model = Column(String, nullable=False)
    embedding_vector = Column(Text, nullable=False)  # JSON形式で保存
    chunk_index = Column(Integer, default=0)
    chunk_size = Column(Integer, default=0)
    similarity_score = Column(Float, default=0.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class ChatSession(Base):
    """チャットセッション管理テーブル"""
    __tablename__ = "chat_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, unique=True, nullable=False, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    title = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    is_active = Column(Boolean, default=True)

class ChatMessage(Base):
    """チャットメッセージ管理テーブル"""
    __tablename__ = "chat_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, nullable=False, index=True)
    role = Column(String, nullable=False)  # "user" or "assistant"
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    tokens_used = Column(Integer, default=0)
    referenced_files = Column(JSON)  # 参照されたファイルのIDリスト

class ProcessingQueue(Base):
    """処理キュー管理テーブル"""
    __tablename__ = "processing_queue"
    
    id = Column(Integer, primary_key=True, index=True)
    file_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    task_type = Column(String, nullable=False)  # text_extraction, vectorization, indexing
    priority = Column(Integer, default=0)
    status = Column(String, default="pending")  # pending, processing, completed, failed
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    error_message = Column(Text)

class SystemConfig(Base):
    """システム設定テーブル"""
    __tablename__ = "system_config"
    
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True, nullable=False)
    value = Column(Text)
    description = Column(Text)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now()) 