# REM: auth_functions.py @2024-12-19
# REM: 認証機能の関数型実装（クラス不使用、FastAPI依存注入活用）

# ── 標準ライブラリ ──
from typing import Optional, Dict, Any

# ── サードパーティ ──
from fastapi import Request, HTTPException, status
from fastapi.responses import RedirectResponse

# ── プロジェクト内 ──
from new.schemas import UserSession, UserResponse
from new.config import LOGGER

# ──────────────────────────────────────────────────────────
# 認証関数群（Pure Functions）
# ──────────────────────────────────────────────────────────

def validate_credentials(username: str, password: str) -> Optional[UserSession]:
    """
    認証情報検証（スタブ実装）
    
    Args:
        username: ユーザー名
        password: パスワード
    
    Returns:
        UserSession: 認証成功時のユーザー情報
        None: 認証失敗時
    """
    # ガードクローズ: 早期リターン
    if not username or not password:
        return None
    
    # スタブ認証ロジック
    if username == "admin" and password == "password":
        return UserSession(
            id=1,
            username="admin",
            role="admin",
            email="admin@example.com"
        )
    elif username == "user" and password == "user":
        return UserSession(
            id=2,
            username="user", 
            role="user",
            email="user@example.com"
        )
    
    return None

def get_current_user_from_session(request: Request) -> Optional[UserSession]:
    """
    セッションからユーザー情報取得
    
    Args:
        request: FastAPIリクエストオブジェクト
    
    Returns:
        UserSession: ユーザー情報
        None: セッションにユーザー情報がない場合
    """
    try:
        user_data = request.session.get("user")
        if not user_data:
            return None
        
        return UserSession(**user_data)
    except Exception as exc:
        LOGGER.warning(f"セッションからのユーザー取得エラー: {exc}")
        return None

def create_user_session(request: Request, user: UserSession) -> None:
    """
    セッションにユーザー情報保存
    
    Args:
        request: FastAPIリクエストオブジェクト
        user: 保存するユーザー情報
    """
    try:
        request.session["user"] = user.dict()
        LOGGER.info(f"ユーザーセッション作成: {user.username}")
    except Exception as exc:
        LOGGER.error(f"セッション作成エラー: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="セッション作成に失敗しました"
        )

def clear_user_session(request: Request) -> None:
    """
    セッションからユーザー情報削除
    
    Args:
        request: FastAPIリクエストオブジェクト
    """
    try:
        if "user" in request.session:
            username = request.session.get("user", {}).get("username", "unknown")
            del request.session["user"]
            LOGGER.info(f"ユーザーセッション削除: {username}")
    except Exception as exc:
        LOGGER.error(f"セッション削除エラー: {exc}")

# ──────────────────────────────────────────────────────────
# アクセス制御関数群
# ──────────────────────────────────────────────────────────

def require_authentication(request: Request) -> UserSession:
    """
    認証必須チェック（ガードクローズパターン）
    
    Args:
        request: FastAPIリクエストオブジェクト
    
    Returns:
        UserSession: 認証済みユーザー情報
    
    Raises:
        HTTPException: 未認証時
    """
    user = get_current_user_from_session(request)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="認証が必要です"
        )
    
    return user

def require_admin_role(request: Request) -> UserSession:
    """
    管理者権限必須チェック
    
    Args:
        request: FastAPIリクエストオブジェクト
    
    Returns:
        UserSession: 管理者ユーザー情報
    
    Raises:
        HTTPException: 権限不足時
    """
    user = require_authentication(request)
    
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="管理者権限が必要です"
        )
    
    return user

# ──────────────────────────────────────────────────────────
# UI認証ヘルパー関数群
# ──────────────────────────────────────────────────────────

def check_login_required(request: Request) -> Optional[RedirectResponse]:
    """
    ログイン必須ページのチェック（UI用）
    
    Args:
        request: FastAPIリクエストオブジェクト
    
    Returns:
        RedirectResponse: ログインページへのリダイレクト
        None: 認証済みの場合
    """
    user = get_current_user_from_session(request)
    
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    
    return None

def check_admin_required(request: Request) -> Optional[RedirectResponse]:
    """
    管理者権限必須ページのチェック（UI用）
    
    Args:
        request: FastAPIリクエストオブジェクト
    
    Returns:
        RedirectResponse: ログインページまたは権限エラーページへのリダイレクト
        None: 管理者認証済みの場合
    """
    user = get_current_user_from_session(request)
    
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="管理者権限が必要です"
        )
    
    return None

# ──────────────────────────────────────────────────────────
# 従来互換性関数（段階的移行用）
# ──────────────────────────────────────────────────────────

def get_current_user(request: Request) -> Dict[str, Any]:
    """従来のget_current_user互換関数"""
    user = get_current_user_from_session(request)
    return user.dict() if user else {}

def get_optional_user(request: Request) -> Optional[Dict[str, Any]]:
    """従来のget_optional_user互換関数"""
    user = get_current_user_from_session(request)
    return user.dict() if user else None

def require_admin(request: Request) -> Dict[str, Any]:
    """従来のrequire_admin互換関数"""
    user = require_admin_role(request)
    return user.dict()