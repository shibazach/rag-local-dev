#!/usr/bin/env python3
"""
V4大容量PDF対応 - 画像変換専用ストリーミングサーバー

技術方式:
- PDF → PNG/WebP画像変換 (PyMuPDF使用)
- 完全V3独立アーキテクチャ
- 高速化: LRUキャッシュ + 先読み + ETag
- フォーマット: PNG/WebP/JPEG対応
- 右ペイン内表示: ft.Image専用設計

主要エンドポイント:
- /pdf/{file_id} : PDF本体ダウンロード
- /img/{file_id}/{page} : ページ画像 (w/dpr/fmt)
- /info/{file_id} : PDF基本情報 (ページ数等)
- /health : サーバー状態確認

V3との差別化:
- WebView不使用 → プラットフォーム制限なし
- PDF.js不使用 → シンプルな画像表示
- 画像最適化 → 高速レンダリング + キャッシュ

パフォーマンス最適化:
- ETags によるHTTPキャッシュ
- CORS完全対応
- 非同期画像生成
- 先読みAPI提供
- 段階的品質制御
"""

import os
import tempfile
import logging
import asyncio
import threading
import json
from typing import Dict, Optional, Tuple, Literal
from datetime import datetime

from aiohttp import web
from .pdf_page_renderer import (
    render_page_image_async, 
    get_pdf_page_count, 
    prefetch_pages,
    clear_document_cache
)

# ログ設定
logger = logging.getLogger(__name__)
if not logging.getLogger().hasHandlers():
    logging.basicConfig(level=logging.INFO)

# aiohttp アクセスログを抑制（先読み処理の大量出力防止）
aiohttp_access_logger = logging.getLogger('aiohttp.access')
aiohttp_access_logger.setLevel(logging.WARNING)  # INFO → WARNING に変更

# 環境変数設定
DEFAULT_BIND_HOST = os.getenv("PDF_STREAM_V4_BIND", "127.0.0.1")
DEFAULT_PUBLIC_HOST = os.getenv("PDF_STREAM_V4_PUBLIC", "127.0.0.1") 
DEFAULT_PORT = int(os.getenv("PDF_STREAM_V4_PORT", "0"))  # 0=動的割当

# デフォルト設定
DEFAULT_IMAGE_WIDTH = 1200
DEFAULT_DPR = 1.0
DEFAULT_FORMAT = "png"
SUPPORTED_FORMATS = ["png", "webp", "jpeg"]

# ---------------------------
# CORS ミドルウェア (V4専用)
# ---------------------------
@web.middleware
async def cors_middleware_v4(request: web.Request, handler):
    """V4専用CORSミドルウェア"""
    if request.method == "OPTIONS":
        response = web.Response(status=204)
    else:
        response = await handler(request)

    # CORS ヘッダー設定
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, HEAD, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "*"
    response.headers["Access-Control-Expose-Headers"] = (
        "Accept-Ranges, Content-Range, Content-Length, Content-Type, ETag, Cache-Control"
    )
    
    return response


