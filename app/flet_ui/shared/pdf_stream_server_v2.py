#!/usr/bin/env python3
"""
大容量PDF対応ストリーミングサーバ（V2改訂版）
- 常駐イベントループを持つバックグラウンドスレッドでサーバを維持
- web.FileResponse を用いて Range/HEAD/条件付き応答を aiohttp に委譲
- CORS 対応（GET/HEAD/OPTIONS）
- バインド用ホスト（PDF_STREAM_BIND）とURL公開用ホスト（PDF_STREAM_PUBLIC）を分離
"""

import os
import tempfile
import logging
import asyncio
import threading
from pathlib import Path
from typing import Dict, Optional, Tuple

from aiohttp import web

logger = logging.getLogger(__name__)

# 環境変数（必要に応じて変更）
DEFAULT_BIND_HOST = os.getenv("PDF_STREAM_BIND", "0.0.0.0")  # 修正: コンテナ対応
DEFAULT_PUBLIC_HOST = os.getenv("PDF_STREAM_PUBLIC", "127.0.0.1")  # 修正: 外部アクセス用
DEFAULT_PORT = int(os.getenv("PDF_STREAM_PORT", "0"))  # 0=動的


# ---------------------------
# CORS ミドルウェア
# ---------------------------
@web.middleware
async def cors_middleware(request: web.Request, handler):
    if request.method == "OPTIONS":
        # プリフライトに即応答
        resp = web.Response(status=204)
    else:
        resp = await handler(request)

    # 必要最小限。必要なら許可元を絞る
    resp.headers["Access-Control-Allow-Origin"] = "*"
    resp.headers["Access-Control-Allow-Methods"] = "GET, HEAD, OPTIONS"
    resp.headers["Access-Control-Allow-Headers"] = "*"
    # fetch でヘッダを参照できるように
    resp.headers["Access-Control-Expose-Headers"] = (
        "Accept-Ranges, Content-Range, Content-Length, Content-Type"
    )
    return resp


