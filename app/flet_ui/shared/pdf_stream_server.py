#!/usr/bin/env python3
"""
大容量PDF対応ストリーミングサーバ
HTTPレンジリクエスト対応でPDFを分割配信
"""

import os
import re
import io
import threading
import tempfile
import time
from typing import Dict, Optional, Tuple
from aiohttp import web
import aiohttp
from pathlib import Path
import asyncio
import logging

logger = logging.getLogger(__name__)


class PDFStreamServer:
    """PDF用HTTPストリーミングサーバ（Range要求対応）"""
    
    def __init__(self, host: str = "127.0.0.1", port: int = 0):
        self.host = host
        self.port = port
        self.actual_port = None
        self.app = web.Application()
        self.runner = None
        self.site = None
        self.temp_dir = tempfile.mkdtemp(prefix="pdf_stream_")
        self.pdf_files: Dict[str, str] = {}  # file_id -> temp_path のマッピング
        self._setup_routes()
        
    def _setup_routes(self):
        """ルート設定"""
        self.app.router.add_get("/pdf/{file_id}", self._serve_pdf)
        self.app.router.add_get("/health", self._health_check)
        
    async def _health_check(self, request):
        """ヘルスチェック用エンドポイント"""
        return web.json_response({"status": "ok", "port": self.actual_port})
        
    async def _serve_pdf(self, request):
        """PDF配信（Range要求対応）"""
        file_id = request.match_info["file_id"]
        
        if file_id not in self.pdf_files:
            return web.Response(status=404, text="PDF not found")
            
        file_path = self.pdf_files[file_id]
        if not os.path.isfile(file_path):
            return web.Response(status=404, text="PDF file not found")
            
        try:
            file_size = os.path.getsize(file_path)
            range_header = request.headers.get("Range")
            
            # Range要求の処理
            if range_header:
                return await self._handle_range_request(file_path, file_size, range_header, request)
            else:
                return await self._handle_full_request(file_path, file_size, request)
                
        except Exception as e:
            logger.error(f"PDF配信エラー: {e}")
            return web.Response(status=500, text=f"Server error: {e}")
    
    async def _handle_range_request(self, file_path: str, file_size: int, range_header: str, request):
        """Range要求の処理"""
        # Range: bytes=START-END
        match = re.match(r"bytes=(\d+)-(\d+)?", range_header)
        if not match:
            # 不正なRangeヘッダーの場合は全体を返す
            return await self._handle_full_request(file_path, file_size, request)
            
        start = int(match.group(1))
        end = file_size - 1 if match.group(2) is None else int(match.group(2))
        
        # 範囲チェック
        if start >= file_size:
            return web.Response(
                status=416,  # Range Not Satisfiable
                headers={"Content-Range": f"bytes */{file_size}"}
            )
            
        if end >= file_size:
            end = file_size - 1
            
        content_length = end - start + 1
        
        response = web.StreamResponse(
            status=206,  # Partial Content
            headers={
                "Content-Type": "application/pdf",
                "Accept-Ranges": "bytes",
                "Content-Range": f"bytes {start}-{end}/{file_size}",
                "Content-Length": str(content_length),
                "Cache-Control": "no-cache"
            }
        )
        
        await response.prepare(request)
        
        # ファイルの指定範囲を読み込み
        with open(file_path, "rb") as f:
            f.seek(start)
            remaining = content_length
            chunk_size = min(64 * 1024, remaining)  # 64KB chunks
            
            while remaining > 0:
                data = f.read(min(chunk_size, remaining))
                if not data:
                    break
                await response.write(data)
                remaining -= len(data)
                
        await response.write_eof()
        return response
        
    async def _handle_full_request(self, file_path: str, file_size: int, request):
        """全体要求の処理"""
        response = web.StreamResponse(
            headers={
                "Content-Type": "application/pdf",
                "Accept-Ranges": "bytes",
                "Content-Length": str(file_size),
                "Cache-Control": "no-cache"
            }
        )
        
        await response.prepare(request)
        
        with open(file_path, "rb") as f:
            while True:
                data = f.read(64 * 1024)  # 64KB chunks
                if not data:
                    break
                await response.write(data)
                
        await response.write_eof()
        return response
    
    async def start(self):
        """サーバ開始"""
        try:
            logger.info(f"[DEBUG] サーバ開始処理開始: host={self.host}, port={self.port}")
            
            self.runner = web.AppRunner(self.app)
            await self.runner.setup()
            logger.info(f"[DEBUG] AppRunner.setup() 完了")
            
            self.site = web.TCPSite(self.runner, self.host, self.port)
            await self.site.start()
            logger.info(f"[DEBUG] TCPSite.start() 完了")
            
            # 実際のポート番号を取得
            sockets = list(self.site._server.sockets)
            logger.info(f"[DEBUG] ソケット数: {len(sockets)}")
            
            for socket in sockets:
                port_info = socket.getsockname()
                self.actual_port = port_info[1]
                logger.info(f"[DEBUG] ポート取得: {port_info} -> actual_port={self.actual_port}")
                break
            
            if self.actual_port is None:
                raise RuntimeError("ポート番号の取得に失敗しました")
                
            logger.info(f"PDF Stream Server started on {self.host}:{self.actual_port}")
            
        except Exception as e:
            logger.error(f"サーバ開始エラー: {e}")
            import traceback
            logger.error(f"スタックトレース: {traceback.format_exc()}")
            raise
            
    async def stop(self):
        """サーバ停止"""
        try:
            if self.site:
                await self.site.stop()
            if self.runner:
                await self.runner.cleanup()
                
            # 一時ファイル削除
            self._cleanup_temp_files()
            
        except Exception as e:
            logger.error(f"サーバ停止エラー: {e}")
            
    def _cleanup_temp_files(self):
        """一時ファイルの削除"""
        try:
            import shutil
            if os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
        except Exception as e:
            logger.error(f"一時ファイル削除エラー: {e}")
            
    def register_pdf(self, file_id: str, pdf_data: bytes) -> str:
        """PDFデータを一時ファイルとして登録し、URL を返す"""
        try:
            logger.info(f"[DEBUG] register_pdf開始: file_id={file_id}, actual_port={self.actual_port}")
            
            # 一時ファイルに保存
            temp_path = os.path.join(self.temp_dir, f"{file_id}.pdf")
            with open(temp_path, "wb") as f:
                f.write(pdf_data)
                
            self.pdf_files[file_id] = temp_path
            
            # アクセス用URLを生成
            if self.actual_port is None:
                logger.error(f"[DEBUG] actual_portがNoneです！ host={self.host}")
                raise RuntimeError("サーバが適切に開始されていません（actual_port=None）")
            
            url = f"http://{self.host}:{self.actual_port}/pdf/{file_id}"
            
            logger.info(f"PDF registered: {file_id} -> {url} ({len(pdf_data)} bytes)")
            return url
            
        except Exception as e:
            logger.error(f"PDF登録エラー: {e}")
            raise
            
    def unregister_pdf(self, file_id: str):
        """PDFファイルの登録解除"""
        try:
            if file_id in self.pdf_files:
                temp_path = self.pdf_files[file_id]
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                del self.pdf_files[file_id]
                logger.info(f"PDF unregistered: {file_id}")
        except Exception as e:
            logger.error(f"PDF登録解除エラー: {e}")
            
    def get_pdf_url(self, file_id: str) -> Optional[str]:
        """PDFのURL取得"""
        if file_id in self.pdf_files and self.actual_port:
            return f"http://{self.host}:{self.actual_port}/pdf/{file_id}"
        return None


