"""
ファイルサービス
File management service with upload, processing, and metadata handling
"""

import asyncio
import hashlib
import mimetypes
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, BinaryIO
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from fastapi import UploadFile, HTTPException

from app.config import config, logger
from app.core.database import get_db
from app.core.models import FilesMeta, FilesText, FilesBlob
from app.core.schemas import FileUploadResponse, FileListResponse, ProcessingConfig


class FileService:
    """ファイル管理サービス"""
    
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
        self.upload_dir = config.UPLOAD_DIR
        self.processed_dir = config.PROCESSED_DIR
        
        # ディレクトリ作成
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.processed_dir.mkdir(parents=True, exist_ok=True)
    
    async def upload_file(
        self,
        file: UploadFile,
        user_id: Optional[str] = None
    ) -> FileUploadResponse:
        """ファイルアップロード"""
        try:
            # バリデーション
            await self._validate_file(file)
            
            # ファイル保存
            file_path, checksum = await self._save_file(file)
            
            # 重複チェック
            existing_file = await self._check_duplicate(checksum)
            if existing_file:
                # 既存ファイルを返す
                return FileUploadResponse(
                    success=True,
                    file_id=str(existing_file.id),
                    filename=existing_file.filename,
                    message="既存ファイルが見つかりました"
                )
            
            # データベース保存
            file_record = await self._create_file_record(
                file=file,
                file_path=file_path,
                checksum=checksum,
                user_id=user_id
            )
            
            logger.info(f"ファイルアップロード完了: {file.filename} -> {file_record.id}")
            
            return FileUploadResponse(
                success=True,
                file_id=str(file_record.id),
                filename=file_record.filename,
                message="アップロード完了"
            )
            
        except Exception as e:
            logger.error(f"ファイルアップロードエラー: {e}")
            raise HTTPException(status_code=500, detail=f"アップロードに失敗しました: {str(e)}")
    
    async def get_files(
        self,
        page: int = 1,
        limit: int = 50,
        status_filter: Optional[str] = None,
        search_query: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> FileListResponse:
        """ファイル一覧取得"""
        try:
            query = select(FilesMeta)
            
            # フィルター適用
            if status_filter:
                query = query.where(FilesMeta.status == status_filter)
            
            if search_query:
                query = query.where(FilesMeta.filename.ilike(f"%{search_query}%"))
            
            if user_id:
                query = query.where(FilesMeta.created_by == user_id)
            
            # ページネーション
            offset = (page - 1) * limit
            query = query.offset(offset).limit(limit)
            
            # 実行
            result = await self.db.execute(query)
            files = result.scalars().all()
            
            # トータル件数取得
            count_query = select(FilesMeta).where(*query.whereclause.clauses if query.whereclause else [])
            count_result = await self.db.execute(count_query)
            total = len(count_result.scalars().all())
            
            return FileListResponse(
                files=[self._file_to_dict(f) for f in files],
                total=total,
                page=page,
                limit=limit
            )
            
        except Exception as e:
            logger.error(f"ファイル一覧取得エラー: {e}")
            raise HTTPException(status_code=500, detail="ファイル一覧の取得に失敗しました")
    
    async def get_file_binary(self, file_id: str) -> bytes:
        """ファイルバイナリ取得"""
        try:
            # ファイル取得
            query = select(FilesMeta).where(FilesMeta.id == file_id)
            result = await self.db.execute(query)
            file_record = result.scalar_one_or_none()
            
            if not file_record:
                raise HTTPException(status_code=404, detail="ファイルが見つかりません")
            
            # バイナリ読み込み
            file_path = self.upload_dir / file_record.stored_path
            if not file_path.exists():
                raise HTTPException(status_code=404, detail="ファイルが存在しません")
            
            return file_path.read_bytes()
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"ファイルバイナリ取得エラー: {e}")
            raise HTTPException(status_code=500, detail="ファイルの取得に失敗しました")
    
    async def delete_file(self, file_id: str, user_id: Optional[str] = None) -> bool:
        """ファイル削除"""
        try:
            # ファイル取得
            query = select(FilesMeta).where(FilesMeta.id == file_id)
            result = await self.db.execute(query)
            file_record = result.scalar_one_or_none()
            
            if not file_record:
                raise HTTPException(status_code=404, detail="ファイルが見つかりません")
            
            # 権限チェック（必要に応じて）
            if user_id and file_record.created_by != user_id:
                raise HTTPException(status_code=403, detail="削除権限がありません")
            
            # 物理ファイル削除
            file_path = self.upload_dir / file_record.stored_path
            if file_path.exists():
                file_path.unlink()
            
            # データベース削除（カスケード）
            await self.db.delete(file_record)
            await self.db.commit()
            
            logger.info(f"ファイル削除完了: {file_id}")
            return True
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"ファイル削除エラー: {e}")
            raise HTTPException(status_code=500, detail="ファイルの削除に失敗しました")
    
    async def update_file_status(
        self,
        file_id: str,
        status: str,
        progress: Optional[int] = None,
        error_message: Optional[str] = None
    ) -> bool:
        """ファイルステータス更新"""
        try:
            update_data = {
                "status": status,
                "updated_at": datetime.utcnow()
            }
            
            if progress is not None:
                update_data["progress"] = progress
            
            if error_message:
                update_data["error_message"] = error_message
            
            query = (
                update(File)
                .where(FilesMeta.id == file_id)
                .values(**update_data)
            )
            
            await self.db.execute(query)
            await self.db.commit()
            
            return True
            
        except Exception as e:
            logger.error(f"ファイルステータス更新エラー: {e}")
            return False
    
    # プライベートメソッド
    
    async def _validate_file(self, file: UploadFile) -> None:
        """ファイルバリデーション"""
        # サイズチェック
        if file.size and file.size > config.MAX_UPLOAD_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"ファイルサイズが上限を超えています: {file.size} bytes"
            )
        
        # 拡張子チェック
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in config.ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"サポートされていないファイル形式です: {file_ext}"
            )
    
    async def _save_file(self, file: UploadFile) -> tuple[Path, str]:
        """ファイル保存"""
        # ファイル内容読み取り
        content = await file.read()
        await file.seek(0)
        
        # チェックサム計算
        checksum = hashlib.sha256(content).hexdigest()
        
        # 保存パス生成
        timestamp = datetime.now().strftime("%Y%m%d")
        filename = f"{timestamp}_{uuid.uuid4().hex[:8]}_{file.filename}"
        file_path = self.upload_dir / filename
        
        # ファイル保存
        with file_path.open("wb") as f:
            f.write(content)
        
        return file_path, checksum
    
    async def _check_duplicate(self, checksum: str) -> Optional[FilesMeta]:
        """重複チェック"""
        query = select(FilesMeta).where(FilesMeta.checksum == checksum)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def _create_file_record(
        self,
        file: UploadFile,
        file_path: Path,
        checksum: str,
        user_id: Optional[str] = None
    ) -> FilesMeta:
        """ファイルレコード作成"""
        mime_type = mimetypes.guess_type(file.filename)[0] or "application/octet-stream"
        
        file_record = FilesMeta(
            id=str(uuid.uuid4()),
            filename=file.filename,
            original_filename=file.filename,
            stored_path=file_path.name,
            mime_type=mime_type,
            size=file_path.stat().st_size,
            checksum=checksum,
            status="uploaded",
            created_by=user_id,
            created_at=datetime.utcnow()
        )
        
        self.db.add(file_record)
        await self.db.commit()
        await self.db.refresh(file_record)
        
        return file_record
    
    def _file_to_dict(self, file: FilesMeta) -> Dict[str, Any]:
        """ファイルモデルを辞書に変換"""
        return {
            "id": file.id,
            "filename": file.filename,
            "size": file.size,
            "mime_type": file.mime_type,
            "status": file.status,
            "progress": file.progress,
            "error_message": file.error_message,
            "created_at": file.created_at.isoformat() if file.created_at else None,
            "updated_at": file.updated_at.isoformat() if file.updated_at else None,
            "created_by": file.created_by
        }


# 依存性注入用ファクトリ
async def get_file_service(db: AsyncSession = None) -> FileService:
    """ファイルサービス取得"""
    if db is None:
        db = next(get_db())
    return FileService(db)