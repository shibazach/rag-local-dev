# REM: bin/embed_file_runner.py（更新日時: 2025-07-13 00:55）
# REM: テキスト → チャンク → 埋め込み → DB 登録のユーティリティ

import os, hashlib, numpy as np, torch
from typing import List, Sequence, Tuple

from langchain.text_splitter  import RecursiveCharacterTextSplitter
from langchain_ollama         import OllamaEmbeddings
from sentence_transformers    import SentenceTransformer
from sqlalchemy.sql           import text as sql_text

from src import bootstrap
from src.config import (
    DB_ENGINE, DEVELOPMENT_MODE, EMBEDDING_OPTIONS, OLLAMA_BASE
)
from db.handler import (
    insert_file_full,
    ensure_embedding_table,
    bulk_insert_embeddings
)
from src.utils import debug_print

# ──────────────────────────────────────────────
# REM: GPU 空き VRAM をチェックしてデバイスを返す
def pick_embed_device(min_free_vram_mb: int = 1024) -> str:
    if torch.cuda.is_available():
        try:
            free, _ = torch.cuda.mem_get_info()
            free_mb = free // (1024 * 1024)
        except Exception:
            from pynvml import (
                nvmlInit, nvmlDeviceGetHandleByIndex, nvmlDeviceGetMemoryInfo
            )
            nvmlInit()
            handle = nvmlDeviceGetHandleByIndex(0)
            info   = nvmlDeviceGetMemoryInfo(handle)
            free_mb = info.free // (1024 * 1024)
        if free_mb >= min_free_vram_mb:
            return "cuda"
    return "cpu"

# ──────────────────────────────────────────────
# REM: numpy 配列 → pgvector 文字列リテラル
def to_pgvector_literal(vec: Sequence[float] | np.ndarray) -> str:
    if isinstance(vec, np.ndarray):
        vec = vec.tolist()
    return "[" + ",".join(f"{float(x):.6f}" for x in vec) + "]"

# ──────────────────────────────────────────────
# REM: メイン関数
def embed_and_insert(
    texts: List[str],
    file_path: str,
    *,
    model_keys: List[str] | None = None,
    quality_score: float = 0.0,
    return_data: bool = False,
) -> Tuple[List[str], np.ndarray] | None:
    """抽出済み texts をチャンク化→埋め込み→DB 登録"""
    splitter    = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks      = [s for t in texts for s in splitter.split_text(t)]
    if not chunks:
        debug_print(f"[DEBUG] embed_and_insert: no chunks for {file_path}")
        return None

    full_text   = "\n".join(chunks)

    # ① files_* へ一括 INSERT（空 raw_text）
    file_id = insert_file_full(file_path, "", full_text, quality_score, tags=[])

    # ② 各 Embedding モデルで処理
    for key, cfg in EMBEDDING_OPTIONS.items():
        if model_keys and key not in model_keys:
            debug_print(f"⚠️ 未対応の埋め込み: {config['embedder']}")
            continue

        # 2-A) ベクトル生成
        if cfg["embedder"] == "OllamaEmbeddings":
            embedder   = OllamaEmbeddings(model=cfg["model_name"], base_url=OLLAMA_BASE)
            vectors    = embedder.embed_documents(chunks)
        else:
            from torch.cuda import OutOfMemoryError
            device   = pick_embed_device()
            try:
                st_model = SentenceTransformer(cfg["model_name"], device=device)
            except OutOfMemoryError:
                torch.cuda.empty_cache()
                st_model = SentenceTransformer(cfg["model_name"], device="cpu")
                device   = "cpu"
            vectors = st_model.encode(
                chunks,
                batch_size=(16 if device == "cuda" else 8),
                convert_to_numpy=True,
                show_progress_bar=(device == "cuda"),
            )

        # 2-B) 埋め込みテーブル名
        table_name = cfg["model_name"].replace("/", "_").replace("-", "_") + f"_{cfg['dimension']}"

        # 2-C) テーブル作成（UUID 外部キー）
        ensure_embedding_table(table_name, cfg["dimension"])

        # 2-D) レコード一括 INSERT
        records = [
            {"content": c, "embedding": to_pgvector_literal(v), "file_id": file_id}
            for c, v in zip(chunks, vectors)
        ]
        debug_print(f"[DEBUG] ⏳ inserting {len(records)} records into: {table_name}")
        bulk_insert_embeddings(table_name, records)

    return (chunks, vectors) if return_data else None
