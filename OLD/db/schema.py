# db/schema.py
# REM: ============================================================================
# REM: DB スキーマ初期化ユーティリティ
# REM: ============================================================================
import uuid
from sqlalchemy import (
    MetaData, Table, Column, String, Text, Integer, Float,
    TIMESTAMP, LargeBinary, ForeignKey, event)
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.sql import func

from OLD.src import config
from OLD.src.utils import debug_print

# REM: メタデータ定義
metadata = MetaData()

# REM: ファイルバイナリ格納テーブル（主テーブル）
files_blob = Table(
    "files_blob",
    metadata,
    Column("id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
    Column("checksum", String, nullable=False, unique=True),
    Column("blob_data", LargeBinary, nullable=False),
    Column("stored_at", TIMESTAMP(timezone=True), server_default=func.now()),
)

# REM: ファイルメタ情報テーブル（1:1対応）
files_meta = Table(
    "files_meta",
    metadata,
    Column(
        "blob_id",
        UUID(as_uuid=True),
        ForeignKey("files_blob.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column("file_name", String, nullable=False),
    Column("mime_type", String, nullable=False),
    Column("size", Integer, nullable=False),
    Column("created_at", TIMESTAMP(timezone=True), server_default=func.now()),
)

# REM: ファイルテキスト格納テーブル（1:1対応）
files_text = Table(
    "files_text",
    metadata,
    Column(
        "blob_id",
        UUID(as_uuid=True),
        ForeignKey("files_blob.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column("raw_text", Text),
    Column("refined_text", Text),
    Column("quality_score", Float),
    Column("tags", ARRAY(String), server_default='{}'),
    Column("updated_at", TIMESTAMP(timezone=True), server_default=func.now()),
)

# REM: カラムコメントを付与（読みやすさ重視）
@event.listens_for(files_blob, "after_create")
def _add_comments(target, connection, **kw):
    connection.execute(
        """
        COMMENT ON TABLE files_blob IS '実ファイルのバイナリ (主テーブル)';
        COMMENT ON COLUMN files_blob.id IS 'UUID 主キー';
        COMMENT ON COLUMN files_blob.checksum IS 'チェックサム (一意制約)';
        COMMENT ON COLUMN files_blob.blob_data IS 'ファイル本体';
        COMMENT ON COLUMN files_blob.stored_at IS '格納日時';
        """
    )
    connection.execute(
        """
        COMMENT ON TABLE files_meta IS 'ファイルメタ情報';
        COMMENT ON COLUMN files_meta.blob_id IS 'files_blob への外部キー (主キー)';
        COMMENT ON COLUMN files_meta.file_name IS 'アップロード時のファイル名';
        COMMENT ON COLUMN files_meta.mime_type IS 'MIME タイプ';
        COMMENT ON COLUMN files_meta.size IS 'バイトサイズ';
        COMMENT ON COLUMN files_meta.created_at IS '登録日時 (UTC)';
        """
    )
    connection.execute(
        """
        COMMENT ON TABLE files_text IS 'OCRテキスト・整形結果';
        COMMENT ON COLUMN files_text.blob_id IS 'files_blob への外部キー (主キー)';
        COMMENT ON COLUMN files_text.raw_text IS 'OCR 生テキスト';
        COMMENT ON COLUMN files_text.refined_text IS '辞書補正後テキスト';
        COMMENT ON COLUMN files_text.quality_score IS '整形品質スコア';
        COMMENT ON COLUMN files_text.tags IS 'タグ配列';
        COMMENT ON COLUMN files_text.updated_at IS '更新日時';
        """
    )

# REM: スキーマ初期化関数 ---------------------------------------------------------
def init_schema(engine=config.DB_ENGINE) -> None:
    """
    DB 接続済み engine を受け取り、テーブルが無ければ作成する。
    """
    metadata.create_all(engine)
    debug_print("[db_schema] Schema initialized (if not exists).")

# REM: 外部参照用のエイリアス定義（create_rag_data.py などから参照される）
TABLE_FILES = files_meta
TABLE_FILE_BINARY = files_blob
TABLE_FILE_TEXT = files_text
