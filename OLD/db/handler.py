# REM: db/handler.py（更新日時: 2025-07-18 15:30 JST）
"""
DB 操作ヘルパー（UUID ＋ 3 テーブル構成 - checksum主導設計）
-------------------------------------------------
- files_blob   : バイナリ（主テーブル、checksum一意制約）
- files_meta   : メタデータ（1:1対応）
- files_text   : OCR & 整形テキスト / タグ（1:1対応）
- embeddings   : ベクトル（外部でテーブル作成済み）

呼び出し側は極力このモジュール経由で DB に触れる。
全てのテーブルは blob_id で統一された UUID を使用。
"""

from __future__ import annotations

# REM: 標準 / サードパーティ
import os
import hashlib
import mimetypes
from typing import Any, Sequence, Optional, List, Dict

from sqlalchemy.sql import text as sql_text
from uuid import UUID

# REM: プロジェクト共通
from OLD.src.config import DB_ENGINE, DEVELOPMENT_MODE
from OLD.src.utils import debug_print

# ──────────────────────────────────────────────────────────
# REM: 内部ユーティリティ
# ──────────────────────────────────────────────────────────
def _calc_sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

DEFAULT_MIME = "application/octet-stream"

def _normalize_tags(tags: Optional[Sequence[str]]) -> list[str]:
    return list(dict.fromkeys([t.strip() for t in (tags or []) if t.strip()]))

# ──────────────────────────────────────────────────────────
# REM: 開発モード専用 DB 初期化
# ──────────────────────────────────────────────────────────
def reset_dev_database() -> None:
    if not DEVELOPMENT_MODE:
        return
    from sqlalchemy import text as _t
    with DB_ENGINE.begin() as conn:
        conn.execute(_t("TRUNCATE files_blob, files_meta, files_text CASCADE"))
        rows = conn.execute(
            _t("""SELECT tablename FROM pg_tables
                   WHERE schemaname='public'
                     AND tablename ~ '^[a-zA-Z0-9_]+_[0-9]+$'""")
        ).fetchall()
        for (tbl,) in rows:
            conn.execute(_t(f'TRUNCATE "{tbl}"'))
    debug_print("[DEBUG] reset_dev_database: all tables truncated.")

# ──────────────────────────────────────────────────────────
# REM: 重複チェック機能
# ──────────────────────────────────────────────────────────
def find_existing_by_checksum(checksum: str) -> Optional[str]:
    """checksumで既存ファイルを検索し、あればそのblob_idを返す"""
    with DB_ENGINE.connect() as conn:
        row = conn.execute(
            sql_text("SELECT id FROM files_blob WHERE checksum = :checksum"),
            {"checksum": checksum}
        ).first()
    return str(row[0]) if row else None

# ──────────────────────────────────────────────────────────
# REM: ファイル一括 INSERT
# ──────────────────────────────────────────────────────────
def insert_file_full(
    file_path: str,
    raw_text: str,
    refined_text: str,
    quality_score: float,
    tags: Optional[Sequence[str]] | None = None,
) -> str:
    """
    新しい設計でのファイル一括INSERT
    1. checksum計算
    2. 既存blob検索（重複チェック）
    3. files_blob INSERT（新規の場合）
    4. files_meta INSERT/UPDATE
    5. files_text INSERT/UPDATE
    """
    file_hash = _calc_sha256(file_path)
    size = os.path.getsize(file_path)
    mime_type = mimetypes.guess_type(file_path)[0] or DEFAULT_MIME
    tags_list = _normalize_tags(tags)
    
    with open(file_path, "rb") as fp:
        data = fp.read()

    with DB_ENGINE.begin() as conn:
        # 1. 既存blob検索
        existing_blob_id = find_existing_by_checksum(file_hash)
        
        if existing_blob_id:
            # 既存blobを使用
            blob_id = existing_blob_id
            debug_print(f"[handler] Using existing blob: {blob_id}")
        else:
            # 新規blob作成
            blob_id = conn.execute(
                sql_text("""
                    INSERT INTO files_blob (checksum, blob_data)
                    VALUES (:checksum, :data)
                    RETURNING id
                """),
                {"checksum": file_hash, "data": data}
            ).scalar_one()
            debug_print(f"[handler] Created new blob: {blob_id}")

        # 2. files_meta INSERT/UPDATE
        conn.execute(
            sql_text("""
                INSERT INTO files_meta (blob_id, file_name, mime_type, size)
                VALUES (:blob_id, :fn, :mt, :sz)
                ON CONFLICT (blob_id) DO UPDATE SET
                    file_name = EXCLUDED.file_name,
                    mime_type = EXCLUDED.mime_type,
                    size = EXCLUDED.size,
                    created_at = NOW()
            """),
            {"blob_id": blob_id, "fn": os.path.basename(file_path), 
             "mt": mime_type, "sz": size}
        )

        # 3. files_text INSERT/UPDATE
        conn.execute(
            sql_text("""
                INSERT INTO files_text (blob_id, raw_text, refined_text, quality_score, tags)
                VALUES (:blob_id, :raw, :ref, :qs, :tags)
                ON CONFLICT (blob_id) DO UPDATE SET
                    raw_text = EXCLUDED.raw_text,
                    refined_text = EXCLUDED.refined_text,
                    quality_score = EXCLUDED.quality_score,
                    tags = EXCLUDED.tags,
                    updated_at = NOW()
            """),
            {"blob_id": blob_id, "raw": raw_text, "ref": refined_text,
             "qs": quality_score, "tags": tags_list}
        )
    
    return str(blob_id)

