# db/blob_handler.py
# ファイルバイナリ操作専用ハンドラ

import os
import hashlib
import mimetypes
from typing import Optional
from uuid import UUID
from sqlalchemy.sql import text as sql_text

from src.config import DB_ENGINE
from src.utils import debug_print

DEFAULT_MIME = "application/octet-stream"

def _calc_sha256(path: str) -> str:
    """ファイルのSHA256ハッシュを計算"""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def find_existing_by_checksum(checksum: str) -> Optional[str]:
    """checksumで既存ファイルを検索し、あればそのblob_idを返す"""
    with DB_ENGINE.connect() as conn:
        row = conn.execute(sql_text("""
            SELECT blob_id FROM files_blob WHERE checksum = :checksum
        """), {"checksum": checksum}).fetchone()
    return str(row[0]) if row else None

def get_file_blob(blob_id: str) -> Optional[bytes]:
    """files_blob からバイナリを取得"""
    with DB_ENGINE.connect() as conn:
        row = conn.execute(sql_text("""
            SELECT file_blob FROM files_blob WHERE blob_id = :blob_id
        """), {"blob_id": blob_id}).fetchone()
    return row[0] if row else None

def insert_file_blob(file_path: str) -> tuple[str, str]:
    """
    ファイルをfiles_blobに挿入し、(blob_id, checksum)を返す
    重複チェック済みの前提
    """
    import uuid
    
    # ファイル情報取得
    checksum = _calc_sha256(file_path)
    file_size = os.path.getsize(file_path)
    mime_type = mimetypes.guess_type(file_path)[0] or DEFAULT_MIME
    
    # バイナリ読み込み
    with open(file_path, "rb") as f:
        file_blob = f.read()
    
    # UUID生成
    blob_id = str(uuid.uuid4())
    
    # DB挿入
    with DB_ENGINE.begin() as conn:
        conn.execute(sql_text("""
            INSERT INTO files_blob (blob_id, checksum, file_blob, size, mime_type)
            VALUES (:blob_id, :checksum, :file_blob, :size, :mime_type)
        """), {
            "blob_id": blob_id,
            "checksum": checksum,
            "file_blob": file_blob,
            "size": file_size,
            "mime_type": mime_type
        })
    
    debug_print(f"✅ files_blob 挿入完了: {blob_id}")
    return blob_id, checksum