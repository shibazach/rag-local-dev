# new/database/models.py  
# データベーステーブル定義（旧系からの移植・改良版）

import uuid
from sqlalchemy import (
    MetaData, Table, Column, String, Text, Integer, Float,
    TIMESTAMP, LargeBinary, ForeignKey, event, Index
)
from sqlalchemy.dialects.postgresql import UUID, ARRAY
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
    Column("id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
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
        UUID(as_uuid=True),
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
        UUID(as_uuid=True),
        ForeignKey("files_blob.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column("raw_text", Text, nullable=True),           # OCR生テキスト
    Column("refined_text", Text, nullable=True),       # LLM整形後テキスト
    Column("quality_score", Float, nullable=True),     # 整形品質スコア（0.0-1.0）
    Column("tags", ARRAY(String), server_default='{}'), # タグ配列
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
# テーブルコメント追加（可読性向上）
# ============================================================================

@event.listens_for(files_blob, "after_create")
def _add_table_comments(target, connection, **kw):
    """テーブル・カラムコメントを追加"""
    
    # files_blobテーブル
    connection.execute(
        """
        COMMENT ON TABLE files_blob IS 'ファイルバイナリ格納テーブル（主テーブル）';
        COMMENT ON COLUMN files_blob.id IS 'UUID主キー';
        COMMENT ON COLUMN files_blob.checksum IS 'SHA256チェックサム（重複防止）';
        COMMENT ON COLUMN files_blob.blob_data IS 'ファイル本体データ';
        COMMENT ON COLUMN files_blob.stored_at IS 'ファイル格納日時（UTC）';
        """
    )
    
    # files_metaテーブル
    connection.execute(
        """
        COMMENT ON TABLE files_meta IS 'ファイルメタ情報テーブル';
        COMMENT ON COLUMN files_meta.blob_id IS 'files_blob外部キー（主キー）';
        COMMENT ON COLUMN files_meta.file_name IS 'アップロード時ファイル名';
        COMMENT ON COLUMN files_meta.mime_type IS 'MIMEタイプ';
        COMMENT ON COLUMN files_meta.size IS 'ファイルサイズ（バイト）';
        COMMENT ON COLUMN files_meta.page_count IS 'ページ数（PDF等）';
        COMMENT ON COLUMN files_meta.status IS '処理ステータス';
        COMMENT ON COLUMN files_meta.created_at IS '作成日時（UTC）';
        COMMENT ON COLUMN files_meta.updated_at IS '更新日時（UTC）';
        """
    )
    
    # files_textテーブル
    connection.execute(
        """
        COMMENT ON TABLE files_text IS 'ファイルテキスト・処理結果テーブル';
        COMMENT ON COLUMN files_text.blob_id IS 'files_blob外部キー（主キー）';
        COMMENT ON COLUMN files_text.raw_text IS 'OCR抽出生テキスト';
        COMMENT ON COLUMN files_text.refined_text IS 'LLM整形後テキスト';
        COMMENT ON COLUMN files_text.quality_score IS 'テキスト品質スコア（0.0-1.0）';
        COMMENT ON COLUMN files_text.tags IS 'タグ配列';
        COMMENT ON COLUMN files_text.processing_log IS '処理ログ・エラー情報';
        COMMENT ON COLUMN files_text.ocr_engine IS '使用OCRエンジン名';
        COMMENT ON COLUMN files_text.llm_model IS '使用LLMモデル名';
        COMMENT ON COLUMN files_text.updated_at IS '最終更新日時（UTC）';
        """
    )