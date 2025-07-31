# new/api/upload.py
# ファイルアップロードAPI

import os
import hashlib
import mimetypes
from typing import List
from uuid import uuid4
from fastapi import APIRouter, File, UploadFile, HTTPException, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.engine import Connection

from database.connection import get_db_connection
from database.models import FILE_STATUS
from config import SUPPORTED_EXTENSIONS, MAX_FILE_SIZE, UPLOAD_TEMP_DIR, LOGGER
from schemas import UploadResponse, BatchUploadResponse

router = APIRouter(prefix="/upload", tags=["upload"])


def _calculate_checksum(file_path: str) -> str:
    """ファイルのSHA256チェックサムを計算"""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()


def _validate_file(file: UploadFile) -> None:
    """ファイルの妥当性検証"""
    if not file.filename:
        raise HTTPException(status_code=400, detail="ファイル名が指定されていません")
    
    # 拡張子チェック
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=400, 
            detail=f"サポートされていない拡張子です: {file_ext}"
        )
    
    # ファイルサイズチェック（ヘッダーから）
    if hasattr(file, 'size') and file.size and file.size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413, 
            detail=f"ファイルサイズが上限を超えています: {file.size} bytes"
        )


def _save_temp_file(file: UploadFile) -> str:
    """一時ファイルとして保存"""
    temp_filename = f"{uuid4()}{os.path.splitext(file.filename)[1]}"
    temp_path = os.path.join(UPLOAD_TEMP_DIR, temp_filename)
    
    try:
        with open(temp_path, "wb") as buffer:
            file.file.seek(0)  # ファイルポインタをリセット
            total_size = 0
            
            while True:
                chunk = file.file.read(8192)
                if not chunk:
                    break
                
                total_size += len(chunk)
                if total_size > MAX_FILE_SIZE:
                    os.unlink(temp_path)  # 一時ファイル削除
                    raise HTTPException(
                        status_code=413,
                        detail=f"ファイルサイズが上限を超えています: {total_size} bytes"
                    )
                
                buffer.write(chunk)
        
        return temp_path
        
    except Exception as e:
        if os.path.exists(temp_path):
            os.unlink(temp_path)
        raise


def _store_file_to_db(
    file: UploadFile, 
    temp_path: str, 
    connection: Connection
) -> str:
    """ファイルをデータベースに格納"""
    try:
        # ファイル情報取得
        file_size = os.path.getsize(temp_path)
        checksum = _calculate_checksum(temp_path)
        mime_type = mimetypes.guess_type(file.filename)[0] or "application/octet-stream"
        
        # 重複チェック
        duplicate_query = "SELECT id FROM files_blob WHERE checksum = :checksum"
        existing = connection.execute(text(duplicate_query), {"checksum": checksum}).fetchone()
        
        if existing:
            raise HTTPException(
                status_code=409,
                detail=f"同じファイルが既に存在します: {file.filename}"
            )
        
        # バイナリデータ読み込み
        with open(temp_path, "rb") as f:
            blob_data = f.read()
        
        # ファイルID生成
        file_id = str(uuid4())
        
        # files_blobテーブルに挿入
        blob_insert = """
            INSERT INTO files_blob (id, checksum, blob_data)
            VALUES (:id, :checksum, :blob_data)
        """
        connection.execute(text(blob_insert), {
            "id": file_id,
            "checksum": checksum,
            "blob_data": blob_data
        })
        
        # files_metaテーブルに挿入
        meta_insert = """
            INSERT INTO files_meta (blob_id, file_name, mime_type, size, status)
            VALUES (:blob_id, :file_name, :mime_type, :size, :status)
        """
        connection.execute(text(meta_insert), {
            "blob_id": file_id,
            "file_name": file.filename,
            "mime_type": mime_type,
            "size": file_size,
            "status": FILE_STATUS["UPLOADED"]
        })
        
        connection.commit()
        return file_id
        
    except HTTPException:
        connection.rollback()
        raise
    except Exception as e:
        connection.rollback()
        LOGGER.error(f"Failed to store file to database: {e}")
        raise HTTPException(status_code=500, detail="ファイルの保存に失敗しました")


