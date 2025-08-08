"""
ファイルサービス - Prototype統合版 + new/系高機能移植
ファイル管理・アップロード・メタデータ処理（同期処理版）
"""

import hashlib
import mimetypes
import os
import tempfile
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Union, BinaryIO, Tuple
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import select, update, delete, func
from fastapi import UploadFile, HTTPException

from app.config import config, logger
from app.core.database import get_db_session, SessionLocal
from app.core.db_handler import FileDBHandler
from app.core.models import FilesBlob, FilesMeta, FilesText, FilesImage
from app.core.schemas import UploadResponse, BatchUploadResponse, FileInfoResponse

class FileService:
    """ファイル管理サービス（同期処理版 + new/系高機能移植）"""
    
    def __init__(self, db_session: Optional[Session] = None):
        """
        Args:
            db_session: データベースセッション（オプショナル）
        """
        self.db = db_session
        self.upload_dir = config.UPLOAD_DIR
        self.processed_dir = config.PROCESSED_DIR
        
        # ディレクトリ作成
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.processed_dir.mkdir(parents=True, exist_ok=True)
    
        # サポート対象拡張子・MIMEタイプマッピング
        self.supported_extensions = set(config.ALLOWED_EXTENSIONS)
        self.mime_mappings = {
            '.pdf': 'application/pdf',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            '.txt': 'text/plain',
            '.csv': 'text/csv',
            '.json': 'application/json',
            '.eml': 'message/rfc822',
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg'
        }
    
    def upload_file(
        self,
        file: UploadFile,
        user_id: Optional[str] = None
    ) -> UploadResponse:
        """
        単一ファイルアップロード（new/系移植版）
        
        Args:
            file: アップロードファイル
            user_id: ユーザーID
            
        Returns:
            アップロード結果レスポンス
        """
        temp_path = None
        
        try:
            # ファイルバリデーション
            self._validate_file(file)
            
            # 一時ファイル保存
            temp_path = self._save_temp_file(file)
            
            # チェックサム計算
            checksum = FileDBHandler.calc_checksum(temp_path)
            
            # データベース登録
            file_id, is_new = self._store_file_to_db(file, temp_path, checksum, user_id)
            
            # 一時ファイル削除
            os.unlink(temp_path)
            
            message = f"ファイル '{file.filename}' をアップロードしました"
            if not is_new:
                message = f"ファイル '{file.filename}' は既に存在します（重複スキップ）"
            
            logger.info(f"ファイルアップロード成功: {file.filename} (ID: {file_id})")
            
            return UploadResponse(
                status="success",
                message=message,
                file_id=UUID(file_id),
                file_name=file.filename,
                size=os.path.getsize(temp_path) if os.path.exists(temp_path) else file.size,
                checksum=checksum
            )
            
        except HTTPException:
            if temp_path and os.path.exists(temp_path):
                os.unlink(temp_path)
            raise
        except Exception as e:
            if temp_path and os.path.exists(temp_path):
                os.unlink(temp_path)
            logger.error(f"ファイルアップロードエラー: {e}")
            return UploadResponse(
                status="error",
                message=f"アップロードに失敗しました: {str(e)}",
                file_name=file.filename or "unknown"
            )
    
    def _validate_file(self, file: UploadFile) -> None:
        """ファイルバリデーション（new/系強化版）"""
        if not file.filename:
            raise HTTPException(status_code=400, detail="ファイル名が指定されていません")
        
        # 拡張子チェック
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in self.supported_extensions:
            raise HTTPException(
                status_code=415,
                detail=f"サポートされていない拡張子です: {file_ext}。"
                       f"対応形式: {', '.join(sorted(self.supported_extensions))}"
            )
        
        # ファイルサイズチェック（ヘッダーから）
        if hasattr(file, 'size') and file.size and file.size > config.MAX_UPLOAD_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"ファイルサイズが制限を超えています: {file.size // 1024 // 1024}MB "
                       f"（最大: {config.MAX_UPLOAD_SIZE // 1024 // 1024}MB）"
            )
    
    def _save_temp_file(self, file: UploadFile) -> str:
        """一時ファイル保存（new/系移植版）"""
        temp_filename = f"{uuid.uuid4()}{Path(file.filename).suffix}"
        temp_path = os.path.join(tempfile.gettempdir(), temp_filename)
        
        try:
            with open(temp_path, "wb") as buffer:
                file.file.seek(0)  # ファイルポインタをリセット
                total_size = 0
                
                while True:
                    chunk = file.file.read(8192)
                    if not chunk:
                        break
                    
                    total_size += len(chunk)
                    # 実際のファイルサイズチェック
                    if total_size > config.MAX_UPLOAD_SIZE:
                        os.unlink(temp_path)  # 一時ファイル削除
                        raise HTTPException(
                            status_code=413,
                            detail=f"ファイルサイズが制限を超えています: {total_size // 1024 // 1024}MB"
                        )
                    
                    buffer.write(chunk)
            
            logger.info(f"一時ファイル保存完了: {temp_path}")
            return temp_path
            
        except Exception as e:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
            raise
    
    def _store_file_to_db(
        self,
        file: UploadFile,
        temp_path: str,
        checksum: str,
        user_id: Optional[str] = None
    ) -> Tuple[str, bool]:
        """
        ファイルをデータベースに格納（Files4兄弟対応）
        
        Args:
            file: アップロードファイル
            temp_path: 一時ファイルパス
            checksum: SHA256チェックサム
            user_id: ユーザーID
            
        Returns:
            (file_id, is_new) のタプル
        """
        try:
            # データベースセッション取得
            with get_db_session() as db:
                db_handler = FileDBHandler(db)
                
                # 重複チェック
                existing_id = db_handler.find_existing_by_checksum(checksum)
                if existing_id:
                    logger.info(f"既存ファイル検出: {file.filename} (ID: {existing_id})")
                    return existing_id, False
                
                # ファイル情報準備
                file_size = os.path.getsize(temp_path)
                file_ext = Path(file.filename).suffix.lower()
                mime_type = self.mime_mappings.get(file_ext) or mimetypes.guess_type(file.filename)[0] or "application/octet-stream"
                
                # FileDBHandlerでFiles4兄弟に一括登録
                file_id, is_new = db_handler.insert_file_full(
                    file_path=temp_path,
                    original_filename=file.filename,
                    raw_text=None,  # OCR処理は後で実行
                    refined_text=None,
                    quality_score=None,
                    tags=[]
                )
                
                logger.info(f"ファイルDB登録完了: {file.filename} (ID: {file_id}, new: {is_new})")
                return file_id, is_new
                
        except Exception as e:
            logger.error(f"データベース登録エラー: {e}")
            raise HTTPException(status_code=500, detail="ファイルの保存に失敗しました")
    
    def upload_batch_files(
        self,
        files: List[UploadFile],
        user_id: Optional[str] = None
    ) -> BatchUploadResponse:
        """
        バッチファイルアップロード（new/系移植版）
        
        Args:
            files: アップロードファイルリスト
            user_id: ユーザーID
            
        Returns:
            バッチアップロード結果レスポンス
        """
        if len(files) > 50:  # 一度に50ファイルまで
            raise HTTPException(status_code=400, detail="一度にアップロードできるファイル数は50個までです")
        
        results = []
        success_count = 0
        error_count = 0
        
        for file in files:
            try:
                result = self.upload_file(file, user_id)
                if result.status == "success":
                    success_count += 1
                else:
                    error_count += 1
                results.append(result)
                
            except HTTPException as e:
                error_result = UploadResponse(
                    status="error",
                    message=str(e.detail),
                    file_name=file.filename or "unknown"
                )
                results.append(error_result)
                error_count += 1
                
            except Exception as e:
                error_result = UploadResponse(
                    status="error",
                    message=f"予期しないエラー: {str(e)}",
                    file_name=file.filename or "unknown"
                )
                results.append(error_result)
                error_count += 1
        
        overall_status = "success" if error_count == 0 else "partial"
        message = f"バッチアップロード完了: 成功 {success_count}件, 失敗 {error_count}件"
        
        logger.info(f"バッチアップロード完了: 成功={success_count}, 失敗={error_count}")
        
        return BatchUploadResponse(
            status=overall_status,
            message=message,
            results=results,
            success_count=success_count,
            error_count=error_count
        )
    
    def get_upload_status(self) -> Dict[str, Any]:
        """
        アップロード機能のステータス取得（new/系移植版）
        
        Returns:
            アップロードステータス情報
        """
        try:
            import shutil
            
            # ディスク使用量チェック
            upload_dir_str = str(self.upload_dir)
            total, used, free = shutil.disk_usage(upload_dir_str)
            
            return {
                "status": "success",
                "data": {
                    "max_file_size": config.MAX_UPLOAD_SIZE,
                    "supported_extensions": sorted(list(self.supported_extensions)),
                    "upload_dir": upload_dir_str,
                    "processed_dir": str(self.processed_dir),
                    "disk_usage": {
                        "total": total,
                        "used": used,
                        "free": free,
                        "usage_percent": round(used / total * 100, 1)
                    },
                    "upload_available": free > config.MAX_UPLOAD_SIZE
                }
            }
            
        except Exception as e:
            logger.error(f"アップロードステータス取得エラー: {e}")
            return {
                "status": "error",
                "data": {
                    "error": str(e)
                }
            }
    
    def get_file_list(
        self,
        user_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        ファイルリスト取得（同期処理版）
        読み込み専用なのでcommit不要
        
        Returns:
            ファイルリスト情報
        """
        try:
            # with文でセッション管理（読み込み専用）
            with SessionLocal() as db:
                # ファイル総数を取得
                count_query = select(func.count()).select_from(FilesBlob)
                total_result = db.execute(count_query)
                total = total_result.scalar() or 0
                
                # ファイルリストを取得（blob_dataと大きなテキストフィールドを除外）
                query = select(
                    FilesBlob.id,
                    FilesBlob.checksum,
                    FilesBlob.stored_at,
                    FilesMeta.blob_id,
                    FilesMeta.file_name,
                    FilesMeta.mime_type,
                    FilesMeta.size,
                    FilesMeta.created_at,
                    FilesText.blob_id.label('text_blob_id'),
                    func.coalesce(func.length(FilesText.raw_text), 0).label('raw_text_length'),
                    func.coalesce(func.length(FilesText.refined_text), 0).label('refined_text_length'),
                    FilesText.quality_score,
                    FilesText.tags,
                    FilesText.updated_at
                ).select_from(FilesBlob).join(
                    FilesMeta, FilesBlob.id == FilesMeta.blob_id, isouter=True
                ).join(
                    FilesText, FilesBlob.id == FilesText.blob_id, isouter=True
                )
                
                query = query.order_by(FilesBlob.stored_at.desc())
                query = query.limit(limit).offset(offset)
                
                result = db.execute(query)
                files = []
                
                for row in result:
                    # PDFかどうかの判定フラグを追加
                    is_pdf = row.mime_type == 'application/pdf' if row.mime_type else False
                    
                    file_info = {
                        "file_id": str(row.id),
                        "checksum": row.checksum,
                        "filename": row.file_name if row.file_name else "unknown",
                        "file_size": row.size if row.size else 0,
                        "content_type": row.mime_type if row.mime_type else "application/octet-stream",
                        "is_pdf": is_pdf,  # PDFプレビュー可否判定用
                        "created_at": row.stored_at.isoformat(),
                        "has_text": row.text_blob_id is not None,
                        "text_length": (row.refined_text_length or row.raw_text_length or 0) if row.text_blob_id else 0,
                        "status": "processed" if row.text_blob_id else "pending"
                    }
                    files.append(file_info)
                
                # 読み込み専用なのでcommit不要、自動的にセッションがクローズされる
                return {
                    "files": files,
                    "total": total,
                    "limit": limit,
                    "offset": offset
                }
                
        except Exception as e:
            logger.error(f"ファイルリスト取得エラー: {e}")
            import traceback
            logger.error(f"トレースバック:\n{traceback.format_exc()}")
            return {
                "files": [],
                "total": 0,
                "limit": limit,
                "offset": offset
            }
    
    def get_file_with_blob(self, file_id: str) -> Optional[Dict[str, Any]]:
        """
        個別ファイル取得（blob含む）- PDFプレビューや個別処理用
        
        Args:
            file_id: ファイルID
            
        Returns:
            ファイル情報（blob含む）またはNone
        """
        try:
            with SessionLocal() as db:
                # ファイル情報を取得（blob含む）
                query = select(
                    FilesBlob.id,
                    FilesBlob.checksum,
                    FilesBlob.blob_data,  # ここでblobを取得
                    FilesBlob.stored_at,
                    FilesMeta.file_name,
                    FilesMeta.mime_type,
                    FilesMeta.size,
                    FilesMeta.created_at,
                    FilesText.raw_text,
                    FilesText.refined_text,
                    FilesText.quality_score,
                    FilesText.tags,
                    FilesText.updated_at
                ).select_from(FilesBlob).join(
                    FilesMeta, FilesBlob.id == FilesMeta.blob_id, isouter=True
                ).join(
                    FilesText, FilesBlob.id == FilesText.blob_id, isouter=True
                ).where(
                    FilesBlob.id == UUID(file_id)
                )
                
                result = db.execute(query).first()
                
                if not result:
                    return None
                
                return {
                    "file_id": str(result.id),
                    "checksum": result.checksum,
                    "blob_data": result.blob_data,  # バイナリデータ
                    "filename": result.file_name if result.file_name else "unknown",
                    "file_size": result.size if result.size else 0,
                    "content_type": result.mime_type if result.mime_type else "application/octet-stream",
                    "created_at": result.stored_at.isoformat(),
                    "raw_text": result.raw_text,
                    "refined_text": result.refined_text,
                    "quality_score": result.quality_score,
                    "tags": result.tags,
                    "updated_at": result.updated_at.isoformat() if result.updated_at else None
                }
                
        except Exception as e:
            logger.error(f"ファイル取得エラー（ID: {file_id}）: {e}")
            import traceback
            logger.error(f"トレースバック:\n{traceback.format_exc()}")
            return None
    
    def delete_file(
        self,
        file_id: str,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        ファイル削除（同期処理版・CASCADE対応）
        
        Args:
            file_id: ファイルID（UUIDまたは文字列）
            user_id: ユーザーID
            
        Returns:
            削除結果
        """
        try:
            with get_db_session() as db:
                # FilesBlob削除（CASCADE削除で関連テーブルも自動削除）
                result = db.execute(
                    delete(FilesBlob).where(FilesBlob.id == file_id)
                )
                
                db.commit()
                
                if result.rowcount > 0:
                    logger.info(f"ファイル削除成功: {file_id}")
                    return {
                        "status": "success",
                        "message": "ファイルを削除しました"
                    }
                else:
                    return {
                        "status": "error",
                        "message": "ファイルが見つかりません"
                    }
                    
        except Exception as e:
            logger.error(f"ファイル削除エラー: {e}")
            return {
                "status": "error",
                "message": f"削除中にエラーが発生しました: {str(e)}"
            }
    
    def get_file_metadata(
        self,
        file_id: str,
        user_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        ファイルメタデータ取得（同期処理版）
        
        Args:
            file_id: ファイルID（UUID文字列）
            user_id: ユーザーID
            
        Returns:
            ファイルメタデータまたはNone
        """
        try:
            with get_db_session() as db:
                # ファイル情報を取得（Files4兄弟 JOIN）
                query = select(FilesBlob, FilesMeta, FilesText).join(
                    FilesMeta, FilesBlob.id == FilesMeta.blob_id, isouter=True
                ).join(
                    FilesText, FilesBlob.id == FilesText.blob_id, isouter=True
                ).where(FilesBlob.id == file_id)
                
                result = db.execute(query)
                row = result.first()
                
                if not row:
                    return None
                
                blob, meta, text = row
                
                metadata = {
                    "file_id": str(blob.id),
                    "checksum": blob.checksum,
                    "filename": meta.file_name if meta else "unknown",
                    "size": len(blob.blob_data) if blob.blob_data else 0,
                    "mime_type": meta.mime_type if meta else "application/octet-stream",
                    "uploaded_at": blob.stored_at.isoformat(),
                    "status": "processed" if text else "pending",
                    "has_extracted_text": text is not None and text.raw_text is not None,
                    "has_refined_text": text is not None and text.refined_text is not None,
                    "text_length": len(text.refined_text or text.raw_text or "") if text else 0,
                    "quality_score": text.quality_score if text else None,
                    "tags": text.tags if text else []
                }
                
                return metadata
                
        except Exception as e:
            logger.error(f"メタデータ取得エラー: {e}")
            return None

    def upload_folder(self, folder_path: str, include_subfolders: bool = False, user_id: Optional[str] = None) -> Dict[str, Any]:
        """サーバーフォルダ内のファイルを一括アップロード（new/系移植版）"""
        import mimetypes
        from pathlib import Path
        
        try:
            # パスの正規化
            if folder_path.startswith('/'):
                folder_dir = Path(folder_path)
            else:
                # 相対パスの場合は /workspace からの相対パスとして処理
                folder_dir = Path("/workspace") / folder_path
                
            if not folder_dir.exists():
                return {
                    "status": "error",
                    "message": f"指定されたフォルダが見つかりません: {folder_path}",
                    "results": [],
                    "success_count": 0,
                    "error_count": 1
                }
            
            if not folder_dir.is_dir():
                return {
                    "status": "error", 
                    "message": f"指定されたパスはディレクトリではありません: {folder_path}",
                    "results": [],
                    "success_count": 0,
                    "error_count": 1
                }
            
            results = []
            success_count = 0
            error_count = 0
            
            # サブフォルダ処理の選択
            if include_subfolders:
                file_paths = [f for f in folder_dir.rglob("*") if f.is_file()]
            else:
                file_paths = [f for f in folder_dir.iterdir() if f.is_file()]
            
            logger.info(f"フォルダスキャン完了: {len(file_paths)}個のファイルを発見")
            
            for file_path in file_paths:
                try:
                    # 拡張子チェック
                    file_ext = file_path.suffix.lower()
                    if file_ext not in self.supported_extensions:
                        continue
                    
                    # ファイルサイズチェック
                    file_size = file_path.stat().st_size
                    if file_size > config.MAX_UPLOAD_SIZE:
                        result = UploadResponse(
                            status="error",
                            message=f"ファイルサイズが制限を超えています: {file_size // 1024 // 1024}MB",
                            file_name=file_path.name
                        )
                        results.append(result)
                        error_count += 1
                        continue
                    
                    # チェックサム計算
                    checksum = FileDBHandler.calc_checksum(str(file_path))
                    
                    # 重複チェック
                    with get_db_session() as db:
                        db_handler = FileDBHandler(db)
                        existing_id = db_handler.find_existing_by_checksum(checksum)
                        
                        if existing_id:
                            # 既存ファイルの作成日時を取得
                            from sqlalchemy import select
                            existing_query = select(FilesMeta.created_at).where(FilesMeta.blob_id == existing_id)
                            existing_meta = db.execute(existing_query).first()
                            created_at = existing_meta[0] if existing_meta else None
                            
                            result = UploadResponse(
                                status="duplicate",
                                message="重複スキップ",
                                file_id=UUID(existing_id),
                                file_name=file_path.name,
                                size=file_size,
                                checksum=checksum,
                                created_at=created_at,
                                upload_status="duplicate"
                            )
                            results.append(result)
                            success_count += 1
                            continue
                        
                        # 新規ファイル登録
                        file_id, is_new = db_handler.insert_file_full(
                            file_path=str(file_path),
                            original_filename=file_path.name,
                            raw_text=None,
                            refined_text=None,
                            quality_score=None,
                            tags=[]
                        )
                        
                        # 作成日時を取得
                        from sqlalchemy import select
                        meta_query = select(FilesMeta.created_at).where(FilesMeta.blob_id == file_id)
                        meta_result = db.execute(meta_query).first()
                        created_at = meta_result[0] if meta_result else None
                        
                        result = UploadResponse(
                            status="uploaded",
                            message="アップロード完了",
                            file_id=UUID(file_id),
                            file_name=file_path.name,
                            size=file_size,
                            checksum=checksum,
                            created_at=created_at,
                            upload_status="uploaded"
                        )
                        results.append(result)
                        success_count += 1
                        logger.info(f"サーバーファイル登録完了: {file_path.name}")
                        
                except Exception as e:
                    result = UploadResponse(
                        status="error",
                        message="処理エラー",
                        file_name=file_path.name if file_path else "unknown",
                        upload_status="error"
                    )
                    results.append(result)
                    error_count += 1
                    logger.error(f"サーバーファイル処理エラー: {file_path} - {e}")
            
            # 詳細な統計情報
            uploaded_count = len([r for r in results if r.status == "uploaded"])
            duplicate_count = len([r for r in results if r.status == "duplicate"]) 
            error_count = len([r for r in results if r.status == "error"])
            
            overall_status = "success" if error_count == 0 else "partial" if success_count > 0 else "error"
            message = f"アップロード: {uploaded_count}件, 重複: {duplicate_count}件, エラー: {error_count}件"
            
            logger.info(f"サーバーフォルダアップロード完了: {folder_path} - 成功={success_count}, 失敗={error_count}")
            
            return {
                "status": overall_status,
                "message": message,
                "results": [result.dict() for result in results],
                "success_count": success_count,
                "error_count": error_count
            }
            
        except Exception as e:
            logger.error(f"フォルダアップロードエラー: {e}")
            return {
                "status": "error",
                "message": f"フォルダアップロードに失敗しました: {str(e)}",
                "results": [],
                "success_count": 0,
                "error_count": 1
            }

    def list_server_folders(self, path: str = "") -> Dict[str, Any]:
        """サーバーフォルダブラウザ機能（new/系移植版）"""
        import os
        from pathlib import Path
        
        try:
            # パスの正規化
            if path:
                # 相対パスの場合は /workspace からの相対パスとして処理
                if path.startswith('/'):
                    folder_path = Path(path)
                else:
                    folder_path = Path("/workspace") / path
            else:
                folder_path = Path("/workspace")
            
            # セキュリティチェック: /workspace以下のみアクセス許可
            try:
                folder_path = folder_path.resolve()
                workspace_path = Path("/workspace").resolve()
                if not str(folder_path).startswith(str(workspace_path)):
                    logger.warning(f"不正なパスアクセス試行: {path}")
                    return {
                        "folders": [],
                        "error": "アクセス権限がありません"
                    }
            except Exception as e:
                logger.warning(f"パス解決エラー: {path} - {e}")
                return {
                    "folders": [],
                    "error": "無効なパスです"
                }
            
            if not folder_path.exists():
                return {
                    "folders": [],
                    "error": "フォルダが見つかりません"
                }
            
            if not folder_path.is_dir():
                return {
                    "folders": [],
                    "error": "指定されたパスはディレクトリではありません"
                }
            
            folders = []
            try:
                for item in folder_path.iterdir():
                    if item.is_dir() and not item.name.startswith('.'):
                        folders.append(item.name)
            except PermissionError:
                logger.warning(f"フォルダアクセス権限エラー: {folder_path}")
                return {
                    "folders": [],
                    "error": "フォルダへのアクセス権限がありません"
                }
            
            folders.sort()
            logger.info(f"フォルダリスト取得成功: {folder_path} ({len(folders)}個)")
            
            return {
                "folders": folders,
                "current_path": str(folder_path.relative_to(workspace_path)) if folder_path != workspace_path else ""
            }
            
        except Exception as e:
            logger.error(f"フォルダリスト取得エラー: {e}")
            return {
                "folders": [],
                "error": f"フォルダリストの取得に失敗しました: {str(e)}"
            }

    def get_file_preview(self, file_id: str) -> Optional[Dict[str, Any]]:
        """ファイルプレビュー機能（new/系移植版）"""
        try:
            with get_db_session() as db:
                # Files4兄弟からデータ取得
                query = select(FilesBlob, FilesMeta).join(
                    FilesMeta, FilesBlob.id == FilesMeta.blob_id
                ).where(FilesBlob.id == file_id)
                
                result = db.execute(query)
                row = result.first()
                
                if not row:
                    logger.warning(f"ファイルが見つかりません: {file_id}")
                    return None
                
                blob, meta = row
                
                if not blob.blob_data:
                    logger.warning(f"ファイルデータが空です: {file_id}")
                    return None
                
                file_name = meta.file_name
                mime_type = meta.mime_type
                data = blob.blob_data
                
                logger.info(f"ファイルプレビュー取得成功: {file_name} ({mime_type})")
                
                if mime_type == "application/pdf":
                    return {
                        "type": "binary",
                        "filename": file_name,
                        "mime_type": mime_type,
                        "data": data
                    }
                elif mime_type.startswith("text/"):
                    # テキストファイルの場合
                    try:
                        content = data.decode("utf-8")
                    except UnicodeDecodeError:
                        content = data.decode("utf-8", errors="ignore")
                    
                    return {
                        "type": "text",
                        "content": content,
                        "filename": file_name,
                        "mime_type": mime_type
                    }
                else:
                    # その他のバイナリファイル
                    return {
                        "type": "binary",
                        "filename": file_name,
                        "mime_type": mime_type,
                        "data": data
                    }
                
        except Exception as e:
            logger.error(f"ファイルプレビュー取得エラー: {e}")
            return None

# サービスインスタンス作成ヘルパー（同期処理版）
def get_file_service(db_session: Optional[Session] = None) -> FileService:
    """ファイルサービスインスタンス取得"""
    return FileService(db_session)