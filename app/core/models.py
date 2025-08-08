"""
データベースモデル定義 - PostgreSQL専用版
Files4兄弟 (files_blob, files_meta, files_text, files_image) + Embedding のみの構成
"""

import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import Column, String, Text, DateTime, Float, LargeBinary, ForeignKey, Integer, Index
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from .database import Base


# ========== Files3兄弟 (OLD系準拠) ==========

class FilesBlob(Base):
    """
    ファイルバイナリ格納テーブル（主テーブル）
    実ファイルのバイナリ (主テーブル)
    """
    __tablename__ = "files_blob"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    checksum = Column(String(64), nullable=False, unique=True, index=True)
    blob_data = Column(LargeBinary, nullable=False)
    stored_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # リレーション
    meta = relationship("FilesMeta", back_populates="blob", uselist=False, cascade="all, delete-orphan")
    text = relationship("FilesText", back_populates="blob", uselist=False, cascade="all, delete-orphan")
    embeddings = relationship("FileEmbedding", back_populates="blob", cascade="all, delete-orphan")
    images = relationship("FilesImage", back_populates="blob", cascade="all, delete-orphan")
    
    # インデックス
    __table_args__ = (
        Index("idx_files_blob_checksum", "checksum"),
        Index("idx_files_blob_stored_at", "stored_at"),
    )
    
    def __repr__(self):
        return f"<FilesBlob(id={self.id}, checksum={self.checksum[:8]}...)>"


class FilesMeta(Base):
    """
    ファイルメタ情報テーブル（1:1対応）
    アップロード時のファイル名、MIMEタイプ、サイズ等
    """
    __tablename__ = "files_meta"
    
    blob_id = Column(UUID(as_uuid=True), ForeignKey("files_blob.id", ondelete="CASCADE"), primary_key=True)
    file_name = Column(String(255), nullable=False, index=True)
    mime_type = Column(String(100), nullable=False)
    size = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 将来の拡張用（画像・グラフページ検出）
    # OLD/db/構想.txt より：
    # PDFに写真やグラフを含むものは、将来のLLMがマルチモーダルになった際に
    # 優先的に再認識させたいのでフラグを立てておきたい
    # image_pages = Column(ARRAY(Integer), server_default='{}')  # 画像があるページ番号リスト
    # chart_pages = Column(ARRAY(Integer), server_default='{}')  # グラフがあるページ番号リスト
    
    # リレーション
    blob = relationship("FilesBlob", back_populates="meta")
    
    # インデックス
    __table_args__ = (
        Index("idx_files_meta_file_name", "file_name"),
        Index("idx_files_meta_created_at", "created_at"),
    )
    
    def __repr__(self):
        return f"<FilesMeta(blob_id={self.blob_id}, name={self.file_name})>"


class FilesText(Base):
    """
    ファイルテキスト格納テーブル（1:1対応）
    OCRテキスト・整形結果
    """
    __tablename__ = "files_text"
    
    blob_id = Column(UUID(as_uuid=True), ForeignKey("files_blob.id", ondelete="CASCADE"), primary_key=True)
    raw_text = Column(Text)  # OCR 生テキスト
    refined_text = Column(Text)  # 辞書補正後テキスト
    quality_score = Column(Float)  # 整形品質スコア
    tags = Column(ARRAY(String), server_default='{}')  # タグ配列
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # リレーション
    blob = relationship("FilesBlob", back_populates="text")
    
    # インデックス
    __table_args__ = (
        Index("idx_files_text_tags", "tags", postgresql_using="gin"),
        Index("idx_files_text_updated_at", "updated_at"),
    )
    
    def __repr__(self):
        return f"<FilesText(blob_id={self.blob_id}, score={self.quality_score})>"


# ========== Embedding テーブル ==========

