# src/file_embedder.py
<<<<<<< HEAD

# REM: ベクトル化処理とDB登録を行うユーティリティモジュール
import hashlib
import os
import sys
import json
from typing import List, Optional, Tuple

import numpy as np
import torch
=======
# REM: ベクトル化処理とDB登録を行うユーティリティモジュール
import hashlib, os, numpy as np, torch
>>>>>>> b54278c (更新)
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings
from sentence_transformers import SentenceTransformer
from sqlalchemy import inspect
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.sql import text as sql_text

from src.config import (
    DB_ENGINE,
    DEVELOPMENT_MODE,
    TRUNCATE_ON_STARTUP,
    AUTO_INIT_SCHEMA,
    EMBEDDING_OPTIONS,
    OLLAMA_BASE,
)
from src.error_handler import install_global_exception_handler
install_global_exception_handler()

<<<<<<< HEAD

# ── ユーティリティ関数 ──────────────────────────────────────────

# REM: 利用可能なデバイスを選択（CUDA or CPU）
def pick_embed_device(min_free_vram_mb: int = 1024) -> str:
    """
    GPU が利用可能かつ空き VRAM が min_free_vram_mb 以上あれば "cuda"、
    それ以外は "cpu" を返す。
    """
=======
# ── GPU 空きVRAMをチェックしてデバイスを返すユーティリティ ──
def pick_embed_device(min_free_vram_mb: int = 1024) -> str:
>>>>>>> b54278c (更新)
    if torch.cuda.is_available():
        try:
            free_mb = torch.cuda.mem_get_info()[0] // (1024 * 1024)
        except Exception:
<<<<<<< HEAD
            from pynvml import nvmlInit, nvmlDeviceGetHandleByIndex, nvmlDeviceGetMemoryInfo
=======
            from pynvml import (nvmlInit, nvmlDeviceGetHandleByIndex,
                                nvmlDeviceGetMemoryInfo)
>>>>>>> b54278c (更新)
            nvmlInit()
            handle = nvmlDeviceGetHandleByIndex(0)
            free_mb = nvmlDeviceGetMemoryInfo(handle).free // (1024 * 1024)
        if free_mb >= min_free_vram_mb:
            return "cuda"
    return "cpu"

<<<<<<< HEAD
# REM: numpy配列→pgvector用文字列表現
def to_pgvector_literal(vec: np.ndarray) -> str:
    """
    numpy 配列を pgvector 用の文字列表現に変換する。
    """
    lst = vec.tolist() if isinstance(vec, np.ndarray) else vec
    return "[" + ",".join(f"{float(x):.6f}" for x in lst) + "]"


# ── スキーマ初期化処理 ──────────────────────────────────────────
=======
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
>>>>>>> b54278c (更新)

# REM: 必要テーブルを自動で生成 or 検証し、カラムコメントも付与
def init_schema():
    """
    プロセス起動時に必要テーブルを安全に初期化。
      - AUTO_INIT_SCHEMA=True の場合は DROP → CREATE
      - それ以外は「なければ CREATE」、既存定義と差分があれば警告して終了
      - カラムごとに COMMENT ON を実行
    """
    inspector = inspect(DB_ENGINE)
    with DB_ENGINE.begin() as conn:
