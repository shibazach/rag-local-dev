# new/routes/ui.py
# UIルーター（認証制御付き）

from fastapi import APIRouter, Request, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from ..config import TEMPLATES_DIR
from ..auth import get_optional_user, get_current_user

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
    user = get_optional_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    return templates.TemplateResponse("chat.html", {"request": request})

@router.get("/files", response_class=HTMLResponse)
async def files_page(request: Request):
    """ファイル管理ページ（admin権限必要）"""
    user = get_optional_user(request)
    if not user or user.role != 'admin':
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    return templates.TemplateResponse("files.html", {"request": request})

@router.get("/upload", response_class=HTMLResponse)
async def upload_page(request: Request):
    """ファイルアップロードページ（admin権限必要）"""
    user = get_optional_user(request)
    if not user or user.role != 'admin':
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    return templates.TemplateResponse("upload.html", {"request": request})

@router.get("/admin", response_class=HTMLResponse)
async def admin_page(request: Request):
    """管理者ページ（admin権限必要）"""
    user = get_optional_user(request)
    if not user or user.role != 'admin':
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    return templates.TemplateResponse("admin.html", {"request": request}) 