@router.post("/single", response_model=UploadResponse)
async def upload_single_file(
    file: UploadFile = File(...),
    connection: Connection = Depends(get_db_connection)
):
    """
    単一ファイルをアップロードする
    """
    temp_path = None
    
    try:
        # ファイル検証
        _validate_file(file)
        
        # 一時ファイル保存
        temp_path = _save_temp_file(file)
        
        # データベースに格納
        file_id = _store_file_to_db(file, temp_path, connection)
        
        # 一時ファイル削除
        os.unlink(temp_path)
        
        return UploadResponse(
            status="success",
            message=f"ファイル '{file.filename}' をアップロードしました",
            file_id=file_id,
            file_name=file.filename,
            size=os.path.getsize(temp_path) if os.path.exists(temp_path) else 0,
            checksum=_calculate_checksum(temp_path) if os.path.exists(temp_path) else ""
        )
        
    except HTTPException:
        if temp_path and os.path.exists(temp_path):
            os.unlink(temp_path)
        raise
    except Exception as e:
        if temp_path and os.path.exists(temp_path):
            os.unlink(temp_path)
        LOGGER.error(f"Upload failed: {e}")
        raise HTTPException(status_code=500, detail="アップロードに失敗しました")


@router.post("/batch", response_model=BatchUploadResponse)
async def upload_multiple_files(
    files: List[UploadFile] = File(...),
    connection: Connection = Depends(get_db_connection)
):
    """
    複数ファイルを一括アップロードする
    """
    if len(files) > 50:  # 一度に50ファイルまで
        raise HTTPException(status_code=400, detail="一度にアップロードできるファイル数は50個までです")
    
    results = []
    success_count = 0
    error_count = 0
    
    for file in files:
        temp_path = None
        try:
            # ファイル検証
            _validate_file(file)
            
            # 一時ファイル保存
            temp_path = _save_temp_file(file)
            
            # データベースに格納
            file_id = _store_file_to_db(file, temp_path, connection)
            
            # 成功結果追加
            results.append({
                "filename": file.filename,
                "file_id": file_id,
                "status": "success",
                "size": os.path.getsize(temp_path),
                "message": "アップロード成功"
            })
            success_count += 1
            
            # 一時ファイル削除
            os.unlink(temp_path)
            
        except HTTPException as e:
            # エラー結果追加
            results.append({
                "filename": file.filename,
                "file_id": None,
                "status": "error",
                "size": 0,
                "message": str(e.detail)
            })
            error_count += 1
            
            if temp_path and os.path.exists(temp_path):
                os.unlink(temp_path)
                
        except Exception as e:
            # 予期しないエラー
            results.append({
                "filename": file.filename,
                "file_id": None,
                "status": "error",
                "size": 0,
                "message": f"予期しないエラー: {str(e)}"
            })
            error_count += 1
            
            if temp_path and os.path.exists(temp_path):
                os.unlink(temp_path)
    
    return BatchUploadResponse(
        status="success" if error_count == 0 else "partial",
        message=f"アップロード完了: 成功 {success_count}件, 失敗 {error_count}件",
        results=results,
        success_count=success_count,
        error_count=error_count
    )


@router.get("/status")
def get_upload_status():
    """
    アップロード機能のステータスを取得する
    """
    try:
        # ディスク容量チェック
        import shutil
        total, used, free = shutil.disk_usage(UPLOAD_TEMP_DIR)
        
        return JSONResponse({
            "status": "success",
            "data": {
                "max_file_size": MAX_FILE_SIZE,
                "supported_extensions": list(SUPPORTED_EXTENSIONS),
                "temp_dir": UPLOAD_TEMP_DIR,
                "disk_usage": {
                    "total": total,
                    "used": used,
                    "free": free,
                    "usage_percent": round(used / total * 100, 1)
                },
                "upload_available": free > MAX_FILE_SIZE
            }
        })
        
    except Exception as e:
        LOGGER.error(f"Failed to get upload status: {e}")
        raise HTTPException(status_code=500, detail="アップロードステータスの取得に失敗しました")