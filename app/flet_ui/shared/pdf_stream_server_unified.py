#!/usr/bin/env python3
"""
統合PDFストリーミングサーバー
V3 (WebView/HTML) + V4 (画像変換) 統合版

主要機能:
- WebView方式：PDF.js + HTMLビューア (小容量PDF用)
- 画像方式：PyMuPDF + PNG変換 (大容量PDF用)
- 自動フォールバック：ファイルサイズベース切り替え
- 統一API：シングルサーバーで両方式提供

エンドポイント:
- /pdf/{file_id} : PDF本体配信
- /viewer/{file_id} : HTMLビューア (V3方式)
- /img/{file_id}/{page} : ページ画像 (V4方式)
- /info/{file_id} : PDF情報取得
- /health : サーバー状態
"""

import os
import json
import logging
import asyncio
import tempfile
import shutil
from typing import Dict, Optional, Tuple, Any
from pathlib import Path

from aiohttp import web, hdrs
from aiohttp.web import FileResponse
import aiofiles

# V3/V4機能インポート
from .pdf_stream_server_v3 import PDFStreamServerV3
from .pdf_stream_server_v4 import PDFStreamServerV4
from .pdf_page_renderer import get_pdf_page_count

logger = logging.getLogger(__name__)

# サイズ閾値設定
SIZE_THRESHOLD_SMALL = 1.5 * 1024 * 1024    # 1.5MB - data:URL可能
SIZE_THRESHOLD_WEBVIEW = 20 * 1024 * 1024   # 20MB - WebView推奨上限
SIZE_THRESHOLD_IMAGE = 100 * 1024 * 1024    # 100MB - 画像変換推奨


