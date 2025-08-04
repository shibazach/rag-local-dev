"""
R&D RAGシステム - メインアプリケーション
Enterprise-grade FastAPI API Backend (Pure API Server)
"""

import uvicorn
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from starlette.middleware.sessions import SessionMiddleware
from contextlib import asynccontextmanager

from app.config import config, logger
from app.core import init_database, db_health_check
from app.auth import AuthenticationError, AuthorizationError
from datetime import datetime
from app.api.v1 import auth, files, processing, admin, chat
from app.utils.logging import performance_log, security_log
from app.utils.security import rate_limiter, admin_ip_whitelist

# ========== アプリケーションライフサイクル ==========

@asynccontextmanager
async def lifespan(app: FastAPI):
    """アプリケーションライフサイクル管理"""
    # 起動時処理
    logger.info("🚀 RAGシステム起動開始")
    
    try:
        # データベース初期化
        init_database()
        logger.info("✅ データベース初期化完了")
        
        # 必要ディレクトリ作成
        config.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        config.PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
        config.LOG_DIR.mkdir(parents=True, exist_ok=True)
        logger.info("✅ ディレクトリ初期化完了")
        
        # NiceGUI統合（技術的課題により無効化）
        # AssertionError: assert core.loop is not None 
        # この問題はNiceGUI + FastAPI統合の複雑なイベントループ競合
        logger.info("✅ NiceGUI統合スキップ（API専用システムのため）")
        
        logger.info("🎉 RAGシステム起動完了")
        
    except Exception as e:
        logger.error(f"❌ 起動エラー: {e}")
        raise
    
    yield
    
    # 終了時処理
    logger.info("🛑 RAGシステム終了処理開始")
    # TODO: リソースクリーンアップ実装
    logger.info("✅ RAGシステム終了完了")

# ========== FastAPIアプリケーション作成 ==========

app = FastAPI(
    title=config.APP_NAME,
    description=config.APP_DESCRIPTION,
    version=config.APP_VERSION,
    docs_url=config.API_DOCS_URL,
    redoc_url=config.API_REDOC_URL,
    openapi_url=f"{config.API_V1_PREFIX}/openapi.json",
    lifespan=lifespan,
    openapi_tags=[
        {"name": "Authentication", "description": "認証・ユーザー管理"},
        {"name": "File Management", "description": "ファイルアップロード・管理"},
        {"name": "Processing", "description": "ファイル処理・OCR・LLM"},
        {"name": "Search", "description": "セマンティック検索"},
        {"name": "Chat", "description": "チャット・会話"},
        {"name": "Admin", "description": "システム管理"},
        {"name": "System", "description": "システム情報・ヘルスチェック"}
    ]
)

# ========== ミドルウェア設定 ==========

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"]
)

# セッション管理
app.add_middleware(
    SessionMiddleware,
    secret_key=config.SECRET_KEY,
    session_cookie=config.SESSION_COOKIE_NAME,
    max_age=config.SESSION_COOKIE_MAX_AGE,
    same_site=config.SESSION_COOKIE_SAMESITE,
    https_only=config.SESSION_COOKIE_SECURE
)

# セキュリティヘッダー
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """セキュリティヘッダー追加"""
    response = await call_next(request)
    
    # NiceGUI用の緩いCSP設定
    if request.url.path.startswith(config.NICEGUI_MOUNT_PATH):
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
        # 通常ページ用の厳しいCSP設定
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
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Content-Security-Policy"] = csp
    
    # HTTPS環境でのみ設定するヘッダー
    if config.SESSION_COOKIE_SECURE:
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    
    return response

# ========== 例外ハンドラー ==========

@app.exception_handler(AuthenticationError)
async def authentication_exception_handler(request: Request, exc: AuthenticationError):
    """認証エラーハンドラー"""
    logger.warning(f"認証エラー: {exc.detail} - {request.url}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error_code": "AUTHENTICATION_ERROR",
            "error_message": exc.detail,
            "redirect_url": "/login"
        }
    )

