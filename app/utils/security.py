"""
セキュリティユーティリティ - Prototype統合版
セキュリティヘッダー設定・ミドルウェア
"""

from fastapi import Request
from fastapi.responses import Response

from app.config import config, logger

async def add_security_headers(request: Request, call_next):
    """
    セキュリティヘッダーを追加するミドルウェア
    new系から移植・改良
    """
    response = await call_next(request)
    
    # NiceGUIパスの場合は制限を緩和
    if request.url.path.startswith('/nicegui/') or request.url.path.startswith('/_nicegui/'):
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
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Content-Security-Policy"] = csp
    
    # 開発環境では追加のヘッダーをログ出力
    if config.DEBUG:
        logger.debug(f"Security headers added for path: {request.url.path}")
    
    return response

def get_security_headers() -> dict:
    """
    基本的なセキュリティヘッダーを取得
    
    Returns:
        セキュリティヘッダーの辞書
    """
    return {
        "X-Content-Type-Options": "nosniff",
        "X-XSS-Protection": "1; mode=block",
        "Referrer-Policy": "strict-origin-when-cross-origin"
    }

def get_csp_header(is_nicegui: bool = False) -> str:
    """
    Content Security Policyヘッダーを取得
    
    Args:
        is_nicegui: NiceGUI用の緩和されたポリシーを使用するか
        
    Returns:
        CSPヘッダー文字列
    """
    if is_nicegui:
        return (
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
        return (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' data:; "
            "connect-src 'self' ws: wss:; "
            "frame-src 'self'; "
            "child-src 'self';"
        )