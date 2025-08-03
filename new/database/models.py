# new/database/models.py  
# データベーステーブル定義（旧系からの移植・改良版）

import uuid
from sqlalchemy import (
    MetaData, Table, Column, String, Text, Integer, Float,
    TIMESTAMP, LargeBinary, ForeignKey, event, Index
)
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy import JSON
from sqlalchemy.sql import func

# ============================================================================
# メタデータ定義
# ============================================================================

metadata = MetaData()

# ============================================================================
# テーブル定義（旧系3テーブル構成を踏襲）
# ============================================================================

# ファイルバイナリ格納テーブル（主テーブル）
files_blob = Table(
    "files_blob",
    metadata,
    Column("id", String(36), primary_key=True, default=lambda: str(uuid.uuid4())),
    Column("checksum", String(64), nullable=False, unique=True, index=True),
    Column("blob_data", LargeBinary, nullable=False),
    Column("stored_at", TIMESTAMP(timezone=True), server_default=func.now()),
    
    # インデックス追加でパフォーマンス向上
    Index("idx_files_blob_checksum", "checksum"),
    Index("idx_files_blob_stored_at", "stored_at"),
)

# ファイルメタ情報テーブル（1:1対応）
files_meta = Table(
    "files_meta", 
    metadata,
    Column(
        "blob_id",
        String(36),
        ForeignKey("files_blob.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column("file_name", String(255), nullable=False),
    Column("mime_type", String(100), nullable=False),
    Column("size", Integer, nullable=False),
    Column("page_count", Integer, nullable=True),  # PDFページ数等
    Column("status", String(50), nullable=False, default="uploaded"),  # uploaded, processing, completed, error
    Column("created_at", TIMESTAMP(timezone=True), server_default=func.now()),
    Column("updated_at", TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now()),
    
    # インデックス追加
    Index("idx_files_meta_status", "status"),
    Index("idx_files_meta_created_at", "created_at"),
    Index("idx_files_meta_file_name", "file_name"),
)

# ファイルテキスト格納テーブル（1:1対応）  
files_text = Table(
    "files_text",
    metadata,
    Column(
        "blob_id",
        String(36),
        ForeignKey("files_blob.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column("raw_text", Text, nullable=True),           # OCR生テキスト
    Column("refined_text", Text, nullable=True),       # LLM整形後テキスト
    Column("quality_score", Float, nullable=True),     # 整形品質スコア（0.0-1.0）
    Column("tags", JSON, server_default='[]'), # タグ配列（SQLite対応）
    Column("processing_log", Text, nullable=True),      # 処理ログ
    Column("ocr_engine", String(50), nullable=True),   # 使用したOCRエンジン
    Column("llm_model", String(100), nullable=True),   # 使用したLLMモデル
    Column("updated_at", TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now()),
    
    # インデックス追加
    Index("idx_files_text_updated_at", "updated_at"),
)

# ============================================================================
# ステータス定義（列挙型の代わり）  
# ============================================================================

FILE_STATUS = {
    "UPLOADED": "uploaded",           # アップロード完了
    "PENDING_PROCESSING": "pending_processing",  # 処理待ち
    "PROCESSING": "processing",       # 処理中
    "TEXT_EXTRACTED": "text_extracted",  # テキスト抽出完了
    "TEXT_REFINED": "text_refined",   # テキスト整形完了
    "PROCESSED": "processed",         # 完全処理完了
    "ERROR": "error",                 # エラー
}

# ============================================================================
# テーブルコメント追加（SQLiteでは無効化）
# ============================================================================

# @event.listens_for(files_blob, "after_create") 
# def _add_table_comments(target, connection, **kw):
#     """テーブル・カラムコメントを追加（PostgreSQL専用）"""
#     # SQLiteではCOMMENT構文をサポートしていないため無効化