class PDFStreamServerV4:
    """V4画像変換専用ストリーミングサーバー"""

    def __init__(self, host: str = DEFAULT_BIND_HOST, port: int = DEFAULT_PORT, public_host: Optional[str] = None):
        self.host = host
        self.public_host = public_host or DEFAULT_PUBLIC_HOST
        self.port = port
        self.actual_port: Optional[int] = None
        
        # aiohttp アプリケーション
        self.app = web.Application(middlewares=[cors_middleware_v4])
        self.runner: Optional[web.AppRunner] = None
        self.site: Optional[web.TCPSite] = None
        
        # PDF管理
        self.temp_dir = tempfile.mkdtemp(prefix="pdf_stream_v4_")
        self.pdf_files: Dict[str, str] = {}  # file_id -> temp_path
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        
        # 統計情報
        self.stats = {
            "requests_total": 0,
            "images_served": 0,
            "cache_hits": 0,
            "errors": 0,
            "start_time": datetime.now().isoformat()
        }
        
        self._setup_routes()

    def _setup_routes(self):
        """ルート設定"""
        # PDF本体配信 (GETは自動的にHEADも処理)
        self.app.router.add_get("/pdf/{file_id}", self._serve_pdf)
        
        # 画像配信 (メインエンドポイント・GETは自動的にHEADも処理)
        self.app.router.add_get("/img/{file_id}/{page:\\d+}", self._serve_page_image)
        
        # PDF情報取得
        self.app.router.add_get("/info/{file_id}", self._serve_pdf_info)
        
        # 先読み要求
        self.app.router.add_post("/prefetch/{file_id}", self._handle_prefetch)
        
        # ヘルスチェック
        self.app.router.add_get("/health", self._health_check)
        
        # 統計情報
        self.app.router.add_get("/stats", self._get_stats)
        
        # OPTIONS対応
        self.app.router.add_route("OPTIONS", "/{path:.*}", self._options_handler)
        
    async def _options_handler(self, request: web.Request):
        """OPTIONSリクエスト処理"""
        return web.Response(status=204)

    async def _health_check(self, request: web.Request):
        """ヘルスチェック"""
        self.stats["requests_total"] += 1
        
        return web.json_response({
            "status": "healthy",
            "version": "v4",
            "server_type": "image_conversion",
            "port": self.actual_port,
            "pdf_count": len(self.pdf_files),
            "uptime": (datetime.now() - datetime.fromisoformat(self.stats["start_time"])).total_seconds()
        })

    async def _get_stats(self, request: web.Request):
        """統計情報取得"""
        return web.json_response(self.stats)

    async def _serve_pdf(self, request: web.Request):
        """PDF本体配信 (ダウンロード用)"""
        file_id = request.match_info["file_id"]
        path = self.pdf_files.get(file_id)
        
        self.stats["requests_total"] += 1
        
        if not path or not os.path.isfile(path):
            self.stats["errors"] += 1
            return web.Response(status=404, text="PDF not found")

        # PDF配信 (Range対応はFileResponseに委譲)
        headers = {
            "Content-Type": "application/pdf",
            "Accept-Ranges": "bytes",
            "Cache-Control": "private, max-age=300",
            "X-Content-Type-Options": "nosniff"
        }
        
        return web.FileResponse(path=path, headers=headers, chunk_size=64 * 1024)

    async def _serve_pdf_info(self, request: web.Request):
        """PDF基本情報取得 (ページ数等)"""
        file_id = request.match_info["file_id"]
        path = self.pdf_files.get(file_id)
        
        self.stats["requests_total"] += 1
        
        if not path or not os.path.isfile(path):
            self.stats["errors"] += 1
            return web.json_response({"error": "PDF not found"}, status=404)

        try:
            # PDFページ数取得
            page_count = await asyncio.get_running_loop().run_in_executor(
                None, get_pdf_page_count, path
            )
            
            # ファイル情報
            stat = os.stat(path)
            
            info = {
                "file_id": file_id,
                "page_count": page_count,
                "file_size": stat.st_size,
                "modified_time": stat.st_mtime,
                "available_formats": SUPPORTED_FORMATS,
                "default_width": DEFAULT_IMAGE_WIDTH,
                "supported_dprs": [1.0, 1.5, 2.0, 3.0]
            }
            
            return web.json_response(info)
            
        except Exception as e:
            self.stats["errors"] += 1
            logger.error(f"[V4-Server] PDF info error {file_id}: {e}")
            return web.json_response({"error": str(e)}, status=500)

    async def _serve_page_image(self, request: web.Request):
        """ページ画像配信 (メインエンドポイント)"""
        file_id = request.match_info["file_id"]
        page_str = request.match_info["page"]
        
        self.stats["requests_total"] += 1
        self.stats["images_served"] += 1
        
        try:
            page_index = int(page_str)
            if page_index < 0:
                raise ValueError("Page index must be >= 0")
        except ValueError as e:
            self.stats["errors"] += 1
            return web.json_response({"error": f"Invalid page index: {e}"}, status=400)

        # PDFパス確認
        path = self.pdf_files.get(file_id)
        if not path or not os.path.isfile(path):
            self.stats["errors"] += 1
            return web.json_response({"error": "PDF not found"}, status=404)

        # クエリパラメータ解析
        try:
            width = int(request.query.get("w", str(DEFAULT_IMAGE_WIDTH)))
            dpr = float(request.query.get("dpr", str(DEFAULT_DPR)))
            format_type = request.query.get("fmt", DEFAULT_FORMAT).lower()
            quality = int(request.query.get("q", "85"))  # 品質 (JPEG/WebP用)
            
            # パラメータ検証
            if width <= 0 or width > 4000:
                width = DEFAULT_IMAGE_WIDTH
            if dpr <= 0 or dpr > 5.0:
                dpr = DEFAULT_DPR
            if format_type not in SUPPORTED_FORMATS:
                format_type = DEFAULT_FORMAT
            if quality < 10 or quality > 100:
                quality = 85
                
        except ValueError:
            width = DEFAULT_IMAGE_WIDTH
            dpr = DEFAULT_DPR
            format_type = DEFAULT_FORMAT
            quality = 85

        # ETag生成 (キャッシュ制御)
        etag_data = f"{file_id}:{page_index}:{width}:{dpr}:{format_type}:{os.path.getmtime(path)}"
        etag = f'"{hash(etag_data) & 0x7FFFFFFF:08x}"'
        
        # クライアントETag確認
        client_etag = request.headers.get("If-None-Match")
        if client_etag == etag:
            self.stats["cache_hits"] += 1
            return web.Response(status=304)  # Not Modified

        # 画像レンダリング
        try:
            image_data = await render_page_image_async(
                path, page_index, width, dpr, format_type, use_cache=True
            )
            
            # Content-Type決定
            content_type_map = {
                "png": "image/png",
                "webp": "image/webp", 
                "jpeg": "image/jpeg"
            }
            content_type = content_type_map.get(format_type, "image/png")
            
            # レスポンス生成
            headers = {
                "Content-Type": content_type,
                "ETag": etag,
                "Cache-Control": "private, max-age=600",  # 10分キャッシュ
                "X-Page-Index": str(page_index),
                "X-Image-Width": str(width),
                "X-Image-DPR": str(dpr),
                "X-Render-Format": format_type
            }
            
            return web.Response(body=image_data, headers=headers)
            
        except Exception as e:
            self.stats["errors"] += 1
            logger.error(f"[V4-Server] Image render error {file_id}:{page_index}: {e}")
            return web.json_response({"error": f"Render error: {e}"}, status=500)

    async def _handle_prefetch(self, request: web.Request):
        """先読みリクエスト処理"""
        file_id = request.match_info["file_id"]
        path = self.pdf_files.get(file_id)
        
        if not path or not os.path.isfile(path):
            return web.json_response({"error": "PDF not found"}, status=404)

        try:
            data = await request.json()
            current_page = data.get("current_page", 0)
            width = data.get("width", DEFAULT_IMAGE_WIDTH) 
            dpr = data.get("dpr", DEFAULT_DPR)
            range_size = data.get("range", 2)
            
            # バックグラウンド先読み実行
            await asyncio.get_running_loop().run_in_executor(
                None, prefetch_pages, path, current_page, width, dpr, range_size
            )
            
            return web.json_response({"status": "prefetch_started", "current_page": current_page})
            
        except Exception as e:
            logger.error(f"[V4-Server] Prefetch error {file_id}: {e}")
            return web.json_response({"error": str(e)}, status=500)

    async def start(self):
        """サーバー開始"""
        try:
            logger.info(f"[V4-Server] Starting on {self.host}:{self.port}")
            
            self.runner = web.AppRunner(self.app)
            await self.runner.setup()
            
            self.site = web.TCPSite(self.runner, self.host, self.port)
            await self.site.start()
            
            # 実際のポート番号取得
            sockets = list(self.site._server.sockets)  # type: ignore[attr-defined]
            if sockets:
                self.actual_port = sockets[0].getsockname()[1]
            
            if self.actual_port is None:
                raise RuntimeError("Failed to get actual port number")
            
            self._loop = asyncio.get_running_loop()
            
            logger.info(f"[V4-Server] Started on {self.host}:{self.actual_port} (public: {self.public_host})")
            
        except Exception as e:
            logger.error(f"[V4-Server] Start error: {e}")
            raise

    async def stop(self):
        """サーバー停止"""
        try:
            logger.info("[V4-Server] Stopping...")
            
            if self.site:
                await self.site.stop()
                
            if self.runner:
                await self.runner.cleanup()
                
            # 一時ファイル削除
            self._cleanup_temp_files()
            
            # レンダラーキャッシュクリア
            clear_document_cache()
            
            logger.info("[V4-Server] Stopped")
            
        except Exception as e:
            logger.error(f"[V4-Server] Stop error: {e}")

    def _cleanup_temp_files(self):
        """一時ファイル削除"""
        import shutil
        try:
            if os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
                logger.info(f"[V4-Server] Cleaned temp dir: {self.temp_dir}")
        except Exception as e:
            logger.warning(f"[V4-Server] Temp cleanup error: {e}")

    async def register_pdf_async(self, file_id: str, pdf_data: bytes) -> str:
        """PDF登録（非同期版・スレッド安全）"""
        if self.actual_port is None or self._loop is None:
            raise RuntimeError("Server not started")

        async def _register():
            # 一時ファイル作成
            temp_path = os.path.join(self.temp_dir, f"{file_id}.pdf")
            
            # ファイル書き込み (別スレッド)
            await asyncio.get_running_loop().run_in_executor(
                None, lambda: self._write_temp_file(temp_path, pdf_data)
            )
            
            # 登録
            self.pdf_files[file_id] = temp_path
            
            # URL生成
            pdf_url = f"http://{self.public_host}:{self.actual_port}/pdf/{file_id}"
            
            logger.info(f"[V4-Server] PDF registered: {file_id} -> {pdf_url} ({len(pdf_data)} bytes)")
            return pdf_url

        if self._loop == asyncio.get_running_loop():
            # 同じループ内
            return await _register()
        else:
            # 異なるスレッドから呼び出し
            return await asyncio.run_coroutine_threadsafe(_register(), self._loop).result(timeout=10)

    def register_pdf_sync(self, file_id: str, pdf_data: bytes) -> str:
        """PDF登録（同期版）"""
        if self.actual_port is None or self._loop is None:
            raise RuntimeError("Server not started")

        async def _register():
            return await self.register_pdf_async(file_id, pdf_data)

        future = asyncio.run_coroutine_threadsafe(_register(), self._loop)
        return future.result(timeout=10)

    def _write_temp_file(self, path: str, data: bytes):
        """一時ファイル書き込み（同期処理）"""
        with open(path, "wb") as f:
            f.write(data)

    async def unregister_pdf_async(self, file_id: str):
        """PDF登録解除（非同期版）"""
        if self._loop is None:
            return

        async def _unregister():
            temp_path = self.pdf_files.pop(file_id, None)
            if temp_path and os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                    logger.info(f"[V4-Server] PDF unregistered: {file_id}")
                except Exception as e:
                    logger.warning(f"[V4-Server] Unregister error {file_id}: {e}")

        if self._loop == asyncio.get_running_loop():
            await _unregister()
        else:
            asyncio.run_coroutine_threadsafe(_unregister(), self._loop)

    def unregister_pdf_sync(self, file_id: str):
        """PDF登録解除（同期版）"""
        if self._loop is None:
            return

        async def _unregister():
            await self.unregister_pdf_async(file_id)

        asyncio.run_coroutine_threadsafe(_unregister(), self._loop)

    def get_pdf_url(self, file_id: str) -> Optional[str]:
        """PDF URL取得"""
        if file_id in self.pdf_files and self.actual_port:
            return f"http://{self.public_host}:{self.actual_port}/pdf/{file_id}"
        return None

    def get_image_url(self, file_id: str, page_index: int, **params) -> Optional[str]:
        """画像URL取得"""
        if file_id not in self.pdf_files or not self.actual_port:
            return None
        
        base_url = f"http://{self.public_host}:{self.actual_port}/img/{file_id}/{page_index}"
        
        # クエリパラメータ追加
        query_parts = []
        if "width" in params or "w" in params:
            width = params.get("width", params.get("w", DEFAULT_IMAGE_WIDTH))
            query_parts.append(f"w={width}")
        if "dpr" in params:
            query_parts.append(f"dpr={params['dpr']}")
        if "format" in params or "fmt" in params:
            fmt = params.get("format", params.get("fmt"))
            query_parts.append(f"fmt={fmt}")
        
        if query_parts:
            return f"{base_url}?{'&'.join(query_parts)}"
        return base_url

    def get_info_url(self, file_id: str) -> Optional[str]:
        """PDF情報URL取得"""
        if file_id in self.pdf_files and self.actual_port:
            return f"http://{self.public_host}:{self.actual_port}/info/{file_id}"
        return None


