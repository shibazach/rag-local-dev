"""
認証モジュール - Prototype統合版
FastAPI + NiceGUI統合認証システム
"""

from .dependencies import (
    get_current_user_optional,
    get_current_user_required,
    require_admin,
    require_api_key,
    require_auth,
    AuthenticationError,
    AuthorizationError
)
from .session import SessionManager, session_manager

__all__ = [
    # FastAPI依存関係
    "get_current_user_optional",
    "get_current_user_required", 
    "require_admin",
    "require_api_key",
    # NiceGUIデコレーター
    "require_auth",
    # 例外クラス
    "AuthenticationError",
    "AuthorizationError",
    # セッション管理
    "SessionManager",
    "session_manager"
]
