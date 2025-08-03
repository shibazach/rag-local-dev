"""
セッション管理
Session management with security enhancements
"""

import uuid
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

from fastapi import Request, Response
from app.config import config, logger

class SessionManager:
    """セッション管理クラス"""
    
    @staticmethod
    def create_session_id() -> str:
        """セキュアなセッションID生成"""
        return str(uuid.uuid4())
    
    @staticmethod
    def hash_password(password: str, salt: str = None) -> tuple[str, str]:
        """パスワードハッシュ化"""
        if salt is None:
            salt = uuid.uuid4().hex
        
        password_hash = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            100000  # iterations
        )
        return password_hash.hex(), salt
    
    @staticmethod
    def verify_password(password: str, hashed: str, salt: str) -> bool:
        """パスワード検証"""
        password_hash, _ = SessionManager.hash_password(password, salt)
        return password_hash == hashed
    
    @staticmethod
    def create_user_session(
        request: Request,
        response: Response,
        user_data: Dict[str, Any]
    ) -> str:
        """ユーザーセッション作成"""
        session_id = SessionManager.create_session_id()
        
        # セッションデータ準備
        session_data = {
            "session_id": session_id,
            "user_id": user_data.get("id"),
            "username": user_data.get("username"),
            "email": user_data.get("email"),
            "is_admin": user_data.get("is_admin", False),
            "created_at": datetime.utcnow().isoformat(),
            "last_activity": datetime.utcnow().isoformat()
        }
        
        # セッション保存
        request.session["user"] = session_data
        
        # セキュアクッキー設定
        response.set_cookie(
            key=config.SESSION_COOKIE_NAME,
            value=session_id,
            max_age=config.SESSION_COOKIE_MAX_AGE,
            secure=config.SESSION_COOKIE_SECURE,
            httponly=config.SESSION_COOKIE_HTTPONLY,
            samesite=config.SESSION_COOKIE_SAMESITE
        )
        
        logger.info(f"セッション作成: {user_data.get('username', 'unknown')}")
        return session_id
    
    @staticmethod
    def update_last_activity(request: Request) -> None:
        """最終活動時刻更新"""
        if "user" in request.session:
            request.session["user"]["last_activity"] = datetime.utcnow().isoformat()
    
    @staticmethod
    def destroy_session(request: Request, response: Response) -> None:
        """セッション破棄"""
        user_info = request.session.get("user", {})
        username = user_info.get("username", "unknown")
        
        # セッション削除
        request.session.clear()
        
        # クッキー削除
        response.delete_cookie(
            key=config.SESSION_COOKIE_NAME,
            secure=config.SESSION_COOKIE_SECURE,
            httponly=config.SESSION_COOKIE_HTTPONLY,
            samesite=config.SESSION_COOKIE_SAMESITE
        )
        
        logger.info(f"セッション破棄: {username}")
    
    @staticmethod
    def is_session_valid(request: Request) -> bool:
        """セッション有効性チェック"""
        user_data = request.session.get("user")
        if not user_data:
            return False
        
        # セッション期限チェック
        try:
            created_at = datetime.fromisoformat(user_data["created_at"])
            max_age = timedelta(seconds=config.SESSION_COOKIE_MAX_AGE)
            
            if datetime.utcnow() > created_at + max_age:
                logger.warning(f"セッション期限切れ: {user_data.get('username', 'unknown')}")
                return False
                
            return True
        except (KeyError, ValueError) as e:
            logger.error(f"セッション検証エラー: {e}")
            return False
    
    @staticmethod
    def cleanup_expired_sessions():
        """期限切れセッション清理（バックグラウンドタスク用）"""
        # TODO: セッションストア実装後に実装
        pass

# デフォルトインスタンス
session_manager = SessionManager()