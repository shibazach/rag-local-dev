# new/main.py
# セキュリティ設計に基づく新しいFastAPIアプリケーション

import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from .config import (
    DEBUG_MODE, CORS_ORIGINS, SECRET_KEY, 
    SESSION_COOKIE_NAME, SESSION_COOKIE_SECURE,
    SESSION_COOKIE_HTTPONLY, SESSION_COOKIE_SAMESITE,
    STATIC_DIR, TEMPLATES_DIR, API_PREFIX, LOGGER
)
from .database import init_db
from .auth import get_current_user

# FastAPIアプリケーション作成
app = FastAPI(
    title="R&D RAGシステム",
    description="R&D RAGシステムのAPI",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    openapi_tags=[
        {"name": "auth", "description": "認証関連API"},
        {"name": "files", "description": "ファイル管理API"},
        {"name": "search", "description": "検索API"},
        {"name": "chat", "description": "チャットAPI"},
        {"name": "queue", "description": "キュー管理API"},
        {"name": "stats", "description": "統計API"},
    ]
)

# アプリケーション起動時の処理
@app.on_event("startup")
async def startup_event():
    """アプリケーション起動時の処理"""
    try:
        # データベース初期化
        await init_database()
        
        # 必要なディレクトリを作成
        INPUT_DIR.mkdir(parents=True, exist_ok=True)
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        
    except Exception as e:
        LOGGER.error(f"起動エラー: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """アプリケーション終了時の処理"""
    try:
        # クリーンアップ処理
        pass
    except Exception as e:
        LOGGER.error(f"終了エラー: {e}")

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# セッション管理（CORSの後に追加）
app.add_middleware(
    SessionMiddleware,
    secret_key=SECRET_KEY,
    session_cookie=SESSION_COOKIE_NAME,
    max_age=3600,  # 1時間
    same_site=SESSION_COOKIE_SAMESITE,
    https_only=SESSION_COOKIE_SECURE
)

# セキュリティヘッダー設定
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """セキュリティヘッダーを追加"""
    response = await call_next(request)
    
    # セキュリティヘッダー設定
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    
    # Content Security Policy
    csp = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data: https:; "
        "font-src 'self'; "
        "connect-src 'self' ws: wss:;"
    )
    response.headers["Content-Security-Policy"] = csp
    
    return response

# 静的ファイル配信
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# テンプレート設定
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# ルーター登録
from .routes import api_router, ui_router

# APIルーター（認証付き）
app.include_router(api_router, prefix=API_PREFIX, tags=["API"])

# UIルーター（認証不要）
app.include_router(ui_router, tags=["UI"])

# ヘルスチェック
@app.get("/health")
async def health_check():
    """ヘルスチェックエンドポイント"""
    return {"status": "healthy", "version": "2.0.0"}

# ルートエンドポイント
@app.get("/")
async def root(request: Request):
    """ルートエンドポイント"""
    return templates.TemplateResponse("index.html", {"request": request})

# エラーハンドリング
@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    """404エラーハンドリング"""
    return templates.TemplateResponse("404.html", {"request": request}, status_code=404)

@app.exception_handler(500)
async def internal_error_handler(request: Request, exc):
    """500エラーハンドリング"""
    LOGGER.exception("内部サーバーエラー")
    return templates.TemplateResponse("500.html", {"request": request}, status_code=500)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "new.main:app",
        host="0.0.0.0",
        port=8000,
        reload=DEBUG_MODE,
        log_level="info"
    ) 