"""
セッション管理 - Prototype統合版
FastAPI SessionMiddleware + NiceGUI storage統合
"""

import uuid
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

from fastapi import Request, Response
from nicegui import ui

from app.config import config, logger

class SessionManager:
    """統合セッション管理クラス"""
    
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
        user_data: Dict[str, Any],
        use_nicegui: bool = True
    ) -> str:
        """
        ユーザーセッション作成
        FastAPIセッション + NiceGUIストレージの両方に保存
        """
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
        
        # FastAPIセッション保存
        if hasattr(request, 'session'):
            request.session["user"] = session_data
        
        # NiceGUIストレージ保存
        if use_nicegui and hasattr(ui, 'storage') and ui.storage.user:
            ui.storage.user['user'] = session_data
        
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
    def create_nicegui_session(user_data: Dict[str, Any]) -> str:
        """
        NiceGUI専用セッション作成（UIページ用）
        """
        session_id = SessionManager.create_session_id()
        
        session_data = {
            "session_id": session_id,
            "user_id": user_data.get("id"),
            "username": user_data.get("username"),
            "email": user_data.get("email"),
            "is_admin": user_data.get("is_admin", False),
            "created_at": datetime.utcnow().isoformat(),
            "last_activity": datetime.utcnow().isoformat()
        }
        
        # NiceGUIストレージに保存（初期化も含む）
        if hasattr(ui, 'storage') and ui.storage.user is not None:
            ui.storage.user['user'] = session_data
        else:
            # ストレージが未初期化の場合のフォールバック処理
            logger.warning("NiceGUIストレージが未初期化のため、セッション保存をスキップ")
        
        logger.info(f"NiceGUIセッション作成: {user_data.get('username', 'unknown')}")
        return session_id
    
    @staticmethod
    def update_last_activity(request: Request = None) -> None:
        """最終活動時刻更新"""
        current_time = datetime.utcnow().isoformat()
        
        # FastAPIセッション更新
        if request and hasattr(request, 'session') and "user" in request.session:
            request.session["user"]["last_activity"] = current_time
        
        # NiceGUIストレージ更新
        if hasattr(ui, 'storage') and ui.storage.user and 'user' in ui.storage.user:
            ui.storage.user['user']['last_activity'] = current_time
    
    @staticmethod
    def destroy_session(request: Request = None, response: Response = None) -> None:
        """セッション破棄"""
        username = "unknown"
        
        # FastAPIセッション削除
        if request and hasattr(request, 'session'):
            user_info = request.session.get("user", {})
            username = user_info.get("username", username)
            request.session.clear()
        
        # NiceGUIストレージ削除
        if hasattr(ui, 'storage') and ui.storage.user:
            if 'user' in ui.storage.user:
                username = ui.storage.user['user'].get('username', username)
                del ui.storage.user['user']
        
        # クッキー削除
        if response:
            response.delete_cookie(
                key=config.SESSION_COOKIE_NAME,
                secure=config.SESSION_COOKIE_SECURE,
                httponly=config.SESSION_COOKIE_HTTPONLY,
                samesite=config.SESSION_COOKIE_SAMESITE
            )
        
        logger.info(f"セッション破棄: {username}")
    
    @staticmethod
    def destroy_nicegui_session() -> None:
        """NiceGUI専用セッション破棄"""
        username = "unknown"
        
        if ui.storage.user and 'user' in ui.storage.user:
            username = ui.storage.user['user'].get('username', username)
            del ui.storage.user['user']
        
        logger.info(f"NiceGUIセッション破棄: {username}")
    
    @staticmethod
    def is_session_valid(request: Request = None) -> bool:
        """セッション有効性チェック"""
        user_data = None
        
        # NiceGUIストレージから確認（優先）
        if hasattr(ui, 'storage') and ui.storage.user:
            user_data = ui.storage.user.get('user')
        
        # FastAPIセッションから確認
        if not user_data and request and hasattr(request, 'session'):
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
    def get_current_user() -> Optional[Dict[str, Any]]:
        """現在のユーザー情報取得（シンプル統合版）"""
        try:
            # シンプルセッション管理を使用
            from app.auth.session_simple import SimpleSessionManager
            return SimpleSessionManager.get_current_user()
        except Exception as e:
            logger.error(f"❌ シンプル認証確認エラー: {e}")
            return None
    
    @staticmethod
    def cleanup_expired_sessions():
        """期限切れセッション清理（バックグラウンドタスク用）"""
        # TODO: データベースベースのセッションストア実装後に実装
        pass

# デフォルトインスタンス
session_manager = SessionManager()