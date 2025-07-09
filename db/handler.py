# db/handler.py
# REM: DB 操作ヘルパーを一元管理（files／embedding 共通）

from __future__ import annotations
import os, hashlib
from typing import Sequence

from sqlalchemy.sql import text as sql_text
from src.config import DB_ENGINE, DEVELOPMENT_MODE

# ──────────────────────────────────────────────────────────
# REM: guard オブジェクト（TRUNCATE を 1 処理で 1 回に抑える）
class _Guard:
    files_truncated: bool = False
    truncated_tables: set[str] = set()

_guard = _Guard()

# ──────────────────────────────────────────────────────────
# REM: SHA256 計算ユーティリティ
def _calc_sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

# ──────────────────────────────────────────────────────────
# REM: files テーブルを保証
def _ensure_files_table() -> None:
    with DB_ENGINE.begin() as conn:
        conn.execute(sql_text("""
            CREATE TABLE IF NOT EXISTS files (
                file_id SERIAL PRIMARY KEY,
                filename TEXT,
                content  TEXT,
                file_blob BYTEA,
                quality_score FLOAT,
                file_hash TEXT UNIQUE
            )
        """))

# ──────────────────────────────────────────────────────────
# REM: files 行を upsert して file_id を取得
def upsert_file(
    filepath: str,
    content: str = "",
    score: float = 0.0,
    *,
    truncate_once: bool = True,
) -> int:
    """
    - 既に同一ハッシュ(file_hash) があればその file_id を返す  
    - 無ければ INSERT して新規 file_id を返す  
    - DEVELOPMENT_MODE かつ truncate_once=True の時、最初の 1 回だけ TRUNCATE
    """
    _ensure_files_table()
    file_hash = _calc_sha256(filepath)

    with DB_ENGINE.begin() as conn:
        # 初回のみ TRUNCATE
        if DEVELOPMENT_MODE and truncate_once and not _guard.files_truncated:
            conn.execute(sql_text("TRUNCATE TABLE files CASCADE"))
            _guard.files_truncated = True

        row = conn.execute(
            sql_text("SELECT file_id FROM files WHERE file_hash = :h"),
            {"h": file_hash}
        ).fetchone()
        if row:
            return row.file_id

        with open(filepath, "rb") as f:
            blob = f.read()

        return conn.execute(sql_text("""
            INSERT INTO files (filename, content, file_blob, quality_score, file_hash)
            VALUES (:fn, :ct, :bl, :sc, :h) RETURNING file_id
        """), {
            "fn": os.path.basename(filepath),
            "ct": content,
            "bl": blob,
            "sc": score,
            "h": file_hash,
        }).scalar()

# ──────────────────────────────────────────────────────────
# REM: embedding テーブルを作成し、overwrite=True なら 1 回だけ TRUNCATE
def prepare_embedding_table(table_name: str, dim: int, *, overwrite: bool) -> None:
    with DB_ENGINE.begin() as conn:
        conn.execute(sql_text(f"""
            CREATE TABLE IF NOT EXISTS "{table_name}" (
                id SERIAL PRIMARY KEY,
                content   TEXT,
                embedding VECTOR({dim}),
                file_id   INTEGER REFERENCES files(file_id)
            )
        """))
        if overwrite and table_name not in _guard.truncated_tables:
            conn.execute(sql_text(f'TRUNCATE TABLE "{table_name}" CASCADE'))
            _guard.truncated_tables.add(table_name)