# ──────────────────────────────────────────────────────────
# REM: 取得系
# ──────────────────────────────────────────────────────────
def get_file_meta(blob_id: str) -> Optional[dict]:
    """files_meta から (file_name, mime_type, size, created_at) を取得"""
    with DB_ENGINE.connect() as conn:
        row = conn.execute(
            sql_text("""
                SELECT file_name, mime_type, size, created_at
                  FROM files_meta
                 WHERE blob_id = :blob_id
            """), {"blob_id": blob_id}
        ).mappings().first()
    return dict(row) if row else None

def get_file_blob(blob_id: str) -> Optional[bytes]:
    """files_blob からバイナリを取得"""
    with DB_ENGINE.connect() as conn:
        row = conn.execute(
            sql_text("SELECT blob_data FROM files_blob WHERE id = :blob_id"),
            {"blob_id": blob_id}
        ).first()
    return row[0] if row else None

def get_file_text(blob_id: str) -> Optional[dict]:
    """files_text から (raw_text, refined_text, quality_score, tags) を取得"""
    with DB_ENGINE.connect() as conn:
        row = conn.execute(
            sql_text("""
                SELECT raw_text, refined_text, quality_score, tags
                  FROM files_text
                 WHERE blob_id = :blob_id
            """), {"blob_id": blob_id}
        ).mappings().first()
    return dict(row) if row else None

# ──────────────────────────────────────────────────────────
# REM: 更新系
# ──────────────────────────────────────────────────────────
def update_file_text(
    blob_id: str,
    refined_text: str | None = None,
    raw_text: str | None = None,
    quality_score: float | None = None,
    tags: Optional[Sequence[str]] | None = None,
) -> None:
    """files_text を更新"""
    sets, params = [], {"blob_id": blob_id}
    if refined_text is not None: 
        sets.append("refined_text = :ref")
        params["ref"] = refined_text
    if raw_text is not None: 
        sets.append("raw_text = :raw")
        params["raw"] = raw_text
    if quality_score is not None: 
        sets.append("quality_score = :qs")
        params["qs"] = quality_score
    if tags is not None: 
        sets.append("tags = :tags")
        params["tags"] = _normalize_tags(tags)
    
    if not sets:
        return

    sets.append("updated_at = NOW()")
    sql = f"UPDATE files_text SET {', '.join(sets)} WHERE blob_id = :blob_id"
    with DB_ENGINE.begin() as conn:
        conn.execute(sql_text(sql), params)

# ──────────────────────────────────────────────────────────
# REM: 埋め込みテーブル操作
# ──────────────────────────────────────────────────────────
def ensure_embedding_table(table_name: str, dim: int) -> None:
    """埋め込みテーブルを作成（blob_id参照に変更）"""
    with DB_ENGINE.begin() as conn:
        conn.execute(sql_text(f"""
            CREATE TABLE IF NOT EXISTS "{table_name}" (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                content TEXT,
                embedding VECTOR({dim}),
                blob_id UUID REFERENCES files_blob(id) ON DELETE CASCADE
            )
        """))

def bulk_insert_embeddings(table_name: str, records: List[Dict[str, Any]]) -> None:
    """埋め込みレコードの一括INSERT（blob_id使用）"""
    if not records: 
        return
    with DB_ENGINE.begin() as conn:
        conn.execute(
            sql_text(f"""INSERT INTO "{table_name}"
                         (content, embedding, blob_id)
                         VALUES (:content, :embedding, :blob_id)"""),
            records
        )

