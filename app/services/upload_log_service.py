"""
アップロードログサービス
"""
import json
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
import asyncio
from app.core.db_simple import fetch_all, fetch_one, execute
from app.config import logger, config

class UploadLogService:
    """アップロードログ管理サービス"""
    
    def __init__(self):
        """初期化（db_simple.pyを使用するため特別な処理不要）"""
        pass
    
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
            query = """
                INSERT INTO upload_logs (
                    id, session_id, file_name, file_size, 
                    status, message, metadata
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s
                )
            """
            
            params = (
                log_id,
                session_id,
                file_name,
                file_size,
                status,
                message or "",
                json.dumps(metadata or {})
            )
            
            execute(query, params)
            logger.info(f"Upload log created: {log_id} for {file_name}")
            return log_id
            
        except Exception as e:
            logger.error(f"Failed to create upload log: {e}")
            return None
    
    def update_log(
        self,
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
            params = []
            
            if status is not None:
                updates.append("status = %s")
                params.append(status)
                
            if progress is not None:
                updates.append("progress = %s")
                params.append(progress)
                
            if message is not None:
                updates.append("message = %s")
                params.append(message)
                
            if error_detail is not None:
                updates.append("error_detail = %s")
                params.append(error_detail)
                
            if metadata is not None:
                updates.append("metadata = %s")
                params.append(json.dumps(metadata))
            
            if not updates:
                return True
                
            # log_idをparamsの最後に追加
            params.append(log_id)
            
            query = f"""
                UPDATE upload_logs 
                SET {', '.join(updates)}, updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """
            
            execute(query, tuple(params))
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
            query = """
                SELECT 
                    id, session_id, file_name, file_size,
                    status, progress, message, error_detail,
                    metadata, created_at, updated_at
                FROM upload_logs
                ORDER BY created_at DESC
                LIMIT %s OFFSET %s
            """
            
            result = fetch_all(query, (limit, offset))
            
            logs = []
            for row in result:
                log_data = dict(row)
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
            query = """
                SELECT 
                    id, session_id, file_name, file_size,
                    status, progress, message, error_detail,
                    metadata, created_at, updated_at
                FROM upload_logs
                WHERE session_id = %s
                ORDER BY created_at ASC
            """
            
            result = fetch_all(query, (session_id,))
            
            logs = []
            for row in result:
                log_data = dict(row)
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
            query = """
                SELECT 
                    id, session_id, file_name, file_size,
                    status, progress, message, error_detail,
                    metadata, created_at, updated_at
                FROM upload_logs
                WHERE status IN ('pending', 'uploading', 'processing')
                ORDER BY updated_at DESC, created_at DESC
                LIMIT %s
            """
            
            result = fetch_all(query, (limit,))
            
            logs = []
            for row in result:
                log_data = dict(row)
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
                query = """
                    SELECT 
                        id, session_id, file_name, file_size,
                        status, progress, message, error_detail,
                        metadata, created_at, updated_at
                    FROM upload_logs
                    WHERE created_at > %s OR updated_at > %s
                    ORDER BY created_at DESC
                """
                
                result = fetch_all(query, (last_check, last_check))
                
                new_logs = []
                for row in result:
                    log_data = dict(row)
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
