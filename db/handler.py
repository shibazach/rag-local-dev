# db/handler.py  # REM: 最終更新 2025-07-12 15:35
# REM: DB 操作ヘルパーを一元管理（files／embedding 共通）

from __future__ import annotations
import os, hashlib
from typing import Sequence, Optional, Any

from sqlalchemy.sql import text as sql_text
from src.config import DB_ENGINE, DEVELOPMENT_MODE
from src.utils import debug_print

# REM: 初回TRUNCATE実行済みテーブル管理
_truncated_tables: set[str] = set()

# REM: テーブル名ごとに一度だけTRUNCATEを実行
def truncate_table_once(table_name: str) -> None:
    global _truncated_tables
    if DEVELOPMENT_MODE and table_name not in _truncated_tables:
        with DB_ENGINE.begin() as conn:
            conn.execute(sql_text(f'TRUNCATE TABLE "{table_name}" CASCADE'))
        _truncated_tables.add(table_name)

# REM: SHA256 計算ユーティリティ
def _calc_sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

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

# REM: files 行を upsert して file_id を取得
def upsert_file(
    filepath: str,
    content:  str = "",
    score:    float = 0.0,
    *,
    overwrite:     bool = False,
) -> int:
    """
    1. file_hash が一致する行があればその file_id を返す  
       - overwrite=True の場合は無条件で UPDATE  
       - overwrite=False の場合でも、以下いずれかで UPDATE  
         (a) DB の content が空 → 引数 content が非空  
         (b) 引数 score > DB の quality_score  
    2. 行が無ければ INSERT して新規 file_id を返す  
    """
    # REM: files テーブル初回TRUNCATE
    truncate_table_once("files")
    _ensure_files_table()
    file_hash = _calc_sha256(filepath)

    with DB_ENGINE.begin() as conn:
        row = conn.execute(
            sql_text("""
                SELECT file_id, content, quality_score
                  FROM files
                 WHERE file_hash = :h
            """),
            {"h": file_hash}
        ).fetchone()

        if row:
            need_update = False
            if overwrite:
                need_update = True
            elif content and not row.content:
                need_update = True
            elif content and score > (row.quality_score or 0.0):
                need_update = True

            if need_update:
                conn.execute(
                    sql_text("""
                        UPDATE files
                           SET content       = :ct,
                               quality_score = :sc
                         WHERE file_id       = :fid
                    """),
                    {"ct": content or row.content, "sc": score, "fid": row.file_id}
                )
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

# REM: embedding テーブルを作成
def prepare_embedding_table(table_name: str, dim: int) -> None:
    with DB_ENGINE.begin() as conn:
        conn.execute(sql_text(f"""
            CREATE TABLE IF NOT EXISTS "{table_name}" (
                id SERIAL PRIMARY KEY,
                content   TEXT,
                embedding VECTOR({dim}),
                file_id   INTEGER REFERENCES files(file_id)
            )
        """))

# REM: 指定 file_id の古い埋め込みレコードを削除
def delete_embedding_for_file(table_name: str, file_id: int) -> None:
    with DB_ENGINE.begin() as conn:
        conn.execute(
            sql_text(f'DELETE FROM "{table_name}" WHERE file_id = :fid'),
            {"fid": file_id}
        )

# REM: 指定テーブルへ embedding レコードを一括 INSERT
def insert_embeddings(table_name: str, records: list[dict]) -> None:
    insert_sql = sql_text(f"""
        INSERT INTO "{table_name}" (content, embedding, file_id)
        VALUES (:content, :embedding, :file_id)
    """)
    with DB_ENGINE.begin() as conn:
        debug_print(f"[DEBUG] insert_embeddings: table={table_name}, count={len(records)}")
        if not records:
            debug_print(f"[DEBUG] insert_embeddings: no records, skip insert into {table_name}")
            return
        for rec in records:
            if "content" not in rec:
                raise ValueError(f"[DEBUG] record missing 'content': {rec!r}")
        conn.execute(insert_sql, records)

# REM: 指定 file_id のファイルメタ情報（content, quality_score）を取得
def get_file_metadata(file_id: int) -> Optional[dict]:
    with DB_ENGINE.connect() as conn:
        row = conn.execute(
            sql_text("""
                SELECT content, quality_score
                  FROM files
                 WHERE file_id = :fid
            """),
            {"fid": file_id}
        ).mappings().first()
    return dict(row) if row else None

# REM: 指定 file_id の content / score を更新
def update_file_content(file_id: int, content: str, score: float) -> None:
    with DB_ENGINE.begin() as conn:
        conn.execute(
            sql_text("""
                UPDATE files
                   SET content       = :ct,
                       quality_score = :sc
                 WHERE file_id       = :fid
            """),
            {"ct": content, "sc": score, "fid": file_id}
        )

# REM: 埋め込みテーブルを作成・初回TRUNCATE制御
def ensure_embedding_table(
    table_name: str,
    dim: int
) -> None:
    """
    - テーブル作成
    - 初回TRUNCATEはtruncate_table_onceで担保
    """
    prepare_embedding_table(table_name, dim)
    truncate_table_once(table_name)

# REM: 埋め込みレコードを一括挿入
def bulk_insert_embeddings(
    table_name: str,
    records: list[dict]
) -> None:
    """
    - レコードリストを insert_embeddings 経由で一括INSERT
    """
    insert_embeddings(table_name, records)

# ──────────────────────────────────────────────────────────
# REM: 上位Kチャンクを取得
def fetch_top_chunks(
    query_vec: str,
    table_name: str,
    limit: int = 5
) -> list[dict[str, Any]]:
    """
    - table_name の埋め込みテーブルから、クエリベクトルに近い上位limit件を取得
    """
    sql = f"""
        SELECT e.content AS snippet,
               f.file_id,
               f.filename
          FROM "{table_name}" AS e
          JOIN files AS f ON e.file_id = f.file_id
         ORDER BY e.embedding <-> '{query_vec}'::vector
         LIMIT :limit
    """
    with DB_ENGINE.connect() as conn:
        rows = conn.execute(sql_text(sql), {"limit": limit}).mappings().all()
    return [dict(r) for r in rows]

# REM: 上位Kファイルを取得
def fetch_top_files(
    query_vec: str,
    table_name: str,
    limit: int = 10
) -> list[dict[str, Any]]:
    """
    - table_name の埋め込みテーブルから、ファイルごとに最小距離順で上位limit件を取得
    """
    sql = f"""
        SELECT DISTINCT
               f.file_id,
               f.filename,
               f.content,
               f.file_blob,
               MIN(e.embedding <-> '{query_vec}'::vector) AS distance
          FROM "{table_name}" AS e
          JOIN files AS f ON e.file_id = f.file_id
         GROUP BY f.file_id, f.filename, f.content, f.file_blob
         ORDER BY distance ASC
         LIMIT :limit
    """
    with DB_ENGINE.connect() as conn:
        rows = conn.execute(sql_text(sql), {"limit": limit}).mappings().all()
    return [dict(r) for r in rows]
