#!/usr/bin/env python3
"""
🔴 DEPRECATED - V3専用サーバー（非推奨）

⚠️  このファイルは非推奨です。新しい統合サーバーが利用されます：
    app.flet_ui.shared.pdf_stream_server_unified.py

V5統合サーバーの利点:
- V3/V4統合管理
- 自動戦略選択
- 統一エンドポイント

大容量PDF対応ストリーミングサーバ（V3完全版・HTTP統一）
- /pdf/{file_id} : PDF本体（Range/HEAD/条件付は FileResponse に委譲）
- /viewer        : PDF.js ビューアHTMLをHTTPで配信（data:URL不使用）
- CORS 対応（GET/HEAD/OPTIONS）
- bind 用ホスト（PDF_STREAM_BIND）と公開URL用ホスト（PDF_STREAM_PUBLIC）を分離
- register/unregister はイベントループスレッドで直列実行（スレッド安全）

技術改善点：
- スレッド安全性確保: pdf_files辞書操作をループスレッドで直列化
- /viewer エンドポイント追加: WebView data:URL制限の完全回避
- get_viewer_url() 提供: クライアントの利便性向上
- 堅牢なエラーハンドリング: タイムアウト・競合状態対応
"""

import os
import tempfile
import logging
import asyncio
import threading
from typing import Dict, Optional, Tuple

from aiohttp import web

# ----- ログ（最低限） -----
logger = logging.getLogger(__name__)
if not logging.getLogger().hasHandlers():
    logging.basicConfig(level=logging.INFO)

# ----- 環境変数 -----
DEFAULT_BIND_HOST = os.getenv("PDF_STREAM_BIND", "0.0.0.0")      # コンテナ等で待受
DEFAULT_PUBLIC_HOST = os.getenv("PDF_STREAM_PUBLIC", "127.0.0.1") # UIが到達可能なホスト
DEFAULT_PORT = int(os.getenv("PDF_STREAM_PORT", "0"))             # 0=動的割当

# ---------------------------
# CORS ミドルウェア
# ---------------------------
@web.middleware
async def cors_middleware(request: web.Request, handler):
    if request.method == "OPTIONS":
        resp = web.Response(status=204)
    else:
        resp = await handler(request)

    resp.headers["Access-Control-Allow-Origin"] = "*"
    resp.headers["Access-Control-Allow-Methods"] = "GET, HEAD, OPTIONS"
    resp.headers["Access-Control-Allow-Headers"] = "*"
    resp.headers["Access-Control-Expose-Headers"] = (
        "Accept-Ranges, Content-Range, Content-Length, Content-Type"
    )
    return resp


