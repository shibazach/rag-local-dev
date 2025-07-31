# new/auth.py
# 認証関連モジュール（一時的なスタブ）

from fastapi import Depends, HTTPException, status

def get_current_user():
    """
    現在のユーザーを取得する（一時的なスタブ）
    TODO: 実際の認証実装
    """
    # 一時的に常にadminユーザーを返す
    return {
        "username": "admin",
        "role": "admin",
        "is_active": True
    }

def require_admin():
    """
    管理者権限を要求する
    """
    user = get_current_user()
    if user["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="管理者権限が必要です"
        )
    return user