<<<<<<< HEAD
        # ── files テーブル ───────────────────────────────────────
        if AUTO_INIT_SCHEMA or not inspector.has_table("files"):
            if inspector.has_table("files"):
                conn.execute(sql_text("DROP TABLE files CASCADE"))
            conn.execute(sql_text("""
                CREATE TABLE files (
                    file_id      SERIAL        PRIMARY KEY,      -- メタID
                    filename     TEXT          NOT NULL UNIQUE,-- 元ファイル名
                    file_hash    TEXT          NOT NULL,        -- SHA256 ハッシュ
                    created_at   TIMESTAMPTZ   NOT NULL DEFAULT now(),  -- 初回登録日時
                    updated_at   TIMESTAMPTZ   NOT NULL DEFAULT now()   -- 最終更新日時
                )
            """))
        else:
            cols = {c["name"] for c in inspector.get_columns("files")}
            for req in ("file_id", "filename", "file_hash", "created_at", "updated_at"):
                if req not in cols:
                    print(f"❌ files テーブルに必須カラム '{req}' がありません。", file=sys.stderr)
                    sys.exit(1)
        # REM: files テーブル各カラムに説明を付与
        conn.execute(sql_text("COMMENT ON COLUMN files.file_id    IS 'メタID（SERIAL PRIMARY KEY）'"))
        conn.execute(sql_text("COMMENT ON COLUMN files.filename   IS '元ファイル名（TEXT, UNIQUE）'"))
        conn.execute(sql_text("COMMENT ON COLUMN files.file_hash  IS 'SHA256 ハッシュ値（ファイル重複検知用）'"))
        conn.execute(sql_text("COMMENT ON COLUMN files.created_at IS '初回登録日時（TIMESTAMPTZ）'"))
        conn.execute(sql_text("COMMENT ON COLUMN files.updated_at IS '最終更新日時（TIMESTAMPTZ）'"))

        # ── file_blobs テーブル ─────────────────────────────────────
        if AUTO_INIT_SCHEMA or not inspector.has_table("file_blobs"):
            if inspector.has_table("file_blobs"):
                conn.execute(sql_text("DROP TABLE file_blobs CASCADE"))
            conn.execute(sql_text("""
                CREATE TABLE file_blobs (
                    blob_id      SERIAL      PRIMARY KEY,
                    file_id      INT         NOT NULL
                                 REFERENCES files(file_id) ON DELETE CASCADE,
                    file_blob    BYTEA       NOT NULL,      -- 元ファイルバイナリ
                    uploaded_at  TIMESTAMPTZ NOT NULL DEFAULT now()  -- アップロード日時
                )
            """))
        else:
            cols = {c["name"] for c in inspector.get_columns("file_blobs")}
            for req in ("blob_id", "file_id", "file_blob", "uploaded_at"):
                if req not in cols:
                    print(f"❌ file_blobs テーブルに必須カラム '{req}' がありません。", file=sys.stderr)
                    sys.exit(1)
        # REM: file_blobs テーブル各カラムに説明を付与
        conn.execute(sql_text("COMMENT ON COLUMN file_blobs.blob_id     IS 'バイナリID（SERIAL PRIMARY KEY）'"))
        conn.execute(sql_text("COMMENT ON COLUMN file_blobs.file_id     IS 'files テーブルへの外部キー'"))
        conn.execute(sql_text("COMMENT ON COLUMN file_blobs.file_blob   IS '元ファイルのバイナリデータ（BYTEA）'"))
        conn.execute(sql_text("COMMENT ON COLUMN file_blobs.uploaded_at IS 'アップロード日時（TIMESTAMPTZ）'"))

        # ── file_contents テーブル ─────────────────────────────────
        if AUTO_INIT_SCHEMA or not inspector.has_table("file_contents"):
            if inspector.has_table("file_contents"):
                conn.execute(sql_text("DROP TABLE file_contents CASCADE"))
            conn.execute(sql_text("""
                CREATE TABLE file_contents (
                    content_id             SERIAL        PRIMARY KEY,
                    file_id                INT           NOT NULL
                                             REFERENCES files(file_id) ON DELETE CASCADE,
                    ocr_raw_text           TEXT          NOT NULL,       -- OCR 未整形テキスト
                    refined_text           TEXT          NOT NULL,       -- LLM 整形後テキスト
                    quality_score          DOUBLE PRECISION,             -- 整形品質スコア
                    refined_at             TIMESTAMPTZ   NOT NULL DEFAULT now(), -- 整形日時
                    is_refined_overwrite   BOOLEAN       NOT NULL DEFAULT TRUE   -- 上書き可否
                )
            """))
        else:
            cols = {c["name"] for c in inspector.get_columns("file_contents")}
            for req in ("content_id", "file_id", "ocr_raw_text", "refined_text",
                        "quality_score", "refined_at", "is_refined_overwrite"):
                if req not in cols:
                    print(f"❌ file_contents テーブルに必須カラム '{req}' がありません。", file=sys.stderr)
                    sys.exit(1)
        # REM: file_contents テーブル各カラムに説明を付与
        conn.execute(sql_text("COMMENT ON COLUMN file_contents.content_id           IS 'コンテンツID（SERIAL PRIMARY KEY）'"))
        conn.execute(sql_text("COMMENT ON COLUMN file_contents.file_id              IS 'files テーブルへの外部キー'"))
        conn.execute(sql_text("COMMENT ON COLUMN file_contents.ocr_raw_text         IS 'OCR 未整形テキスト（TEXT）'"))
        conn.execute(sql_text("COMMENT ON COLUMN file_contents.refined_text         IS 'LLM 整形後テキスト（TEXT）'"))
        conn.execute(sql_text("COMMENT ON COLUMN file_contents.quality_score        IS '整形品質スコア（DOUBLE PRECISION）'"))
        conn.execute(sql_text("COMMENT ON COLUMN file_contents.refined_at           IS '整形日時（TIMESTAMPTZ）'"))
        conn.execute(sql_text("COMMENT ON COLUMN file_contents.is_refined_overwrite IS '上書き可否フラグ（BOOLEAN）'"))

# REM: 自動スキーマ初期化・検証
init_schema()


# ── ファイルメタ UPSERT ──────────────────────────────────────────

