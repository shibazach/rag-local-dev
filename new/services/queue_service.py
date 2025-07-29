#!/usr/bin/env python3
# new/services/queue_service.py
# 処理キューサービス

import logging
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc
from pathlib import Path

from ..models import ProcessingQueue, File, FileText, FileImage, Embedding
from ..config import LOGGER
from .text_processor import TextProcessor
from .image_processor import ImageProcessor
from .embedding_service import EmbeddingService

class QueueService:
    """処理キューサービス"""
    
    def __init__(self):
        self.text_processor = TextProcessor()
        self.image_processor = ImageProcessor()
        self.embedding_service = EmbeddingService()
    
    def add_to_queue(self, db: Session, file_id: str, task_type: str, priority: int = 0) -> bool:
        """キューにタスクを追加"""
        try:
            LOGGER.info(f"📋 キューにタスク追加: ファイルID={file_id}, タスク={task_type}")
            
            # 既存のタスクをチェック
            existing_task = db.query(ProcessingQueue).filter(
                and_(
                    ProcessingQueue.file_id == file_id,
                    ProcessingQueue.task_type == task_type,
                    ProcessingQueue.status.in_(["pending", "processing"])
                )
            ).first()
            
            if existing_task:
                LOGGER.warning(f"⚠️ 既存のタスクが存在: ファイルID={file_id}, タスク={task_type}")
                return False
            
            # 新しいタスクを作成
            task = ProcessingQueue(
                file_id=file_id,
                task_type=task_type,
                priority=priority,
                status="pending"
            )
            
            db.add(task)
            db.commit()
            
            LOGGER.info(f"✅ タスク追加完了: ID={task.id}")
            return True
            
        except Exception as e:
            LOGGER.error(f"タスク追加エラー: {e}")
            db.rollback()
            return False
    
    def get_pending_tasks(self, db: Session, task_type: str = None, limit: int = 10) -> List[Dict[str, Any]]:
        """待機中のタスクを取得"""
        try:
            query = db.query(ProcessingQueue).filter(
                ProcessingQueue.status == "pending"
            )
            
            if task_type:
                query = query.filter(ProcessingQueue.task_type == task_type)
            
            tasks = query.order_by(desc(ProcessingQueue.priority), ProcessingQueue.created_at).limit(limit).all()
            
            return [
                {
                    "id": task.id,
                    "file_id": str(task.file_id),
                    "task_type": task.task_type,
                    "priority": task.priority,
                    "status": task.status,
                    "created_at": task.created_at.isoformat() if task.created_at else None
                }
                for task in tasks
            ]
            
        except Exception as e:
            LOGGER.error(f"待機タスク取得エラー: {e}")
            return []
    
    def process_task(self, db: Session, task_id: int) -> bool:
        """タスクを処理"""
        try:
            task = db.query(ProcessingQueue).filter(ProcessingQueue.id == task_id).first()
            if not task:
                LOGGER.error(f"タスクが見つかりません: ID={task_id}")
                return False
            
            LOGGER.info(f"🔄 タスク処理開始: ID={task_id}, ファイルID={task.file_id}, タスク={task.task_type}")
            
            # タスクステータスを更新
            task.status = "processing"
            task.started_at = datetime.now()
            db.commit()
            
            success = False
            
            try:
                if task.task_type == "text_extraction":
                    success = self._process_text_extraction(db, task.file_id)
                elif task.task_type == "image_extraction":
                    success = self._process_image_extraction(db, task.file_id)
                elif task.task_type == "vectorization":
                    success = self._process_vectorization(db, task.file_id)
                elif task.task_type == "indexing":
                    success = self._process_indexing(db, task.file_id)
                else:
                    LOGGER.error(f"未対応のタスクタイプ: {task.task_type}")
                    success = False
                
            except Exception as e:
                LOGGER.error(f"タスク処理エラー: {e}")
                success = False
            
            # タスクステータスを更新
            if success:
                task.status = "completed"
                task.completed_at = datetime.now()
                LOGGER.info(f"✅ タスク完了: ID={task_id}")
            else:
                task.status = "failed"
                task.error_message = str(e) if 'e' in locals() else "Unknown error"
                task.retry_count += 1
                LOGGER.error(f"❌ タスク失敗: ID={task_id}")
            
            db.commit()
            return success
            
        except Exception as e:
            LOGGER.error(f"タスク処理全体エラー: {e}")
            return False
    
    def _process_text_extraction(self, db: Session, file_id: str) -> bool:
        """テキスト抽出処理"""
        try:
            file = db.query(File).filter(File.id == file_id).first()
            if not file:
                return False
            
            # ファイルからテキストを抽出
            from ..utils.file_converter import FileConverter
            file_path = Path(file.file_path)
            
            text_content = FileConverter.extract_text_from_file(file_path)
            if not text_content:
                LOGGER.warning(f"テキスト抽出失敗: ファイルID={file_id}")
                return False
            
            # テキスト処理
            processed_text = self.text_processor.process_text(text_content, str(file_id))
            
            # データベースに保存
            file_text = FileText(
                file_id=file_id,
                raw_text=processed_text["raw_text"],
                refined_text=processed_text["cleaned_text"],
                text_chunks=processed_text["chunks"],
                quality_score=processed_text["metadata"].get("quality_score", 0.0),
                language=processed_text["metadata"].get("language", "ja")
            )
            
            db.add(file_text)
            
            # ファイルステータスを更新
            file.status = "text_extracted"
            file.processing_stage = "text_extracted"
            file.file_metadata = processed_text["metadata"]
            
            db.commit()
            LOGGER.info(f"✅ テキスト抽出完了: ファイルID={file_id}")
            return True
            
        except Exception as e:
            LOGGER.error(f"テキスト抽出エラー: {e}")
            return False
    
    def _process_image_extraction(self, db: Session, file_id: str) -> bool:
        """画像抽出処理"""
        try:
            file = db.query(File).filter(File.id == file_id).first()
            if not file:
                return False
            
            file_path = Path(file.file_path)
            if file_path.suffix.lower() != '.pdf':
                LOGGER.warning(f"PDFファイルではありません: {file_path}")
                return False
            
            # PDFから画像を抽出
            images = self.image_processor.extract_images_from_pdf(file_path)
            
            if not images:
                LOGGER.info(f"画像が見つかりません: ファイルID={file_id}")
                return True  # 画像がない場合は成功とする
            
            # 各画像を処理
            for img_data in images:
                processed_image = self.image_processor.process_image(
                    img_data["image_data"],
                    img_data["page_number"],
                    img_data["image_number"],
                    str(file_id)
                )
                
                # データベースに保存
                file_image = FileImage(
                    file_id=file_id,
                    page_number=processed_image["page_number"],
                    image_number=processed_image["image_number"],
                    image_size=processed_image["image_info"],
                    image_format=processed_image["image_info"]["format"],
                    ocr_text=processed_image["ocr_text"],
                    llm_description=processed_image["llm_description"],
                    llm_analysis=processed_image["llm_analysis"],
                    confidence_score=processed_image["ocr_confidence"],
                    processing_status=processed_image["processing_status"]
                )
                
                db.add(file_image)
            
            db.commit()
            LOGGER.info(f"✅ 画像抽出完了: ファイルID={file_id}, {len(images)}個の画像")
            return True
            
        except Exception as e:
            LOGGER.error(f"画像抽出エラー: {e}")
            return False
    
    def _process_vectorization(self, db: Session, file_id: str) -> bool:
        """ベクトル化処理"""
        try:
            # テキストチャンクを取得
            file_text = db.query(FileText).filter(FileText.file_id == file_id).first()
            if not file_text or not file_text.text_chunks:
                LOGGER.warning(f"テキストチャンクが見つかりません: ファイルID={file_id}")
                return False
            
            # 既存の埋め込みを削除
            db.query(Embedding).filter(Embedding.file_id == file_id).delete()
            
            # チャンクをベクトル化
            embeddings = self.embedding_service.batch_create_embeddings(file_text.text_chunks)
            
            # データベースに保存
            for embedding_data in embeddings:
                embedding = Embedding(
                    file_id=file_id,
                    chunk_id=embedding_data["chunk_id"],
                    text_chunk=embedding_data["text"],
                    embedding_model=embedding_data["embedding_model"],
                    embedding_vector=embedding_data["embedding_vector"],
                    chunk_index=embedding_data["chunk_index"],
                    chunk_size=embedding_data["size"]
                )
                db.add(embedding)
            
            # ファイルステータスを更新
            file = db.query(File).filter(File.id == file_id).first()
            file.processing_stage = "vectorized"
            
            db.commit()
            LOGGER.info(f"✅ ベクトル化完了: ファイルID={file_id}, {len(embeddings)}個のベクトル")
            return True
            
        except Exception as e:
            LOGGER.error(f"ベクトル化エラー: {e}")
            return False
    
    def _process_indexing(self, db: Session, file_id: str) -> bool:
        """インデックス作成処理"""
        try:
            # 現在はベクトル化と同じ処理
            # 将来的にはpgvectorのインデックス作成などを行う
            file = db.query(File).filter(File.id == file_id).first()
            file.processing_stage = "indexed"
            file.status = "completed"
            
            db.commit()
            LOGGER.info(f"✅ インデックス作成完了: ファイルID={file_id}")
            return True
            
        except Exception as e:
            LOGGER.error(f"インデックス作成エラー: {e}")
            return False
    
    def process_all_pending_tasks(self, db: Session) -> Dict[str, int]:
        """全待機タスクを処理"""
        try:
            pending_tasks = self.get_pending_tasks(db, limit=100)
            LOGGER.info(f"🔄 一括処理開始: {len(pending_tasks)}個のタスク")
            
            success_count = 0
            error_count = 0
            
            for task_data in pending_tasks:
                if self.process_task(db, task_data["id"]):
                    success_count += 1
                else:
                    error_count += 1
            
            LOGGER.info(f"🎉 一括処理完了: 成功={success_count}件, 失敗={error_count}件")
            return {
                "success": success_count,
                "error": error_count,
                "total": len(pending_tasks)
            }
            
        except Exception as e:
            LOGGER.error(f"一括処理エラー: {e}")
            return {"success": 0, "error": 0, "total": 0} 