class PDFStreamManager:
    """PDFストリームサーバ管理クラス（シングルトン）"""
    
    _instance = None
    _server = None
    _loop = None
    _thread = None
    
    @classmethod
    async def get_instance(cls) -> PDFStreamServer:
        """サーバインスタンス取得（必要に応じて開始）"""
        logger.info(f"[DEBUG] get_instance呼出: _instance={cls._instance is not None}")
        
        if cls._instance is None:
            logger.info(f"[DEBUG] 新しいPDFStreamServerインスタンス作成")
            cls._instance = PDFStreamServer()
            logger.info(f"[DEBUG] PDFStreamServer.start()開始")
            await cls._instance.start()
            logger.info(f"[DEBUG] PDFStreamServer.start()完了 - actual_port={cls._instance.actual_port}")
            
        return cls._instance
        
    @classmethod
    def get_instance_sync(cls) -> PDFStreamServer:
        """同期版インスタンス取得"""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # 非同期コンテキスト内の場合は待機して実際のインスタンスを返す
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(lambda: asyncio.run(cls.get_instance()))
                    return future.result(timeout=10)
            else:
                return loop.run_until_complete(cls.get_instance())
        except RuntimeError:
            # イベントループがない場合
            return asyncio.run(cls.get_instance())
                
    @classmethod
    async def cleanup(cls):
        """リソース整理"""
        if cls._instance:
            await cls._instance.stop()
            cls._instance = None


def create_pdf_stream_server(host: str = "127.0.0.1", port: int = 0) -> PDFStreamServer:
    """PDFストリームサーバ作成（ファクトリー関数）"""
    return PDFStreamServer(host, port)


# 便利関数
async def serve_pdf_from_bytes(pdf_data: bytes, file_id: str = None) -> Tuple[str, PDFStreamServer]:
    """バイトデータからPDF配信URL作成"""
    if file_id is None:
        import uuid
        file_id = str(uuid.uuid4())
        
    server = await PDFStreamManager.get_instance()
    pdf_url = server.register_pdf(file_id, pdf_data)
    
    return pdf_url, server


if __name__ == "__main__":
    # テスト用スタンドアロン実行
    import sys
    
    async def test_server():
        server = PDFStreamServer()
        await server.start()
        print(f"Test server started on {server.host}:{server.actual_port}")
        
        # テスト用ダミーPDF
        dummy_pdf = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
        url = server.register_pdf("test", dummy_pdf)
        print(f"Test URL: {url}")
        
        # サーバを保持
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            await server.stop()
            
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        asyncio.run(test_server())
