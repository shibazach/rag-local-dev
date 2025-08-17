"""
アップロードログサービス
"""
import json
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
import asyncio
from sqlalchemy import text, create_engine
from app.config import logger, config

class UploadLogService:
    """アップロードログ管理サービス"""
    
    def __init__(self):
        self.engine = create_engine(config.DATABASE_URL)
    
    def create_session(self) -> str:
        """新しいアップロードセッションを作成"""
        return str(uuid.uuid4())
    
    def create_log(
        self,
        session_id: str,
        file_name: str,
        file_size: int,
        status: str = "pending",
        message: str = None,
        metadata: Dict[str, Any] = None
    ) -> Optional[str]:
        """
        アップロードログを作成
        
        Returns:
            log_id: 作成されたログのID
        """
        try:
            log_id = str(uuid.uuid4())
            query = text("""
                INSERT INTO upload_logs (
                    id, session_id, file_name, file_size, 
                    status, message, metadata
                ) VALUES (
                    :id, :session_id, :file_name, :file_size,
                    :status, :message, :metadata
                )
            """)
            
            with self.engine.connect() as conn:
                conn.execute(query, {
                    "id": log_id,
                    "session_id": session_id,
                    "file_name": file_name,
                    "file_size": file_size,
                    "status": status,
                    "message": message or "",
                    "metadata": json.dumps(metadata or {})
                })
                conn.commit()
            
            logger.info(f"Upload log created: {log_id} for {file_name}")
            return log_id
            
        except Exception as e:
            logger.error(f"Failed to create upload log: {e}")
            return None
    
    def update_log(
        log_id: str,
        status: str = None,
        progress: int = None,
        message: str = None,
        error_detail: str = None,
        metadata: Dict[str, Any] = None
    ) -> bool:
        """アップロードログを更新"""
        try:
            updates = []
            params = {"id": log_id}
            
            if status is not None:
                updates.append("status = :status")
                params["status"] = status
                
            if progress is not None:
                updates.append("progress = :progress")
                params["progress"] = progress
                
            if message is not None:
                updates.append("message = :message")
                params["message"] = message
                
            if error_detail is not None:
                updates.append("error_detail = :error_detail")
                params["error_detail"] = error_detail
                
            if metadata is not None:
                updates.append("metadata = :metadata")
                params["metadata"] = json.dumps(metadata)
            
            if not updates:
                return True
                
            query = text(f"""
                UPDATE upload_logs 
                SET {', '.join(updates)}, updated_at = CURRENT_TIMESTAMP
                WHERE id = :id
            """)
            
            with self.engine.connect() as conn:
                conn.execute(query, params)
                conn.commit()
            return True
            
        except Exception as e:
            logger.error(f"Failed to update upload log {log_id}: {e}")
            return False
    
    def get_recent_logs(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """
        最近のアップロードログを取得（最新順）
        
        Returns:
            ログのリスト
        """
        try:
            query = text("""
                SELECT 
                    id, session_id, file_name, file_size,
                    status, progress, message, error_detail,
                    metadata, created_at, updated_at
                FROM upload_logs
                ORDER BY created_at DESC
                LIMIT :limit OFFSET :offset
            """)
            
            with self.engine.connect() as conn:
                result = conn.execute(query, {"limit": limit, "offset": offset})
            
            logs = []
            for row in result:
                log_data = dict(row._mapping)
                # JSONデータをパース
                if log_data.get("metadata"):
                    try:
                        log_data["metadata"] = json.loads(log_data["metadata"])
                    except:
                        log_data["metadata"] = {}
                logs.append(log_data)
                
            return logs
            
        except Exception as e:
            logger.error(f"Failed to get recent logs: {e}")
            return []
    
    def get_session_logs(self, session_id: str) -> List[Dict[str, Any]]:
        """特定セッションのログを取得"""
        try:
            query = text("""
                SELECT 
                    id, session_id, file_name, file_size,
                    status, progress, message, error_detail,
                    metadata, created_at, updated_at
                FROM upload_logs
                WHERE session_id = :session_id
                ORDER BY created_at ASC
            """)
            
            with self.engine.connect() as conn:
                result = conn.execute(query, {"session_id": session_id})
            
            logs = []
            for row in result:
                log_data = dict(row._mapping)
                if log_data.get("metadata"):
                    try:
                        log_data["metadata"] = json.loads(log_data["metadata"])
                    except:
                        log_data["metadata"] = {}
                logs.append(log_data)
                
            return logs
            
        except Exception as e:
            logger.error(f"Failed to get session logs: {e}")
            return []

    def get_in_progress_logs(self, limit: int = 200) -> List[Dict[str, Any]]:
        """
        未完了（pending / uploading / processing）のログを取得（最新順）
        """
        try:
            query = text("""
                SELECT 
                    id, session_id, file_name, file_size,
                    status, progress, message, error_detail,
                    metadata, created_at, updated_at
                FROM upload_logs
                WHERE status IN ('pending', 'uploading', 'processing')
                ORDER BY updated_at DESC, created_at DESC
                LIMIT :limit
            """)
            with self.engine.connect() as conn:
                result = conn.execute(query, {"limit": limit})
            logs = []
            for row in result:
                log_data = dict(row._mapping)
                if log_data.get("metadata"):
                    try:
                        log_data["metadata"] = json.loads(log_data["metadata"])
                    except:
                        log_data["metadata"] = {}
                logs.append(log_data)
            return logs
        except Exception as e:
            logger.error(f"Failed to get in-progress logs: {e}")
            return []
    
    async def stream_logs(self, callback, interval: float = 1.0):
        """
        ログをストリーミング（ポーリング方式）
        
        Args:
            callback: 新しいログが見つかった時に呼ばれる関数
            interval: ポーリング間隔（秒）
        """
        last_check = datetime.utcnow()
        
        while True:
            try:
                # 最後のチェック以降の新しいログを取得
                query = text("""
                    SELECT 
                        id, session_id, file_name, file_size,
                        status, progress, message, error_detail,
                        metadata, created_at, updated_at
                    FROM upload_logs
                    WHERE created_at > :last_check OR updated_at > :last_check
                    ORDER BY created_at DESC
                """)
                
                with self.engine.connect() as conn:
                    result = conn.execute(query, {"last_check": last_check})
                
                new_logs = []
                for row in result:
                    log_data = dict(row._mapping)
                    if log_data.get("metadata"):
                        try:
                            log_data["metadata"] = json.loads(log_data["metadata"])
                        except:
                            log_data["metadata"] = {}
                    new_logs.append(log_data)
                
                if new_logs:
                    await callback(new_logs)
                
                last_check = datetime.utcnow()
                await asyncio.sleep(interval)
                
            except Exception as e:
                logger.error(f"Error streaming logs: {e}")
                await asyncio.sleep(interval)

# シングルトンインスタンス
upload_log_service = UploadLogService()
