# REM: ============================================================================
# REM: DB スキーマ初期化ユーティリティ
# REM: ============================================================================
import uuid
from sqlalchemy import (
    MetaData, Table, Column, String, Text, Integer, Float,
    TIMESTAMP, LargeBinary, ForeignKey, event
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from src import config

# REM: メタデータ定義
metadata = MetaData()

# REM: ファイルメタ情報テーブル
file_metadata = Table(
    "file_metadata",
    metadata,
    Column("file_uuid", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
    Column("filename", String, nullable=False),
    Column("mime", String(128)),
    Column("size_bytes", Integer),
    Column("md5", String(32), unique=True, index=True),
    Column("uploaded_at", TIMESTAMP(timezone=True), server_default=func.now()),
    Column("quality_score", Float),
    Column("ocr_text_raw", Text),
    Column("ocr_text_clean", Text),
)

# REM: ファイルバイナリ格納テーブル
file_binary = Table(
    "file_binary",
    metadata,
    Column(
        "file_uuid",
        UUID(as_uuid=True),
        ForeignKey("file_metadata.file_uuid", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column("blob", LargeBinary, nullable=False),
)

# REM: カラムコメントを付与（読みやすさ重視）
@event.listens_for(file_metadata, "after_create")
def _add_comments(target, connection, **kw):
    connection.execute(
        """
        COMMENT ON TABLE file_metadata IS 'バイナリを除くファイル情報・全文テキスト';
        COMMENT ON COLUMN file_metadata.file_uuid IS 'UUID 主キー';
        COMMENT ON COLUMN file_metadata.filename   IS 'アップロード時のファイル名';
        COMMENT ON COLUMN file_metadata.mime       IS 'MIME タイプ';
        COMMENT ON COLUMN file_metadata.size_bytes IS 'バイトサイズ';
        COMMENT ON COLUMN file_metadata.md5        IS '同一バイナリ判定用 md5ハッシュ';
        COMMENT ON COLUMN file_metadata.uploaded_at IS '登録日時 (UTC)';
        COMMENT ON COLUMN file_metadata.quality_score IS '整形品質スコア';
        COMMENT ON COLUMN file_metadata.ocr_text_raw IS 'OCR 生テキスト';
        COMMENT ON COLUMN file_metadata.ocr_text_clean IS '辞書補正後テキスト';
        """
    )
    connection.execute(
        """
        COMMENT ON TABLE file_binary IS '実ファイルのバイナリ (BYTEA)';
        COMMENT ON COLUMN file_binary.blob IS 'ファイル本体';
        """
    )

# REM: スキーマ初期化関数 ---------------------------------------------------------
def init_schema(engine=config.DB_ENGINE) -> None:
    """
    DB 接続済み engine を受け取り、テーブルが無ければ作成する。
    """
    metadata.create_all(engine)
    print("[db_schema] Schema initialized (if not exists).")
