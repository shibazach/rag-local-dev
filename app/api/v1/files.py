"""
ファイル管理API v1
File management endpoints with upload/download/processing
"""

import hashlib
import mimetypes
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Request, Response, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.core import (
    get_db,
    FilesBlob,
    FilesMeta,
    FilesText,
    FileResponse,
    FileListResponse,
    FileTextResponse,
    UploadResponse,
    BatchUploadResponse,
    BaseResponse,
    PaginatedResponse
)
from app.api import (
    DatabaseSession,
    Pagination,
    FileFilters,
    log_api_request,
    create_error_response
)
from app.auth.dependencies import get_current_user_optional, get_current_user_required
from app.config import config, logger

router = APIRouter(prefix="/files", tags=["File Management"])

def calculate_checksum(file_content: bytes) -> str:
    """ファイルチェックサム計算"""
    return hashlib.sha256(file_content).hexdigest()

def get_mime_type(filename: str) -> str:
    """MIMEタイプ取得"""
    mime_type, _ = mimetypes.guess_type(filename)
    return mime_type or "application/octet-stream"

@router.post("/upload", response_model=UploadResponse)
async def upload_file(
    request: Request,
    file: UploadFile = File(...),
    current_user = Depends(get_current_user_required),
    db: Session = DatabaseSession
):
    """
    ファイルアップロード
    Upload file with deduplication and metadata storage
    """
    try:
        # ファイル検証
        if not file.filename:
            raise create_error_response(
                400, "FILE_INVALID",
                "ファイル名が指定されていません"
            )
        
        # 拡張子チェック
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in config.ALLOWED_EXTENSIONS:
            raise create_error_response(
                400, "FILE_TYPE_NOT_ALLOWED",
                f"サポートされていないファイル形式です: {file_ext}"
            )
        
        # ファイル読み込み
        file_content = await file.read()
        
        # サイズチェック
        if len(file_content) > config.MAX_UPLOAD_SIZE:
            raise create_error_response(
                413, "FILE_TOO_LARGE",
                f"ファイルサイズが上限を超えています: {config.MAX_UPLOAD_SIZE} bytes"
            )
        
        # チェックサム計算
        checksum = calculate_checksum(file_content)
        
        # 重複チェック
        existing_blob = db.query(FilesBlob).filter(FilesBlob.checksum == checksum).first()
        if existing_blob:
            existing_meta = db.query(FilesMeta).filter(FilesMeta.blob_id == existing_blob.id).first()
            log_api_request(request, current_user, f"file_duplicate_{checksum[:8]}")
            
            return UploadResponse(
                success=True,
                message="同じファイルが既に存在します",
                file_id=existing_blob.id,
                filename=existing_meta.original_filename if existing_meta else file.filename,
                size=len(file_content),
                checksum=checksum
            )
        
        # MIMEタイプ取得
        mime_type = get_mime_type(file.filename)
        
        # ファイルバイナリ保存
        blob = FilesBlob(
            checksum=checksum,
            blob_data=file_content
        )
        db.add(blob)
        db.flush()  # IDを取得するためフラッシュ
        
        # メタデータ保存
        meta = FilesMeta(
            blob_id=blob.id,
            file_name=file.filename,
            original_filename=file.filename,
            mime_type=mime_type,
            file_size=len(file_content),
            processing_status="uploaded",
            processing_stage="uploaded"
        )
        db.add(meta)
        
        db.commit()
        
        log_api_request(request, current_user, f"file_upload_{file.filename}")
        
        return UploadResponse(
            success=True,
            message="ファイルをアップロードしました",
            file_id=blob.id,
            filename=file.filename,
            size=len(file_content),
            checksum=checksum
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"ファイルアップロードエラー: {e}")
        db.rollback()
        raise create_error_response(
            500, "FILE_UPLOAD_ERROR",
            "ファイルアップロード中にエラーが発生しました"
        )

