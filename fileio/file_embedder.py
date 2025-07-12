# workspace/fileio/file_embedder.py  # REM: 最終更新 2025-07-12 00:14
# REM: ベクトル化処理と DB 登録ユーティリティ（handler 統合版）
import os, hashlib, torch
import numpy as np
from typing import List, Sequence, Optional

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings
from sentence_transformers import SentenceTransformer

from src import bootstrap
from src.config import (
    DB_ENGINE, DEVELOPMENT_MODE, EMBEDDING_OPTIONS, OLLAMA_BASE
)

from db.handler import (upsert_file, prepare_embedding_table, delete_embedding_for_file, insert_embeddings)
from src.utils import debug_print

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
    model_keys: Optional[List[str]] = None,
    *,
    return_data: bool = False,
    quality_score: float = 0.0,
    overwrite: bool = False,
    file_id: Optional[int] = None,
):
    """
    ・texts         : 抽出／整形済みテキストリスト  
    ・filename      : ファイルパス（file_id指定時はダミー可）  
    ・model_keys    : EMBEDDING_OPTIONS のキーリスト  
    ・return_data   : True で (chunks, embeddings) を返却  
    ・quality_score : files.quality_score へ  
    ・overwrite     : True で既存埋め込みを上書き  
    ・file_id       : None→upsert_file 呼び出し、指定→既存行利用  
    """
    # REM: debug 出力開始
    debug_print(f"[DEBUG] embed_and_insert start: filename={filename}, texts count={len(texts)}")

    # 1) チャンク分割 ------------------------------------------------------------
    splitter     = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks_lists = [splitter.split_text(t) for t in texts]
    flat_chunks  = [s for lst in chunks_lists for s in lst]
    full_text    = "\n".join(flat_chunks)
    debug_print(f"[DEBUG] total chunks = {len(flat_chunks)}")

    # REM: チャンク空の場合は以降の埋め込み処理をスキップ
    if not flat_chunks:
        debug_print(f"[DEBUG] embed_and_insert: no chunks for {filename}, skip embedding")
        return

    # 2) files テーブル upsert or スキップ --------------------------------------
    if file_id is None:
        file_id = upsert_file(filename, full_text, quality_score)
        debug_print(f"[DEBUG] upsert_file returned file_id = {file_id}")

    # 3) 各モデルで埋め込み ------------------------------------------------------
    for key, cfg in EMBEDDING_OPTIONS.items():
        if model_keys and key not in model_keys:
            continue

        debug_print(f"[DEBUG] embedding with model = {cfg['model_name']}")

        # 3-A) 埋め込み生成
        if cfg["embedder"] == "OllamaEmbeddings":
            embedder   = OllamaEmbeddings(model=cfg["model_name"], base_url=OLLAMA_BASE)
            embeddings = embedder.embed_documents(flat_chunks)
        else:
            from torch.cuda import OutOfMemoryError
            # デバイス選択
            device = pick_embed_device()
            try:
                st_model = SentenceTransformer(cfg["model_name"], device=device)
            except OutOfMemoryError:
                torch.cuda.empty_cache()
                device   = "cpu"
                st_model = SentenceTransformer(cfg["model_name"], device=device)
            batch      = 16 if device == "cuda" else 8
            embeddings = st_model.encode(
                flat_chunks,
                batch_size=batch,
                convert_to_numpy=True,
                show_progress_bar=(device == "cuda"),
            )

        # 3-B) 埋め込みテーブル名 & 旧レコード削除／準備 ---------------------------
        table_name = cfg["model_name"].replace("/", "_").replace("-", "_") + f"_{cfg['dimension']}"
        if overwrite and file_id is not None:
            delete_embedding_for_file(table_name, file_id)
            debug_print(f"[DEBUG] deleted existing embeddings for file_id = {file_id} in {table_name}")
        prepare_embedding_table(table_name, cfg['dimension'], overwrite=False)
        debug_print(f"[DEBUG] prepared table = {table_name}")

        # 3-C) 新レコード挿入 ------------------------------------------------------
        records = [
            {"content": chunk, "embedding": to_pgvector_literal(vec), "file_id": file_id}
            for chunk, vec in zip(flat_chunks, embeddings)
        ]
        debug_print(f"[DEBUG] inserting {len(records)} records into {table_name}")
        insert_embeddings(table_name, records)

    # 4) 必要ならデータを返却 ----------------------------------------------------
    if return_data:
        return flat_chunks, embeddings
