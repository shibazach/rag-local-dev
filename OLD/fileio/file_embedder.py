# fileio/file_embedder.py  最終更新 2025-07-13 00:50
# REM: ベクトル化処理と DB 登録ユーティリティ（handler 統合版）

import os, hashlib, torch
import numpy as np
from typing import List, Sequence, Optional

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings
from sentence_transformers import SentenceTransformer

from OLD.src import bootstrap
from OLD.src.config import (
    DB_ENGINE, DEVELOPMENT_MODE, EMBEDDING_OPTIONS, OLLAMA_BASE
)

from OLD.db.handler import (
    insert_file_full,
    delete_embedding_for_file,
    ensure_embedding_table,
    bulk_insert_embeddings
)
from OLD.src.utils import debug_print, to_pgvector_literal

# ──────────────────────────────────────────────────────────
# REM: GPU 空き VRAM をチェックしてエンベッド用デバイスを返す
def pick_embed_device(min_free_vram_mb: int = 1024) -> str:
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

# ──────────────────────────────────────────────────────────

# ──────────────────────────────────────────────────────────
# REM: メイン関数 ─ チャンク分割 → 埋め込み → DB 登録
def embed_and_insert(
    texts: List[str],
    file_name: str,
    model_keys: Optional[List[str]] = None,
    *,
    return_data: bool = False,
    quality_score: float = 0.0,
    overwrite: bool = False,
    file_id: Optional[int] = None,
):
    """
    ・texts         : 抽出／整形済みテキストリスト  
    ・file_name     : ファイルパス（file_id指定時はダミー可）  
    ・model_keys    : EMBEDDING_OPTIONS のキーリスト  
    ・return_data   : True で (chunks, embeddings) を返却  
    ・quality_score : files.quality_score へ  
    ・overwrite     : True で既存埋め込みを上書き  
    ・file_id       : None→upsert_file 呼び出し、指定→既存行利用  
    """
    debug_print(f"[DEBUG] embed_and_insert start: file_name={file_name}, texts count={len(texts)}")

    # 1) チャンク分割
    splitter     = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks_lists = [splitter.split_text(t) for t in texts]
    flat_chunks  = [s for lst in chunks_lists for s in lst]
    full_text    = "\n".join(flat_chunks)
    debug_print(f"[DEBUG] total chunks = {len(flat_chunks)}")

    if not flat_chunks:
        debug_print(f"[DEBUG] embed_and_insert: no chunks for {file_name}, skip embedding")
        return
    
    # CPU環境でのチャンク数制限（メモリ不足対策）
    MAX_CHUNKS_CPU = 100  # CPU環境での最大チャンク数
    if len(flat_chunks) > MAX_CHUNKS_CPU:
        debug_print(f"[WARNING] Too many chunks ({len(flat_chunks)}), limiting to {MAX_CHUNKS_CPU} for CPU processing")
        flat_chunks = flat_chunks[:MAX_CHUNKS_CPU]

    # 2) files テーブル upsert or スキップ
    if file_id is None:
        debug_print(f"[DEBUG] upsert_file returned file_id = {file_id}")
        file_id = insert_file_full(file_name, full_text, quality_score, tags=[])

    # 3) 各モデルで埋め込み
    for key, cfg in EMBEDDING_OPTIONS.items():
        if model_keys and key not in model_keys:
            continue

        debug_print(f"[DEBUG] embedding with model = {cfg['model_name']}")

        # 3-A) 埋め込み生成
        try:
            if cfg["embedder"] == "OllamaEmbeddings":
                debug_print(f"[DEBUG] Using Ollama embeddings: {cfg['model_name']}")
                embedder   = OllamaEmbeddings(model=cfg["model_name"], base_url=OLLAMA_BASE)
                embeddings = embedder.embed_documents(flat_chunks)
            else:
                from torch.cuda import OutOfMemoryError
                device = pick_embed_device()
                debug_print(f"[DEBUG] Using SentenceTransformer on device: {device}")
                
                try:
                    debug_print(f"[DEBUG] Loading model: {cfg['model_name']}")
                    st_model = SentenceTransformer(cfg["model_name"], device=device)
                except OutOfMemoryError as e:
                    debug_print(f"[WARNING] GPU OOM, falling back to CPU: {e}")
                    torch.cuda.empty_cache()
                    device   = "cpu"
                    st_model = SentenceTransformer(cfg["model_name"], device=device)
                except Exception as e:
                    debug_print(f"[ERROR] Failed to load SentenceTransformer model: {e}")
                    raise
                
                batch = 16 if device == "cuda" else 2  # CPU環境でさらに削減
                debug_print(f"[DEBUG] Encoding {len(flat_chunks)} chunks with batch_size={batch}")
                
                embeddings = st_model.encode(
                    flat_chunks,
                    batch_size=batch,
                    convert_to_numpy=True,
                    show_progress_bar=True,  # CPU環境でも進捗表示
                )
                debug_print(f"[DEBUG] Encoding completed, embeddings shape: {embeddings.shape}")
                
        except Exception as e:
            debug_print(f"[ERROR] Embedding generation failed for model {cfg['model_name']}: {e}")
            raise

        # 3-B) 埋め込みテーブル名 & 旧レコード削除／準備
        table_name = cfg["model_name"].replace("/", "_").replace("-", "_") + f"_{cfg['dimension']}"
        if overwrite and file_id is not None:
            debug_print(f"[DEBUG] deleted existing embeddings for file_id = {file_id} in {table_name}")
            delete_embedding_for_file(table_name, file_id)

        # REM: テーブル作成＆初回TRUNCATE制御（handler 側で一元化）
        debug_print(f"[DEBUG] ensured embedding table = {table_name}")
        ensure_embedding_table(table_name, cfg["dimension"])

        # 3-C) 新レコード挿入
        records = [
            {"content": chunk, "embedding": to_pgvector_literal(vec), "blob_id": file_id}
            for chunk, vec in zip(flat_chunks, embeddings)
        ]
        debug_print(f"[DEBUG] bulk_insert_embeddings into {table_name}: count={len(records)}")
        bulk_insert_embeddings(table_name, records)

    if return_data:
        return flat_chunks, embeddings
