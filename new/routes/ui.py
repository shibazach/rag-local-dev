# new/routes/ui.py
# UIルーター（認証制御付き）

from fastapi import APIRouter, Request, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from new.config import TEMPLATES_DIR
from new.auth import get_optional_user, get_current_user
from new.auth_utils import require_login, require_admin, get_current_user_from_session

router = APIRouter()
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """メインページ"""
    from new.auth import get_optional_user
    user = get_optional_user(request)
    show_auth_ui = True
    return templates.TemplateResponse("index.html", {"request": request, "is_home": True, "show_auth_ui": show_auth_ui, "user": user})

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """ログインページ"""
    return templates.TemplateResponse("login.html", {"request": request, "show_auth_ui": False})

@router.get("/logout")
async def logout_page(request: Request):
    """ログアウト処理"""
    # セッションクリア
    request.session.clear()
    # ホームページにリダイレクト
    return RedirectResponse(url="/", status_code=302)



@router.get("/files", response_class=HTMLResponse)
async def files_page(request: Request):
    """ファイル管理ページ（認証必要）"""
    auth_result = require_login(request)
    if isinstance(auth_result, RedirectResponse):
        return auth_result
    return templates.TemplateResponse("files.html", {"request": request, "show_auth_ui": True})

@router.get("/upload", response_class=HTMLResponse)
async def upload_page(request: Request):
    """ファイルアップロードページ（admin権限必要）"""
    auth_result = require_admin(request)
    if isinstance(auth_result, RedirectResponse):
        return auth_result
    return templates.TemplateResponse("upload.html", {"request": request, "show_auth_ui": True})

@router.get("/admin", response_class=HTMLResponse)
async def admin_page(request: Request):
    """管理者ページ（admin権限必要）"""
    auth_result = require_admin(request)
    if isinstance(auth_result, RedirectResponse):
        return auth_result
    return templates.TemplateResponse("admin.html", {"request": request, "show_auth_ui": True})

@router.get("/data-registration", response_class=HTMLResponse)
async def data_registration_page(request: Request):
    """データ登録ページ（admin権限必要）"""
    auth_result = require_admin(request)
    if isinstance(auth_result, RedirectResponse):
        return auth_result

    # 埋め込みオプション（OLD系互換）
    from new.config import EMBEDDING_OPTIONS
    embedding_options = EMBEDDING_OPTIONS

    return templates.TemplateResponse("data_registration.html", {
        "request": request,
        "embedding_options": embedding_options,
        "show_auth_ui": True
    })

@router.get("/ocr-comparison", response_class=HTMLResponse)
async def ocr_comparison_page(request: Request):
    """OCR比較検証ページ（admin権限必要）"""
    auth_result = require_admin(request)
    if isinstance(auth_result, RedirectResponse):
        return auth_result
    return templates.TemplateResponse("ocr_comparison.html", {"request": request, "show_auth_ui": True})

@router.get("/chat", response_class=HTMLResponse)
async def chat_page(request: Request):
    """チャット検索ページ（認証必要）"""
    auth_result = require_login(request)
    if isinstance(auth_result, RedirectResponse):
        return auth_result
    
    user = get_optional_user(request)
    
    # 埋め込みオプション（OLD系互換）
    from new.config import EMBEDDING_OPTIONS
    embedding_options = EMBEDDING_OPTIONS
    
    return templates.TemplateResponse("chat.html", {
        "request": request,
        "user": user,
        "embedding_options": embedding_options,
        "show_auth_ui": True
    }) 