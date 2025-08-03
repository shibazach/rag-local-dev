"""
処理サービス
Document processing service with OCR, LLM, and embedding
"""

import asyncio
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, Callable, AsyncGenerator, List
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import config, logger
from app.core.database import get_db
from app.core.models import FilesMeta, FilesText
from app.services.file_service import FileService


class ProcessingService:
    """文書処理サービス"""
    
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
        self.file_service = FileService(db_session)
        self.processing_queue = asyncio.Queue()
        self.active_jobs = {}
    
    async def start_processing(
        self,
        file_ids: List[str],
        processing_config: Dict[str, Any],
        progress_callback: Optional[Callable] = None,
        user_id: Optional[str] = None
    ) -> str:
        """処理開始"""
        try:
            # ジョブID生成
            job_id = str(uuid.uuid4())
            
            # ジョブ情報作成
            job_info = {
                "job_id": job_id,
                "file_ids": file_ids,
                "config": processing_config,
                "progress_callback": progress_callback,
                "user_id": user_id,
                "status": "queued",
                "created_at": datetime.utcnow(),
                "total_files": len(file_ids),
                "completed_files": 0,
                "current_file": None,
                "error_count": 0
            }
            
            # アクティブジョブに追加
            self.active_jobs[job_id] = job_info
            
            # 処理キューに追加
            await self.processing_queue.put(job_info)
            
            # バックグラウンド処理開始
            asyncio.create_task(self._process_job(job_info))
            
            logger.info(f"処理ジョブ開始: {job_id}, ファイル数: {len(file_ids)}")
            return job_id
            
        except Exception as e:
            logger.error(f"処理開始エラー: {e}")
            raise
    
    async def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """ジョブステータス取得"""
        return self.active_jobs.get(job_id)
    
    async def cancel_job(self, job_id: str) -> bool:
        """ジョブキャンセル"""
        try:
            job_info = self.active_jobs.get(job_id)
            if job_info:
                job_info["status"] = "cancelled"
                logger.info(f"処理ジョブキャンセル: {job_id}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"ジョブキャンセルエラー: {e}")
            return False
    
    async def stream_progress(self, job_id: str) -> AsyncGenerator[Dict[str, Any], None]:
        """進捗ストリーミング"""
        try:
            job_info = self.active_jobs.get(job_id)
            if not job_info:
                yield {"type": "error", "message": "ジョブが見つかりません"}
                return
            
            # 初期状態送信
            yield {
                "type": "job_start",
                "job_id": job_id,
                "total_files": job_info["total_files"],
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # ジョブ完了まで定期的にステータス送信
            while job_info.get("status") not in ["completed", "cancelled", "error"]:
                yield {
                    "type": "progress_update",
                    "job_id": job_id,
                    "status": job_info.get("status", "unknown"),
                    "completed_files": job_info.get("completed_files", 0),
                    "total_files": job_info.get("total_files", 0),
                    "current_file": job_info.get("current_file"),
                    "error_count": job_info.get("error_count", 0),
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                await asyncio.sleep(1)  # 1秒間隔で更新
            
            # 最終状態送信
            yield {
                "type": "job_complete",
                "job_id": job_id,
                "status": job_info.get("status"),
                "completed_files": job_info.get("completed_files", 0),
                "total_files": job_info.get("total_files", 0),
                "error_count": job_info.get("error_count", 0),
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"進捗ストリーミングエラー: {e}")
            yield {"type": "error", "message": str(e)}
    
    # プライベートメソッド
    
    async def _process_job(self, job_info: Dict[str, Any]) -> None:
        """ジョブ処理実行"""
        job_id = job_info["job_id"]
        
        try:
            job_info["status"] = "processing"
            job_info["started_at"] = datetime.utcnow()
            
            # 各ファイルを処理
            for i, file_id in enumerate(job_info["file_ids"]):
                # キャンセルチェック
                if job_info.get("status") == "cancelled":
                    logger.info(f"ジョブキャンセル検出: {job_id}")
                    break
                
                # ファイル処理
                try:
                    job_info["current_file"] = file_id
                    await self._process_single_file(job_info, file_id)
                    job_info["completed_files"] += 1
                    
                except Exception as e:
                    logger.error(f"ファイル処理エラー ({file_id}): {e}")
                    job_info["error_count"] += 1
                    
                    # ファイルステータス更新
                    await self.file_service.update_file_status(
                        file_id=file_id,
                        status="error",
                        error_message=str(e)
                    )
            
            # ジョブ完了
            if job_info.get("status") != "cancelled":
                job_info["status"] = "completed"
            
            job_info["completed_at"] = datetime.utcnow()
            
            logger.info(f"ジョブ処理完了: {job_id}, 成功: {job_info['completed_files']}, エラー: {job_info['error_count']}")
            
        except Exception as e:
            logger.error(f"ジョブ処理エラー: {job_id}, {e}")
            job_info["status"] = "error"
            job_info["error_message"] = str(e)
        
        finally:
            # 一定時間後にジョブ情報をクリーンアップ
            await asyncio.sleep(3600)  # 1時間後
            self.active_jobs.pop(job_id, None)
    
    async def _process_single_file(self, job_info: Dict[str, Any], file_id: str) -> None:
        """単一ファイル処理"""
        progress_callback = job_info.get("progress_callback")
        config_data = job_info.get("config", {})
        
        try:
            # ファイルステータス更新
            await self.file_service.update_file_status(file_id, "processing", 0)
            
            # 進捗通知
            if progress_callback:
                await progress_callback({
                    "type": "file_start",
                    "file_id": file_id,
                    "timestamp": datetime.utcnow().isoformat()
                })
            
            # Step 1: OCR処理
            await self.file_service.update_file_status(file_id, "processing", 20)
            if progress_callback:
                await progress_callback({
                    "type": "ocr_start",
                    "file_id": file_id,
                    "message": "OCR処理開始"
                })
            
            raw_text = await self._perform_ocr(file_id, config_data)
            
            # Step 2: LLM整形
            await self.file_service.update_file_status(file_id, "processing", 60)
            if progress_callback:
                await progress_callback({
                    "type": "llm_start", 
                    "file_id": file_id,
                    "message": "LLM整形開始"
                })
            
            refined_text = await self._perform_llm_refinement(file_id, raw_text, config_data)
            
            # Step 3: 埋め込み生成
            await self.file_service.update_file_status(file_id, "processing", 80)
            if progress_callback:
                await progress_callback({
                    "type": "embedding_start",
                    "file_id": file_id,
                    "message": "埋め込み生成開始"
                })
            
            await self._generate_embeddings(file_id, refined_text, config_data)
            
            # 完了
            await self.file_service.update_file_status(file_id, "processed", 100)
            if progress_callback:
                await progress_callback({
                    "type": "file_complete",
                    "file_id": file_id,
                    "message": "処理完了"
                })
            
        except Exception as e:
            logger.error(f"ファイル処理エラー ({file_id}): {e}")
            raise
    
    async def _perform_ocr(self, file_id: str, config: Dict[str, Any]) -> str:
        """OCR処理"""
        try:
            # TODO: 実際のOCR処理実装
            # ocrmypdf, tesseract等との連携
            
            # ダミー実装
            await asyncio.sleep(2)  # OCR処理のシミュレーション
            
            return f"OCR結果のダミーテキスト (ファイルID: {file_id})\n\nこれは文書の内容をOCRで読み取った結果です。実際の実装では、PDFからテキストを抽出し、画像の場合は文字認識を行います。"
            
        except Exception as e:
            logger.error(f"OCR処理エラー ({file_id}): {e}")
            raise
    
    async def _perform_llm_refinement(
        self,
        file_id: str,
        raw_text: str,
        config: Dict[str, Any]
    ) -> str:
        """LLM整形処理"""
        try:
            # TODO: Ollama連携実装
            
            # ダミー実装
            await asyncio.sleep(3)  # LLM処理のシミュレーション
            
            return f"LLM整形結果:\n\n{raw_text}\n\n[整形済み] 文書の内容を自然な日本語に整形し、読みやすくしました。OCRエラーの修正や文章の構造化を行っています。"
            
        except Exception as e:
            logger.error(f"LLM整形エラー ({file_id}): {e}")
            # フォールバック: 元のテキストを返す
            return raw_text
    
    async def _generate_embeddings(
        self,
        file_id: str,
        text: str,
        config: Dict[str, Any]
    ) -> None:
        """埋め込み生成"""
        try:
            # TODO: 埋め込み生成実装
            # SentenceTransformer, OpenAI embeddings等との連携
            
            # ダミー実装
            await asyncio.sleep(1)  # 埋め込み生成のシミュレーション
            
            # FileTextレコード作成
            file_text = FileText(
                id=str(uuid.uuid4()),
                file_id=file_id,
                raw_text=text,
                refined_text=text,
                quality_score=0.85,
                created_at=datetime.utcnow()
            )
            
            self.db.add(file_text)
            await self.db.commit()
            
        except Exception as e:
            logger.error(f"埋め込み生成エラー ({file_id}): {e}")
            raise


# 依存性注入用ファクトリ
async def get_processing_service(db = None):
    """処理サービス取得"""
    if db is None:
        db = next(get_db())
    return ProcessingService(db)