# ──────────────────────────────────────────────────────────
# REM: 近傍検索
# ──────────────────────────────────────────────────────────
def fetch_top_chunks(query_vec: str, table_name: str, limit: int = 5) -> list[dict]:
    """チャンク単位での近傍検索（新しいJOIN構造）"""
    sql = f"""
        SELECT e.content   AS snippet,
               b.id        AS blob_id,
               m.file_name AS file_name
          FROM "{table_name}" AS e
          JOIN files_blob AS b ON e.blob_id = b.id
          JOIN files_meta AS m ON b.id = m.blob_id
         ORDER BY e.embedding <-> '{query_vec}'::vector
         LIMIT :limit
    """
    with DB_ENGINE.connect() as conn:
        rows = conn.execute(sql_text(sql), {"limit": limit}).mappings().all()
    return [dict(r) for r in rows]

def fetch_top_files(query_vec: str, table_name: str, limit: int = 10) -> list[dict]:
    """ファイル単位での近傍検索（新しいJOIN構造）"""
    sql = f"""
        SELECT DISTINCT
               b.id            AS blob_id,
               m.file_name     AS file_name,
               t.refined_text  AS refined_text,
               MIN(e.embedding <-> '{query_vec}'::vector) AS distance
          FROM "{table_name}" AS e
          JOIN files_blob AS b ON e.blob_id = b.id
          JOIN files_meta AS m ON b.id = m.blob_id
          JOIN files_text AS t ON b.id = t.blob_id
         GROUP BY b.id, m.file_name, t.refined_text
         ORDER BY distance ASC
         LIMIT :limit
    """
    with DB_ENGINE.connect() as conn:
        rows = conn.execute(sql_text(sql), {"limit": limit}).mappings().all()
    return [dict(r) for r in rows]

# ──────────────────────────────────────────────────────────
# REM: 削除系
# ──────────────────────────────────────────────────────────
def delete_embedding_for_file(table_name: str, blob_id: str) -> None:
    """指定blob_idの古い埋め込みレコードを削除（overwrite用）"""
    with DB_ENGINE.begin() as conn:
        conn.execute(sql_text(f'DELETE FROM "{table_name}" WHERE blob_id = :blob_id'),
                     {"blob_id": blob_id})

# ──────────────────────────────────────────────────────────
# REM: ステータス更新（将来拡張用）
# ──────────────────────────────────────────────────────────
def update_file_status(blob_id: str, *, status: str, note: str | None = None) -> None:
    """インジェスト進捗用ステータス更新（ダミー実装）"""
    import logging
    logging.getLogger("ingest").debug(
        "update_file_status: %s status=%s note=%s", blob_id, status, note
    )
    # REM: 将来files_metaにstatus/noteカラムを追加した場合:
    # with DB_ENGINE.begin() as conn:
    #     conn.execute(
    #         sql_text("UPDATE files_meta SET status=:st, note=:nt WHERE blob_id=:bid"),
    #         {"st": status, "nt": note, "bid": blob_id},
    #     )

# REM: OCR比較用の追加関数
def get_all_files() -> List[Dict[str, Any]]:
    """全ファイルの一覧を取得（OCR比較用）"""
    sql = """
        SELECT b.id, m.file_name, m.mime_type, m.size, m.created_at
        FROM files_blob b
        JOIN files_meta m ON b.id = m.blob_id
        ORDER BY m.created_at DESC
    """
    with DB_ENGINE.connect() as conn:
        rows = conn.execute(sql_text(sql)).mappings().all()
    return [dict(r) for r in rows]

def get_file_path(blob_id: str) -> Optional[str]:
    """ファイルIDからファイルパスを取得（一時的な実装）"""
    # 注意: 実際の実装では、ファイルはDBに保存されているため、
    # 一時ファイルとして書き出す必要があります
    import tempfile
    
    # バイナリデータを取得
    blob_data = get_file_blob(blob_id)
    if not blob_data:
        return None
    
    # メタデータを取得してファイル名を決定
    meta = get_file_meta(blob_id)
    if not meta:
        return None
    
    # 一時ファイルに書き出し
    suffix = os.path.splitext(meta['file_name'])[1] or '.pdf'
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
        temp_file.write(blob_data)
        return temp_file.name