"""
データベース操作ハンドラ - Files3兄弟管理
OLD/db/handler.py の現代化版

checksum主導設計により、ファイルの重複を防ぎ、
効率的なストレージ管理を実現します。
"""

import hashlib
import mimetypes
import os
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from uuid import UUID
from datetime import datetime

from sqlalchemy import select, update, delete, and_, or_
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.core.models import FilesBlob, FilesMeta, FilesText, FileEmbedding, FilesImage
from app.config import logger


class FileDBHandler:
    """
    ファイルデータベース操作ハンドラ
    Files3兄弟（blob, meta, text）の統一的な操作を提供
    """
    
    def __init__(self, db_session: Session):
        self.db = db_session
        
    # ========== ユーティリティ ==========
    
    @staticmethod
    def calc_checksum(file_path: str) -> str:
        """ファイルのSHA256チェックサムを計算"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    
    @staticmethod
    def calc_checksum_from_bytes(data: bytes) -> str:
        """バイトデータのSHA256チェックサムを計算"""
        return hashlib.sha256(data).hexdigest()
    
    @staticmethod
    def normalize_tags(tags: Optional[List[str]]) -> List[str]:
        """タグの正規化（重複削除、空白除去）"""
        if not tags:
            return []
        return list(dict.fromkeys([t.strip() for t in tags if t.strip()]))
    
    # ========== 重複チェック ==========
    
    def find_existing_by_checksum(self, checksum: str) -> Optional[str]:
        """
        checksumで既存ファイルを検索
        
        Args:
            checksum: SHA256チェックサム
            
        Returns:
            既存ファイルのblob_id (UUID文字列) またはNone
        """
        try:
            stmt = select(FilesBlob.id).where(FilesBlob.checksum == checksum)
            result = self.db.execute(stmt).first()
            return str(result[0]) if result else None
        except SQLAlchemyError as e:
            logger.error(f"Checksum検索エラー: {e}")
            return None
    
    # ========== ファイル登録（Files3兄弟一括） ==========
    
    def insert_file_full(
        self,
        file_path: str,
        raw_text: Optional[str] = None,
        refined_text: Optional[str] = None,
        quality_score: Optional[float] = None,
        tags: Optional[List[str]] = None,
        original_filename: Optional[str] = None
    ) -> Tuple[str, bool]:
        """
        ファイルをFiles3兄弟に一括登録
        
        Args:
            file_path: ファイルパス
            raw_text: OCR生テキスト
            refined_text: 整形済みテキスト
            quality_score: 品質スコア (0.0-1.0)
            tags: タグリスト
            original_filename: 元のファイル名（指定しない場合はfile_pathから取得）
            
        Returns:
            (blob_id, is_new) のタプル
            blob_id: 登録されたファイルのID
            is_new: 新規登録の場合True、既存の場合False
        """
        # ファイル情報取得
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"ファイルが見つかりません: {file_path}")
            
        checksum = self.calc_checksum(str(file_path))
        file_size = file_path.stat().st_size
        mime_type = mimetypes.guess_type(str(file_path))[0] or "application/octet-stream"
        file_name = original_filename or file_path.name
        
        # 既存チェック
        existing_id = self.find_existing_by_checksum(checksum)
        if existing_id:
            logger.info(f"既存ファイル検出 (checksum: {checksum[:8]}...): {existing_id}")
            # 既存の場合はメタデータとテキストを更新
            self._update_existing_file(
                blob_id=existing_id,
                raw_text=raw_text,
                refined_text=refined_text,
                quality_score=quality_score,
                tags=tags
            )
            return existing_id, False
        
        # 新規登録
        try:
            # ファイルデータ読み込み
            with open(file_path, "rb") as f:
                blob_data = f.read()
            
            # 1. files_blob
            blob = FilesBlob(
                checksum=checksum,
                blob_data=blob_data
            )
            self.db.add(blob)
            self.db.flush()  # IDを取得するため
            
            blob_id = str(blob.id)
            
            # 2. files_meta
            meta = FilesMeta(
                blob_id=blob.id,
                file_name=file_name,
                mime_type=mime_type,
                size=file_size
            )
            self.db.add(meta)
            
            # 3. files_text（テキストがある場合）
            if raw_text or refined_text:
                text = FilesText(
                    blob_id=blob.id,
                    raw_text=raw_text,
                    refined_text=refined_text,
                    quality_score=quality_score,
                    tags=self.normalize_tags(tags)
                )
                self.db.add(text)
            
            self.db.commit()
            logger.info(f"新規ファイル登録完了: {blob_id} ({file_name})")
            return blob_id, True
            
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"ファイル登録エラー: {e}")
            raise
    
    def _update_existing_file(
        self,
        blob_id: str,
        raw_text: Optional[str] = None,
        refined_text: Optional[str] = None,
        quality_score: Optional[float] = None,
        tags: Optional[List[str]] = None
    ):
        """既存ファイルのテキスト情報を更新"""
        try:
            # files_textの存在確認
            text_record = self.db.query(FilesText).filter_by(blob_id=blob_id).first()
            
            if text_record:
                # 既存レコードを更新
                if raw_text is not None:
                    text_record.raw_text = raw_text
                if refined_text is not None:
                    text_record.refined_text = refined_text
                if quality_score is not None:
                    text_record.quality_score = quality_score
                if tags is not None:
                    text_record.tags = self.normalize_tags(tags)
                text_record.updated_at = datetime.utcnow()
            else:
                # 新規作成
                if raw_text or refined_text:
                    text = FilesText(
                        blob_id=blob_id,
                        raw_text=raw_text,
                        refined_text=refined_text,
                        quality_score=quality_score,
                        tags=self.normalize_tags(tags) if tags else []
                    )
                    self.db.add(text)
            
            self.db.commit()
            logger.info(f"既存ファイルのテキスト更新: {blob_id}")
            
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"テキスト更新エラー: {e}")
            raise
    
    # ========== ファイル取得 ==========
    
    def get_file_by_id(self, blob_id: str) -> Optional[Dict[str, Any]]:
        """
        blob_idでファイル情報を取得（3テーブル結合）
        
        Returns:
            ファイル情報の辞書、または None
        """
        try:
            # 3テーブルを結合して取得
            stmt = (
                select(FilesBlob, FilesMeta, FilesText)
                .join(FilesMeta, FilesBlob.id == FilesMeta.blob_id)
                .outerjoin(FilesText, FilesBlob.id == FilesText.blob_id)
                .where(FilesBlob.id == blob_id)
            )
            
            result = self.db.execute(stmt).first()
            if not result:
                return None
            
            blob, meta, text = result
            
            return {
                "blob_id": str(blob.id),
                "checksum": blob.checksum,
                "file_name": meta.file_name,
                "mime_type": meta.mime_type,
                "size": meta.size,
                "created_at": meta.created_at,
                "raw_text": text.raw_text if text else None,
                "refined_text": text.refined_text if text else None,
                "quality_score": text.quality_score if text else None,
                "tags": text.tags if text else [],
                "text_updated_at": text.updated_at if text else None
            }
            
        except SQLAlchemyError as e:
            logger.error(f"ファイル取得エラー: {e}")
            return None
    
    def get_file_binary(self, blob_id: str) -> Optional[bytes]:
        """ファイルのバイナリデータを取得"""
        try:
            stmt = select(FilesBlob.blob_data).where(FilesBlob.id == blob_id)
            result = self.db.execute(stmt).scalar()
            return result
        except SQLAlchemyError as e:
            logger.error(f"バイナリ取得エラー: {e}")
            return None
    
    # ========== ファイルリスト ==========
    
    def list_files(
        self,
        limit: int = 100,
        offset: int = 0,
        has_text: Optional[bool] = None,
        tags: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        ファイルリストを取得
        
        Args:
            limit: 取得件数
            offset: オフセット
            has_text: テキストありでフィルタ（True/False/None）
            tags: タグでフィルタ（いずれかを含む）
            
        Returns:
            ファイル情報のリスト
        """
        try:
            # 基本クエリ
            stmt = (
                select(FilesBlob, FilesMeta, FilesText)
                .join(FilesMeta, FilesBlob.id == FilesMeta.blob_id)
                .outerjoin(FilesText, FilesBlob.id == FilesText.blob_id)
            )
            
            # フィルタ条件
            if has_text is True:
                stmt = stmt.where(FilesText.blob_id.isnot(None))
            elif has_text is False:
                stmt = stmt.where(FilesText.blob_id.is_(None))
            
            if tags:
                # いずれかのタグを含む
                tag_conditions = [FilesText.tags.contains([tag]) for tag in tags]
                stmt = stmt.where(or_(*tag_conditions))
            
            # 並び順とページング
            stmt = stmt.order_by(FilesMeta.created_at.desc())
            stmt = stmt.limit(limit).offset(offset)
            
            results = self.db.execute(stmt).all()
            
            files = []
            for blob, meta, text in results:
                files.append({
                    "blob_id": str(blob.id),
                    "checksum": blob.checksum[:8] + "...",  # 短縮表示
                    "file_name": meta.file_name,
                    "mime_type": meta.mime_type,
                    "size": meta.size,
                    "created_at": meta.created_at,
                    "has_text": text is not None,
                    "quality_score": text.quality_score if text else None,
                    "tags": text.tags if text else []
                })
            
            return files
            
        except SQLAlchemyError as e:
            logger.error(f"ファイルリスト取得エラー: {e}")
            return []
    
    # ========== ファイル削除 ==========
    
    def delete_file(self, blob_id: str) -> bool:
        """
        ファイルを削除（CASCADE削除により関連テーブルも自動削除）
        
        Returns:
            削除成功時True
        """
        try:
            blob = self.db.query(FilesBlob).filter_by(id=blob_id).first()
            if not blob:
                logger.warning(f"削除対象ファイルが見つかりません: {blob_id}")
                return False
            
            self.db.delete(blob)
            self.db.commit()
            logger.info(f"ファイル削除完了: {blob_id}")
            return True
            
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"ファイル削除エラー: {e}")
            return False
    
    # ========== タグ操作 ==========
    
    def update_tags(self, blob_id: str, tags: List[str], append: bool = False) -> bool:
        """
        ファイルのタグを更新
        
        Args:
            blob_id: ファイルID
            tags: 新しいタグリスト
            append: True の場合は既存タグに追加、False の場合は置換
            
        Returns:
            更新成功時True
        """
        try:
            text_record = self.db.query(FilesText).filter_by(blob_id=blob_id).first()
            
            if not text_record:
                # files_textレコードがない場合は作成
                text_record = FilesText(
                    blob_id=blob_id,
                    tags=self.normalize_tags(tags)
                )
                self.db.add(text_record)
            else:
                if append:
                    # 既存タグに追加
                    combined_tags = list(text_record.tags) + tags
                    text_record.tags = self.normalize_tags(combined_tags)
                else:
                    # タグを置換
                    text_record.tags = self.normalize_tags(tags)
                text_record.updated_at = datetime.utcnow()
            
            self.db.commit()
            logger.info(f"タグ更新完了: {blob_id}")
            return True
            
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"タグ更新エラー: {e}")
            return False
    
    # ========== 統計情報 ==========
    
    def get_statistics(self) -> Dict[str, Any]:
        """データベースの統計情報を取得"""
        try:
            total_files = self.db.query(FilesBlob).count()
            total_size = self.db.query(func.sum(FilesMeta.size)).scalar() or 0
            files_with_text = self.db.query(FilesText).count()
            files_with_refined = self.db.query(FilesText).filter(
                FilesText.refined_text.isnot(None)
            ).count()
            total_embeddings = self.db.query(FileEmbedding).count()
            total_images = self.db.query(FilesImage).count()
            
            # タグ統計
            all_tags = self.db.query(FilesText.tags).all()
            tag_counts = {}
            for (tags,) in all_tags:
                if tags:
                    for tag in tags:
                        tag_counts[tag] = tag_counts.get(tag, 0) + 1
            
            return {
                "total_files": total_files,
                "total_size": total_size,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "files_with_text": files_with_text,
                "files_with_refined_text": files_with_refined,
                "total_embeddings": total_embeddings,
                "total_images": total_images,
                "unique_tags": len(tag_counts),
                "top_tags": sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:10]
            }
            
        except SQLAlchemyError as e:
            logger.error(f"統計情報取得エラー: {e}")
            return {}


# SQLAlchemyのfunc import忘れ防止
from sqlalchemy import func