@router.post("/upload/batch", response_model=BatchUploadResponse)
async def upload_multiple_files(
    request: Request,
    files: List[UploadFile] = File(...),
    current_user = Depends(get_current_user_required),
    db: Session = DatabaseSession
):
    """
    複数ファイル一括アップロード
    Batch upload multiple files
    """
    try:
        uploaded_files = []
        failed_files = []
        
        for file in files:
            try:
                # 個別ファイルアップロード処理
                upload_result = await upload_file(request, file, current_user, db)
                uploaded_files.append(upload_result)
                
            except Exception as e:
                logger.error(f"ファイルアップロード失敗 {file.filename}: {e}")
                failed_files.append(file.filename or "unknown")
        
        log_api_request(
            request, current_user, 
            f"batch_upload_{len(uploaded_files)}_{len(failed_files)}"
        )
        
        return BatchUploadResponse(
            success=len(failed_files) == 0,
            message=f"{len(uploaded_files)}件のファイルをアップロードしました",
            uploaded_files=uploaded_files,
            failed_files=failed_files,
            total_uploaded=len(uploaded_files),
            total_failed=len(failed_files)
        )
        
    except Exception as e:
        logger.error(f"バッチアップロードエラー: {e}")
        raise create_error_response(
            500, "BATCH_UPLOAD_ERROR",
            "バッチアップロード中にエラーが発生しました"
        )

