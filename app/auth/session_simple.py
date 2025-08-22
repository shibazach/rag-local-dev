"""
シンプルセッション管理 - 最小限設計
複雑な実装を排除し、確実に動作する最小限の実装
"""

import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

from app.config import logger
from app.core.db_simple import fetch_one, execute

# グローバルセッション格納（メモリベース）
_active_sessions: Dict[str, Dict[str, Any]] = {}

class SimpleSessionManager:
    """
    シンプルセッション管理 - 最小限実装
    """
    
    @classmethod
    def create_session(cls, user_data: Dict[str, Any]) -> str:
        """セッション作成"""
        session_id = str(uuid.uuid4())
        
        session_info = {
            "session_id": session_id,
            "user_id": user_data.get("id", 1),
            "username": user_data.get("username"),
            "email": user_data.get("email"),
            "is_admin": user_data.get("is_admin", False),
            "created_at": datetime.utcnow(),
            "last_activity": datetime.utcnow()
        }
        
        # メモリに保存
        _active_sessions[session_id] = session_info
        
        # データベースにも保存（永続化）
        try:
            execute("""
                INSERT INTO user_sessions (session_id, user_id, username, email, is_admin, created_at, last_activity, expires_at, is_active)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (session_id) DO UPDATE SET
                    last_activity = EXCLUDED.last_activity,
                    is_active = TRUE
            """, (
                session_id,
                session_info["user_id"],
                session_info["username"],
                session_info["email"],
                session_info["is_admin"],
                session_info["created_at"],
                session_info["last_activity"],
                datetime.utcnow() + timedelta(hours=24),  # 24時間後に期限切れ
                True
            ))
            logger.info(f"✅ シンプルセッション作成: {user_data.get('username')} -> {session_id[:8]}...")
        except Exception as e:
            logger.error(f"❌ セッション保存エラー: {e}")
            # メモリからも削除
            _active_sessions.pop(session_id, None)
            return ""
        
        return session_id
    
    @classmethod
    def get_current_user(cls) -> Optional[Dict[str, Any]]:
        """現在のユーザー取得（最新のアクティブセッション）"""
        try:
            # まずメモリから最新セッションを確認
            if _active_sessions:
                # 最新の活動セッションを取得
                latest_session = max(
                    _active_sessions.values(), 
                    key=lambda s: s['last_activity']
                )
                
                # 期限チェック（1時間）
                if datetime.utcnow() - latest_session['last_activity'] < timedelta(hours=1):
                    # 活動時刻更新
                    latest_session['last_activity'] = datetime.utcnow()
                    return latest_session
                else:
                    # 期限切れセッションを削除
                    _active_sessions.pop(latest_session['session_id'], None)
            
            # メモリにない場合、データベースから取得
            db_session = fetch_one("""
                SELECT * FROM user_sessions 
                WHERE is_active = TRUE 
                  AND expires_at > %s
                ORDER BY last_activity DESC 
                LIMIT 1
            """, (datetime.utcnow(),))
            
            if db_session:
                session_info = {
                    "session_id": db_session["session_id"],
                    "user_id": db_session["user_id"],
                    "username": db_session["username"],
                    "email": db_session["email"],
                    "is_admin": db_session["is_admin"],
                    "created_at": db_session["created_at"],
                    "last_activity": datetime.utcnow()
                }
                
                # メモリに復元
                _active_sessions[db_session["session_id"]] = session_info
                
                # DB更新
                execute("""
                    UPDATE user_sessions 
                    SET last_activity = %s 
                    WHERE session_id = %s
                """, (datetime.utcnow(), db_session["session_id"]))
                
                logger.debug(f"✅ セッション復元: {session_info['username']}")
                return session_info
            
            return None
            
        except Exception as e:
            logger.error(f"❌ ユーザー取得エラー: {e}")
            return None
    
    @classmethod
    def destroy_current_session(cls) -> bool:
        """現在のセッション破棄"""
        try:
            # 全アクティブセッションを無効化
            _active_sessions.clear()
            
            execute("""
                UPDATE user_sessions 
                SET is_active = FALSE, last_activity = %s 
                WHERE is_active = TRUE
            """, (datetime.utcnow(),))
            
            logger.info("🗑️ 全セッション破棄完了")
            return True
            
        except Exception as e:
            logger.error(f"❌ セッション破棄エラー: {e}")
            return False
    
    @classmethod
    def cleanup_expired_sessions(cls):
        """期限切れセッションのクリーンアップ"""
        try:
            # メモリから期限切れを削除
            current_time = datetime.utcnow()
            expired_sessions = [
                sid for sid, session in _active_sessions.items()
                if current_time - session['last_activity'] > timedelta(hours=1)
            ]
            
            for sid in expired_sessions:
                _active_sessions.pop(sid, None)
            
            # データベースから期限切れを削除
            execute("""
                UPDATE user_sessions 
                SET is_active = FALSE 
                WHERE expires_at <= %s
            """, (current_time,))
            
            if expired_sessions:
                logger.info(f"🧹 期限切れセッション削除: {len(expired_sessions)}件")
                
        except Exception as e:
            logger.error(f"❌ セッションクリーンアップエラー: {e}")




