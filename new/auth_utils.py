# new/auth_utils.py
# 認証処理の統一化ユーティリティ

from fastapi import Request, status
from fastapi.responses import RedirectResponse
from new.auth import get_optional_user

def require_login(request: Request):
    """
    ログイン必須チェック
    
    Returns:
        user: ユーザー情報（辞書）
        None: 未ログインの場合はRedirectResponseを発生
    """
    user = get_optional_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    return user

def require_admin(request: Request):
    """
    admin権限必須チェック
    
    Returns:
        user: ユーザー情報（辞書）
        None: 権限不足の場合はRedirectResponseを発生
    """
    user = get_optional_user(request)
    if not user or user.get('role') != 'admin':
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    return user

def is_admin_user(user):
    """
    ユーザーがadmin権限を持つかチェック
    
    Args:
        user: ユーザー情報（辞書）
        
    Returns:
        bool: admin権限の有無
    """
    return user and user.get('role') == 'admin'