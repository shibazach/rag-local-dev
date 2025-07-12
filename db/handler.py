# REM: db/handler.py（更新日時: 2025-07-13 00:00 JST）
"""
DB 操作ヘルパー（UUID ＋ 3 テーブル構成）
-------------------------------------------------
- files_meta   : 不変メタデータ
- files_blob   : バイナリ
- files_text   : OCR & 整形テキスト / タグ
- embeddings   : ベクトル（外部でテーブル作成済み）

呼び出し側は極力このモジュール経由で DB に触れる。
"""

from __future__ import annotations

# REM: 標準 / サードパーティ
import os
import hashlib
import mimetypes
from typing import Any, Sequence, Optional, Iterable, List, Dict

from sqlalchemy.sql import text as sql_text
from sqlalchemy.exc import IntegrityError
from uuid import UUID

# REM: プロジェクト共通
from src.config import DB_ENGINE, DEVELOPMENT_MODE
from src.utils import debug_print

# ──────────────────────────────────────────────────────────
# REM: 内部ユーティリティ
# ──────────────────────────────────────────────────────────

# REM: SHA256 計算
def _calc_sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

# REM: default mime
DEFAULT_MIME = "application/octet-stream"

# REM: タグを DB 用配列に変換
def _normalize_tags(tags: Optional[Sequence[str]]) -> list[str]:
    return list(dict.fromkeys([t.strip() for t in (tags or []) if t.strip()]))

# ──────────────────────────────────────────────────────────
# REM: ファイル一括 INSERT
# ──────────────────────────────────────────────────────────

def insert_file_full(
    filepath: str,
    raw_text: str,
    refined_text: str,
    quality_score: float,
    tags: Optional[Sequence[str]] | None = None,
) -> str:
    """meta / blob / text をまとめて登録し、生成 UUID を返す"""
    file_hash = _calc_sha256(filepath)
    size = os.path.getsize(filepath)
    mime_type, _ = mimetypes.guess_type(filepath)
    mime_type = mime_type or DEFAULT_MIME
    tags_list = _normalize_tags(tags)

    with open(filepath, "rb") as f:
        data = f.read()

    with DB_ENGINE.begin() as conn:
        # REM: files_meta へ INSERT（重複ハッシュならスキップ）
        file_id: str | None = conn.execute(
            sql_text(
                """
                WITH ins AS (
                    INSERT INTO files_meta (file_name, mime_type, size)
                    VALUES (:fn, :mt, :sz)
                    ON CONFLICT (file_name, size) DO NOTHING
                    RETURNING id
                )
                SELECT COALESCE((SELECT id FROM ins), id)
                  FROM files_meta
                 WHERE file_name = :fn AND size = :sz
                """
            ),
            {"fn": os.path.basename(filepath), "mt": mime_type, "sz": size},
        ).scalar()

        # REM: 初回 INSERT 時に ins テーブルから id が返る、それ以外は既存 id
        if not file_id:
            # 再取得
            file_id = conn.execute(
                sql_text(
                    "SELECT id FROM files_meta WHERE file_name = :fn AND size = :sz"
                ),
                {"fn": os.path.basename(filepath), "sz": size},
            ).scalar()

        # REM: blob/upsert
        conn.execute(
            sql_text(
                """
                INSERT INTO files_blob (file_id, blob_data, checksum)
                VALUES (:fid, :bl, :ch)
                ON CONFLICT (file_id) DO UPDATE SET
                    blob_data = EXCLUDED.blob_data,
                    checksum  = EXCLUDED.checksum
                """
            ),
            {"fid": file_id, "bl": data, "ch": file_hash},
        )

        # REM: text/upsert
        conn.execute(
            sql_text(
                """
                INSERT INTO files_text (file_id, raw_text, refined_text, quality_score, tags)
                VALUES (:fid, :raw, :ref, :qs, :tags)
                ON CONFLICT (file_id) DO UPDATE SET
                    raw_text      = EXCLUDED.raw_text,
                    refined_text  = EXCLUDED.refined_text,
                    quality_score = EXCLUDED.quality_score,
                    tags          = EXCLUDED.tags
                """
            ),
            {
                "fid": file_id,
                "raw": raw_text,
                "ref": refined_text,
                "qs": quality_score,
                "tags": tags_list,
            },
        )
    return str(file_id)

