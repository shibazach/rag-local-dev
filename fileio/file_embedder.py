# fileio/file_embedder.py
# REM: ベクトル化処理と DB 登録ユーティリティ（overwrite フラグ対応版）

import os, hashlib, torch
import numpy as np
from typing import List, Sequence

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings
from sentence_transformers import SentenceTransformer
from sqlalchemy.sql import text as sql_text

from src import bootstrap
from src.config import (
    DB_ENGINE, DEVELOPMENT_MODE, EMBEDDING_OPTIONS, OLLAMA_BASE
)

# REM: DB ヘルパー
from db.handler import upsert_file, prepare_embedding_table

# ──────────────────────────────────────────────────────────
# REM: GPU 空き VRAM をチェックしてエンベッド用デバイスを返す
def pick_embed_device(min_free_vram_mb: int = 1024) -> str:
    """
    GPU が利用可能かつ空き VRAM が min_free_vram_mb 以上なら "cuda" を返す。
    それ以外は "cpu"。
    """
    if torch.cuda.is_available():
        try:
            free, _ = torch.cuda.mem_get_info()
            free_mb = free // (1024 * 1024)
        except Exception:
            # PyTorch が古く NVML へフォールバックする場合
            from pynvml import nvmlInit, nvmlDeviceGetHandleByIndex, nvmlDeviceGetMemoryInfo
            nvmlInit()
            handle = nvmlDeviceGetHandleByIndex(0)
            info = nvmlDeviceGetMemoryInfo(handle)
            free_mb = info.free // (1024 * 1024)
        if free_mb >= min_free_vram_mb:
            return "cuda"
    return "cpu"


# REM: numpy 配列を pgvector 文字列リテラルに変換
def to_pgvector_literal(vec: Sequence[float] | np.ndarray) -> str:
    if isinstance(vec, np.ndarray):
        vec = vec.tolist()
    return "[" + ",".join(f"{float(x):.6f}" for x in vec) + "]"


# ──────────────────────────────────────────────────────────
# REM: メイン関数 ─ チャンク分割 → 埋め込み → DB 登録
def embed_and_insert(
    texts: List[str],
    filename: str,
    model_keys: List[str] | None = None,
    *,
    return_data: bool = False,
    quality_score: float = 0.0,
    overwrite: bool = False,
):
    """
    ・texts         : 抽出／整形済みページテキストのリスト  
    ・filename      : 実ファイルへのパス  
    ・model_keys    : EMBEDDING_OPTIONS のキーリスト（None=全モデル）  
    ・return_data   : True の時は (chunks, embeddings) を返す  
    ・quality_score : files.quality_score へ保存する値  
    ・overwrite     : True で既存 embeddings テーブルを TRUNCATE して上書き
    """
    # 1) チャンク分割 ------------------------------------------------------------
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks_lists = [splitter.split_text(t) for t in texts]
    flat_chunks  = [s for lst in chunks_lists for s in lst]
    full_text    = "\n".join(flat_chunks)

    # 2) files テーブル登録（既存があれば再利用） -------------------------------
    file_id = upsert_file(filename, full_text, quality_score, truncate_once=True)

    # 3) 各モデルごとに埋め込み --------------------------------------------------
    for key, cfg in EMBEDDING_OPTIONS.items():
        if model_keys is not None and key not in model_keys:
            continue

        # 3-A) 埋め込み器を初期化
        if cfg["embedder"] == "OllamaEmbeddings":
            embedder = OllamaEmbeddings(model=cfg["model_name"], base_url=OLLAMA_BASE)
            embeddings = embedder.embed_documents(flat_chunks)

        elif cfg["embedder"] == "SentenceTransformer":
            from torch.cuda import OutOfMemoryError
            device = pick_embed_device()
            try:
                st_model = SentenceTransformer(cfg["model_name"], device=device)
            except OutOfMemoryError:
                torch.cuda.empty_cache()
                device = "cpu"
                st_model = SentenceTransformer(cfg["model_name"], device=device)
            batch = 16 if device == "cuda" else 8
            embeddings = st_model.encode(
                flat_chunks,
                batch_size=batch,
                convert_to_numpy=True,
                show_progress_bar=(device == "cuda"),
            )
        else:
            print(f"⚠️ 未対応 embedder: {cfg['embedder']}")
            continue

        # 3-B) テーブル名 & 準備
        table_name = cfg["model_name"].replace("/", "_").replace("-", "_") + f"_{cfg['dimension']}"
        prepare_embedding_table(table_name, cfg["dimension"], overwrite=overwrite)

        # 3-C) INSERT
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
        with DB_ENGINE.begin() as conn:
            conn.execute(insert_sql, records)

    # 4) 必要ならデータを返却 ----------------------------------------------------
    if return_data:
        return flat_chunks, embeddings