# REM: files テーブルに UPSERT して file_id を取得
def insert_file_and_get_id(filepath: str, file_hash: str) -> int:
    """
    files テーブルに UPSERT して file_id を返す。
    filename で衝突したら hash と updated_at を更新。
    """
    with DB_ENGINE.begin() as conn:
=======
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
        if DEVELOPMENT_MODE and truncate_once and not _truncate_files_done:
            conn.execute(sql_text("TRUNCATE TABLE files CASCADE"))
            _truncate_files_done = True

        existing = conn.execute(sql_text(
            "SELECT file_id FROM files WHERE file_hash = :hash"
        ), {"hash": file_hash}).fetchone()
        if existing:
            return existing[0]

>>>>>>> b54278c (更新)
        result = conn.execute(sql_text("""
            INSERT INTO files (filename, file_hash)
            VALUES (:fn, :hash)
            ON CONFLICT (filename)
              DO UPDATE SET
                file_hash  = EXCLUDED.file_hash,
                updated_at = now()
            RETURNING file_id
        """), {
            "fn": os.path.basename(filepath),
            "hash": file_hash
        })
        return result.scalar()

<<<<<<< HEAD

# ── バイナリ INSERT ────────────────────────────────────────────
=======
# REM: embedding_* テーブルの TRUNCATE 状態管理
_truncate_done_tables = set()
>>>>>>> b54278c (更新)

# REM: file_blobs にバイナリを INSERT、blob_id を返す
def insert_blob(file_id: int, blob: bytes) -> int:
    with DB_ENGINE.begin() as conn:
        result = conn.execute(sql_text("""
            INSERT INTO file_blobs (file_id, file_blob)
            VALUES (:fid, :blob)
            RETURNING blob_id
        """), {"fid": file_id, "blob": blob})
        return result.scalar()

<<<<<<< HEAD

# ── テキスト UPSERT ────────────────────────────────────────────

# REM: file_contents に OCR/raw/refined を INSERT or UPDATE
def upsert_content(
    file_id: int,
    ocr_raw: str,
    refined: str,
    score: float,
    overwrite_flag: bool = True
) -> int:
    """
    file_contents テーブルに INSERT or UPDATE。
    既存レコードがあって is_refined_overwrite=False の場合は何もしない。
    """
    with DB_ENGINE.begin() as conn:
        existing = conn.execute(sql_text("""
            SELECT content_id, is_refined_overwrite
            FROM file_contents
            WHERE file_id = :fid
        """), {"fid": file_id}).fetchone()

        if existing:
            cid, lock_flag = existing
            if not lock_flag:
                return cid
            # REM: 上書き許可なら更新
            result = conn.execute(sql_text("""
                UPDATE file_contents
                SET
                  ocr_raw_text  = :ocr,
                  refined_text  = :ref,
                  quality_score = :sc,
                  refined_at    = now()
                WHERE content_id = :cid
                RETURNING content_id
            """), {
                "ocr": ocr_raw,
                "ref": refined,
                "sc": score,
                "cid": cid
            })
            return result.scalar()
        else:
            # REM: 新規 INSERT
            result = conn.execute(sql_text("""
                INSERT INTO file_contents
                  (file_id, ocr_raw_text, refined_text, quality_score)
                VALUES
                  (:fid, :ocr, :ref, :sc)
                RETURNING content_id
            """), {
                "fid": file_id,
                "ocr": ocr_raw,
                "ref": refined,
                "sc": score
            })
            return result.scalar()


# ── 埋め込み＋各種 INSERT ──────────────────────────────────────────

_truncate_tables = set()

# REM: テキストをチャンク化→ファイルメタ/バイナリ/テキスト/埋め込み を一括登録
def embed_and_insert(
    texts: List[str],
    filepath: str,
    model_keys: Optional[List[str]] = None,
    return_data: bool = False,
    quality_score: float = 0.0,
    ocr_raw_text: Optional[str] = None
) -> Optional[Tuple[List[str], List[np.ndarray]]]:
    """
    1) ファイルバイナリ＆ハッシュ
    2) file_blobs への保存
    3) texts 内の各文字列をチャンク化 → flat リスト化
    4) file_contents への UPSERT (ocr_raw_text は texts[0] を想定)
    5) 各モデルでベクトル化 → モデル別テーブルへ保存
    """
    # REM: 1) バイナリ読み込み＆ハッシュ算出
    blob = open(filepath, "rb").read()
    file_hash = hashlib.sha256(blob).hexdigest()

    # REM: 2) メタ／バイナリ登録
    file_id = insert_file_and_get_id(filepath, file_hash)
    insert_blob(file_id, blob)

    # REM: 3) チャンク分割
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks = [splitter.split_text(t) for t in texts]
    flat = [s for grp in chunks for s in grp]
    full = "\n".join(flat)
    raw = ocr_raw_text or full

    # REM: 4) テキスト保存
    upsert_content(file_id, raw, full, quality_score)

    all_chunks: List[str] = []
    all_embeds: List[np.ndarray] = []

    # REM: 5) モデルごとにベクトル化＆専用テーブルへ
