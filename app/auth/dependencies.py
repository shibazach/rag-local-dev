"""
認証依存性注入 - Prototype統合版
FastAPI + NiceGUIの統合認証システム
"""

from typing import Optional, Dict, Any
from fastapi import Request, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from nicegui import ui

from app.config import logger

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

def get_current_user_optional(request: Request = None) -> Optional[Dict[str, Any]]:
    """
    オプショナル認証
    ログインしていなくてもアクセス可能なページ用
    NiceGUIのストレージも確認
    """
    try:
        # NiceGUIストレージから確認（優先）
        if hasattr(ui, 'storage') and ui.storage.user:
            user_data = ui.storage.user.get('user')
            if user_data:
                logger.debug(f"NiceGUI認証済みユーザー: {user_data.get('username', 'unknown')}")
                return user_data
        
        # FastAPIセッションから確認
        if request and hasattr(request, 'session'):
            user_data = request.session.get("user")
            if user_data:
                logger.debug(f"セッション認証済みユーザー: {user_data.get('username', 'unknown')}")
                return user_data
        
        return None
    except Exception as e:
        logger.warning(f"認証情報取得エラー: {e}")
        return None

def get_current_user_required(request: Request = None) -> Dict[str, Any]:
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

# NiceGUI用認証デコレーター
def require_auth(admin_only: bool = False):
    """
    NiceGUIページ用認証デコレーター
    
    Usage:
        @ui.page('/protected')
        @require_auth()
        def protected_page():
            ui.label('Protected content')
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            user = get_current_user_optional()
            
            if not user:
                # 未認証の場合はログインページへリダイレクト
                ui.open('/login')
                return
            
            if admin_only and not user.get('is_admin', False):
                # 権限不足の場合
                ui.notify('管理者権限が必要です', color='negative')
                ui.open('/')
                return
            
            # 認証成功
            return await func(*args, **kwargs) if hasattr(func, '__await__') else func(*args, **kwargs)
        
        return wrapper
    return decorator