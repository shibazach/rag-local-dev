# new/routes/ui.py
# UIルーター（認証制御付き）

from fastapi import APIRouter, Request, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from new.config import TEMPLATES_DIR
from new.auth import get_optional_user, get_current_user
from new.auth_utils import require_login, require_admin

router = APIRouter()
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """メインページ"""
    return templates.TemplateResponse("index.html", {"request": request})

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """ログインページ"""
    return templates.TemplateResponse("login.html", {"request": request})

@router.get("/chat", response_class=HTMLResponse)
async def chat_page(request: Request):
    """チャットページ（認証必要）"""
    auth_result = require_login(request)
    if isinstance(auth_result, RedirectResponse):
        return auth_result
    return templates.TemplateResponse("chat.html", {"request": request})

@router.get("/files", response_class=HTMLResponse)
async def files_page(request: Request):
    """ファイル管理ページ（認証必要）"""
    auth_result = require_login(request)
    if isinstance(auth_result, RedirectResponse):
        return auth_result
    return templates.TemplateResponse("files.html", {"request": request})

@router.get("/upload", response_class=HTMLResponse)
async def upload_page(request: Request):
    """ファイルアップロードページ（admin権限必要）"""
    auth_result = require_admin(request)
    if isinstance(auth_result, RedirectResponse):
        return auth_result
    return templates.TemplateResponse("upload.html", {"request": request})

@router.get("/admin", response_class=HTMLResponse)
async def admin_page(request: Request):
    """管理者ページ（admin権限必要）"""
    auth_result = require_admin(request)
    if isinstance(auth_result, RedirectResponse):
        return auth_result
    return templates.TemplateResponse("admin.html", {"request": request})

@router.get("/data-registration", response_class=HTMLResponse)
async def data_registration_page(request: Request):
    """データ登録ページ（admin権限必要）"""
    auth_result = require_admin(request)
    if isinstance(auth_result, RedirectResponse):
        return auth_result
    return templates.TemplateResponse("data_registration.html", {"request": request})

@router.get("/ocr-comparison", response_class=HTMLResponse)
async def ocr_comparison_page(request: Request):
    """OCR比較検証ページ（admin権限必要）"""
    auth_result = require_admin(request)
    if isinstance(auth_result, RedirectResponse):
        return auth_result
    return templates.TemplateResponse("ocr_comparison.html", {"request": request}) 