class PDFStreamServerV2:
    """PDF用HTTPストリーミングサーバ（Range等はFileResponseに委譲）"""

    def __init__(self, host: str = DEFAULT_BIND_HOST, port: int = DEFAULT_PORT, public_host: Optional[str] = None):
        self.host = host
        self.public_host = public_host or DEFAULT_PUBLIC_HOST
        self.port = port
        self.actual_port: Optional[int] = None

        self.app = web.Application(middlewares=[cors_middleware])
        self.runner: Optional[web.AppRunner] = None
        self.site: Optional[web.TCPSite] = None

        self.temp_dir = tempfile.mkdtemp(prefix="pdf_stream_v2_")
        self.pdf_files: Dict[str, str] = {}  # file_id -> temp_path のマッピング

        self._setup_routes()

    def _setup_routes(self):
        self.app.router.add_get("/pdf/{file_id}", self._serve_pdf)  # GETルートでHEADも自動対応
        self.app.router.add_route("OPTIONS", "/pdf/{file_id}", self._options_pdf)  # CORSプリフライト
        self.app.router.add_get("/health", self._health_check)

    async def _options_pdf(self, request: web.Request):
        return web.Response(status=204)

    async def _health_check(self, request: web.Request):
        return web.json_response({"status": "ok", "port": self.actual_port, "version": "v2"})

    async def _serve_pdf(self, request: web.Request):
        """PDF配信（FileResponseに任せる）"""
        file_id = request.match_info["file_id"]

        path = self.pdf_files.get(file_id)
        if not path or not os.path.isfile(path):
            return web.Response(status=404, text="PDF not found")

        # FileResponse は Range/HEAD/If-Modified-Since 等を処理
        headers = {
            "Content-Type": "application/pdf",
            "Accept-Ranges": "bytes",
            "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
            "X-Content-Type-Options": "nosniff",
        }
        logger.info(f"[V2-DEBUG] PDF配信: {file_id} -> {path}")
        return web.FileResponse(path=path, headers=headers, chunk_size=64 * 1024)

    async def start(self):
        """サーバ開始（呼び出し側のイベントループ上で）"""
        try:
            logger.info(f"[V2-DEBUG] サーバ開始: host={self.host}, port={self.port}, public={self.public_host}")
            self.runner = web.AppRunner(self.app)
            await self.runner.setup()
            self.site = web.TCPSite(self.runner, self.host, self.port)
            await self.site.start()

            # 実際のポート番号
            assert self.site is not None
            sockets = list(self.site._server.sockets)  # type: ignore[attr-defined]
            if sockets:
                self.actual_port = sockets[0].getsockname()[1]
            if self.actual_port is None:
                raise RuntimeError("ポート番号の取得に失敗しました")

            logger.info(f"PDF Stream Server V2 started on {self.host}:{self.actual_port} (public host: {self.public_host})")

        except Exception as e:
            logger.exception(f"[V2-ERROR] サーバ開始エラー: {e}")
            raise

    async def stop(self):
        """サーバ停止"""
        try:
            logger.info("[V2-DEBUG] サーバ停止開始")
            if self.site:
                await self.site.stop()
            if self.runner:
                await self.runner.cleanup()
            self._cleanup_temp_files()
            logger.info("[V2-DEBUG] サーバ停止完了")
        except Exception:
            logger.exception("[V2-ERROR] サーバ停止エラー")

    def _cleanup_temp_files(self):
        """一時ファイルの削除"""
        import shutil
        try:
            if os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
                logger.info(f"[V2-DEBUG] 一時ディレクトリ削除: {self.temp_dir}")
        except Exception:
            logger.exception("[V2-ERROR] 一時ファイル削除エラー")

    def register_pdf(self, file_id: str, pdf_data: bytes) -> str:
        """PDFデータを一時ファイルとして登録し、URL を返す"""
        if self.actual_port is None:
            raise RuntimeError("サーバが開始されていません（actual_port=None）")

        temp_path = os.path.join(self.temp_dir, f"{file_id}.pdf")
        with open(temp_path, "wb") as f:
            f.write(pdf_data)

        self.pdf_files[file_id] = temp_path
        url = f"http://{self.public_host}:{self.actual_port}/pdf/{file_id}"
        logger.info(f"[V2-DEBUG] PDF registered: {file_id} -> {url} ({len(pdf_data)} bytes)")
        return url

    def unregister_pdf(self, file_id: str):
        """PDFファイルの登録解除"""
        try:
            path = self.pdf_files.pop(file_id, None)
            if path and os.path.exists(path):
                os.remove(path)
            logger.info(f"[V2-DEBUG] PDF unregistered: {file_id}")
        except Exception:
            logger.exception("[V2-ERROR] PDF登録解除エラー")

    def get_pdf_url(self, file_id: str) -> Optional[str]:
        """PDFのURL取得"""
        if file_id in self.pdf_files and self.actual_port:
            return f"http://{self.public_host}:{self.actual_port}/pdf/{file_id}"
        return None


