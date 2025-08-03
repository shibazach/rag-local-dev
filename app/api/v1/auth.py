"""
認証API v1
Authentication endpoints with session management
"""

from fastapi import APIRouter, Request, Response, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import Dict, Any

from app.core import (
    get_db,
    User,
    UserCreate,
    UserLogin,
    UserResponse,
    AuthResponse,
    BaseResponse
)
from app.auth import (
    SessionManager,
    session_manager,
    get_current_user_optional,
    get_current_user_required,
    require_admin
)
from app.api import log_api_request, create_error_response
from app.config import logger

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/login", response_model=AuthResponse)
async def login(
    credentials: UserLogin,
    request: Request,
    response: Response,
    db: Session = Depends(get_db)
):
    """
    ユーザーログイン
    Creates user session and returns user info
    """
    try:
        # ユーザー検索
        user = db.query(User).filter(User.username == credentials.username).first()
        if not user or not user.is_active:
            log_api_request(request, action="login_failed")
            raise create_error_response(
                401, "AUTH_INVALID_CREDENTIALS", 
                "ユーザー名またはパスワードが正しくありません"
            )
        
        # パスワード検証
        if not session_manager.verify_password(
            credentials.password, 
            user.password_hash, 
            user.password_salt
        ):
            log_api_request(request, action="login_failed")
            raise create_error_response(
                401, "AUTH_INVALID_CREDENTIALS",
                "ユーザー名またはパスワードが正しくありません"
            )
        
        # セッション作成
        user_data = {
            "id": str(user.id),
            "username": user.username,
            "email": user.email,
            "display_name": user.display_name,
            "role": user.role,
            "is_admin": user.is_admin
        }
        
        session_id = session_manager.create_user_session(request, response, user_data)
        
        # 最終ログイン時刻更新
        from datetime import datetime
        user.last_login_at = datetime.utcnow()
        db.commit()
        
        log_api_request(request, user_data, "login_success")
        
        return AuthResponse(
            success=True,
            message="ログインしました",
            user=UserResponse.from_orm(user),
            session_id=session_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"ログインエラー: {e}")
        raise create_error_response(
            500, "AUTH_LOGIN_ERROR",
            "ログイン処理中にエラーが発生しました"
        )

@router.post("/logout", response_model=BaseResponse)
async def logout(
    request: Request,
    response: Response,
    current_user = Depends(get_current_user_required)
):
    """
    ユーザーログアウト
    Destroys user session
    """
    try:
        session_manager.destroy_session(request, response)
        log_api_request(request, current_user, "logout")
        
        return BaseResponse(
            success=True,
            message="ログアウトしました"
        )
        
    except Exception as e:
        logger.error(f"ログアウトエラー: {e}")
        raise create_error_response(
            500, "AUTH_LOGOUT_ERROR",
            "ログアウト処理中にエラーが発生しました"
        )

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user = Depends(get_current_user_required),
    db: Session = Depends(get_db)
):
    """
    現在のユーザー情報取得
    Returns current user information
    """
    try:
        user = db.query(User).filter(User.id == current_user["id"]).first()
        if not user:
            raise create_error_response(
                404, "USER_NOT_FOUND",
                "ユーザーが見つかりません"
            )
        
        return UserResponse.from_orm(user)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"ユーザー情報取得エラー: {e}")
        raise create_error_response(
            500, "USER_INFO_ERROR",
            "ユーザー情報取得中にエラーが発生しました"
        )

@router.post("/register", response_model=AuthResponse)
async def register_user(
    user_data: UserCreate,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    admin_user = Depends(require_admin)
):
    """
    ユーザー登録（管理者のみ）
    Register new user (admin only)
    """
    try:
        # 重複チェック
        existing_user = db.query(User).filter(
            (User.username == user_data.username) | 
            (User.email == user_data.email)
        ).first()
        
        if existing_user:
            raise create_error_response(
                409, "USER_EXISTS",
                "ユーザー名またはメールアドレスが既に使用されています"
            )
        
        # パスワードハッシュ化
        password_hash, salt = session_manager.hash_password(user_data.password)
        
        # ユーザー作成
        new_user = User(
            username=user_data.username,
            email=user_data.email,
            password_hash=password_hash,
            password_salt=salt,
            display_name=user_data.display_name,
            department=user_data.department,
            role=user_data.role,
            is_active=True,
            is_verified=True
        )
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        log_api_request(
            request, admin_user, 
            f"user_register_{new_user.username}"
        )
        
        return AuthResponse(
            success=True,
            message="ユーザーを登録しました",
            user=UserResponse.from_orm(new_user)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"ユーザー登録エラー: {e}")
        db.rollback()
        raise create_error_response(
            500, "USER_REGISTER_ERROR",
            "ユーザー登録中にエラーが発生しました"
        )

@router.get("/session/check", response_model=BaseResponse)
async def check_session(
    request: Request,
    current_user = Depends(get_current_user_optional)
):
    """
    セッション有効性チェック
    Check session validity
    """
    try:
        if current_user and session_manager.is_session_valid(request):
            session_manager.update_last_activity(request)
            return BaseResponse(
                success=True,
                message="セッションは有効です"
            )
        else:
            return BaseResponse(
                success=False,
                message="セッションが無効です"
            )
            
    except Exception as e:
        logger.error(f"セッションチェックエラー: {e}")
        raise create_error_response(
            500, "SESSION_CHECK_ERROR",
            "セッションチェック中にエラーが発生しました"
        )

@router.post("/session/refresh", response_model=BaseResponse)
async def refresh_session(
    request: Request,
    response: Response,
    current_user = Depends(get_current_user_required)
):
    """
    セッション更新
    Refresh user session
    """
    try:
        # 新しいセッションID生成
        new_session_id = session_manager.create_session_id()
        
        # セッションデータ更新
        if "user" in request.session:
            request.session["user"]["session_id"] = new_session_id
            session_manager.update_last_activity(request)
        
        log_api_request(request, current_user, "session_refresh")
        
        return BaseResponse(
            success=True,
            message="セッションを更新しました"
        )
        
    except Exception as e:
        logger.error(f"セッション更新エラー: {e}")
        raise create_error_response(
            500, "SESSION_REFRESH_ERROR",
            "セッション更新中にエラーが発生しました"
        )