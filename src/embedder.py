# src/embedder.py

# REM: ベクトル化処理とDB登録を行うユーティリティモジュール
import hashlib
import os

import numpy as np
import torch
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings
from sentence_transformers import SentenceTransformer
from sqlalchemy.sql import text as sql_text

from src import bootstrap
from src.config import (DB_ENGINE, DEVELOPMENT_MODE, EMBEDDING_OPTIONS,
                        OLLAMA_BASE)
from src.error_handler import install_global_exception_handler

# REM: 例外発生時のログをグローバルに記録するハンドラを有効化
install_global_exception_handler()

# REM: numpy配列をpgvector文字列リテラルに変換
def to_pgvector_literal(vec):
    if isinstance(vec, np.ndarray):
        vec = vec.tolist()
    return "[" + ",".join(f"{float(x):.6f}" for x in vec) + "]"

# REM: ファイル内容のハッシュ生成
def compute_hash(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

# REM: files テーブルの TRUNCATE 状態管理（初回のみ実行）
_truncate_files_done = False

# REM: embedding_* テーブルの TRUNCATE 状態管理（モデルごとに1回のみ）
_truncate_done_tables = set()

# REM: filesテーブルにファイルを登録しfile_idを返す
def insert_file_and_get_id(filepath, refined_ja, score, truncate_once=False):
    global _truncate_files_done

    with open(filepath, "rb") as f:
        file_blob = f.read()

    file_hash = hashlib.sha256(file_blob).hexdigest()

    with DB_ENGINE.begin() as conn:
        # REM: files テーブル作成（存在しなければ）
        conn.execute(sql_text("""
            CREATE TABLE IF NOT EXISTS files (
                file_id SERIAL PRIMARY KEY,
                filename TEXT,
                content TEXT,
                file_blob BYTEA,
                quality_score FLOAT,
                file_hash TEXT UNIQUE
            )
        """))

        # REM: 開発モードかつ初回のみ TRUNCATE 実行
        if DEVELOPMENT_MODE and truncate_once and not _truncate_files_done:
            print("🧨 DEVELOPMENT_MODE: files テーブルを TRUNCATE（初回のみ）")
            conn.execute(sql_text("TRUNCATE TABLE files CASCADE"))
            _truncate_files_done = True

        # REM: 同一ファイルがすでに登録されている場合はそのIDを返す
        existing = conn.execute(sql_text(
            "SELECT file_id FROM files WHERE file_hash = :hash"
        ), {"hash": file_hash}).fetchone()

        if existing:
            print(f"📎 file_id {existing[0]} を files テーブルより取得")
            return existing[0]

        # REM: 新規ファイルを登録
        result = conn.execute(sql_text("""
            INSERT INTO files (filename, content, file_blob, quality_score, file_hash)
            VALUES (:filename, :content, :file_blob, :score, :hash)
            RETURNING file_id
        """), {
            "filename": os.path.basename(filepath),
            "content": refined_ja,
            "file_blob": file_blob,
            "score": score,
            "hash": file_hash
        })
        file_id = result.scalar()
        print(f"📎 file_id {file_id} を新規登録")
        return file_id

# REM: ベクトル化とDB登録（モデル指定対応）
def embed_and_insert(texts, filename, model_keys=None, return_data=False, quality_score=0.0):
    global _truncate_done_tables

    # REM: チャンク分割（500文字 + 50重複）
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks = [splitter.split_text(t) for t in texts]
    flat_chunks = [s for c in chunks for s in c]
    full_text = "\n".join(flat_chunks)

    # REM: files テーブルへの登録（初回のみ TRUNCATE）
    file_id = insert_file_and_get_id(filename, full_text, quality_score, truncate_once=True)

    all_chunks = []
    all_embeddings = []

    for key, config in EMBEDDING_OPTIONS.items():
        # REM: 指定モデル以外はスキップ
        if model_keys is not None and key not in model_keys:
            continue

        print(f"🔍 モデル {key}: {config['model_name']} による埋め込み中...")

        # REM: モデルに応じて埋め込みエンジンを切り替え
        if config["embedder"] == "OllamaEmbeddings":
            embedder = OllamaEmbeddings(
                model=config["model_name"],
                base_url=OLLAMA_BASE
            )
            embeddings = embedder.embed_documents(flat_chunks)

        elif config["embedder"] == "SentenceTransformer":
            device = "cuda" if torch.cuda.is_available() else "cpu"
            embedder = SentenceTransformer(config["model_name"], device=device)
            embeddings = embedder.encode(flat_chunks, convert_to_numpy=True)

        else:
            print(f"⚠️ 未対応の埋め込み: {config['embedder']}")
            continue

        # REM: テーブル名をモデル名と次元から生成
        table_name = config["model_name"].replace("/", "_").replace("-", "_") + f"_{config['dimension']}"

        # REM: テーブル作成と初期化（初回のみ）
        with DB_ENGINE.begin() as conn:
            conn.execute(sql_text(f"""
                CREATE TABLE IF NOT EXISTS "{table_name}" (
                    id SERIAL PRIMARY KEY,
                    content TEXT,
                    embedding VECTOR({config['dimension']}),
                    file_id INTEGER REFERENCES files(file_id)
                )
            """))

            if table_name not in _truncate_done_tables:
                conn.execute(sql_text(f'TRUNCATE TABLE "{table_name}" CASCADE'))
                print(f"🧹 テーブル {table_name} を初期化しました")
                _truncate_done_tables.add(table_name)

            # REM: チャンクごとにベクトルと一緒に登録
            insert_sql = sql_text(f"""
                INSERT INTO "{table_name}" (content, embedding, file_id)
                VALUES (:content, :embedding, :file_id)
            """)
            records = [
                {"content": chunk, "embedding": to_pgvector_literal(vec), "file_id": file_id}
                for chunk, vec in zip(flat_chunks, embeddings)
            ]
            conn.execute(insert_sql, records)
            print(f"✅ {len(records)} 件を {table_name} に挿入完了")

        if return_data:
            all_chunks.extend(flat_chunks)
            all_embeddings.extend(embeddings)

    if return_data:
        return all_chunks, all_embeddings