class PDFStreamServerUnified:
    """統合PDFストリーミングサーバー (V3+V4統合)"""

    def __init__(self, host: str = "127.0.0.1", port: int = 0):
        self.host = host
        self.port = port
        self.actual_port: Optional[int] = None
        self.public_host = host
        
        # 子サーバーインスタンス
        self.v3_server: Optional[PDFStreamServerV3] = None
        self.v4_server: Optional[PDFStreamServerV4] = None
        
        # 共通状態管理
        self.pdf_files: Dict[str, str] = {}  # file_id -> file_path
        self.pdf_sizes: Dict[str, int] = {}  # file_id -> file_size
        self.pdf_strategies: Dict[str, str] = {}  # file_id -> strategy
        
        # サーバー管理
        self.app = web.Application()
        self.runner: Optional[web.AppRunner] = None
        self.site: Optional[web.TCPSite] = None
        
        # 統計情報
        self.stats = {
            "requests_total": 0,
            "webview_requests": 0,
            "image_requests": 0,
            "strategy_auto": 0,
            "strategy_forced": 0
        }
        
        self._setup_routes()

    def _setup_routes(self):
        """ルート設定"""
        # 統合エンドポイント
        self.app.router.add_get("/pdf/{file_id}", self._serve_pdf)
        self.app.router.add_get("/viewer/{file_id}", self._serve_viewer)
        self.app.router.add_get("/img/{file_id}/{page:\\d+}", self._serve_image)
        self.app.router.add_get("/info/{file_id}", self._serve_info)
        self.app.router.add_get("/health", self._serve_health)

    def _determine_strategy(self, file_path: str, file_size: int, force_strategy: Optional[str] = None) -> str:
        """表示方式決定"""
        if force_strategy:
            self.stats["strategy_forced"] += 1
            return force_strategy
        
        self.stats["strategy_auto"] += 1
        
        # サイズベース自動判定
        # 一時的に画像戦略のみ（V3問題回避）
        return "image"

    async def register_pdf(self, file_path: str, file_id: Optional[str] = None, force_strategy: Optional[str] = None) -> str:
        """PDF登録（統合版・非同期）"""
        import uuid
        
        if file_id is None:
            file_id = str(uuid.uuid4())
        
        # ファイル情報取得
        file_size = os.path.getsize(file_path)
        strategy = self._determine_strategy(file_path, file_size, force_strategy)
        
        # 登録
        self.pdf_files[file_id] = file_path
        self.pdf_sizes[file_id] = file_size
        self.pdf_strategies[file_id] = strategy
        
        # 子サーバーに登録
        if strategy == "webview":
            if not self.v3_server:
                self.v3_server = PDFStreamServerV3(self.host, 0)
                await self.v3_server.start()
            self.v3_server.register_pdf(file_path, file_id)
        elif strategy == "image":
            if not self.v4_server:
                self.v4_server = PDFStreamServerV4(self.host, 0)
                await self.v4_server.start()
            # V4サーバーはバイトデータが必要
            with open(file_path, "rb") as f:
                pdf_data = f.read()
            await self.v4_server.register_pdf_async(file_id, pdf_data)
        
        logger.info(f"[Unified] PDF registered: {file_id} -> {strategy} strategy ({file_size} bytes)")
        return file_id

    async def _serve_pdf(self, request: web.Request):
        """PDF本体配信"""
        file_id = request.match_info["file_id"]
        self.stats["requests_total"] += 1
        
        if file_id not in self.pdf_files:
            return web.json_response({"error": "PDF not found"}, status=404)
        
        file_path = self.pdf_files[file_id]
        strategy = self.pdf_strategies[file_id]
        
        # 戦略に応じて子サーバーに委任
        if strategy == "webview" and self.v3_server:
            return await self.v3_server._serve_pdf(request)
        elif strategy == "image" and self.v4_server:
            return await self.v4_server._serve_pdf(request)
        
        # フォールバック: 直接配信
        return FileResponse(file_path, headers={
            "Content-Type": "application/pdf",
            "Content-Disposition": f"inline; filename={os.path.basename(file_path)}"
        })

    async def _serve_viewer(self, request: web.Request):
        """HTMLビューア配信 (WebView方式専用)"""
        file_id = request.match_info["file_id"]
        self.stats["webview_requests"] += 1
        
        if file_id not in self.pdf_files:
            return web.json_response({"error": "PDF not found"}, status=404)
        
        strategy = self.pdf_strategies[file_id]
        
        if strategy == "webview" and self.v3_server:
            return await self.v3_server._serve_viewer(request)
        
        return web.json_response({"error": "WebView not available for this PDF"}, status=400)

    async def _serve_image(self, request: web.Request):
        """画像配信 (画像方式専用)"""
        file_id = request.match_info["file_id"]
        self.stats["image_requests"] += 1
        
        if file_id not in self.pdf_files:
            return web.json_response({"error": "PDF not found"}, status=404)
        
        strategy = self.pdf_strategies[file_id]
        
        if strategy == "image" and self.v4_server:
            return await self.v4_server._serve_page_image(request)
        
        return web.json_response({"error": "Image rendering not available for this PDF"}, status=400)

    async def _serve_info(self, request: web.Request):
        """PDF情報配信"""
        file_id = request.match_info["file_id"]
        
        if file_id not in self.pdf_files:
            return web.json_response({"error": "PDF not found"}, status=404)
        
        file_path = self.pdf_files[file_id]
        file_size = self.pdf_sizes[file_id]
        strategy = self.pdf_strategies[file_id]
        
        try:
            page_count = get_pdf_page_count(file_path)
            
            return web.json_response({
                "file_id": file_id,
                "file_path": os.path.basename(file_path),
                "file_size": file_size,
                "page_count": page_count,
                "strategy": strategy,
                "recommended_strategy": self._determine_strategy(file_path, file_size),
                "thresholds": {
                    "webview_max": SIZE_THRESHOLD_WEBVIEW,
                    "image_recommended": SIZE_THRESHOLD_IMAGE
                }
            })
        except Exception as e:
            logger.error(f"[Unified] PDF info error: {e}")
            return web.json_response({"error": f"PDF analysis failed: {e}"}, status=500)

    async def _serve_health(self, request: web.Request):
        """ヘルスチェック"""
        return web.json_response({
            "status": "healthy",
            "server_type": "unified",
            "port": self.actual_port,
            "v3_active": self.v3_server is not None,
            "v4_active": self.v4_server is not None,
            "registered_pdfs": len(self.pdf_files),
            "stats": self.stats
        })

    async def start(self):
        """サーバー開始"""
        try:
            self.runner = web.AppRunner(self.app)
            await self.runner.setup()
            
            self.site = web.TCPSite(self.runner, self.host, self.port)
            await self.site.start()
            
            # 実際のポート取得
            for socket in self.site._server.sockets:
                if socket.family.name == 'AF_INET':
                    self.actual_port = socket.getsockname()[1]
                    break
            
            # 子サーバー開始 (必要時)
            if self.v3_server:
                await self.v3_server.start()
            if self.v4_server:
                await self.v4_server.start()
            
            logger.info(f"[Unified] Server started on {self.host}:{self.actual_port}")
            
        except Exception as e:
            logger.error(f"[Unified] Start error: {e}")
            raise

    async def stop(self):
        """サーバー停止"""
        try:
            # 子サーバー停止
            if self.v3_server:
                await self.v3_server.stop()
            if self.v4_server:
                await self.v4_server.stop()
            
            # メインサーバー停止
            if self.site:
                await self.site.stop()
            if self.runner:
                await self.runner.cleanup()
            
            logger.info("[Unified] Server stopped")
            
        except Exception as e:
            logger.error(f"[Unified] Stop error: {e}")

    def get_viewer_url(self, file_id: str) -> Optional[str]:
        """WebViewビューアURL取得"""
        if file_id not in self.pdf_files or not self.actual_port:
            return None
        
        strategy = self.pdf_strategies[file_id]
        if strategy != "webview":
            return None
        
        return f"http://{self.public_host}:{self.actual_port}/viewer/{file_id}"

    def get_image_url(self, file_id: str, page_index: int, **params) -> Optional[str]:
        """画像URL取得"""
        if file_id not in self.pdf_files or not self.actual_port:
            return None
        
        strategy = self.pdf_strategies[file_id]
        if strategy != "image":
            return None
        
        base_url = f"http://{self.public_host}:{self.actual_port}/img/{file_id}/{page_index}"
        
        # パラメータ追加
        query_parts = []
        for key in ["width", "w", "dpr", "fmt", "rotation"]:
            if key in params:
                query_parts.append(f"{key}={params[key]}")
        
        if query_parts:
            return f"{base_url}?{'&'.join(query_parts)}"
        return base_url

    def get_pdf_url(self, file_id: str) -> Optional[str]:
        """PDF本体URL取得"""
        if file_id not in self.pdf_files or not self.actual_port:
            return None
        return f"http://{self.public_host}:{self.actual_port}/pdf/{file_id}"

    def get_info_url(self, file_id: str) -> Optional[str]:
        """PDF情報URL取得"""
        if file_id not in self.pdf_files or not self.actual_port:
            return None
        return f"http://{self.public_host}:{self.actual_port}/info/{file_id}"


