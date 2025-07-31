#!/usr/bin/env python3
# new/services/file_service.py
# ファイルサービス

import logging
import shutil
from typing import List, Dict, Any, Optional
from pathlib import Path
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from ..models import File as FileModel, FileText as FileTextModel
from ..config import LOGGER, INPUT_DIR
from ..utils.file_converter import FileConverter
from ..db_handler import insert_file_blob_with_details

class FileService:
    """ファイルサービス"""
    
    def __init__(self):
        pass
    
    def get_files(self, db: Session) -> List[Dict[str, Any]]:
        """ファイル一覧を取得"""
        try:
            files = db.query(FileModel).order_by(FileModel.created_at.desc()).all()
            
            return [
                {
                    "id": str(file.id),
                    "filename": file.file_name,
                    "file_path": file.file_path,
                    "file_size": file.file_size,
                    "file_type": file.file_type,
                    "status": file.status,
                    "processing_stage": file.processing_stage,
                    "user_id": file.user_id,
                    "created_at": file.created_at.isoformat() if file.created_at else None,
                    "updated_at": file.updated_at.isoformat() if file.updated_at else None,
                    "note": file.note,
                    "file_metadata": file.file_metadata,
                    "page_count": file.page_count
                }
                for file in files
            ]
        except Exception as e:
            LOGGER.error(f"ファイル一覧取得エラー: {e}")
            return []
    
    def get_file(self, db: Session, file_id: str) -> Optional[Dict[str, Any]]:
        """ファイル詳細を取得"""
        try:
            file = db.query(FileModel).filter(FileModel.id == file_id).first()
            if not file:
                return None
            
            return {
                "id": str(file.id),
                "filename": file.file_name,
                "file_path": file.file_path,
                "file_size": file.file_size,
                "file_type": file.file_type,
                "status": file.status,
                "processing_stage": file.processing_stage,
                "user_id": file.user_id,
                "created_at": file.created_at.isoformat() if file.created_at else None,
                "updated_at": file.updated_at.isoformat() if file.updated_at else None,
                "note": file.note,
                "file_metadata": file.file_metadata,
                "page_count": file.page_count
            }
        except Exception as e:
            LOGGER.error(f"ファイル詳細取得エラー: {e}")
            return None
    
    def get_file_by_path(self, db: Session, file_path: str) -> Optional[Dict[str, Any]]:
        """ファイルパスでファイルを取得"""
        try:
            file = db.query(FileModel).filter(FileModel.file_path == file_path).first()
            if not file:
                return None
            
            return {
                "id": str(file.id),
                "filename": file.file_name,
                "file_path": file.file_path,
                "file_size": file.file_size,
                "file_type": file.file_type,
                "status": file.status,
                "processing_stage": file.processing_stage,
                "user_id": file.user_id,
                "created_at": file.created_at.isoformat() if file.created_at else None,
                "updated_at": file.updated_at.isoformat() if file.updated_at else None,
                "note": file.note,
                "file_metadata": file.file_metadata
            }
        except Exception as e:
            LOGGER.error(f"ファイルパス取得エラー: {e}")
            return None
    
    def save_file(self, db: Session, file_data: Dict[str, Any]) -> FileModel:
        """ファイル情報を保存（完全版：PDF変換→テキスト抽出→ベクトル化）"""
        try:
            # ファイルパスからファイルタイプを判定
            file_path = Path(file_data["file_path"])
            file_type = file_path.suffix.lower().lstrip('.')  # 小文字で、ドットを除去
            
            # ファイルメタデータの初期化
            file_metadata = {}
            
            # PDFファイルの場合、頁数を取得
            if file_type == "pdf":
                try:
                    import fitz  # PyMuPDF
                    doc = fitz.open(file_path)
                    page_count = len(doc)
                    doc.close()
                    file_metadata["page_count"] = page_count
                    LOGGER.info(f"PDF頁数取得: {file_path.name} - {page_count}頁")
                except ImportError:
                    LOGGER.warning("PyMuPDFがインストールされていません。頁数は取得できません。")
                except Exception as e:
                    LOGGER.error(f"PDF頁数取得エラー: {e}")
            
            # データベースに保存
            file = FileModel(
                file_name=file_data["file_name"],
                file_path=file_data["file_path"],
                file_size=file_data["file_size"],
                file_type=file_type,
                user_id=file_data["user_id"],
                status=file_data.get("status", "uploaded"),
                processing_stage=file_data.get("processing_stage", "uploaded"),
                note=file_data.get("note"),
                file_metadata=file_metadata
            )
            
            db.add(file)
            db.commit()
            db.refresh(file)
            
            LOGGER.info(f"ファイル保存完了: {file.file_name} (ID: {file.id})")
            return file
            
        except Exception as e:
            db.rollback()
            LOGGER.error(f"ファイル保存エラー: {e}")
            raise
    
    def save_file_text(self, db: Session, file_id: str, text_content: str) -> bool:
        """ファイルテキストを保存"""
        try:
            # 既存のテキストを削除
            db.query(FileTextModel).filter(FileTextModel.file_id == file_id).delete()
            
            # 新しいテキストを保存
            file_text = FileTextModel(
                file_id=file_id,
                raw_text=text_content,
                refined_text=text_content,  # 簡易的に同じテキストを使用
                quality_score=1.0  # デフォルト値
            )
            
            db.add(file_text)
            db.commit()
            
            LOGGER.info(f"✅ ファイルテキスト保存完了: ファイルID={file_id}")
            return True
            
        except Exception as e:
            LOGGER.error(f"ファイルテキスト保存エラー: {e}")
            db.rollback()
            return False
    
    def get_file_text(self, db: Session, file_id: str) -> Optional[str]:
        """ファイルテキストを取得"""
        try:
            file_text = db.query(FileTextModel).filter(FileTextModel.file_id == file_id).first()
            if not file_text:
                return None
            
            return file_text.raw_text
            
        except Exception as e:
            LOGGER.error(f"ファイルテキスト取得エラー: {e}")
            return None
    
    def get_file_preview(self, db: Session, file_id: str) -> Optional[Dict[str, Any]]:
        """ファイルプレビューを取得"""
        try:
            file = db.query(FileModel).filter(FileModel.id == file_id).first()
            if not file:
                return None
            
            file_path = Path(file.file_path)
            if not file_path.exists():
                return None
            
            # ファイル情報
            preview = {
                "id": str(file.id),
                "filename": file.file_name,
                "file_size": file.file_size,
                "file_type": file.file_type,
                "status": file.status,
                "processing_stage": file.processing_stage,
                "created_at": file.created_at.isoformat() if file.created_at else None
            }
            
            # テキストプレビュー
            file_text = db.query(FileTextModel).filter(FileTextModel.file_id == file_id).first()
            if file_text:
                preview["text_preview"] = file_text.raw_text[:500] + "..." if len(file_text.raw_text) > 500 else file_text.raw_text
                preview["text_length"] = len(file_text.raw_text)
                preview["quality_score"] = file_text.quality_score
            
            # ファイルサイズ情報
            try:
                stat = file_path.stat()
                preview["actual_size"] = stat.st_size
                preview["modified_time"] = stat.st_mtime
            except Exception as e:
                LOGGER.warning(f"ファイル統計取得エラー: {e}")
            
            return preview
            
        except Exception as e:
            LOGGER.error(f"ファイルプレビュー取得エラー: {e}")
            return None
    
    def upload_folder(self, db: Session, folder_path: str, include_subfolders: bool, user_id: int) -> List[Dict[str, Any]]:
        """フォルダ内のファイルを一括アップロード（新DB設計対応）"""
        from ..db_handler import insert_file_blob_only
        import mimetypes
        
        try:
            # パスの正規化
            if folder_path.startswith('/'):
                folder_dir = Path(folder_path)
            else:
                folder_dir = INPUT_DIR / folder_path
                
            if not folder_dir.exists():
                raise ValueError("指定されたフォルダが見つかりません")
            
            results = []
            supported_exts = {'.pdf', '.txt', '.doc', '.docx', '.jpg', '.jpeg', '.png'}
            
            # サブフォルダ処理の選択
            if include_subfolders:
                file_paths = [f for f in folder_dir.rglob("*") if f.is_file()]
            else:
                file_paths = [f for f in folder_dir.iterdir() if f.is_file()]
            
            for file_path in file_paths:
                try:
                    # 拡張子チェック
                    if file_path.suffix.lower() not in supported_exts:
                        results.append({
                            "filename": file_path.name,
                            "success": False,
                            "error": f"サポートされていないファイル形式: {file_path.suffix}"
                        })
                        continue
                    
                    # ファイルサイズチェック
                    file_size = file_path.stat().st_size
                    if file_size > 50 * 1024 * 1024:
                        results.append({
                            "filename": file_path.name,
                            "success": False,
                            "error": "ファイルサイズが50MBを超えています"
                        })
                        continue
                    
                    # ファイルデータを読み込み
                    with open(file_path, 'rb') as f:
                        file_data = f.read()
                    
                    # MIMEタイプ推定
                    mime_type = mimetypes.guess_type(file_path.name)[0]
                    
                    # 新DB設計でファイルを保存（詳細情報付き）
                    result = insert_file_blob_with_details(
                        file_name=file_path.name,
                        file_data=file_data,
                        mime_type=mime_type
                    )
                    
                    results.append({
                        "filename": file_path.name,
                        "success": True,
                        "id": result["blob_id"],
                        "size": file_size,
                        "is_existing": result["is_existing"],
                        "file_info": result["file_info"],
                        "message": "既存ファイル" if result["is_existing"] else "新規保存完了"
                    })
                    
                except Exception as file_error:
                    results.append({
                        "filename": file_path.name,
                        "success": False,
                        "error": f"ファイル処理エラー: {str(file_error)}"
                    })
            
            return results
            
        except Exception as e:
            LOGGER.error(f"フォルダアップロードエラー: {e}")
            raise
    
    def get_pending_files(self, db: Session) -> List[Dict[str, Any]]:
        """後処理対象のファイル一覧を取得"""
        try:
            files = db.query(FileModel).filter(
                FileModel.status == "pending_processing"
            ).all()
            
            return [
                {
                    "id": str(file.id),
                    "filename": file.file_name,
                    "file_path": file.file_path,
                    "file_size": file.file_size,
                    "status": file.status,
                    "user_id": file.user_id,
                    "created_at": file.created_at.isoformat() if file.created_at else None
                }
                for file in files
            ]
        except Exception as e:
            LOGGER.error(f"後処理対象ファイル取得エラー: {e}")
            raise
    
    def process_pending_file(self, db: Session, file_id: str) -> bool:
        """後処理対象ファイルを処理"""
        try:
            file = db.query(FileModel).filter(FileModel.id == file_id).first()
            if not file:
                LOGGER.error(f"ファイルが見つかりません: ID={file_id}")
                return False
            
            file_path = Path(file.file_path)
            LOGGER.info(f"🔄 後処理開始: {file.file_name}")
            
            # テキスト抽出
            text_content = FileConverter.extract_text_from_file(file_path)
            
            if text_content:
                LOGGER.info(f"✅ テキスト抽出成功: {len(text_content)}文字")
                # テキストをDBに保存
                self.save_file_text(db, file.id, text_content)
                file.status = "text_extracted"
                db.commit()
                LOGGER.info(f"✅ 後処理完了: ID={file.id}")
                return True
            else:
                LOGGER.warning(f"⚠️ テキスト抽出失敗: ID={file.id}")
                file.status = "text_extraction_failed"
                db.commit()
                return False
                
        except Exception as e:
            LOGGER.error(f"後処理エラー: {e}")
            return False
    
    def process_all_pending_files(self, db: Session) -> Dict[str, int]:
        """全後処理対象ファイルを処理"""
        try:
            pending_files = self.get_pending_files(db)
            LOGGER.info(f"🔄 後処理開始: {len(pending_files)}件")
            
            success_count = 0
            error_count = 0
            
            for file_data in pending_files:
                if self.process_pending_file(db, file_data["id"]):
                    success_count += 1
                else:
                    error_count += 1
            
            LOGGER.info(f"✅ 後処理完了: 成功={success_count}件, 失敗={error_count}件")
            return {
                "success": success_count,
                "error": error_count,
                "total": len(pending_files)
            }
            
        except Exception as e:
            LOGGER.error(f"後処理一括実行エラー: {e}")
            raise
    
    def delete_file(self, db: Session, file_id: str) -> bool:
        """ファイルを削除"""
        try:
            file = db.query(FileModel).filter(FileModel.id == file_id).first()
            if not file:
                return False
            
            # ファイルを削除
            file_path = Path(file.file_path)
            if file_path.exists():
                file_path.unlink()
            
            # データベースから削除
            db.delete(file)
            db.commit()
            
            LOGGER.info(f"✅ ファイル削除完了: ID={file_id}")
            return True
            
        except Exception as e:
            LOGGER.error(f"ファイル削除エラー: {e}")
            db.rollback()
            return False 