@app.exception_handler(AuthorizationError)
async def authorization_exception_handler(request: Request, exc: AuthorizationError):
    """認可エラーハンドラー"""
    logger.warning(f"認可エラー: {exc.detail} - {request.url}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error_code": "AUTHORIZATION_ERROR", 
            "error_message": exc.detail
        }
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """HTTP例外ハンドラー"""
    logger.error(f"HTTPエラー {exc.status_code}: {exc.detail} - {request.url}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error_code": f"HTTP_{exc.status_code}",
            "error_message": exc.detail
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """一般例外ハンドラー"""
    logger.error(f"予期しないエラー: {exc} - {request.url}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error_code": "INTERNAL_SERVER_ERROR",
            "error_message": "内部サーバーエラーが発生しました"
        }
    )

# ========== 静的ファイル配信 ==========

try:
    app.mount("/static", StaticFiles(directory="static"), name="static")
    logger.info("✅ 静的ファイル配信設定完了")
except Exception as e:
    logger.warning(f"静的ファイル配信設定スキップ: {e}")

# ========== APIルーター登録 ==========

# 認証API
from app.api.v1.auth import router as auth_router
app.include_router(auth_router, prefix=config.API_V1_PREFIX)

# ファイル管理API
from app.api.v1.files import router as files_router
app.include_router(files_router, prefix=config.API_V1_PREFIX)

# チャットAPI
app.include_router(chat.router, prefix=config.API_V1_PREFIX)

# 処理API  
app.include_router(processing.router, prefix=config.API_V1_PREFIX)

# 管理API
app.include_router(admin.router, prefix=config.API_V1_PREFIX)

# ========== システムエンドポイント ==========

@app.get("/health")
async def health_check():
    """ヘルスチェックエンドポイント"""
    try:
        db_status = db_health_check()
        
        return {
            "status": "healthy" if db_status["status"] == "healthy" else "unhealthy",
            "timestamp": str(datetime.utcnow()),
            "version": config.APP_VERSION,
            "environment": config.ENVIRONMENT,
            "components": {
                "database": db_status["status"],
                "api": "healthy",
                "ui": "healthy"
            }
        }
    except Exception as e:
        logger.error(f"ヘルスチェックエラー: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }

@app.get("/")
async def root():
    """ルートエンドポイント - HTMLページ"""
    html_content = f"""
    <!DOCTYPE html>
    <html lang="ja">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{config.APP_NAME}</title>
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; padding: 2rem; background: #f8f9fa; }}
            .container {{ max-width: 800px; margin: 0 auto; background: white; padding: 2rem; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
            .header {{ text-align: center; margin-bottom: 2rem; }}
            .header h1 {{ color: #2563eb; margin: 0; }}
            .header p {{ color: #6b7280; margin: 0.5rem 0; }}
            .links {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin-top: 2rem; }}
            .link-card {{ padding: 1.5rem; border: 1px solid #e5e7eb; border-radius: 6px; text-decoration: none; color: #374151; transition: all 0.2s; }}
            .link-card:hover {{ border-color: #2563eb; background: #f8fafc; transform: translateY(-2px); }}
            .link-card h3 {{ margin: 0 0 0.5rem 0; color: #2563eb; }}
            .link-card p {{ margin: 0; font-size: 0.9rem; color: #6b7280; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>{config.APP_NAME}</h1>
                <p>Version {config.APP_VERSION}</p>
                <p>Enterprise RAG System with NiceGUI</p>
            </div>
            
            <div class="links">
                <a href="/docs" class="link-card">
                    <h3>📚 API Documentation</h3>
                    <p>FastAPI自動生成API仕様書</p>
                </a>
                
                                            <a href="http://localhost:8082" class="link-card" target="_blank">
                                <h3>🖥️ Web UI</h3>
                                <p>メインWebインターフェース（new/系統）</p>
                            </a>
                
                <a href="/health" class="link-card">
                    <h3>🏥 Health Check</h3>
                    <p>システムヘルスチェック</p>
                </a>
                
                <a href="/api/v1/files" class="link-card">
                    <h3>📁 Files API</h3>
                    <p>ファイル管理API</p>
                </a>
            </div>
        </div>
    </body>
    </html>
    """
    from fastapi.responses import HTMLResponse
    return HTMLResponse(content=html_content)

@app.get("/api")
async def api_root():
    """APIルートエンドポイント - JSON"""
    return {
        "message": f"Welcome to {config.APP_NAME}",
        "version": config.APP_VERSION,
        "docs": config.API_DOCS_URL,
        "ui": config.NICEGUI_MOUNT_PATH
    }

# ========== アプリケーション実行 ==========

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=config.DEBUG,
        log_level=config.LOG_LEVEL.lower()
    )