# ---------------------------
# 統合サーバーマネージャー (シングルトン)
# ---------------------------

_unified_server_manager: Optional[PDFStreamServerUnified] = None

def get_unified_server_manager() -> PDFStreamServerUnified:
    """統合サーバーマネージャー取得"""
    global _unified_server_manager
    if _unified_server_manager is None:
        _unified_server_manager = PDFStreamServerUnified()
    return _unified_server_manager

async def serve_pdf_from_bytes_unified(pdf_data: bytes, filename: str = "document.pdf", force_strategy: Optional[str] = None) -> Tuple[str, str, str]:
    """
    PDFバイトデータから統合サーバー配信
    
    Returns:
        Tuple[file_id, strategy, url] - ファイルID、使用戦略、アクセスURL
    """
    server = get_unified_server_manager()
    
    # 一時ファイル作成
    temp_dir = Path(tempfile.mkdtemp(prefix="pdf_unified_"))
    temp_path = temp_dir / filename
    
    try:
        # PDFデータ書き込み
        async with aiofiles.open(temp_path, "wb") as f:
            await f.write(pdf_data)
        
        # サーバー未起動の場合は起動
        if server.actual_port is None:
            await server.start()
        
        # PDF登録
        file_id = await server.register_pdf(str(temp_path), force_strategy=force_strategy)
        strategy = server.pdf_strategies[file_id]
        
        # URL生成
        if strategy == "webview":
            url = server.get_viewer_url(file_id)
        else:  # image
            url = server.get_info_url(file_id)  # 情報URL (画像は個別ページURL)
        
        return file_id, strategy, url
        
    except Exception as e:
        logger.error(f"[Unified] Serve from bytes error: {e}")
        raise


if __name__ == "__main__":
    # テスト用
    import sys
    
    async def test_unified_server():
        server = PDFStreamServerUnified()
        
        if len(sys.argv) < 2:
            print("Usage: python pdf_stream_server_unified.py <pdf_path>")
            return
        
        pdf_path = sys.argv[1]
        
        try:
            await server.start()
            file_id = server.register_pdf(pdf_path)
            print(f"Server: http://127.0.0.1:{server.actual_port}")
            print(f"PDF: {file_id} ({server.pdf_strategies[file_id]} strategy)")
            
            if server.pdf_strategies[file_id] == "webview":
                print(f"Viewer: {server.get_viewer_url(file_id)}")
            else:
                print(f"Info: {server.get_info_url(file_id)}")
                print(f"Image (page 0): {server.get_image_url(file_id, 0, width=800)}")
            
            # 待機
            print("Press Ctrl+C to stop")
            while True:
                await asyncio.sleep(1)
                
        except KeyboardInterrupt:
            await server.stop()
        except Exception as e:
            logger.error(f"Test error: {e}")
            await server.stop()
    
    asyncio.run(test_unified_server())