class FileEmbedding(Base):
    """
    埋め込みベクトルテーブル
    ファイルのチャンクごとのベクトル保存
    """
    __tablename__ = "embeddings"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    blob_id = Column(UUID(as_uuid=True), ForeignKey("files_blob.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # チャンク情報
    chunk_index = Column(Integer, nullable=False)  # チャンクの順番
    chunk_text = Column(Text, nullable=False)  # チャンクのテキスト
    chunk_start = Column(Integer)  # 開始位置
    chunk_end = Column(Integer)  # 終了位置
    
    # ベクトル情報
    # vector = Column(Vector(dimension))  # pgvector型（後で設定）
    vector_json = Column(Text)  # 一時的にJSON形式で保存
    embedding_model = Column(String(100))  # 使用したモデル名
    embedding_dimension = Column(Integer)  # ベクトル次元数
    
    # メタデータ
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # リレーション
    blob = relationship("FilesBlob", back_populates="embeddings")
    
    # インデックス
    __table_args__ = (
        Index("idx_embeddings_blob_id", "blob_id"),
        Index("idx_embeddings_chunk_index", "blob_id", "chunk_index"),
    )
    
    def __repr__(self):
        return f"<FileEmbedding(id={self.id}, blob_id={self.blob_id}, chunk={self.chunk_index})>"


# ========== Picture テーブル ==========

class FilesImage(Base):
    """
    画像情報テーブル（Files4兄弟の一員）
    PDFやドキュメント内の画像を管理
    """
    __tablename__ = "files_image"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    blob_id = Column(UUID(as_uuid=True), ForeignKey("files_blob.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # 画像情報
    page_number = Column(Integer)  # ページ番号（PDFの場合）
    image_index = Column(Integer)  # ページ内の画像インデックス
    image_type = Column(String(50))  # image, chart, diagram等
    
    # 画像データ
    image_data = Column(LargeBinary)  # 画像バイナリ
    image_format = Column(String(20))  # png, jpg等
    width = Column(Integer)
    height = Column(Integer)
    
    # 抽出情報
    caption = Column(Text)  # キャプション（あれば）
    extracted_text = Column(Text)  # 画像内のテキスト（OCR結果）
    
    # メタデータ
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # リレーション
    blob = relationship("FilesBlob", back_populates="images")
    
    # インデックス
    __table_args__ = (
        Index("idx_file_images_blob_id", "blob_id"),
        Index("idx_file_images_page", "blob_id", "page_number"),
    )
    
    def __repr__(self):
        return f"<FilesImage(id={self.id}, blob_id={self.blob_id}, page={self.page_number})>"


# ========== テーブルコメント（PostgreSQL専用） ==========

from sqlalchemy import event

@event.listens_for(FilesBlob.__table__, "after_create")
def _add_blob_comments(target, connection, **kw):
    connection.execute(text("""
        COMMENT ON TABLE files_blob IS '実ファイルのバイナリ (主テーブル)';
        COMMENT ON COLUMN files_blob.id IS 'UUID 主キー';
        COMMENT ON COLUMN files_blob.checksum IS 'SHA256チェックサム (一意制約)';
        COMMENT ON COLUMN files_blob.blob_data IS 'ファイル本体';
        COMMENT ON COLUMN files_blob.stored_at IS '格納日時';
    """))

@event.listens_for(FilesMeta.__table__, "after_create")
def _add_meta_comments(target, connection, **kw):
    connection.execute(text("""
        COMMENT ON TABLE files_meta IS 'ファイルメタ情報';
        COMMENT ON COLUMN files_meta.blob_id IS 'files_blob への外部キー (主キー)';
        COMMENT ON COLUMN files_meta.file_name IS 'アップロード時のファイル名';
        COMMENT ON COLUMN files_meta.mime_type IS 'MIME タイプ';
        COMMENT ON COLUMN files_meta.size IS 'バイトサイズ';
        COMMENT ON COLUMN files_meta.created_at IS '登録日時 (UTC)';
    """))

@event.listens_for(FilesText.__table__, "after_create")
def _add_text_comments(target, connection, **kw):
    connection.execute(text("""
        COMMENT ON TABLE files_text IS 'OCRテキスト・整形結果';
        COMMENT ON COLUMN files_text.blob_id IS 'files_blob への外部キー (主キー)';
        COMMENT ON COLUMN files_text.raw_text IS 'OCR 生テキスト';
        COMMENT ON COLUMN files_text.refined_text IS '辞書補正後テキスト';
        COMMENT ON COLUMN files_text.quality_score IS '整形品質スコア';
        COMMENT ON COLUMN files_text.tags IS 'タグ配列';
        COMMENT ON COLUMN files_text.updated_at IS '更新日時';
    """))

@event.listens_for(FileEmbedding.__table__, "after_create")
def _add_embedding_comments(target, connection, **kw):
    connection.execute(text("""
        COMMENT ON TABLE embeddings IS 'ベクトル埋め込みデータ';
        COMMENT ON COLUMN embeddings.id IS 'UUID 主キー';
        COMMENT ON COLUMN embeddings.blob_id IS 'files_blob への外部キー';
        COMMENT ON COLUMN embeddings.chunk_index IS 'チャンク順序';
        COMMENT ON COLUMN embeddings.chunk_text IS 'チャンクテキスト';
        COMMENT ON COLUMN embeddings.vector_json IS 'ベクトルJSON（一時）';
        COMMENT ON COLUMN embeddings.embedding_model IS '使用モデル名';
    """))

@event.listens_for(FilesImage.__table__, "after_create")
def _add_images_comments(target, connection, **kw):
    connection.execute(text("""
        COMMENT ON TABLE file_images IS '文書内画像情報';
        COMMENT ON COLUMN file_images.id IS 'UUID 主キー';
        COMMENT ON COLUMN file_images.blob_id IS 'files_blob への外部キー';
        COMMENT ON COLUMN file_images.page_number IS 'ページ番号';
        COMMENT ON COLUMN file_images.image_type IS '画像タイプ（image/chart/diagram）';
        COMMENT ON COLUMN file_images.image_data IS '画像バイナリ';
    """))


# エラー防止のためのimport
from sqlalchemy import text