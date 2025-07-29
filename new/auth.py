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

def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    現在のユーザーを取得する関数
    セキュリティ設計に基づき、後でSAML/OIDCに置き換え可能
    
    Args:
        request: FastAPIリクエスト
        credentials: HTTP認証情報
        db: データベースセッション
    
    Returns:
        User: 認証されたユーザー情報
    
    Raises:
        HTTPException: 認証失敗時
    """
    # セッションからユーザー情報を取得
    session_user = request.session.get("user")
    if session_user:
        LOGGER.info(f"セッションからユーザー取得: {session_user['username']}")
        # idフィールドをuser_idに変換
        user_data = session_user.copy()
        if 'id' in user_data:
            user_data['user_id'] = user_data.pop('id')
        return User(**user_data)
    
    # 開発モードでは仮のユーザーを返す
    if DEBUG_MODE:
        LOGGER.info("開発モード: 仮のユーザーを返します")
        # 開発モードでもセッションに保存
        if "user" not in request.session:
            user = User("admin", "admin@example.com", "admin", 1)
            request.session["user"] = user.to_dict()
        return User("admin", "admin@example.com", "admin", 1)
    
    # Bearer トークン認証
    if credentials:
        token = credentials.credentials
        # ここでJWTトークンの検証を行う（実装予定）
        LOGGER.warning("Bearer トークン認証は未実装")
    
    # 認証失敗
    LOGGER.warning("認証失敗: ユーザー情報が見つかりません")
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="認証が必要です",
        headers={"WWW-Authenticate": "Bearer"},
    )

def get_optional_user(
    request: Request,
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    現在のユーザーを取得する関数（認証不要）
    ユーザーがログインしていない場合はNoneを返す
    """
    try:
        # セッションからユーザー情報を取得
        session_user = request.session.get("user")
        if session_user:
            LOGGER.info(f"セッションからユーザー取得: {session_user['username']}")
            # idフィールドをuser_idに変換
            user_data = session_user.copy()
            if 'id' in user_data:
                user_data['user_id'] = user_data.pop('id')
            return User(**user_data)
        
        # 開発モードでは仮のユーザーを返す
        if DEBUG_MODE:
            LOGGER.info("開発モード: 仮のユーザーを返します")
            # 開発モードでもセッションに保存
            if "user" not in request.session:
                user = User("admin", "admin@example.com", "admin", 1)
                request.session["user"] = user.to_dict()
            return User("admin", "admin@example.com", "admin", 1)
        
        return None
    except Exception as e:
        LOGGER.error(f"ユーザー取得エラー: {e}")
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

def login_user(request: Request, username: str, password: str) -> Optional[User]:
    """
    ユーザーログイン処理
    
    Args:
        request: FastAPIリクエスト
        username: ユーザー名
        password: パスワード
    
    Returns:
        Optional[User]: ログイン成功時はユーザー情報、失敗時はNone
    """
    # 仮の認証（後でSAML/OIDCに置き換え）
    if username in USERS and password == "password":  # 仮のパスワード
        user_data = USERS[username].copy()
        user_data['user_id'] = 1  # デフォルトのユーザーID
        user = User(**user_data)
        
        # セッションにユーザー情報を保存
        request.session["user"] = user.to_dict()
        LOGGER.info(f"ログイン成功: {username}")
        return user
    
    LOGGER.warning(f"ログイン失敗: {username}")
    return None

def logout_user(request: Request):
    """
    ユーザーログアウト処理
    
    Args:
        request: FastAPIリクエスト
    """
    if "user" in request.session:
        username = request.session["user"].get("username", "unknown")
        del request.session["user"]
        LOGGER.info(f"ログアウト: {username}") 