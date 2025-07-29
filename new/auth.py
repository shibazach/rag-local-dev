# new/auth.py
# セキュリティ設計に基づく認証システム

import logging
from typing import Optional, Dict, Any
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from .config import LOGGER, SECRET_KEY, SESSION_COOKIE_NAME, DEBUG_MODE
from .database import get_db

# セキュリティスキーム
security = HTTPBearer(auto_error=False)

# 仮のユーザー管理（後でSAML/OIDCに置き換え予定）
USERS = {
    "admin": {
        "username": "admin",
        "email": "admin@example.com",
        "role": "admin"
    },
    "user": {
        "username": "user", 
        "email": "user@example.com",
        "role": "user"
    }
}

class User:
    """ユーザー情報を管理するクラス"""
    
    def __init__(self, username: str, email: str, role: str, user_id: int = 1):
        self.username = username
        self.email = email
        self.role = role
        self.id = user_id  # APIで使用するID
    
    def is_admin(self) -> bool:
        return self.role == "admin"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "role": self.role
        }

def get_current_user(request: Request) -> User:
    """現在のユーザーを取得（認証必須）"""
    try:
        debug_function("get_current_user")
        
        # セッションからユーザー情報を取得
        session_user = request.session.get("user")
        if not session_user:
            raise HTTPException(
                status_code=401,
                detail="認証が必要です"
            )
        
        # 開発モードの場合は仮のユーザーを返す
        if DEBUG_MODE:
            return User(
                id=session_user.get("id", "dev-user"),
                username=session_user.get("username", "admin"),
                role=session_user.get("role", "admin")
            )
        
        # 実際のユーザー情報を返す
        return User(
            id=session_user.get("id"),
            username=session_user.get("username"),
            role=session_user.get("role", "user")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        debug_error(e, "get_current_user")
        raise HTTPException(
            status_code=401,
            detail="認証が必要です"
        )

def get_optional_user(request: Request) -> Optional[User]:
    """現在のユーザーを取得（認証オプション）"""
    try:
        debug_function("get_optional_user")
        
        # セッションからユーザー情報を取得
        session_user = request.session.get("user")
        if not session_user:
            return None
        
        # 開発モードの場合は仮のユーザーを返す
        if DEBUG_MODE:
            return User(
                id=session_user.get("id", "dev-user"),
                username=session_user.get("username", "admin"),
                role=session_user.get("role", "admin")
            )
        
        # 実際のユーザー情報を返す
        return User(
            id=session_user.get("id"),
            username=session_user.get("username"),
            role=session_user.get("role", "user")
        )
        
    except Exception as e:
        debug_error(e, "get_optional_user")
        return None

def require_admin(user: User = Depends(get_current_user)) -> User:
    """
    管理者権限を要求する依存関数
    
    Args:
        user: 認証されたユーザー
    
    Returns:
        User: 管理者ユーザー
    
    Raises:
        HTTPException: 管理者権限がない場合
    """
    if not user.is_admin():
        LOGGER.warning(f"管理者権限なし: {user.username}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="管理者権限が必要です"
        )
    return user

def login_user(request: Request, username: str, password: str) -> bool:
    """ユーザーログイン処理"""
    try:
        debug_function("login_user", username=username)
        
        # 開発用アカウント認証
        if username == "admin" and password == "password":
            user = User(
                id="admin-1",
                username="admin",
                role="admin"
            )
            request.session["user"] = {
                "id": user.id,
                "username": user.username,
                "role": user.role
            }
            return True
        
        if username == "user" and password == "password":
            user = User(
                id="user-1",
                username="user",
                role="user"
            )
            request.session["user"] = {
                "id": user.id,
                "username": user.username,
                "role": user.role
            }
            return True
        
        return False
        
    except Exception as e:
        debug_error(e, "login_user")
        return False

def logout_user(request: Request) -> bool:
    """ユーザーログアウト処理"""
    try:
        debug_function("logout_user")
        
        # セッションをクリア
        request.session.clear()
        
        return True
        
    except Exception as e:
        debug_error(e, "logout_user")
        return False 