class PDFStreamServerV3:
    """PDF用HTTPストリーミングサーバ（V3版：完全HTTP統一・スレッド安全）"""

    # ---- 簡易PDF.js ビューア（CDN版・レスポンシブ対応） ----
    _VIEWER_HTML = r"""<!doctype html>
<html>
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <title>PDF Viewer</title>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.min.js"></script>
  <style>
    html,body {height:100%;margin:0;font-family:Arial,sans-serif;}
    body {background:#525659;display:flex;flex-direction:column;}
    #toolbar {
      background:#333;color:#fff;padding:8px;
      display:flex;gap:10px;align-items:center;justify-content:center;
      flex-shrink:0;min-height:32px;
    }
    #viewer {
      flex:1;overflow:auto;display:flex;flex-direction:column;
      align-items:center;padding:20px;
    }
    .page {margin:10px 0;background:#fff;box-shadow:0 2px 5px rgba(0,0,0,.3);}
    button {
      background:#4CAF50;color:#fff;border:none;padding:6px 12px;
      border-radius:4px;cursor:pointer;font-size:12px;
    }
    button:hover {background:#45a049;}
    button:disabled {background:#666;cursor:not-allowed;}
    #pageInfo {color:#ccc;margin:0 8px;}
    #zoomLevel {color:#ccc;margin:0 8px;min-width:40px;text-align:center;}
    .separator {color:#666;margin:0 4px;}
    .loading {color:#4CAF50;margin:20px;}
    .error {color:#f88;margin:20px;text-align:center;}
  </style>
</head>
<body>
  <div id="toolbar">
    <button onclick="zoomOut()" title="縮小">−</button>
    <span id="zoomLevel">100%</span>
    <button onclick="zoomIn()" title="拡大">+</button>
    <span class="separator">|</span>
    <button onclick="prevPage()" title="前のページ">◀</button>
    <span id="pageInfo">1 / 1</span>
    <button onclick="nextPage()" title="次のページ">▶</button>
    <span class="separator">|</span>
    <button onclick="fitWidth()" title="幅に合わせる">幅</button>
    <button onclick="fitPage()" title="ページに合わせる">全体</button>
  </div>
  <div id="viewer">
    <div class="loading">PDFを読み込み中...</div>
  </div>
  <script>
    let pdfDoc=null, currentPage=1, scale=1.0, containerWidth=800;
    const viewer=document.getElementById('viewer');
    const pageInfo=document.getElementById('pageInfo');
    const zoomLevel=document.getElementById('zoomLevel');

    function q(name){return new URLSearchParams(location.search).get(name)}
    function updateInfo(){
      if(pdfDoc){
        pageInfo.textContent=`${currentPage} / ${pdfDoc.numPages}`;
        document.querySelector('button[onclick="prevPage()"]').disabled = currentPage <= 1;
        document.querySelector('button[onclick="nextPage()"]').disabled = currentPage >= pdfDoc.numPages;
      }
      zoomLevel.textContent = Math.round(scale*100)+'%';
    }
    function zoomIn(){scale=Math.min(scale*1.25,5.0);render();}
    function zoomOut(){scale=Math.max(scale/1.25,0.1);render();}
    function nextPage(){
      if(pdfDoc&&currentPage<pdfDoc.numPages){
        currentPage++;render();updateInfo();
      }
    }
    function prevPage(){
      if(pdfDoc&&currentPage>1){
        currentPage--;render();updateInfo();
      }
    }
    function fitWidth(){
      if(pdfDoc){
        containerWidth = viewer.clientWidth - 40;
        pdfDoc.getPage(currentPage).then(page => {
          const vp = page.getViewport({scale:1.0});
          scale = containerWidth / vp.width;
          render();
        });
      }
    }
    function fitPage(){
      if(pdfDoc){
        const containerHeight = viewer.clientHeight - 40;
        containerWidth = viewer.clientWidth - 40;
        pdfDoc.getPage(currentPage).then(page => {
          const vp = page.getViewport({scale:1.0});
          const scaleW = containerWidth / vp.width;
          const scaleH = containerHeight / vp.height;
          scale = Math.min(scaleW, scaleH);
          render();
        });
      }
    }

    async function render(){
      if(!pdfDoc) return;
      try {
        const page=await pdfDoc.getPage(currentPage);
        const vp=page.getViewport({scale});
        const canvas=document.createElement('canvas');
        canvas.width=vp.width; 
        canvas.height=vp.height; 
        canvas.className='page';
        
        await page.render({
          canvasContext:canvas.getContext('2d'), 
          viewport:vp
        }).promise;
        
        viewer.innerHTML=''; 
        viewer.appendChild(canvas);
        updateInfo();
      } catch(e) {
        viewer.innerHTML='<div class="error">レンダリングエラー: '+e.message+'</div>';
      }
    }

    async function boot(){
      const file=q('file'); 
      if(!file){
        viewer.innerHTML='<div class="error">ファイルパラメータが指定されていません</div>';
        return;
      }
      try{
        pdfjsLib.GlobalWorkerOptions.workerSrc='https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';
        const task=pdfjsLib.getDocument({
          url:decodeURIComponent(file), 
          cMapUrl:'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/cmaps/', 
          cMapPacked:true
        });
        pdfDoc=await task.promise; 
        currentPage=1; 
        containerWidth = viewer.clientWidth - 40;
        await render();
        fitWidth(); // 初期表示時は幅に合わせる
      }catch(e){
        viewer.innerHTML='<div class="error">PDF読み込みエラー: '+e.message+'</div>';
        console.error('PDF load error:', e);
      }
    }
    
    // キーボードショートカット
    document.addEventListener('keydown', function(e) {
      if (e.target.tagName.toLowerCase() === 'input') return;
      switch(e.key) {
        case 'ArrowLeft': case 'PageUp': prevPage(); e.preventDefault(); break;
        case 'ArrowRight': case 'PageDown': case ' ': nextPage(); e.preventDefault(); break;
        case '+': case '=': zoomIn(); e.preventDefault(); break;
        case '-': zoomOut(); e.preventDefault(); break;
        case '0': fitWidth(); e.preventDefault(); break;
        case '9': fitPage(); e.preventDefault(); break;
      }
    });
    
    // ウィンドウリサイズ対応
    window.addEventListener('resize', function() {
      if (pdfDoc) {
        setTimeout(fitWidth, 100);
      }
    });
    
    boot();
  </script>
</body>
</html>"""

    def __init__(self, host: str = DEFAULT_BIND_HOST, port: int = DEFAULT_PORT, public_host: Optional[str] = None):
        self.host = host
        self.public_host = public_host or DEFAULT_PUBLIC_HOST
        self.port = port
        self.actual_port: Optional[int] = None

        self.app = web.Application(middlewares=[cors_middleware])
        self.runner: Optional[web.AppRunner] = None
        self.site: Optional[web.TCPSite] = None

        self.temp_dir = tempfile.mkdtemp(prefix="pdf_stream_v3_")
        self.pdf_files: Dict[str, str] = {}  # file_id -> temp_path

        # このサーバのイベントループ参照（start() 後に設定）
        self._loop: Optional[asyncio.AbstractEventLoop] = None

        self._setup_routes()

    # ---------- ルート ----------
    def _setup_routes(self):
        self.app.router.add_get("/pdf/{file_id}", self._serve_pdf)              # GET/HEAD
        self.app.router.add_route("OPTIONS", "/pdf/{file_id}", self._options)   # CORS
        self.app.router.add_get("/viewer", self._serve_viewer_html)             # PDF.js viewer
        self.app.router.add_route("OPTIONS", "/viewer", self._options)          # CORS
        self.app.router.add_get("/health", self._health_check)

    async def _options(self, request: web.Request):
        return web.Response(status=204)

    async def _health_check(self, request: web.Request):
        return web.json_response({
            "status": "ok", 
            "port": self.actual_port, 
            "version": "v3",
            "features": ["thread_safe", "viewer_endpoint", "http_unified"]
        })

    async def _serve_viewer_html(self, request: web.Request):
        """PDF.js ビューアHTML配信（data:URL完全回避）"""
        return web.Response(text=self._VIEWER_HTML, content_type="text/html")

    async def _serve_pdf(self, request: web.Request):
        """PDF本体配信（FileResponseでRange/HEAD対応）"""
        file_id = request.match_info["file_id"]
        path = self.pdf_files.get(file_id)
        if not path or not os.path.isfile(path):
            logger.warning(f"[V3] PDF not found: {file_id}")
            return web.Response(status=404, text="PDF not found")

        headers = {
            "Content-Type": "application/pdf",
            "Accept-Ranges": "bytes",
            "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
            "X-Content-Type-Options": "nosniff",
        }
        logger.info(f"[V3] PDF配信: {file_id} -> {path}")
        return web.FileResponse(path=path, headers=headers, chunk_size=64 * 1024)

    # ---------- ライフサイクル ----------
    async def start(self):
        """サーバ起動（イベントループでの実行が必要）"""
        logger.info(f"[V3] サーバ起動開始: bind={self.host}:{self.port}, public={self.public_host}")
        
        try:
            self.runner = web.AppRunner(self.app)
            await self.runner.setup()
            self.site = web.TCPSite(self.runner, self.host, self.port)
            await self.site.start()

            sockets = list(self.site._server.sockets)  # type: ignore[attr-defined]
            if sockets:
                self.actual_port = sockets[0].getsockname()[1]
            if self.actual_port is None:
                raise RuntimeError("ポート番号の取得に失敗しました")

            # この時点のループを保持（register/unregister を直列化するため）
            self._loop = asyncio.get_running_loop()
            logger.info(f"[V3] サーバ起動完了: {self.host}:{self.actual_port} (public: {self.public_host})")
            
        except Exception as e:
            logger.exception(f"[V3] サーバ起動エラー: {e}")
            raise

    async def stop(self):
        """サーバ停止"""
        logger.info("[V3] サーバ停止開始...")
        try:
            if self.site:
                await self.site.stop()
            if self.runner:
                await self.runner.cleanup()
            self._cleanup_temp_files()
            logger.info("[V3] サーバ停止完了")
        except Exception as e:
            logger.exception(f"[V3] サーバ停止エラー: {e}")

    def _cleanup_temp_files(self):
        """一時ファイルクリーンアップ"""
        import shutil
        try:
            if os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
                logger.info(f"[V3] 一時ディレクトリ削除: {self.temp_dir}")
        except Exception:
            logger.exception("[V3] 一時ファイル削除エラー")

    # ---------- 公開API（スレッド安全版） ----------
    def register_pdf(self, file_id: str, pdf_data: bytes) -> str:
        """
        PDF を登録し URL を返す（スレッド安全）
        - 物理ファイル作成と辞書更新はイベントループスレッドで直列実行
        - 呼出スレッドに関係なく安全に動作
        """
        if self.actual_port is None:
            raise RuntimeError("サーバが開始されていません（actual_port=None）")
        if self._loop is None:
            raise RuntimeError("イベントループ未確定：サーバの完全起動を待機してください")

        async def _do_register() -> str:
            # 一時ファイル作成
            temp_path = os.path.join(self.temp_dir, f"{file_id}.pdf")
            
            # ファイル書き込み（非同期実行で I/O ブロッキング回避）
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, lambda: self._write_pdf_file(temp_path, pdf_data))
            
            # 辞書更新（メインループ上で実行、競合なし）
            self.pdf_files[file_id] = temp_path
            
            # URL生成
            url = f"http://{self.public_host}:{self.actual_port}/pdf/{file_id}"
            logger.info(f"[V3] PDF登録完了: {file_id} -> {url} ({len(pdf_data)} bytes)")
            return url

        # 別スレッドからでも安全に実行
        try:
            future = asyncio.run_coroutine_threadsafe(_do_register(), self._loop)
            return future.result(timeout=10)  # 10秒タイムアウト
        except Exception as e:
            logger.error(f"[V3] PDF登録エラー: {e}")
            raise RuntimeError(f"PDF登録に失敗しました: {str(e)}") from e

    def _write_pdf_file(self, temp_path: str, pdf_data: bytes) -> None:
        """PDFファイル書き込み（同期処理）"""
        with open(temp_path, "wb") as f:
            f.write(pdf_data)

    def unregister_pdf(self, file_id: str) -> None:
        """PDF 登録解除（スレッド安全）"""
        if self._loop is None:
            logger.warning(f"[V3] unregister_pdf: イベントループが未設定です ({file_id})")
            return

        async def _do_unregister():
            # 辞書から削除
            path = self.pdf_files.pop(file_id, None)
            
            if path and os.path.exists(path):
                try:
                    # ファイル削除（非同期実行で I/O ブロッキング回避）
                    loop = asyncio.get_running_loop()
                    await loop.run_in_executor(None, lambda: os.remove(path))
                    logger.info(f"[V3] PDF登録解除完了: {file_id} ({path})")
                except Exception as e:
                    logger.error(f"[V3] PDFファイル削除エラー ({file_id}): {e}")
            else:
                logger.warning(f"[V3] PDF登録解除: ファイルが見つかりません ({file_id})")

        try:
            future = asyncio.run_coroutine_threadsafe(_do_unregister(), self._loop)
            future.result(timeout=5)  # 5秒タイムアウト
        except Exception as e:
            logger.error(f"[V3] PDF登録解除エラー ({file_id}): {e}")

    def get_pdf_url(self, file_id: str) -> Optional[str]:
        """PDF直接アクセスURL取得"""
        if file_id in self.pdf_files and self.actual_port:
            return f"http://{self.public_host}:{self.actual_port}/pdf/{file_id}"
        return None

    def get_viewer_url(self, file_url: str) -> str:
        """PDF.js ビューアURL生成（V3版の主要機能）"""
        if self.actual_port is None:
            raise RuntimeError("サーバが開始されていません（actual_port=None）")
        
        from urllib.parse import quote
        viewer_url = f"http://{self.public_host}:{self.actual_port}/viewer?file={quote(file_url, safe='')}"
        logger.debug(f"[V3] ビューアURL生成: {file_url} -> {viewer_url}")
        return viewer_url

    def get_status(self) -> dict:
        """サーバ状態取得"""
        return {
            "version": "v3",
            "host": self.host,
            "public_host": self.public_host, 
            "actual_port": self.actual_port,
            "registered_files": len(self.pdf_files),
            "temp_dir": self.temp_dir,
            "is_running": self._loop is not None and not self._loop.is_closed()
        }


