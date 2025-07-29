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
                    "file_metadata": file.file_metadata
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
                "file_metadata": file.file_metadata
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
            LOGGER.info("=" * 50)
            LOGGER.info("🚀 FileService.save_file 完全版開始")
            LOGGER.info(f"📋 受信データ: {file_data}")
            
            # 元ファイルのパス
            original_path = Path(file_data["file_path"])
            LOGGER.info(f"📁 元ファイルパス: {original_path}")
            LOGGER.info(f"🔍 ファイル存在確認: {original_path.exists()}")
            
            # ステップ1: 基本的なファイル保存
            LOGGER.info("📝 ステップ1: ファイル情報をDBに保存")
            file = FileModel(**file_data)
            db.add(file)
            db.commit()
            db.refresh(file)
            LOGGER.info(f"✅ ファイル保存完了: ID={file.id}")
            
            # ステップ2: ファイル形式判定と処理
            LOGGER.info("🔄 ステップ2: ファイル形式判定と処理開始")
            file_ext = original_path.suffix.lower()
            
            # テキストファイルの場合はPDF変換をスキップ
            if file_ext in ['.txt', '.json', '.csv', '.md']:
                LOGGER.info(f"📝 テキストファイル: {original_path.name} - PDF変換スキップ")
                pdf_path = original_path
            else:
                # その他のファイルはPDF変換を試行
                LOGGER.info(f"📄 非テキストファイル: {original_path.name} - PDF変換試行")
                pdf_path = original_path.parent / f"{original_path.stem}_converted.pdf"
                
                if FileConverter.is_supported_format(original_path.name):
                    if FileConverter.convert_to_pdf(original_path, pdf_path):
                        LOGGER.info(f"✅ PDF変換成功: {pdf_path}")
                        # PDFパスを更新
                        file.file_path = str(pdf_path)
                        file.file_type = "PDF"
                        db.commit()
                    else:
                        LOGGER.warning("⚠️ PDF変換失敗、元ファイルを使用")
                        pdf_path = original_path
                else:
                    LOGGER.warning(f"⚠️ 未対応形式: {original_path.name}")
                    pdf_path = original_path
            
            # ステップ3: テキスト抽出（即座実行）
            LOGGER.info("📖 ステップ3: テキスト抽出開始（即座実行）")
            
            # テキストファイルの場合は即座にテキスト抽出
            if file_ext in ['.txt', '.json', '.csv', '.md']:
                LOGGER.info(f"📝 テキストファイル即座処理: {original_path.name}")
                text_content = FileConverter._extract_text_direct(original_path)
                
                if text_content:
                    LOGGER.info(f"✅ テキスト抽出成功: {len(text_content)}文字")
                    # テキストをDBに保存
                    self.save_file_text(db, file.id, text_content)
                    file.status = "text_extracted"
                else:
                    LOGGER.warning("⚠️ テキスト抽出失敗")
                    file.status = "text_extraction_failed"
                
                db.commit()
                LOGGER.info(f"✅ テキスト保存完了: ステータス={file.status}")
            else:
                # その他のファイルは後処理対象としてマーク
                LOGGER.info(f"📄 後処理対象ファイル: {original_path.name}")
                file.status = "pending_processing"
                db.commit()
                LOGGER.info(f"✅ 後処理対象としてマーク: ステータス={file.status}")
            
            # ステップ4: ベクトル化（将来的に実装）
            LOGGER.info("🧠 ステップ4: ベクトル化（将来実装予定）")
            # TODO: テキストをチャンクに分割してベクトル化
            
            # 元ファイルがPDFでない場合は削除
            if original_path != pdf_path and original_path.exists():
                try:
                    original_path.unlink()
                    LOGGER.info(f"🗑️ 元ファイル削除: {original_path}")
                except Exception as e:
                    LOGGER.warning(f"⚠️ 元ファイル削除失敗: {e}")
            
            LOGGER.info("=" * 50)
            LOGGER.info(f"🎉 ファイル処理完了: ID={file.id}, ステータス={file.status}")
            LOGGER.info("=" * 50)
            return file
                
        except Exception as e:
            LOGGER.error("=" * 50)
            LOGGER.error("💥 FileService.save_file エラー")
            LOGGER.error(f"❌ エラー内容: {e}")
            LOGGER.error(f"📋 エラータイプ: {type(e).__name__}")
            import traceback
            LOGGER.error(f"📋 詳細スタックトレース:")
            LOGGER.error(traceback.format_exc())
            LOGGER.error("=" * 50)
            
            db.rollback()
            LOGGER.error("🔄 データベースロールバック完了")
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
        """フォルダ内のファイルを一括アップロード"""
        try:
            folder_dir = INPUT_DIR / folder_path
            if not folder_dir.exists():
                raise ValueError("指定されたフォルダが見つかりません")
            
            results = []
            # サブフォルダ処理の選択
            if include_subfolders:
                file_paths = folder_dir.rglob("*")
            else:
                file_paths = folder_dir.iterdir()
            
            for file_path in file_paths:
                if file_path.is_file():
                    # ファイルサイズチェック
                    file_size = file_path.stat().st_size
                    if file_size > 50 * 1024 * 1024:
                        results.append({
                            "filename": file_path.name,
                            "success": False,
                            "error": "ファイルサイズが50MBを超えています"
                        })
                        continue
                    
                    # 既存ファイルのチェック（データベース内）
                    existing_file = self.get_file_by_path(db, str(file_path))
                    if existing_file:
                        results.append({
                            "filename": file_path.name,
                            "success": False,
                            "error": "ファイルは既にアップロード済みです"
                        })
                        continue
                    
                    # データベースに記録
                    file_data = {
                        "file_name": file_path.name,
                        "file_path": str(file_path),
                        "file_size": file_size,
                        "status": "uploaded",
                        "user_id": user_id
                    }
                    
                    saved_file = self.save_file(db, file_data)
                    
                    results.append({
                        "filename": file_path.name,
                        "success": True,
                        "file_id": str(saved_file.id),
                        "status": saved_file.status
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