# ---------------------------
# V4サーバーマネージャー (シングルトン)
# ---------------------------
class PDFStreamManagerV4:
    """V4画像変換サーバーマネージャー（バックグラウンドスレッド管理）"""

    _instance: Optional[PDFStreamServerV4] = None
    _loop: Optional[asyncio.AbstractEventLoop] = None
    _thread: Optional[threading.Thread] = None
    _ready: threading.Event = threading.Event()

    @classmethod
    def _thread_main(cls, host: str, port: int, public_host: Optional[str]):
        """バックグラウンドスレッド メイン処理"""
        loop = asyncio.new_event_loop()
        cls._loop = loop
        asyncio.set_event_loop(loop)

        server = PDFStreamServerV4(host=host, port=port, public_host=public_host)

        async def _boot():
            await server.start()
            cls._instance = server
            cls._ready.set()

        # 起動
        loop.create_task(_boot())
        
        try:
            loop.run_forever()
        except KeyboardInterrupt:
            logger.info("[V4-Manager] Interrupted")
        finally:
            # 停止処理
            try:
                if cls._instance:
                    loop.run_until_complete(cls._instance.stop())
            except Exception as e:
                logger.error(f"[V4-Manager] Stop error: {e}")
            finally:
                loop.close()
                cls._loop = None
                cls._instance = None
                cls._ready.clear()

    @classmethod
    def start_background(
        cls, 
        host: str = DEFAULT_BIND_HOST, 
        port: int = DEFAULT_PORT, 
        public_host: Optional[str] = None
    ) -> PDFStreamServerV4:
        """バックグラウンド起動"""
        if cls._instance is not None:
            return cls._instance

        cls._ready.clear()
        
        cls._thread = threading.Thread(
            target=cls._thread_main,
            args=(host, port, public_host),
            name="PDFStreamServerV4Thread",
            daemon=True
        )
        cls._thread.start()

        # 起動完了待ち
        if not cls._ready.wait(timeout=15):
            raise RuntimeError("V4 PDF Stream Server startup timeout")

        assert cls._instance is not None
        return cls._instance

    @classmethod
    def get_instance_sync(
        cls,
        host: str = DEFAULT_BIND_HOST,
        port: int = DEFAULT_PORT, 
        public_host: Optional[str] = None
    ) -> PDFStreamServerV4:
        """同期取得"""
        return cls.start_background(host, port, public_host)

    @classmethod
    def stop_sync(cls):
        """同期停止"""
        if cls._loop:
            cls._loop.call_soon_threadsafe(cls._loop.stop)
        if cls._thread:
            cls._thread.join(timeout=5)
        cls._thread = None


