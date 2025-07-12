# bin/embed_file_runner.py  最終更新 2025-07-12 14:55
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
from db.handler import upsert_file, ensure_embedding_table, bulk_insert_embeddings
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

# REM: ベクトル化とDB登録
def embed_and_insert(texts, filename, model_keys=None, return_data=False, quality_score=0.0):
    # チャンク分割
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks = [splitter.split_text(t) for t in texts]
    flat_chunks = [s for c in chunks for s in c]
    full_text = "\n".join(flat_chunks)

    # REM: files テーブル登録（初回TRUNCATEは handler 側で実施）
    file_id = upsert_file(filename, full_text, quality_score)

    # REM: 各モデルごとに埋め込み
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

        # REM: テーブル作成＆初回TRUNCATE制御
        debug_print(f"[DEBUG] ⏳ ensure table before TRUNCATE/CREATE: {table_name}")
        ensure_embedding_table(table_name, config["dimension"])

        # REM: レコード一括INSERT
        records = [
            {"content": chunk, "embedding": to_pgvector_literal(vec), "file_id": file_id}
            for chunk, vec in zip(flat_chunks, embeddings)
        ]
        debug_print(f"[DEBUG] ⏳ inserting {len(records)} records into: {table_name}")
        bulk_insert_embeddings(table_name, records)

    # 必要ならチャンク＋埋め込みを返す
    if return_data:
        return flat_chunks, embeddings