=======
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks = [splitter.split_text(t) for t in texts]
    flat_chunks = [s for c in chunks for s in c]

    # ★ 空白のみチャンクを除外し、全部空ならスキップ
    flat_chunks = [s for s in flat_chunks if s.strip()]
    if not flat_chunks:
        return [], []

    full_text = "\n".join(flat_chunks)

    file_id = insert_file_and_get_id(filename, full_text, quality_score, truncate_once=True)

>>>>>>> b54278c (更新)
    for key, cfg in EMBEDDING_OPTIONS.items():
        if model_keys and key not in model_keys:
            continue

<<<<<<< HEAD
        # REM: 埋め込み実行
        if cfg["embedder"] == "OllamaEmbeddings":
            emb = OllamaEmbeddings(model=cfg["model_name"], base_url=OLLAMA_BASE)
            vectors = emb.embed_documents(flat)
        else:
            device = pick_embed_device()
            embedder = SentenceTransformer(cfg["model_name"], device=device)
            vectors = embedder.encode(
                flat,
                batch_size=(16 if device == "cuda" else 8),
                convert_to_numpy=True
            )

        tbl = cfg["model_name"].replace("/", "_").replace("-", "_") + f"_{cfg['dimension']}"

        # REM: 初回のみテーブルを TRUNCATE
        if tbl not in _truncate_tables:
            with DB_ENGINE.begin() as conn:
                conn.execute(sql_text(f'TRUNCATE TABLE "{tbl}" CASCADE'))
            _truncate_tables.add(tbl)

        # REM: レコード登録
        recs = [
            {
                "content": txt,
                "embedding": to_pgvector_literal(vec),
                "file_id": file_id
            }
            for txt, vec in zip(flat, vectors)
        ]
        with DB_ENGINE.begin() as conn:
            conn.execute(sql_text(f"""
                INSERT INTO "{tbl}" (content, embedding, file_id)
                VALUES (:content, :embedding, :file_id)
            """), recs)

        if return_data:
            all_chunks.extend(flat)
            all_embeds.extend(vectors)

    if return_data:
        return all_chunks, all_embeds
    return None
=======
        if cfg["embedder"] == "OllamaEmbeddings":
            embedder = OllamaEmbeddings(model=cfg["model_name"], base_url=OLLAMA_BASE)
            embeddings = embedder.embed_documents(flat_chunks)

        elif cfg["embedder"] == "SentenceTransformer":
            from torch.cuda import OutOfMemoryError
            device = pick_embed_device(1024)
            try:
                embedder = SentenceTransformer(cfg["model_name"], device=device)
            except OutOfMemoryError:
                torch.cuda.empty_cache()
                device = "cpu"
                embedder = SentenceTransformer(cfg["model_name"], device=device)

            batch = 16 if device == "cuda" else 8
            try:
                embeddings = embedder.encode(flat_chunks, batch_size=batch,
                                             convert_to_numpy=True,
                                             show_progress_bar=(device == "cuda"))
            except OutOfMemoryError:
                if device == "cuda":
                    torch.cuda.empty_cache()
                    embedder = SentenceTransformer(cfg["model_name"], device="cpu")
                    embeddings = embedder.encode(flat_chunks, batch_size=8,
                                                 convert_to_numpy=True)
                else:
                    raise
        else:
            print(f"⚠️ 未対応の埋め込み: {cfg['embedder']}")
            continue

        table = cfg["model_name"].replace("/", "_").replace("-", "_") + f"_{cfg['dimension']}"
        with DB_ENGINE.begin() as conn:
            conn.execute(sql_text(f"""
                CREATE TABLE IF NOT EXISTS "{table}" (
                    id SERIAL PRIMARY KEY,
                    content TEXT,
                    embedding VECTOR({cfg['dimension']}),
                    file_id INTEGER REFERENCES files(file_id)
                )
            """))
            if table not in _truncate_done_tables:
                conn.execute(sql_text(f'TRUNCATE TABLE "{table}" CASCADE'))
                _truncate_done_tables.add(table)

            insert_sql = sql_text(f"""
                INSERT INTO "{table}" (content, embedding, file_id)
                VALUES (:content, :embedding, :file_id)
            """)
            records = [{
                "content": ch,
                "embedding": to_pgvector_literal(vec),
                "file_id": file_id
            } for ch, vec in zip(flat_chunks, embeddings)]
            conn.execute(insert_sql, records)

    return (flat_chunks, embeddings) if return_data else None
>>>>>>> b54278c (更新)
