# new/main.py
# セキュリティ設計に基づく新しいFastAPIアプリケーション

import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from new.config import (
    DEBUG_MODE, CORS_ORIGINS, SECRET_KEY, 
    SESSION_COOKIE_NAME, SESSION_COOKIE_SECURE,
    SESSION_COOKIE_HTTPONLY, SESSION_COOKIE_SAMESITE,
    STATIC_DIR, TEMPLATES_DIR, API_PREFIX, LOGGER,
    INPUT_DIR, OUTPUT_DIR
)
from new.database import init_db
from new.auth import get_current_user

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
        init_db()
        
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
    
    # NiceGUIパスの場合は制限を緩和
    if request.url.path.startswith('/nicegui/'):
        # NiceGUI用の緩和されたCSP
        csp = (
            "default-src 'self' 'unsafe-inline' 'unsafe-eval' data: blob:; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline' data:; "
            "img-src 'self' data: https: blob:; "
            "font-src 'self' data: https:; "
            "connect-src 'self' ws: wss:; "
            "frame-src 'self'; "
            "child-src 'self';"
        )
    else:
        # 通常ページ用のCSP
        csp = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' data:; "
            "connect-src 'self' ws: wss:; "
            "frame-src 'self'; "
            "child-src 'self';"
        )
    
    # セキュリティヘッダー設定
    response.headers["X-Content-Type-Options"] = "nosniff"
    # X-Frame-Optionsを削除（PDFプレビュー用）
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Content-Security-Policy"] = csp
    
    return response

# 静的ファイル配信
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# テンプレート設定
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# ルーター登録  
from new.api import files_router, upload_router
from new.api.chat import router as chat_router

# 認証APIルーター（api.py）
from new.routes.api import router as api_router
app.include_router(api_router, prefix=API_PREFIX, tags=["Auth"])

# データ登録関連APIルーター
app.include_router(files_router, prefix=API_PREFIX, tags=["Files"])
app.include_router(upload_router, prefix=API_PREFIX, tags=["Upload"])

# Processing API
from new.api.processing import router as processing_router
app.include_router(processing_router, prefix=API_PREFIX, tags=["Processing"])

# Ingest API (データ登録処理・SSE)
from new.api.ingest import router as ingest_router
app.include_router(ingest_router, prefix=API_PREFIX, tags=["Ingest"])

# File Selection API (ファイル選択・フィルタリング)
from new.api.file_selection import router as file_selection_router
app.include_router(file_selection_router, prefix=API_PREFIX, tags=["File Selection"])

# OCR Comparison API (OCR比較検証)
from new.api.ocr_comparison import router as ocr_comparison_router
app.include_router(ocr_comparison_router, prefix=API_PREFIX, tags=["OCR Comparison"])

# Chat API (チャット検索)
app.include_router(chat_router, prefix=API_PREFIX, tags=["Chat"])

# UI Routes (UIルーター)
from new.routes.ui import router as ui_router
app.include_router(ui_router, prefix="", tags=["UI"])

# NiceGUI完全版統合（一時的に無効化）
# try:
#     from new.nicegui_app import init_nicegui_app
#     init_nicegui_app(app)
#     LOGGER.info("🚀 NiceGUI完全版統合完了: /rag-nicegui/")
# except ImportError as e:
#     LOGGER.warning(f"NiceGUI統合スキップ: {e}")
# except Exception as e:
#     LOGGER.error(f"NiceGUI統合エラー: {e}")
LOGGER.info("🚀 NiceGUI統合スキップ（純粋WebUI専用モード）")

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
    import sys
    
    # コマンドライン引数解析
    host = "0.0.0.0"
    port = 8000
    
    for i, arg in enumerate(sys.argv):
        if arg == "--host" and i + 1 < len(sys.argv):
            host = sys.argv[i + 1]
        elif arg == "--port" and i + 1 < len(sys.argv):
            port = int(sys.argv[i + 1])
    
    uvicorn.run(
        "new.main:app",
        host=host,
        port=port,
        reload=False,  # watchfilesループ防止
        log_level="info"
    ) 