# =====================
# マネージャ（バックグラウンドスレッド管理）
# =====================
class PDFStreamManagerV3:
    """V3サーバーのライフサイクル管理（スレッド安全・堅牢性重視）"""
    
    _instance: Optional[PDFStreamServerV3] = None
    _loop: Optional[asyncio.AbstractEventLoop] = None
    _thread: Optional[threading.Thread] = None
    _ready: threading.Event = threading.Event()

    @classmethod
    def _thread_main(cls, host: str, port: int, public_host: Optional[str]):
        """バックグラウンドスレッドのメイン処理"""
        logger.info("[V3-THREAD] バックグラウンドスレッド開始")
        
        # 新しいイベントループを作成・設定
        loop = asyncio.new_event_loop()
        cls._loop = loop
        asyncio.set_event_loop(loop)

        server = PDFStreamServerV3(host=host, port=port, public_host=public_host)

        async def _boot():
            """サーバ起動処理"""
            logger.info("[V3-THREAD] サーバ起動処理開始")
            try:
                await server.start()
                cls._instance = server
                cls._ready.set()  # 起動完了シグナル
                logger.info("[V3-THREAD] サーバ起動完了、常駐モード開始")
            except Exception as e:
                logger.exception(f"[V3-THREAD] サーバ起動失敗: {e}")
                cls._ready.set()  # エラーでも待機解除
                raise

        # サーバ起動タスクをスケジュール
        loop.create_task(_boot())
        
        try:
            # 常駐モード（外部からstopされるまで継続）
            loop.run_forever()
            logger.info("[V3-THREAD] イベントループ終了")
        finally:
            # 終了時のクリーンアップ
            logger.info("[V3-THREAD] クリーンアップ開始")
            try:
                if server and server._loop:
                    loop.run_until_complete(server.stop())
            except Exception:
                logger.exception("[V3-THREAD] サーバ停止エラー")
            finally:
                loop.close()
                cls._loop = None
                cls._instance = None
                cls._ready.clear()
                logger.info("[V3-THREAD] バックグラウンドスレッド完全終了")

    @classmethod
    def start_background(cls, host: str = DEFAULT_BIND_HOST, port: int = DEFAULT_PORT, 
                        public_host: Optional[str] = None) -> PDFStreamServerV3:
        """バックグラウンドサーバ起動（同期API）"""
        if cls._instance is not None:
            logger.info("[V3-MANAGER] 既存インスタンス返却")
            return cls._instance

        logger.info(f"[V3-MANAGER] バックグラウンドサーバ起動開始: host={host}, port={port}, public_host={public_host}")
        
        # 状態をクリア
        cls._ready.clear()
        
        # バックグラウンドスレッド開始
        cls._thread = threading.Thread(
            target=cls._thread_main,
            args=(host, port, public_host),
            name="PDFStreamServerV3Thread",
            daemon=True,
        )
        cls._thread.start()

        # 起動完了を待機（堅牢なタイムアウト）
        logger.info("[V3-MANAGER] サーバ起動完了待機中...")
        if not cls._ready.wait(timeout=20):  # V3は複雑なのでタイムアウト延長
            logger.error("[V3-MANAGER] サーバ起動タイムアウト")
            raise RuntimeError("PDF Stream Server V3 の起動がタイムアウトしました (20秒)")

        if cls._instance is None:
            logger.error("[V3-MANAGER] サーバ起動失敗：インスタンスが作成されていません")
            raise RuntimeError("PDF Stream Server V3 の起動に失敗しました")

        logger.info(f"[V3-MANAGER] バックグラウンドサーバ起動完了: port={cls._instance.actual_port}")
        return cls._instance

    @classmethod
    async def get_instance(cls, host: str = DEFAULT_BIND_HOST, port: int = DEFAULT_PORT, 
                          public_host: Optional[str] = None) -> PDFStreamServerV3:
        """非同期API（内部では同期起動を使用）"""
        return cls.start_background(host=host, port=port, public_host=public_host)

    @classmethod
    def get_instance_sync(cls, host: str = DEFAULT_BIND_HOST, port: int = DEFAULT_PORT, 
                         public_host: Optional[str] = None) -> PDFStreamServerV3:
        """同期API（推奨：UI側から使いやすい）"""
        return cls.start_background(host=host, port=port, public_host=public_host)

    @classmethod
    def stop_sync(cls):
        """サーバ停止（同期API）"""
        logger.info("[V3-MANAGER] サーバ停止処理開始")
        
        loop = cls._loop
        if loop is None:
            logger.info("[V3-MANAGER] 停止対象なし（すでに停止済み）")
            return
        
        # イベントループを停止
        try:
            loop.call_soon_threadsafe(loop.stop)
        except Exception as e:
            logger.warning(f"[V3-MANAGER] ループ停止シグナル送信失敗: {e}")
        
        # スレッド終了待機
        if cls._thread:
            cls._thread.join(timeout=8)
            if cls._thread.is_alive():
                logger.warning("[V3-MANAGER] スレッド終了タイムアウト")
            else:
                logger.info("[V3-MANAGER] スレッド正常終了")
        
        cls._thread = None
        logger.info("[V3-MANAGER] サーバ停止処理完了")

    @classmethod
    async def cleanup(cls):
        """サーバ停止（非同期API）"""
        cls.stop_sync()

    @classmethod 
    def get_status(cls) -> dict:
        """管理状態取得"""
        return {
            "manager_version": "v3",
            "instance_exists": cls._instance is not None,
            "thread_alive": cls._thread.is_alive() if cls._thread else False,
            "loop_running": cls._loop is not None and not cls._loop.is_closed() if cls._loop else False,
            "server_status": cls._instance.get_status() if cls._instance else None
        }


