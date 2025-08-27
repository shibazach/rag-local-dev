#!/usr/bin/env python3
"""
V4大容量PDF対応 - 画像表示専用プレビューコンポーネント

技術仕様:
- 完全ft.Image表示（WebView不使用）
- プラットフォーム制限なし（Linux/Windows完全対応）
- PyMuPDF画像変換 + 高速キャッシュ
- ページ送り・ズーム・先読み機能
- V3完全独立アーキテクチャ

UI設計:
- 右ペイン内完全表示対応
- レスポンシブレイアウト
- タッチ・キーボード操作対応
- エラーハンドリング完備
- パフォーマンス最適化

主要機能:
- load_pdf(): PDF読み込み・表示開始
- navigate(): ページ送り（前/次）
- zoom(): ズーム制御（0.5x～3.0x）
- prefetch(): 先読み実行
- clear_preview(): リソース解放

V3との差別化:
- ✅ 全プラットフォーム動作保証
- ✅ 右ペイン内確実表示
- ✅ シンプル・高速レンダリング
- ❌ PDF.js機能（検索・テキスト選択等）
"""

import flet as ft
import asyncio
import uuid
import logging
from typing import Dict, Any, Optional, List, Literal
from enum import Enum
import time

from .pdf_stream_server_v4 import PDFStreamManagerV4, serve_pdf_from_bytes_v4

logger = logging.getLogger(__name__)


class PreviewState(Enum):
    """V4プレビュー状態"""
    EMPTY = "empty"           # 未読み込み
    LOADING = "loading"       # PDF読み込み中
    ANALYZING = "analyzing"   # PDF解析中
    READY = "ready"          # 表示準備完了
    RENDERING = "rendering"   # 画像生成中
    DISPLAYED = "displayed"   # 画像表示中
    ERROR = "error"          # エラー状態


