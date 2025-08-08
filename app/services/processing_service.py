"""
処理サービス - Prototype統合版
OCR・LLM・Embedding統合処理サービス
"""

import asyncio
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, Callable, AsyncGenerator, List
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import config, logger
from app.core.database import get_db
from app.core.models import FilesBlob, FilesMeta, FilesText
from app.services.ocr.ocr_process import extract_text_from_pdf
from app.services.llm.refiner import refine_text
from app.services.embedding.embedder import EmbeddingService

class ProcessingService:
    """文書処理サービス"""
    
    def __init__(self, db_session: AsyncSession = None):
        """
        Args:
            db_session: データベースセッション（オプショナル）
        """
        self.db = db_session
        self.processing_queue = asyncio.Queue()
        self.active_jobs = {}
    
    async def start_processing(
        self,
        file_ids: List[str],
        processing_config: Dict[str, Any],
        progress_callback: Optional[Callable] = None,
        user_id: Optional[str] = None
    ) -> str:
        """
        処理開始
        
        Args:
            file_ids: 処理対象ファイルIDリスト
            processing_config: 処理設定
            progress_callback: 進捗コールバック
            user_id: ユーザーID
            
        Returns:
            ジョブID
        """
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
                "current_step": "",
                "error": None
            }
            
            # アクティブジョブに追加
            self.active_jobs[job_id] = job_info
            
            # キューに追加
            await self.processing_queue.put(job_info)
            
            logger.info(f"処理ジョブ開始: {job_id}, ファイル数: {len(file_ids)}")
            
            # 非同期処理開始
            asyncio.create_task(self._process_job(job_id))
            
            return job_id
            
        except Exception as e:
            logger.error(f"処理開始エラー: {e}")
            raise
    
    async def _process_job(self, job_id: str) -> None:
        """ジョブ処理実行"""
        job_info = self.active_jobs.get(job_id)
        if not job_info:
            return
        
        try:
            # ステータス更新
            job_info["status"] = "processing"
            job_info["started_at"] = datetime.utcnow()
            
            # ファイルごとに処理
            for idx, file_id in enumerate(job_info["file_ids"]):
                # 進捗更新
                await self._update_progress(
                    job_id,
                    f"ファイル処理中 ({idx + 1}/{job_info['total_files']})",
                    (idx / job_info['total_files']) * 100
                )
                
                # 各処理ステップ実行
                await self._process_file(file_id, job_info["config"], job_id)
                
                job_info["completed_files"] = idx + 1
            
            # 完了
            job_info["status"] = "completed"
            job_info["completed_at"] = datetime.utcnow()
            
            await self._update_progress(job_id, "処理完了", 100)
            
        except Exception as e:
            logger.error(f"ジョブ処理エラー: {e}")
            job_info["status"] = "failed"
            job_info["error"] = str(e)
            await self._update_progress(job_id, f"エラー: {str(e)}", -1)
    
    async def _process_file(
        self,
        file_id: str,
        config: Dict[str, Any],
        job_id: str
    ) -> None:
        """
        ファイル処理
        
        Args:
            file_id: ファイルID
            config: 処理設定
            job_id: ジョブID
        """
        try:
            # データベースからファイル情報取得
            async with get_db() as db:
                file_blob = await db.get(FilesBlob, file_id)
                if not file_blob:
                    raise ValueError(f"ファイルが見つかりません: {file_id}")
                
                # OCR処理
                extracted_text = None
                if config.get("enable_ocr", False):
                    await self._update_progress(job_id, f"OCR処理中: {file_id}", -1)
                    
                    # PDFファイルを一時保存
                    temp_path = Path(f"/tmp/{file_id}.pdf")
                    with open(temp_path, "wb") as f:
                        f.write(file_blob.content)
                    
                    # OCR実行
                    ocr_result = extract_text_from_pdf(
                        str(temp_path),
                        ocr_engine=config.get("ocr_engine", "ocrmypdf")
                    )
                    extracted_text = ocr_result.get("text", "")
                    
                    # 一時ファイル削除
                    temp_path.unlink()
                    
                    logger.info(f"OCR完了: {file_id}, 文字数: {len(extracted_text)}")
                
                # LLM整形
                refined_text = extracted_text
                if config.get("enable_llm_refine", False) and extracted_text:
                    await self._update_progress(job_id, f"テキスト整形中: {file_id}", -1)
                    
                    # LLM整形実行
                    refined_result = refine_text(
                        extracted_text,
                        model_name=config.get("llm_model", config.OLLAMA_MODEL)
                    )
                    refined_text = refined_result.get("text", extracted_text)
                    
                    logger.info(f"LLM整形完了: {file_id}, 品質スコア: {refined_result.get('score', 0)}")
                
                # テキストをデータベースに保存
                if refined_text:
                    files_text = await db.get(FilesText, file_id)
                    if not files_text:
                        files_text = FilesText(file_id=file_id)
                        db.add(files_text)
                    
                    files_text.extracted_text = extracted_text
                    files_text.refined_text = refined_text
                    files_text.last_processed = datetime.utcnow()
                    
                    await db.commit()
                
                # Embedding生成
                if config.get("enable_embedding", True) and refined_text:
                    await self._update_progress(job_id, f"ベクトル生成中: {file_id}", -1)
                    
                    # Embeddingサービス初期化
                    embedding_service = EmbeddingService(
                        embedding_option=config.get("embedding_option", config.DEFAULT_EMBEDDING_OPTION)
                    )
                    
                    # ベクトル生成（チャンク分割含む）
                    chunks_with_embeddings = embedding_service.generate_embeddings(
                        refined_text,
                        file_id=file_id
                    )
                    
                    # ベクトルをデータベースに保存
                    # TODO: FileEmbeddingテーブルへの保存実装
                    
                    logger.info(f"Embedding生成完了: {file_id}, チャンク数: {len(chunks_with_embeddings)}")
                
        except Exception as e:
            logger.error(f"ファイル処理エラー ({file_id}): {e}")
            raise
    
    async def _update_progress(
        self,
        job_id: str,
        message: str,
        progress: float
    ) -> None:
        """進捗更新"""
        job_info = self.active_jobs.get(job_id)
        if not job_info:
            return
        
        job_info["current_step"] = message
        
        # コールバック実行
        if job_info.get("progress_callback"):
            try:
                await job_info["progress_callback"]({
                    "job_id": job_id,
                    "message": message,
                    "progress": progress,
                    "completed_files": job_info["completed_files"],
                    "total_files": job_info["total_files"]
                })
            except Exception as e:
                logger.error(f"進捗コールバックエラー: {e}")
    
    async def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """
        ジョブステータス取得
        
        Args:
            job_id: ジョブID
            
        Returns:
            ジョブステータス情報
        """
        job_info = self.active_jobs.get(job_id)
        if not job_info:
            return {
                "job_id": job_id,
                "status": "not_found",
                "error": "ジョブが見つかりません"
            }
        
        return {
            "job_id": job_id,
            "status": job_info["status"],
            "current_step": job_info["current_step"],
            "completed_files": job_info["completed_files"],
            "total_files": job_info["total_files"],
            "created_at": job_info["created_at"].isoformat(),
            "error": job_info.get("error")
        }
    
    async def cancel_job(self, job_id: str) -> Dict[str, Any]:
        """
        ジョブキャンセル
        
        Args:
            job_id: ジョブID
            
        Returns:
            キャンセル結果
        """
        job_info = self.active_jobs.get(job_id)
        if not job_info:
            return {
                "status": "error",
                "message": "ジョブが見つかりません"
            }
        
        job_info["status"] = "cancelled"
        job_info["cancelled_at"] = datetime.utcnow()
        
        logger.info(f"ジョブキャンセル: {job_id}")
        
        return {
            "status": "success",
            "message": "ジョブをキャンセルしました"
        }
    
    def get_active_jobs(self, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        アクティブジョブ一覧取得
        
        Args:
            user_id: ユーザーID（フィルタリング用）
            
        Returns:
            ジョブリスト
        """
        jobs = []
        for job_id, job_info in self.active_jobs.items():
            if user_id and job_info.get("user_id") != user_id:
                continue
            
            jobs.append({
                "job_id": job_id,
                "status": job_info["status"],
                "total_files": job_info["total_files"],
                "completed_files": job_info["completed_files"],
                "created_at": job_info["created_at"].isoformat()
            })
        
        return jobs

# サービスインスタンス作成ヘルパー
def get_processing_service(db_session: AsyncSession = None) -> ProcessingService:
    """処理サービスインスタンス取得"""
    return ProcessingService(db_session)