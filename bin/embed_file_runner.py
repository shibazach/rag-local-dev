# bin/embed_file_runner.py
# REM: ベクトル化処理とDB登録を行うユーティリティモジュール

import os, hashlib
import numpy as np
import torch

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings
from sentence_transformers import SentenceTransformer
from sqlalchemy.sql import text as sql_text

from src import bootstrap
from src.config import (
    DB_ENGINE, DEVELOPMENT_MODE, EMBEDDING_OPTIONS, OLLAMA_BASE)
from db.schema import TABLE_FILES
from src.utils import debug_print

# REM: GPU 空きVRAMをチェックしてデバイスを返すユーティリティ ──
def pick_embed_device(min_free_vram_mb: int = 1024) -> str:
    """
    GPU が利用可能かつ空き VRAM が min_free_vram_mb 以上あれば "cuda" を返す。
    それ以外は "cpu"。
    """
    if torch.cuda.is_available():
        try:
            free, _ = torch.cuda.mem_get_info()
            free_mb = free // (1024 * 1024)
        except Exception:
            # 古い PyTorch 環境では NVML 経由
            from pynvml import nvmlInit, nvmlDeviceGetHandleByIndex, nvmlDeviceGetMemoryInfo
            nvmlInit()
            handle = nvmlDeviceGetHandleByIndex(0)
            info = nvmlDeviceGetMemoryInfo(handle)
            free_mb = info.free // (1024 * 1024)
        if free_mb >= min_free_vram_mb:
            return "cuda"
    return "cpu"

# REM: numpy配列をpgvector文字列リテラルに変換
def to_pgvector_literal(vec):
    if isinstance(vec, np.ndarray):
        vec = vec.tolist()
    return "[" + ",".join(f"{float(x):.6f}" for x in vec) + "]"

# REM: filesテーブルにファイルを登録しfile_idを返す
_truncate_files_done = False
def insert_file_and_get_id(filepath, refined_ja, score, truncate_once=False):
    global _truncate_files_done

    with open(filepath, "rb") as f:
        file_blob = f.read()

    file_hash = hashlib.sha256(file_blob).hexdigest()

    with DB_ENGINE.begin() as conn:
        # テーブル作成
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

        # 開発モードかつ初回のみ TRUNCATE
        if DEVELOPMENT_MODE and truncate_once and not _truncate_files_done:
            conn.execute(sql_text("TRUNCATE TABLE files CASCADE"))
            _truncate_files_done = True

        # 既存登録チェック
        existing = conn.execute(sql_text(
            "SELECT file_id FROM files WHERE file_hash = :hash"
        ), {"hash": file_hash}).fetchone()
        if existing:
            return existing[0]

        # 新規登録
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
        return result.scalar()

# REM: embedding_* テーブルの TRUNCATE 状態管理（モデルごとに1回のみ）
_truncate_done_tables = set()

# REM: ベクトル化とDB登録
def embed_and_insert(texts, filename, model_keys=None, return_data=False, quality_score=0.0):
    global _truncate_done_tables

    # チャンク分割
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks = [splitter.split_text(t) for t in texts]
    flat_chunks = [s for c in chunks for s in c]
    full_text = "\n".join(flat_chunks)

    # files テーブル登録
    file_id = insert_file_and_get_id(filename, full_text, quality_score, truncate_once=True)

    # 各モデルごとに埋め込み
    for key, config in EMBEDDING_OPTIONS.items():
        if model_keys is not None and key not in model_keys:
            continue

        # OllamaEmbeddings の場合
        if config["embedder"] == "OllamaEmbeddings":
            embedder = OllamaEmbeddings(
                model=config["model_name"],
                base_url=OLLAMA_BASE
            )
            embeddings = embedder.embed_documents(flat_chunks)

        # SentenceTransformer の場合
        elif config["embedder"] == "SentenceTransformer":
            from torch.cuda import OutOfMemoryError

            # 1) デバイス選択
            device = pick_embed_device(min_free_vram_mb=1024)
            try:
                embedder = SentenceTransformer(config["model_name"], device=device)
            except OutOfMemoryError:
                torch.cuda.empty_cache()
                device = "cpu"
                embedder = SentenceTransformer(config["model_name"], device=device)

            # 2) バッチサイズ設定
            batch_size = 16 if device == "cuda" else 8

            # 3) エンコード実行
            try:
                embeddings = embedder.encode(
                    flat_chunks,
                    batch_size=batch_size,
                    convert_to_numpy=True,
                    show_progress_bar=(device == "cuda"),
                )
            except OutOfMemoryError:
                # GPU 時の OOM フォールバック
                if device == "cuda":
                    torch.cuda.empty_cache()
                    device = "cpu"
                    embedder = SentenceTransformer(config["model_name"], device=device)
                    embeddings = embedder.encode(
                        flat_chunks,
                        batch_size=8,
                        convert_to_numpy=True
                    )
                else:
                    raise

        else:
            debug_print(f"⚠️ 未対応の埋め込み: {config['embedder']}")
            continue

        # テーブル名生成
        table_name = (
            config["model_name"].replace("/", "_")
            .replace("-", "_")
            + f"_{config['dimension']}"
        )

        # テーブル作成＆初期化（初回のみ）
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
                _truncate_done_tables.add(table_name)

            # レコード登録
            insert_sql = sql_text(f"""
                INSERT INTO "{table_name}" (content, embedding, file_id)
                VALUES (:content, :embedding, :file_id)
            """)
            records = [
                {
                    "content": chunk,
                    "embedding": to_pgvector_literal(vec),
                    "file_id": file_id
                }
                for chunk, vec in zip(flat_chunks, embeddings)
            ]
            conn.execute(insert_sql, records)

    # 必要ならチャンク＋埋め込みを返す
    if return_data:
        return flat_chunks, embeddings