class PDFStreamManagerV2:
    """
    PDFストリームサーバ管理（バックグラウンドスレッドで常駐ループ）
    - get_instance()/get_instance_sync() は「必ず常駐サーバ」への参照を返す
    """

    _instance: Optional[PDFStreamServerV2] = None
    _loop: Optional[asyncio.AbstractEventLoop] = None
    _thread: Optional[threading.Thread] = None
    _ready: threading.Event = threading.Event()

    @classmethod
    def _thread_main(cls, host: str, port: int, public_host: Optional[str]):
        """
        スレッド内でイベントループを作り、サーバ起動後 run_forever で維持。
        ループ停止時にサーバをクリーンアップ。
        """
        logger.info(f"[V2-THREAD] バックグラウンドスレッド開始")
        loop = asyncio.new_event_loop()
        cls._loop = loop
        asyncio.set_event_loop(loop)

        server = PDFStreamServerV2(host=host, port=port, public_host=public_host)

        async def _boot():
            logger.info(f"[V2-THREAD] サーバ起動処理開始")
            await server.start()
            cls._instance = server
            cls._ready.set()
            logger.info(f"[V2-THREAD] サーバ起動完了、常駐開始")

        # 起動
        loop.create_task(_boot())
        try:
            loop.run_forever()
            logger.info(f"[V2-THREAD] イベントループ終了")
        finally:
            # 停止時にクリーンアップ
            try:
                if server:
                    loop.run_until_complete(server.stop())
            except Exception:
                logger.exception("[V2-THREAD] stop during loop shutdown")
            finally:
                loop.close()
                cls._loop = None
                cls._instance = None
                cls._ready.clear()
                logger.info(f"[V2-THREAD] バックグラウンドスレッド完全終了")

    @classmethod
    def start_background(cls, host: str = DEFAULT_BIND_HOST, port: int = DEFAULT_PORT, public_host: Optional[str] = None) -> PDFStreamServerV2:
        """バックグラウンド起動（同期）"""
        if cls._instance is not None:
            logger.info("[V2-MANAGER] 既存インスタンス返却")
            return cls._instance

        logger.info(f"[V2-MANAGER] バックグラウンドサーバ起動開始")
        cls._ready.clear()  # 明示的にクリア
        
        cls._thread = threading.Thread(
            target=cls._thread_main,
            args=(host, port, public_host),
            name="PDFStreamServerV2Thread",
            daemon=True,
        )
        cls._thread.start()

        # 起動完了を待機（タイムアウトは適宜）
        logger.info(f"[V2-MANAGER] サーバ起動完了待機中...")
        if not cls._ready.wait(timeout=15):  # 修正: タイムアウト延長
            raise RuntimeError("PDF Stream Server V2 の起動待ちでタイムアウトしました")

        assert cls._instance is not None
        logger.info(f"[V2-MANAGER] バックグラウンドサーバ起動完了")
        return cls._instance

    @classmethod
    async def get_instance(cls, host: str = DEFAULT_BIND_HOST, port: int = DEFAULT_PORT, public_host: Optional[str] = None) -> PDFStreamServerV2:
        """非同期APIだが内部でバックグラウンドを起動し、即座にインスタンスを返す"""
        return cls.start_background(host=host, port=port, public_host=public_host)

    @classmethod
    def get_instance_sync(cls, host: str = DEFAULT_BIND_HOST, port: int = DEFAULT_PORT, public_host: Optional[str] = None) -> PDFStreamServerV2:
        """同期API（UI側やCLI等から呼び出しやすい）"""
        return cls.start_background(host=host, port=port, public_host=public_host)

    @classmethod
    async def cleanup(cls):
        """サーバ停止（非同期）"""
        cls.stop_sync()

    @classmethod
    def stop_sync(cls):
        """サーバ停止（同期）"""
        logger.info("[V2-MANAGER] サーバ停止処理開始")
        loop = cls._loop
        if loop is None:
            logger.info("[V2-MANAGER] 停止対象なし")
            return
        # run_forever を止める
        loop.call_soon_threadsafe(loop.stop)
        if cls._thread:
            cls._thread.join(timeout=5)
        cls._thread = None
        logger.info("[V2-MANAGER] サーバ停止処理完了")


def create_pdf_stream_server_v2(host: str = DEFAULT_BIND_HOST, port: int = DEFAULT_PORT, public_host: Optional[str] = None) -> PDFStreamServerV2:
    """PDFストリームサーバV2作成（テストや特殊用途向け）"""
    return PDFStreamServerV2(host, port, public_host)


# 便利関数
async def serve_pdf_from_bytes_v2(pdf_data: bytes, file_id: Optional[str] = None) -> Tuple[str, PDFStreamServerV2]:
    """
    バイトデータからPDF配信URL作成（V2版）
    - 常駐サーバを（まだなら）起動
    - ファイル登録してURLを返す
    """
    import uuid
    if file_id is None:
        file_id = str(uuid.uuid4())

    server = await PDFStreamManagerV2.get_instance()
    pdf_url = server.register_pdf(file_id, pdf_data)
    return pdf_url, server


if __name__ == "__main__":
    # テスト用スタンドアロン実行
    import sys

    async def test_server():
        # バックグラウンドでなく、単発起動で試す
        logger.info("[TEST] 単発テストサーバ起動")
        server = PDFStreamServerV2()
        await server.start()
        print(f"Test server started on {server.host}:{server.actual_port}")

        dummy_pdf = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n%%EOF\n"
        url = server.register_pdf("test", dummy_pdf)
        print(f"Test URL: {url}")

        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            await server.stop()

    if len(sys.argv) > 1 and sys.argv[1] == "test":
        asyncio.run(test_server())
    else:
        # 同期APIでバックグラウンド起動 → 終了待ち
        srv = PDFStreamManagerV2.get_instance_sync()
        print(f"Background server on {srv.host}:{srv.actual_port} (public={srv.public_host})")
        try:
            while True:
                # メインスレッドは待機するだけ
                import time
                time.sleep(1)
        except KeyboardInterrupt:
            PDFStreamManagerV2.stop_sync()