class PDFImagePreviewV4(ft.Container):
    """V4画像表示専用PDFプレビューコンポーネント"""

    def __init__(self, page: Optional[ft.Page] = None):
        super().__init__()
        
        # 基本設定
        self.page = page
        self.expand = True
        self.bgcolor = ft.Colors.WHITE
        self.border_radius = 8
        self.padding = ft.padding.all(4)
        
        # 状態管理
        self._state = PreviewState.EMPTY
        self._error_message = ""
        self._file_id: Optional[str] = None
        self._server: Optional[Any] = None  # PDFStreamServerV4
        
        # PDF情報
        self._current_page = 0
        self._total_pages = 0
        self._current_zoom = 1.0
        self._image_width = 1200
        self._dpr = 1.0
        
        # 表示制御
        self._current_image_url: Optional[str] = None
        self._prefetch_running = False
        
        # スクロール制御
        self._last_scroll_time = 0.0
        self._scroll_debounce_ms = 500  # 500ms デバウンス
        
        # 回転制御
        self._rotation = 0  # 0, 90, 180, 270度
        
        # UI初期化
        self._init_ui()
        self._build_layout()

    def _init_ui(self):
        """UI要素初期化"""
        
        # メイン画像表示
        self._image_display = ft.Image(
            src=None,  # 初期値をNoneに設定
            fit=ft.ImageFit.FIT_WIDTH,  # 🎯 幅方向全体フィット（初期表示最適化）
            width=None,  # fitに任せる
            border_radius=ft.border_radius.all(4),
            gapless_playback=True,  # 画像切替時のちらつき抑制
            visible=False,  # 初期は非表示
            error_content=ft.Container(
                content=ft.Column([
                    ft.Icon(ft.Icons.ERROR_OUTLINE, size=64, color=ft.Colors.RED_400),
                    ft.Text("画像読み込みエラー", size=14, color=ft.Colors.RED_600)
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                alignment=ft.alignment.center,
                height=200
            )
        )
        
        # ページ入力ボックス
        self._page_input = ft.TextField(
            value="1",
            width=50,
            height=32,
            text_size=12,
            text_align=ft.TextAlign.CENTER,
            border_color=ft.Colors.GREY_400,
            focused_border_color=ft.Colors.BLUE_400,
            on_submit=self._on_page_input,
            tooltip="ページ番号を入力してEnter"
        )
        
        self._total_pages_text = ft.Text(
            "/ 0", 
            size=14, 
            color=ft.Colors.GREY_600,
            weight=ft.FontWeight.BOLD
        )
        
        self._zoom_info = ft.Text(
            "100%", 
            size=14, 
            color=ft.Colors.GREY_600
        )
        
        # ナビゲーションボタン
        self._prev_button = ft.IconButton(
            icon=ft.Icons.KEYBOARD_ARROW_LEFT,
            icon_size=24,
            tooltip="前のページ (←)",
            on_click=self._on_prev_page,
            disabled=True
        )
        
        self._next_button = ft.IconButton(
            icon=ft.Icons.KEYBOARD_ARROW_RIGHT,
            icon_size=24,
            tooltip="次のページ (→)",
            on_click=self._on_next_page,
            disabled=True
        )
        
        # ズームボタン
        self._zoom_out_button = ft.IconButton(
            icon=ft.Icons.ZOOM_OUT,
            icon_size=20,
            tooltip="縮小 (-)",
            on_click=self._on_zoom_out,
            disabled=True
        )
        
        self._zoom_in_button = ft.IconButton(
            icon=ft.Icons.ZOOM_IN,
            icon_size=20,
            tooltip="拡大 (+)",
            on_click=self._on_zoom_in,
            disabled=True
        )
        
        self._zoom_fit_button = ft.IconButton(
            icon=ft.Icons.FIT_SCREEN,
            icon_size=20,
            tooltip="フィット (0)",
            on_click=self._on_zoom_fit,
            disabled=True
        )
        
        # 制御ボタン
        self._reload_button = ft.IconButton(
            icon=ft.Icons.REFRESH,
            icon_size=20,
            tooltip="再読み込み",
            on_click=self._on_reload,
            disabled=True
        )
        
        # ダウンロードボタン
        self._download_button = ft.IconButton(
            icon=ft.Icons.DOWNLOAD,
            icon_size=20,
            tooltip="PDFダウンロード",
            on_click=self._on_download,
            disabled=True
        )
        
        # 回転ボタン
        self._rotate_left_button = ft.IconButton(
            icon=ft.Icons.ROTATE_LEFT,
            icon_size=20,
            tooltip="左に90度回転",
            on_click=self._on_rotate_left,
            disabled=True
        )
        
        self._rotate_right_button = ft.IconButton(
            icon=ft.Icons.ROTATE_RIGHT,
            icon_size=20,
            tooltip="右に90度回転",
            on_click=self._on_rotate_right,
            disabled=True
        )
        
        self._clear_button = ft.ElevatedButton(
            text="🗑️ クリア",
            height=32,
            on_click=self._on_clear
        )
        
        # ステータス表示
        self._status_container = ft.Container(
            content=self._build_status_content(),
            alignment=ft.alignment.center,
            expand=True,
            visible=True
        )

    def _build_layout(self):
        """レイアウト構築"""
        
        # ツールバー
        toolbar = ft.Container(
            content=ft.Row([
                # ページナビゲーション
                self._prev_button,
                self._page_input,
                self._total_pages_text,
                self._next_button,
                
                ft.VerticalDivider(width=1, color=ft.Colors.GREY_300),
                
                # ズーム制御
                self._zoom_out_button,
                self._zoom_info,
                self._zoom_in_button,
                self._zoom_fit_button,
                
                ft.VerticalDivider(width=1, color=ft.Colors.GREY_300),
                
                # 回転制御
                self._rotate_left_button,
                self._rotate_right_button,
                
                ft.VerticalDivider(width=1, color=ft.Colors.GREY_300),
                
                # その他制御
                self._reload_button,
                self._download_button,
                
                # 右寄せ
                ft.Container(expand=True),
                self._clear_button
                
            ], spacing=4, alignment=ft.MainAxisAlignment.START),
            bgcolor=ft.Colors.GREY_50,
            padding=ft.padding.all(8),
            border_radius=ft.border_radius.all(4),
            height=48
        )
        
        # スクロール可能な画像表示エリア（縦横両方向対応）
        scrollable_image = ft.Column([
            ft.Container(height=10),  # 上部余白（ツールバー重なり回避）
            ft.Row([
                ft.Container(
                    content=self._image_display,
                    alignment=ft.alignment.center,
                    expand=False
                )
            ], 
            alignment=ft.MainAxisAlignment.CENTER,
            scroll=ft.ScrollMode.AUTO  # 横スクロール
            ),
            ft.Container(height=20)   # 下部余白
        ], 
        spacing=0,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        scroll=ft.ScrollMode.AUTO,  # 縦スクロール
        on_scroll=self._on_scroll,
        expand=True
        )
        
        # メイン表示エリア（スタック構造維持）
        display_area = ft.Stack([
            # スクロール可能画像表示
            scrollable_image,
            
            # ステータスオーバーレイ
            self._status_container
        ], expand=True)
        
        # 全体レイアウト
        self.content = ft.Column([
            toolbar,
            ft.Container(height=4),  # スペーサー
            display_area
        ], spacing=0, expand=True)

    def _build_status_content(self) -> ft.Control:
        """ステータス表示コンテンツ構築"""
        
        if self._state == PreviewState.EMPTY:
            return ft.Column([
                ft.Icon(ft.Icons.PICTURE_AS_PDF, size=80, color=ft.Colors.GREY_400),
                ft.Container(height=16),
                ft.Text("PDF未選択", size=16, color=ft.Colors.GREY_600),
                ft.Text("PDFを読み込んでください", size=12, color=ft.Colors.GREY_500)
            ], 
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER,  # 🎯 縦方向センタリング修正
            spacing=0)
            
        elif self._state == PreviewState.LOADING:
            return ft.Column([
                ft.ProgressRing(width=40, height=40, color=ft.Colors.BLUE_400),
                ft.Container(height=16),
                ft.Text("PDF読み込み中...", size=16, color=ft.Colors.BLUE_600)
            ], 
            horizontal_alignment=ft.CrossAxisAlignment.CENTER, 
            alignment=ft.MainAxisAlignment.CENTER,  # 🎯 縦方向センタリング修正
            spacing=0)
            
        elif self._state == PreviewState.ANALYZING:
            return ft.Column([
                ft.ProgressRing(width=40, height=40, color=ft.Colors.GREEN_400),
                ft.Container(height=16),
                ft.Text("PDF解析中...", size=16, color=ft.Colors.GREEN_600),
                ft.Text("ページ数・サイズ情報取得中", size=12, color=ft.Colors.GREEN_500)
            ], 
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER,  # 🎯 縦方向センタリング修正
            spacing=0)
            
        elif self._state == PreviewState.RENDERING:
            return ft.Column([
                ft.ProgressRing(width=40, height=40, color=ft.Colors.ORANGE_400),
                ft.Container(height=16),
                ft.Text("画像生成中...", size=16, color=ft.Colors.ORANGE_600),
                ft.Text(f"ページ {self._current_page + 1} / {self._total_pages}", size=12, color=ft.Colors.ORANGE_500)
            ], 
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER,  # 🎯 縦方向センタリング修正
            spacing=0)
            
        elif self._state == PreviewState.ERROR:
            return ft.Column([
                ft.Icon(ft.Icons.ERROR_OUTLINE, size=64, color=ft.Colors.RED_400),
                ft.Container(height=16),
                ft.Text("エラー", size=16, color=ft.Colors.RED_600, weight=ft.FontWeight.BOLD),
                ft.Container(height=8),
                ft.Text(
                    self._error_message,
                    size=12,
                    color=ft.Colors.RED_500,
                    text_align=ft.TextAlign.CENTER,
                    selectable=True
                )
            ], 
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER,  # 🎯 縦方向センタリング修正
            spacing=0)
            
        else:
            # READY, DISPLAYED
            return ft.Container()  # 非表示

    def _set_state(self, state: PreviewState, error_message: str = ""):
        """状態変更"""
        self._state = state
        self._error_message = error_message
        
        logger.info(f"[V4-UI] State: {state.value} {f'({error_message})' if error_message else ''}")
        
        # UI更新
        self._update_ui()

    def _update_ui(self):
        """UI状態更新"""
        try:
            # ステータス表示制御
            show_status = self._state in [PreviewState.EMPTY, PreviewState.LOADING, 
                                         PreviewState.ANALYZING, PreviewState.RENDERING, 
                                         PreviewState.ERROR]
            
            self._status_container.visible = show_status
            self._status_container.content = self._build_status_content()
            
            # 画像表示制御（画像が設定されている場合のみ表示）
            image_src_exists = self._image_display.src is not None
            self._image_display.visible = (not show_status) and image_src_exists
            
            # ボタン状態更新
            buttons_enabled = self._state == PreviewState.DISPLAYED and self._total_pages > 0
            
            self._prev_button.disabled = not buttons_enabled or self._current_page <= 0
            self._next_button.disabled = not buttons_enabled or self._current_page >= self._total_pages - 1
            
            self._zoom_out_button.disabled = not buttons_enabled or self._current_zoom <= 0.5
            self._zoom_in_button.disabled = not buttons_enabled or self._current_zoom >= 3.0
            self._zoom_fit_button.disabled = not buttons_enabled
            
            self._reload_button.disabled = not buttons_enabled
            self._download_button.disabled = not buttons_enabled
            self._rotate_left_button.disabled = not buttons_enabled
            self._rotate_right_button.disabled = not buttons_enabled
            
            # 情報表示更新
            if self._total_pages > 0:
                self._page_input.value = str(self._current_page + 1)
                self._total_pages_text.value = f"/ {self._total_pages}"
            else:
                self._page_input.value = "1"
                self._total_pages_text.value = "/ 0"
                
            self._zoom_info.value = f"{int(self._current_zoom * 100)}%"
            
            self.update()
            
        except Exception as e:
            logger.error(f"[V4-UI] UI update error: {e}")

    async def load_pdf(self, file_info: Dict[str, Any], blob_data: bytes):
        """PDF読み込み・表示開始"""
        try:
            self._set_state(PreviewState.LOADING)
            
            # PDF登録
            file_id = file_info.get("id", str(uuid.uuid4()))
            self._file_id = file_id
            
            pdf_url, server = await serve_pdf_from_bytes_v4(blob_data, file_id)
            self._server = server
            
            logger.info(f"[V4-UI] PDF registered: {file_id} ({len(blob_data)} bytes)")
            
            # PDF情報取得
            self._set_state(PreviewState.ANALYZING)
            
            info_url = server.get_info_url(file_id)
            if not info_url:
                raise RuntimeError("Failed to get PDF info URL")
            
            # HTTP で情報取得 (簡易実装)
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get(info_url) as resp:
                    if resp.status != 200:
                        raise RuntimeError(f"PDF info request failed: {resp.status}")
                    info_data = await resp.json()
            
            self._total_pages = info_data.get("page_count", 0)
            self._current_page = 0
            
            if self._total_pages <= 0:
                raise ValueError("Invalid page count")
            
            logger.info(f"[V4-UI] PDF info: {self._total_pages} pages")
            
            # 最初のページ表示
            await self._render_and_display_page(0)
            
            # 先読み開始
            if not self._prefetch_running and self.page:
                self.page.run_task(self._start_prefetch)
                logger.info("[V4-UI] 先読み処理開始（ログ出力は抑制）")
            
        except Exception as e:
            import traceback
            error_detail = f"Type: {type(e).__name__}, Message: '{str(e)}', Traceback: {traceback.format_exc()}"
            logger.error(f"[V4-UI] Load PDF error DETAILED: {error_detail}")
            self._set_state(PreviewState.ERROR, f"PDF読み込みエラー: {type(e).__name__}: {str(e) or '不明なエラー'}")

    async def _render_and_display_page(self, page_index: int):
        """ページレンダリング・表示"""
        try:
            # 画像表示処理開始
            self._set_state(PreviewState.RENDERING)
            self._current_page = page_index
            
            if not self._server or not self._file_id:
                raise RuntimeError("Server or file_id not available")
            
            # 画像URL生成・取得・表示（回転対応）
            image_url = self._server.get_image_url(
                self._file_id, page_index, width=self._image_width, dpr=self._dpr, fmt="png", rotation=self._rotation
            )
            
            if not image_url:
                raise RuntimeError("Failed to generate image URL")
            
            self._current_image_url = image_url
            
            # 画像取得・Base64変換・表示
            import aiohttp, base64
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(image_url) as resp:
                        if resp.status != 200:
                            raise RuntimeError(f"Image server error: {resp.status}")
                        
                        # Base64変換・表示
                        image_bytes = await resp.read()
                        image_b64 = base64.b64encode(image_bytes).decode('ascii')
                        data_url = f"data:image/png;base64,{image_b64}"
                        
                        self._image_display.src = data_url
                        
                        # 表示方法最適化：zoom=1.0なら幅フィット、それ以外は実サイズ
                        if self._current_zoom == 1.0:
                            self._image_display.fit = ft.ImageFit.FIT_WIDTH
                            self._image_display.width = None
                            self._image_display.expand = False
                        else:
                            self._image_display.fit = ft.ImageFit.NONE  
                            self._image_display.width = self._image_width
                            self._image_display.expand = False
                            
                        self._image_display.visible = True
                        self._image_display.update()
                        
            except Exception as url_error:
                raise RuntimeError(f"Image fetch failed: {url_error}")
            
            # 表示完了状態（即座に設定・ローディング短縮）
            self._set_state(PreviewState.DISPLAYED)
            
            # UI更新（最適化）
            if self.page:
                self.page.update()
                
            logger.info(f"[V4-UI] ✅ RENDER COMPLETE: Page {page_index} displayed")
            
        except Exception as e:
            import traceback
            error_detail = f"Type: {type(e).__name__}, Message: '{str(e)}', Traceback: {traceback.format_exc()}"
            logger.error(f"[V4-UI] Render page error DETAILED: {error_detail}")
            self._set_state(PreviewState.ERROR, f"ページ表示エラー: {type(e).__name__}: {str(e) or '不明なエラー'}")

    async def _start_prefetch(self):
        """先読み開始（バックグラウンド）"""
        if self._prefetch_running:
            return
            
        self._prefetch_running = True
        
        try:
            while self._prefetch_running and self._server and self._file_id:
                
                # 先読み実行
                prefetch_url = f"http://{self._server.public_host}:{self._server.actual_port}/prefetch/{self._file_id}"
                
                prefetch_data = {
                    "current_page": self._current_page,
                    "width": self._image_width,
                    "dpr": self._dpr,
                    "range": 2
                }
                
                try:
                    import aiohttp
                    async with aiohttp.ClientSession() as session:
                        async with session.post(prefetch_url, json=prefetch_data) as resp:
                            if resp.status == 200:
                                logger.debug(f"[V4-UI] Prefetch successful: page {self._current_page}")
                            else:
                                logger.debug(f"[V4-UI] Prefetch failed: {resp.status}")
                except Exception as e:
                    logger.debug(f"[V4-UI] Prefetch error: {e}")
                
                # 5秒待機
                await asyncio.sleep(5)
                
        except Exception as e:
            logger.error(f"[V4-UI] Prefetch loop error: {e}")
        finally:
            self._prefetch_running = False

    def _on_prev_page(self, e):
        """前のページ"""
        if self._current_page > 0:
            if self.page:
                async def prev_page():
                    await self._render_and_display_page(self._current_page - 1)
                self.page.run_task(prev_page)

    def _on_next_page(self, e):
        """次のページ"""
        if self._current_page < self._total_pages - 1:
            if self.page:
                async def next_page():
                    await self._render_and_display_page(self._current_page + 1)
                self.page.run_task(next_page)

    def _on_zoom_out(self, e):
        """ズームアウト"""
        new_zoom = max(0.5, self._current_zoom / 1.25)
        self._apply_zoom(new_zoom)

    def _on_zoom_in(self, e):
        """ズームイン"""
        new_zoom = min(3.0, self._current_zoom * 1.25)
        self._apply_zoom(new_zoom)

    def _on_zoom_fit(self, e):
        """フィット"""
        self._apply_zoom(1.0)

    def _apply_zoom(self, zoom: float):
        """ズーム適用"""
        if self._current_zoom == zoom:
            return
            
        self._current_zoom = zoom
        self._image_width = int(1200 * zoom)
        
        # ズーム設定に応じて表示方法を最適化
        if zoom == 1.0:
            # 標準サイズ：幅方向フィット（表示領域に合わせる）
            self._image_display.fit = ft.ImageFit.FIT_WIDTH
            self._image_display.width = None
            self._image_display.expand = False
        else:
            # 拡大時：実サイズ表示（スクロール対応）
            self._image_display.fit = ft.ImageFit.NONE
            self._image_display.width = self._image_width
            self._image_display.expand = False
            
        self._image_display.update()
        
        # 現在ページ再レンダリング
        if self._state == PreviewState.DISPLAYED and self.page:
            async def rerender_current():
                await self._render_and_display_page(self._current_page)
            self.page.run_task(rerender_current)

    def _on_reload(self, e):
        """再読み込み"""
        if self._state == PreviewState.DISPLAYED and self.page:
            async def reload_current():
                await self._render_and_display_page(self._current_page)
            self.page.run_task(reload_current)
    
    def _on_scroll(self, e):
        """スクロールイベント処理（端部ページ遷移）"""
        import time
        
        # デバウンシング：短時間の連続実行を防止
        current_time = time.time() * 1000  # ミリ秒
        if (current_time - self._last_scroll_time) < self._scroll_debounce_ms:
            return
            
        if not hasattr(e, 'pixels') or not hasattr(e, 'max_scroll_extent'):
            return
            
        # スクロール情報取得
        current_position = e.pixels
        max_scroll = e.max_scroll_extent
        
        # スクロール範囲の安全性チェック
        if max_scroll <= 0 or current_position < 0:
            return
        
        # 端部判定の閾値（30px - より敏感に）
        threshold = 30.0
        
        # 上端到達時：前ページ
        if current_position <= threshold and self._current_page > 0:
            if self._state == PreviewState.DISPLAYED:
                self._last_scroll_time = current_time  # デバウンス更新
                self._on_prev_page(e)
                
        # 下端到達時：次ページ  
        elif (max_scroll - current_position) <= threshold and self._current_page < (self._total_pages - 1):
            if self._state == PreviewState.DISPLAYED:
                self._last_scroll_time = current_time  # デバウンス更新
                self._on_next_page(e)

    def _on_page_input(self, e):
        """ページ番号入力処理"""
        try:
            page_num = int(self._page_input.value)
            target_page = max(1, min(page_num, self._total_pages)) - 1
            
            if target_page != self._current_page and self._state == PreviewState.DISPLAYED:
                if self.page:
                    async def go_to_page():
                        await self._render_and_display_page(target_page)
                    self.page.run_task(go_to_page)
            else:
                # 無効な値の場合、現在ページに戻す
                self._page_input.value = str(self._current_page + 1)
                self._page_input.update()
                
        except ValueError:
            # 数値以外の場合、現在ページに戻す
            self._page_input.value = str(self._current_page + 1)
            self._page_input.update()

    def _on_download(self, e):
        """PDFダウンロード処理"""
        if not self._server or not self._file_id:
            return
            
        # PDFファイルのダウンロードURL生成
        download_url = self._server.get_pdf_download_url(self._file_id)
        if download_url and self.page:
            # 新しいタブでダウンロードURL開く
            self.page.launch_url(download_url)

    def _on_rotate_left(self, e):
        """左回転（反時計回り90度）"""
        self._rotation = (self._rotation - 90) % 360
        self._apply_rotation()

    def _on_rotate_right(self, e):
        """右回転（時計回り90度）"""
        self._rotation = (self._rotation + 90) % 360
        self._apply_rotation()
        
    def _apply_rotation(self):
        """回転適用"""
        if self._state == PreviewState.DISPLAYED and self.page:
            async def rerender_rotated():
                await self._render_and_display_page(self._current_page)
            self.page.run_task(rerender_rotated)

    def _on_clear(self, e):
        """クリア"""
        self.clear_preview()

    def clear_preview(self):
        """プレビュークリア・リソース解放"""
        try:
            # 先読み停止
            self._prefetch_running = False
            
            # サーバー登録解除
            if self._server and self._file_id:
                try:
                    self._server.unregister_pdf_sync(self._file_id)
                    logger.info(f"[V4-UI] PDF unregistered: {self._file_id}")
                except Exception as e:
                    logger.warning(f"[V4-UI] Unregister error: {e}")
            
            # 状態リセット
            self._file_id = None
            self._server = None
            self._current_page = 0
            self._total_pages = 0
            self._current_zoom = 1.0
            self._image_width = 1200
            self._dpr = 1.0
            self._current_image_url = None
            self._rotation = 0  # 回転状態リセット
            
            # 画像クリア
            self._image_display.src = None
            self._image_display.visible = False  # 画像非表示
            self._image_display.fit = ft.ImageFit.FIT_WIDTH  # 初期状態に戻す
            self._image_display.width = None  # 初期状態に戻す
            self._image_display.update()  # 🔥 CRITICAL: クリア時UI更新
            
            # 状態変更
            self._set_state(PreviewState.EMPTY)
            
            # 🔥 CRITICAL: クリア完了後の強制UI更新
            if self.page:
                self.page.update()
            
            logger.info("[V4-UI] Preview cleared")
            
        except Exception as e:
            logger.error(f"[V4-UI] Clear error: {e}")

    def navigate_to_page(self, page_index: int):
        """指定ページへ移動"""
        if 0 <= page_index < self._total_pages and page_index != self._current_page and self.page:
            async def navigate():
                await self._render_and_display_page(page_index)
            self.page.run_task(navigate)

    def set_zoom(self, zoom: float):
        """ズーム設定"""
        zoom = max(0.5, min(3.0, zoom))
        self._apply_zoom(zoom)

    def get_current_state(self) -> Dict[str, Any]:
        """現在状態取得"""
        return {
            "state": self._state.value,
            "current_page": self._current_page,
            "total_pages": self._total_pages,
            "zoom": self._current_zoom,
            "file_id": self._file_id,
            "error_message": self._error_message
        }

    def test_basic_image_display(self):
        """Phase 1: 基本画像表示テスト"""
        logger.info("[V4-UI] 🧪 Phase 1: 基本画像表示テスト開始")
        
        # 外部画像URL（確実に動作する）
        test_image_url = "https://httpbin.org/image/png"
        
        try:
            logger.info(f"[V4-UI] 🧪 Phase 1.1: テスト画像URL設定 - {test_image_url}")
            
            # ステータス非表示
            self._status_container.visible = False
            logger.info("[V4-UI] 🧪 Phase 1.2: ステータスコンテナ非表示")
            
            # 画像設定
            self._image_display.src = test_image_url
            self._image_display.visible = True
            logger.info("[V4-UI] 🧪 Phase 1.3: 画像表示設定完了")
            
            # UI更新
            self._image_display.update()
            self.update()
            if self.page:
                self.page.update()
            logger.info("[V4-UI] 🧪 Phase 1.4: UI更新完了")
            
            logger.info("[V4-UI] 🟢 Phase 1 SUCCESS: 基本画像表示テスト完了")
            
        except Exception as e:
            logger.error(f"[V4-UI] 🔴 Phase 1 FAILED: {e}")
            import traceback
            logger.error(f"[V4-UI] 🔴 Phase 1 詳細: {traceback.format_exc()}")


def create_large_pdf_preview_v4(page: Optional[ft.Page] = None) -> PDFImagePreviewV4:
    """V4大容量PDFプレビュー作成"""
    return PDFImagePreviewV4(page)


# テスト用
if __name__ == "__main__":
    import flet as ft
    
    def main(page: ft.Page):
        page.title = "V4 PDF Preview Test"
        page.window_width = 1000
        page.window_height = 700
        
        preview = create_large_pdf_preview_v4(page)
        
        # テスト用ボタン
        test_button = ft.ElevatedButton(
            "テストPDF読み込み",
            on_click=lambda e: test_load_pdf(preview)
        )
        
        page.add(
            ft.Row([test_button]),
            ft.Container(height=10),
            preview
        )
    
    def test_load_pdf(preview):
        # ダミーPDF
        dummy_pdf = b"""%PDF-1.4
1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj
2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj
3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 612 792]>>endobj
%%EOF"""
        
        async def test_load():
            await preview.load_pdf({"id": "test"}, dummy_pdf)
        page.run_task(test_load)
    
    ft.app(target=main, port=8600)