@router.get("/", response_model=FileListResponse)
async def list_files(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    current_user: Optional[dict] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    ファイル一覧取得
    Get paginated file list with filtering
    """
    try:
        # ベースクエリ
        query = db.query(FilesMeta)
        
        # フィルタリング
        if status:
            query = query.filter(FilesMeta.processing_status == status)
        
        if search:
            query = query.filter(FilesMeta.file_name.contains(search))
        
        # TODO: 日付フィルター実装
        
        # 総件数取得
        total = query.count()
        
        # ソート
        if pagination.sort_by == "name":
            if pagination.sort_order == "asc":
                query = query.order_by(FilesMeta.file_name.asc())
            else:
                query = query.order_by(FilesMeta.file_name.desc())
        else:
            # デフォルト: 作成日時降順
            query = query.order_by(FilesMeta.created_at.desc())
        
        # ページネーション適用
        files = query.offset(pagination.offset).limit(pagination.limit).all()
        
        # レスポンス変換
        file_responses = []
        for file_meta in files:
            file_response = FileResponse(
                id=file_meta.blob_id,
                original_filename=file_meta.original_filename,
                file_name=file_meta.file_name,
                mime_type=file_meta.mime_type,
                file_size=file_meta.file_size,
                processing_status=file_meta.processing_status,
                processing_stage=file_meta.processing_stage,
                created_at=file_meta.created_at,
                updated_at=file_meta.updated_at,
                processed_at=file_meta.processed_at,
                is_processed=file_meta.is_processed,
                page_count=file_meta.page_count
            )
            file_responses.append(file_response)
        
        total_pages = (total + pagination.per_page - 1) // pagination.per_page
        
        return FileListResponse(
            files=file_responses,
            total=total,
            page=pagination.page,
            per_page=pagination.per_page,
            total_pages=total_pages
        )
        
    except Exception as e:
        logger.error(f"ファイル一覧取得エラー: {e}")
        raise create_error_response(
            500, "FILE_LIST_ERROR",
            "ファイル一覧取得中にエラーが発生しました"
        )

@router.get("/{file_id}", response_model=FileResponse)
async def get_file_info(
    file_id: str,
    current_user = Depends(get_current_user_required),
    db: Session = DatabaseSession
):
    """
    ファイル情報取得
    Get specific file information
    """
    try:
        file_uuid = UUID(file_id)
        file_meta = db.query(FilesMeta).filter(FilesMeta.blob_id == file_uuid).first()
        
        if not file_meta:
            raise create_error_response(
                404, "FILE_NOT_FOUND",
                "ファイルが見つかりません"
            )
        
        return FileResponse(
            id=file_meta.blob_id,
            original_filename=file_meta.original_filename,
            file_name=file_meta.file_name,
            mime_type=file_meta.mime_type,
            file_size=file_meta.file_size,
            processing_status=file_meta.processing_status,
            processing_stage=file_meta.processing_stage,
            created_at=file_meta.created_at,
            updated_at=file_meta.updated_at,
            processed_at=file_meta.processed_at,
            is_processed=file_meta.is_processed,
            page_count=file_meta.page_count
        )
        
    except ValueError:
        raise create_error_response(
            400, "INVALID_FILE_ID",
            "無効なファイルIDです"
        )
    except Exception as e:
        logger.error(f"ファイル情報取得エラー: {e}")
        raise create_error_response(
            500, "FILE_INFO_ERROR",
            "ファイル情報取得中にエラーが発生しました"
        )

@router.get("/{file_id}/download")
async def download_file(
    file_id: str,
    current_user = Depends(get_current_user_required),
    db: Session = DatabaseSession
):
    """
    ファイルダウンロード
    Download file binary data
    """
    try:
        file_uuid = UUID(file_id)
        
        # ファイル取得
        blob = db.query(FilesBlob).filter(FilesBlob.id == file_uuid).first()
        meta = db.query(FilesMeta).filter(FilesMeta.blob_id == file_uuid).first()
        
        if not blob or not meta:
            raise create_error_response(
                404, "FILE_NOT_FOUND",
                "ファイルが見つかりません"
            )
        
        # ストリーミングレスポンス作成
        def iter_file():
            yield blob.blob_data
        
        return StreamingResponse(
            iter_file(),
            media_type=meta.mime_type,
            headers={
                "Content-Disposition": f"attachment; filename={meta.original_filename}",
                "Content-Length": str(meta.file_size)
            }
        )
        
    except ValueError:
        raise create_error_response(
            400, "INVALID_FILE_ID",
            "無効なファイルIDです"
        )
    except Exception as e:
        logger.error(f"ファイルダウンロードエラー: {e}")
        raise create_error_response(
            500, "FILE_DOWNLOAD_ERROR",
            "ファイルダウンロード中にエラーが発生しました"
        )

@router.get("/{file_id}/preview")
async def preview_file(
    file_id: str,
    current_user = Depends(get_current_user_required),
    db: Session = DatabaseSession
):
    """
    ファイルプレビュー
    Preview file for inline display
    """
    try:
        file_uuid = UUID(file_id)
        
        # ファイル取得
        blob = db.query(FilesBlob).filter(FilesBlob.id == file_uuid).first()
        meta = db.query(FilesMeta).filter(FilesMeta.blob_id == file_uuid).first()
        
        if not blob or not meta:
            raise create_error_response(
                404, "FILE_NOT_FOUND",
                "ファイルが見つかりません"
            )
        
        # ストリーミングレスポンス作成
        def iter_file():
            yield blob.blob_data
        
        return StreamingResponse(
            iter_file(),
            media_type=meta.mime_type,
            headers={
                "Content-Disposition": f"inline; filename={meta.original_filename}",
                "Content-Length": str(meta.file_size)
            }
        )
        
    except ValueError:
        raise create_error_response(
            400, "INVALID_FILE_ID",
            "無効なファイルIDです"
        )
    except Exception as e:
        logger.error(f"ファイルプレビューエラー: {e}")
        raise create_error_response(
            500, "FILE_PREVIEW_ERROR",
            "ファイルプレビュー中にエラーが発生しました"
        )

@router.get("/{file_id}/text", response_model=FileTextResponse)
async def get_file_text(
    file_id: str,
    current_user = Depends(get_current_user_required),
    db: Session = DatabaseSession
):
    """
    ファイルテキスト取得
    Get extracted and refined text content
    """
    try:
        file_uuid = UUID(file_id)
        file_text = db.query(FilesText).filter(FilesText.blob_id == file_uuid).first()
        
        if not file_text:
            raise create_error_response(
                404, "FILE_TEXT_NOT_FOUND",
                "ファイルテキストが見つかりません"
            )
        
        return FileTextResponse.from_orm(file_text)
        
    except ValueError:
        raise create_error_response(
            400, "INVALID_FILE_ID",
            "無効なファイルIDです"
        )
    except Exception as e:
        logger.error(f"ファイルテキスト取得エラー: {e}")
        raise create_error_response(
            500, "FILE_TEXT_ERROR",
            "ファイルテキスト取得中にエラーが発生しました"
        )

@router.delete("/{file_id}", response_model=BaseResponse)
async def delete_file(
    file_id: str,
    current_user = Depends(get_current_user_required),
    db: Session = DatabaseSession
):
    """
    ファイル削除
    Delete file and all associated data
    """
    try:
        file_uuid = UUID(file_id)
        
        # ファイル存在確認
        blob = db.query(FilesBlob).filter(FilesBlob.id == file_uuid).first()
        if not blob:
            raise create_error_response(
                404, "FILE_NOT_FOUND",
                "ファイルが見つかりません"
            )
        
        # ファイル削除（カスケード削除でメタデータも削除される）
        db.delete(blob)
        db.commit()
        
        logger.info(f"ファイル削除完了: {file_id} by {current_user.get('username')}")
        
        return BaseResponse(
            success=True,
            message="ファイルを削除しました"
        )
        
    except ValueError:
        raise create_error_response(
            400, "INVALID_FILE_ID",
            "無効なファイルIDです"
        )
    except Exception as e:
        logger.error(f"ファイル削除エラー: {e}")
        db.rollback()
        raise create_error_response(
            500, "FILE_DELETE_ERROR",
            "ファイル削除中にエラーが発生しました"
        )