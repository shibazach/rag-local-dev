# REM: tests/test_db_handler.py（更新日時: 2025-07-13 JST）
# REM: fetch_top_chunks / fetch_top_files の動作検証（UUID 版）

import pytest
from sqlalchemy import text
from src.config import DB_ENGINE
from db.handler import fetch_top_chunks, fetch_top_files

TEST_TABLE = "test_table_2d"

# ──────────────────────────────────────────────
@pytest.fixture(scope="module", autouse=True)
def setup_and_teardown_db():
    """テスト専用テーブルを作成／削除"""
    with DB_ENGINE.begin() as conn:
        # 1) 旧テーブル掃除
        conn.execute(text(f'DROP TABLE IF EXISTS "{TEST_TABLE}" CASCADE'))

        # 2) 埋め込みテーブル（file_id UUID 外部キー）
        conn.execute(text(f"""
            CREATE TABLE "{TEST_TABLE}" (
                id        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                content   TEXT,
                embedding VECTOR(2),
                file_id   UUID REFERENCES files_meta(id) ON DELETE CASCADE
            )
        """))
    yield
    with DB_ENGINE.begin() as conn:
        conn.execute(text(f'DROP TABLE IF EXISTS "{TEST_TABLE}" CASCADE'))

# ──────────────────────────────────────────────
def insert_dummy_file(conn, name: str) -> str:
    """files_meta + files_blob + files_text に最小挿入して UUID を返す"""
    fid = conn.execute(text("""
        INSERT INTO files_meta (file_name, mime_type, size)
        VALUES (:fn, 'application/pdf', 0)
        RETURNING id
    """), {"fn": name}).scalar()

    # blob / text は空で OK
    conn.execute(text("""
        INSERT INTO files_blob (file_id, blob_data) VALUES (:fid, ''::bytea)
    """), {"fid": fid})
    conn.execute(text("""
        INSERT INTO files_text (file_id, raw_text, refined_text, quality_score, tags)
        VALUES (:fid, '', '', 0.0, '{}')
    """), {"fid": fid})
    return fid

# ──────────────────────────────────────────────
def test_fetch_top_chunks_and_files():
    with DB_ENGINE.begin() as conn:
        # 1) ファイル 2 件 INSERT
        fid1 = insert_dummy_file(conn, "file1.pdf")
        fid2 = insert_dummy_file(conn, "file2.pdf")

        # 2) 埋め込みチャンク INSERT
        conn.execute(text(f"""
            INSERT INTO "{TEST_TABLE}" (content, embedding, file_id)
            VALUES ('chunk1', '[0,0]'::vector, :fid)
        """), {"fid": fid1})
        conn.execute(text(f"""
            INSERT INTO "{TEST_TABLE}" (content, embedding, file_id)
            VALUES ('chunk2', '[1,1]'::vector, :fid)
        """), {"fid": fid2})

    # 3) fetch_top_chunks
    rows = fetch_top_chunks("[0,0]", TEST_TABLE, limit=2)
    assert len(rows) == 2
    assert rows[0]["snippet"] == "chunk1"
    assert rows[1]["snippet"] == "chunk2"

    # 4) fetch_top_files
    f_rows = fetch_top_files("[0,0]", TEST_TABLE, limit=2)
    assert len(f_rows) == 2
    assert f_rows[0]["file_id"] == fid1
    assert f_rows[1]["file_id"] == fid2