# ---------------------------
# 便利関数
# ---------------------------
async def serve_pdf_from_bytes_v4(pdf_data: bytes, file_id: Optional[str] = None) -> Tuple[str, PDFStreamServerV4]:
    """PDFデータから配信URL作成 (V4版)"""
    import uuid
    
    if file_id is None:
        file_id = str(uuid.uuid4())

    server = PDFStreamManagerV4.get_instance_sync()
    pdf_url = server.register_pdf_sync(file_id, pdf_data)
    
    return pdf_url, server

def create_v4_server(host: str = DEFAULT_BIND_HOST, port: int = DEFAULT_PORT, public_host: Optional[str] = None) -> PDFStreamServerV4:
    """V4サーバー作成（テスト用）"""
    return PDFStreamServerV4(host, port, public_host)


# スタンドアロンテスト
if __name__ == "__main__":
    import sys
    import time
    
    async def test_server():
        """サーバーテスト"""
        server = PDFStreamServerV4()
        await server.start()
        
        print(f"V4 Test server started on http://{server.host}:{server.actual_port}")
        
        # ダミーPDF生成
        dummy_pdf = b"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj  
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>
endobj
%%EOF"""
        
        # PDF登録
        pdf_url = await server.register_pdf_async("test", dummy_pdf)
        print(f"Test PDF URL: {pdf_url}")
        
        # 画像URL
        image_url = server.get_image_url("test", 0, width=800, dpr=1.0, fmt="png")
        print(f"Test Image URL: {image_url}")
        
        # 情報URL
        info_url = server.get_info_url("test")
        print(f"Test Info URL: {info_url}")
        
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            print("\nShutting down...")
            await server.stop()

    if len(sys.argv) > 1 and sys.argv[1] == "test":
        asyncio.run(test_server())
    else:
        # バックグラウンド起動
        server = PDFStreamManagerV4.get_instance_sync()
        print(f"V4 Background server: http://{server.host}:{server.actual_port}")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nShutting down...")
            PDFStreamManagerV4.stop_sync()