# =====================
# 便利関数・ユーティリティ
# =====================
def create_pdf_stream_server_v3(host: str = DEFAULT_BIND_HOST, port: int = DEFAULT_PORT, 
                                public_host: Optional[str] = None) -> PDFStreamServerV3:
    """PDFストリームサーバV3作成（テストや特殊用途向け）"""
    return PDFStreamServerV3(host, port, public_host)


async def serve_pdf_from_bytes_v3(pdf_data: bytes, file_id: Optional[str] = None) -> Tuple[str, PDFStreamServerV3]:
    """
    バイトデータからPDF配信URL作成（V3版）
    - 常駐サーバを（まだなら）起動
    - ファイル登録してURLを返す（スレッド安全）
    """
    import uuid
    if file_id is None:
        file_id = str(uuid.uuid4())

    server = await PDFStreamManagerV3.get_instance()
    pdf_url = server.register_pdf(file_id, pdf_data)
    return pdf_url, server


# =====================
# メイン・テスト実行
# =====================
if __name__ == "__main__":
    import sys

    async def test_server():
        """単発テスト実行"""
        logger.info("[TEST] V3サーバー単発テスト開始")
        server = PDFStreamServerV3()
        await server.start()
        
        print(f"✅ Test server started on {server.host}:{server.actual_port}")
        print(f"   Public host: {server.public_host}")
        
        # ダミーPDFテスト
        dummy_pdf = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n%%EOF\n"
        pdf_url = server.register_pdf("test", dummy_pdf)
        viewer_url = server.get_viewer_url(pdf_url)
        
        print(f"📄 PDF URL: {pdf_url}")
        print(f"🌐 Viewer URL: {viewer_url}")
        print(f"❤️  Health: http://{server.public_host}:{server.actual_port}/health")
        
        try:
            print("⏳ サーバ動作中... (Ctrl+C で終了)")
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 サーバ停止中...")
            await server.stop()
            print("✅ サーバ停止完了")

    async def test_manager():
        """マネージャーテスト実行"""
        print("🚀 V3マネージャーテスト開始")
        
        # バックグラウンドサーバ起動
        srv = PDFStreamManagerV3.get_instance_sync()
        print(f"✅ Background server: {srv.host}:{srv.actual_port} (public: {srv.public_host})")
        
        # テストPDF登録
        dummy_pdf = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n%%EOF\n"
        pdf_url = srv.register_pdf("manager_test", dummy_pdf)
        viewer_url = srv.get_viewer_url(pdf_url)
        
        print(f"📄 PDF URL: {pdf_url}")
        print(f"🌐 Viewer URL: {viewer_url}")
        
        # 状態確認
        status = PDFStreamManagerV3.get_status()
        print(f"📊 Status: {status}")
        
        try:
            print("⏳ バックグラウンドサーバ動作中... (Ctrl+C で終了)")
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 サーバ停止中...")
            PDFStreamManagerV3.stop_sync()
            print("✅ サーバ停止完了")

    # コマンドライン引数処理
    if len(sys.argv) > 1:
        if sys.argv[1] == "test":
            asyncio.run(test_server())
        elif sys.argv[1] == "manager":
            asyncio.run(test_manager())
        else:
            print(f"使用法: python {sys.argv[0]} [test|manager]")
    else:
        # デフォルト：バックグラウンドマネージャー実行
        asyncio.run(test_manager())
