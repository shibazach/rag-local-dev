"""
認証依存性注入
Authentication dependencies for FastAPI
"""

from typing import Optional, Dict, Any
from fastapi import Request, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.config import logger
from app.core.database import get_db

security = HTTPBearer(auto_error=False)

class AuthenticationError(HTTPException):
    """認証エラー"""
    def __init__(self, detail: str = "認証が必要です"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"}
        )

class AuthorizationError(HTTPException):
    """認可エラー"""
    def __init__(self, detail: str = "権限が不足しています"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail
        )

def get_current_user_optional(request: Request) -> Optional[Dict[str, Any]]:
    """
    オプショナル認証
    ログインしていなくてもアクセス可能なページ用
    """
    try:
        user_data = request.session.get("user")
        if user_data:
            logger.debug(f"認証済みユーザー: {user_data.get('username', 'unknown')}")
            return user_data
        return None
    except Exception as e:
        logger.warning(f"セッション取得エラー: {e}")
        return None

def get_current_user_required(request: Request) -> Dict[str, Any]:
    """
    必須認証
    ログインが必要なページ用
    """
    user = get_current_user_optional(request)
    if not user:
        logger.warning("未認証アクセス試行")
        raise AuthenticationError()
    return user

def require_admin(current_user = Depends(get_current_user_required)):
    """
    管理者権限必須
    """
    if not current_user.get("is_admin", False):
        logger.warning(f"管理者権限不足: {current_user.get('username', 'unknown')}")
        raise AuthorizationError("管理者権限が必要です")
    return current_user

def require_api_key(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> str:
    """
    API キー認証（将来のAPI拡張用）
    """
    if not credentials:
        raise AuthenticationError("API キーが必要です")
    
    # TODO: API キー検証ロジック実装
    api_key = credentials.credentials
    if not api_key:
        raise AuthenticationError("無効なAPI キーです")
    
    return api_key

# 便利なエイリアス（データベースセッションのみ残存）
DatabaseSession = Depends(get_db)