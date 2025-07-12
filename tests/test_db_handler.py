# tests/test_db_handler.py

import pytest
from sqlalchemy import text
from src.config import DB_ENGINE
from db.handler import fetch_top_chunks, fetch_top_files

TEST_TABLE = "test_table_2d"

@pytest.fixture(scope="module", autouse=True)
def setup_and_teardown_db():
    # ──── セットアップ ────
    with DB_ENGINE.begin() as conn:
        # 既存テーブルを削除してクリーンスタート
        conn.execute(text('DROP TABLE IF EXISTS files CASCADE'))
        conn.execute(text(f'DROP TABLE IF EXISTS "{TEST_TABLE}" CASCADE'))

        # files テーブル作成
        conn.execute(text("""
            CREATE TABLE files (
                file_id SERIAL PRIMARY KEY,
                filename TEXT,
                content TEXT,
                file_blob BYTEA,
                quality_score FLOAT,
                file_hash TEXT UNIQUE
            )
        """))

        # 埋め込みテーブル作成（2次元ベクトルの例）
        conn.execute(text(f"""
            CREATE TABLE "{TEST_TABLE}" (
                id SERIAL PRIMARY KEY,
                content TEXT,
                embedding VECTOR(2),
                file_id INTEGER REFERENCES files(file_id)
            )
        """))

    yield

    # ──── ティアダウン ────
    with DB_ENGINE.begin() as conn:
        conn.execute(text(f'DROP TABLE IF EXISTS "{TEST_TABLE}" CASCADE'))
        conn.execute(text('DROP TABLE IF EXISTS files CASCADE'))

def test_fetch_top_chunks_and_files():
    # テスト用データ挿入
    with DB_ENGINE.begin() as conn:
        # ファイルレコードを2件
        r1 = conn.execute(text("""
            INSERT INTO files (filename, content, file_blob, quality_score, file_hash)
            VALUES ('file1', '', ''::bytea, 0.0, 'hash1')
            RETURNING file_id
        """)).fetchone()
        fid1 = r1[0]

        r2 = conn.execute(text("""
            INSERT INTO files (filename, content, file_blob, quality_score, file_hash)
            VALUES ('file2', '', ''::bytea, 0.0, 'hash2')
            RETURNING file_id
        """)).fetchone()
        fid2 = r2[0]

        # 埋め込みチャンクをそれぞれ挿入
        conn.execute(text(f"""
            INSERT INTO "{TEST_TABLE}" (content, embedding, file_id)
            VALUES ('chunk1', '[0,0]'::vector, :fid)
        """), {"fid": fid1})
        conn.execute(text(f"""
            INSERT INTO "{TEST_TABLE}" (content, embedding, file_id)
            VALUES ('chunk2', '[1,1]'::vector, :fid)
        """), {"fid": fid2})

    # 1) fetch_top_chunks の検証
    rows = fetch_top_chunks("[0,0]", TEST_TABLE, limit=2)
    assert len(rows) == 2
    # 距離ゼロに最も近い chunk1 が先頭
    assert rows[0]["snippet"] == "chunk1"
    assert rows[1]["snippet"] == "chunk2"

    # 2) fetch_top_files の検証
    file_rows = fetch_top_files("[0,0]", TEST_TABLE, limit=2)
    assert len(file_rows) == 2
    # file1 が先頭
    assert file_rows[0]["file_id"] == fid1
    assert file_rows[1]["file_id"] == fid2