# ──────────────────────────────────────────────────────────
# REM: ファイル取得系
# ──────────────────────────────────────────────────────────

def get_file_meta(file_id: str) -> Optional[dict]:
    with DB_ENGINE.connect() as conn:
        row = conn.execute(
            sql_text(
                "SELECT file_name, mime_type, size, created_at FROM files_meta WHERE id = :fid"
            ),
            {"fid": file_id},
        ).mappings().first()
    return dict(row) if row else None


def get_file_text(file_id: str) -> Optional[dict]:
    with DB_ENGINE.connect() as conn:
        row = conn.execute(
            sql_text(
                "SELECT raw_text, refined_text, quality_score, tags FROM files_text WHERE file_id = :fid"
            ),
            {"fid": file_id},
        ).mappings().first()
    return dict(row) if row else None


def get_file_blob(file_id: str) -> Optional[bytes]:
    with DB_ENGINE.connect() as conn:
        row = conn.execute(
            sql_text("SELECT blob_data FROM files_blob WHERE file_id = :fid"),
            {"fid": file_id},
        ).first()
    return row[0] if row else None

# ──────────────────────────────────────────────────────────
# REM: 更新系
# ──────────────────────────────────────────────────────────

def update_file_text(
    file_id: str,
    refined_text: str,
    quality_score: float,
    tags: Optional[Sequence[str]] | None = None,
) -> None:
    with DB_ENGINE.begin() as conn:
        conn.execute(
            sql_text(
                """
                UPDATE files_text
                   SET refined_text  = :ref,
                       quality_score = :qs,
                       tags          = :tags,
                       updated_at    = NOW()
                 WHERE file_id       = :fid
                """
            ),
            {
                "ref": refined_text,
                "qs": quality_score,
                "tags": _normalize_tags(tags),
                "fid": file_id,
            },
        )

# ──────────────────────────────────────────────────────────
# REM: 埋め込み関連
# ──────────────────────────────────────────────────────────

def ensure_embedding_table(table_name: str, dim: int) -> None:
    """埋め込みテーブルを UUID 前提で作成（存在すれば何もしない）"""
    with DB_ENGINE.begin() as conn:
        conn.execute(
            sql_text(
                f"""
                CREATE TABLE IF NOT EXISTS "{table_name}" (
                    id        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    content   TEXT,
                    embedding VECTOR({dim}),
                    file_id   UUID REFERENCES files_meta(id) ON DELETE CASCADE
                )
                """
            )
        )


def bulk_insert_embeddings(table_name: str, records: List[Dict[str, Any]]) -> None:
    if not records:
        debug_print(f"[DEBUG] bulk_insert_embeddings: skip, empty list → {table_name}")
        return

    insert_sql = sql_text(
        f"INSERT INTO \"{table_name}\" (content, embedding, file_id) VALUES (:content, :embedding, :file_id)"
    )
    with DB_ENGINE.begin() as conn:
        conn.execute(insert_sql, records)

# ──────────────────────────────────────────────────────────
# REM: 近傍検索ユーティリティ
# ──────────────────────────────────────────────────────────

def fetch_top_chunks(query_vec: str, table_name: str, limit: int = 5) -> list[dict]:
    sql = f"""
        SELECT e.content AS snippet,
               f.id      AS file_id,
               f.file_name
          FROM \"{table_name}\" AS e
          JOIN files_meta AS f ON e.file_id = f.id
         ORDER BY e.embedding <-> '{query_vec}'::vector
         LIMIT :limit
    """
    with DB_ENGINE.connect() as conn:
        rows = conn.execute(sql_text(sql), {"limit": limit}).mappings().all()
    return [dict(r) for r in rows]


def fetch_top_files(query_vec: str, table_name: str, limit: int = 10) -> list[dict]:
    sql = f"""
        SELECT DISTINCT
               f.id AS file_id,
               f.file_name,
               t.refined_text,
               MIN(e.embedding <-> '{query_vec}'::vector) AS distance
          FROM \"{table_name}\" AS e
          JOIN files_meta  AS f ON e.file_id = f.id
          JOIN files_text  AS t ON e.file_id = t.file_id
         GROUP BY f.id, f.file_name, t.refined_text
         ORDER BY distance ASC
         LIMIT :limit
    """
    with DB_ENGINE.connect() as conn:
        rows = conn.execute(sql_text(sql), {"limit": limit}).mappings().all()
    return [dict(r) for r in rows]
