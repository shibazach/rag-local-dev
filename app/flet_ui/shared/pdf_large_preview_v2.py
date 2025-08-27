#!/usr/bin/env python3
"""
大容量PDF対応プレビューコンポーネント（V2版）
V2ストリーミングサーバ対応版
"""

import flet as ft
import base64
import asyncio
import uuid
import logging
from typing import Dict, Any, Optional
from urllib.parse import quote
from enum import Enum

from .pdf_stream_server_v2 import serve_pdf_from_bytes_v2, PDFStreamManagerV2
from .pdf_image_renderer import PDFImageRenderer

logger = logging.getLogger(__name__)


class LargePreviewState(Enum):
    EMPTY = "empty"
    LOADING = "loading"
    DATA_URL_READY = "data_url_ready"
    PREPARING_STREAM = "preparing_stream"
    STREAM_READY = "stream_ready"
    IMAGE_RENDERING = "image_rendering"
    IMAGE_READY = "image_ready"
    ERROR = "error"


class PDFSizeThreshold:
    """PDF サイズによる処理方式閾値"""
    SMALL_PDF = 1.5 * 1024 * 1024  # 1.5MB未満: data:URL
    LARGE_PDF = 20 * 1024 * 1024   # 20MB未満: HTTPストリーミング
    # 20MB以上: 画像レンダリング


class LargePDFPreviewV2(ft.Container):
    """大容量PDF対応プレビューコンポーネント（V2版）"""
    
    def __init__(self):
        super().__init__()
        
        # 状態管理
        self.current_state = LargePreviewState.EMPTY
        self.current_file_info: Optional[Dict[str, Any]] = None
        self.current_error_message = ""
        self._force_image_mode = False
        self._current_file_id: Optional[str] = None
        self._pdf_url: Optional[str] = None
        
        # UI要素の初期化
        self._init_ui_elements()
        self._init_pdf_viewer_html()
        
        # 初期レイアウト構築
        self._build_layout()
        
        # 画像レンダラ（遅延初期化）
        self._image_renderer: Optional[PDFImageRenderer] = None

    def _init_ui_elements(self):
        """UI要素の初期化"""
        # WebView（ストリーミング・data:URL用）
        self.web_view = ft.WebView(
            url="about:blank",
            expand=True,
            on_page_started=self._on_load_started,
            on_page_ended=self._on_load_ended,
            on_web_resource_error=self._on_load_error
        )
        
        # 画像表示コンテナ（画像モード用）
        self.image_container = ft.Container(
            expand=True,
            alignment=ft.alignment.center
        )
        
        # オーバーレイ（ローディング・エラー・空状態用）
        self.overlay_container = ft.Container(
            expand=True,
            alignment=ft.alignment.center,
            bgcolor=ft.colors.with_opacity(0.8, ft.colors.WHITE)
        )
        
        # コントロールバー
        self.control_bar = ft.Row(
            controls=[
                ft.ElevatedButton(
                    text="🔄 再読み込み",
                    on_click=self._on_reload_click,
                    height=32,
                    disabled=True
                ),
                ft.ElevatedButton(
                    text="🖼️ 画像モード",
                    on_click=self._on_image_mode_toggle,
                    height=32
                )
            ],
            spacing=8
        )

    def _init_pdf_viewer_html(self):
        """PDF.js ビューア用HTMLテンプレート"""
        self._pdf_viewer_html = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>PDF Viewer</title>
    <style>
        body { margin: 0; padding: 0; background: #404040; }
        iframe { width: 100%; height: 100vh; border: none; }
    </style>
</head>
<body>
    <iframe src="https://mozilla.github.io/pdf.js/web/viewer.html?file={{PDF_URL}}" frameborder="0"></iframe>
</body>
</html>
        """

    def _build_layout(self):
        """レイアウト構築"""
        # メインスタック（WebView + 画像コンテナ + オーバーレイ）
        main_stack = ft.Stack(
            controls=[
                self.web_view,
                self.image_container,
                self.overlay_container
            ],
            expand=True
        )
        
        # 全体レイアウト
        self.content = ft.Column(
            controls=[
                self.control_bar,
                main_stack
            ],
            expand=True,
            spacing=4
        )
        
        # 初期状態設定
        self._set_state_and_rebuild(LargePreviewState.EMPTY)

    def _set_state_and_rebuild(self, state: LargePreviewState, error_msg: str = ""):
        """状態変更とUI再構築"""
        self.current_state = state
        self.current_error_message = error_msg
        self._rebuild_overlay()
        
        try:
            self.update()
        except:
            pass

    def _rebuild_overlay(self):
        """オーバーレイコンテンツ再構築"""
        if self.current_state == LargePreviewState.EMPTY:
            self.overlay_container.content = ft.Column(
                controls=[
                    ft.Icon(ft.icons.PICTURE_AS_PDF, size=64, color=ft.colors.GREY_400),
                    ft.Text(
                        "ファイルを選択すると\n大容量PDF対応プレビューが表示されます",
                        size=16,
                        color=ft.colors.GREY_600,
                        text_align=ft.TextAlign.CENTER
                    )
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=16
            )
            self.overlay_container.visible = True
            self.web_view.visible = False
            self.image_container.visible = False
            
        elif self.current_state == LargePreviewState.LOADING:
            self.overlay_container.content = ft.Column(
                controls=[
                    ft.ProgressRing(),
                    ft.Text("PDFを分析中...", size=14, color=ft.colors.GREY_700)
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=8
            )
            self.overlay_container.visible = True
            self.web_view.visible = False
            self.image_container.visible = False
            
        elif self.current_state == LargePreviewState.PREPARING_STREAM:
            self.overlay_container.content = ft.Column(
                controls=[
                    ft.ProgressRing(),
                    ft.Text("ストリーミング準備中...", size=14, color=ft.colors.BLUE_700)
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=8
            )
            self.overlay_container.visible = True
            
        elif self.current_state == LargePreviewState.IMAGE_RENDERING:
            self.overlay_container.content = ft.Column(
                controls=[
                    ft.ProgressRing(),
                    ft.Text("PDFを分析中...", size=14, color=ft.colors.PURPLE_700)
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=8
            )
            self.overlay_container.visible = True
            
        elif self.current_state in [LargePreviewState.DATA_URL_READY, LargePreviewState.STREAM_READY]:
            self.overlay_container.visible = False
            self.web_view.visible = True
            self.image_container.visible = False
            
        elif self.current_state == LargePreviewState.IMAGE_READY:
            self.overlay_container.visible = False
            self.web_view.visible = False
            self.image_container.visible = True
            
        elif self.current_state == LargePreviewState.ERROR:
            self.overlay_container.content = ft.Column(
                controls=[
                    ft.Icon(ft.icons.ERROR, size=48, color=ft.colors.RED_400),
                    ft.Text(
                        f"エラーが発生しました:\n{self.current_error_message}",
                        size=14,
                        color=ft.colors.RED_700,
                        text_align=ft.TextAlign.CENTER
                    )
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=8
            )
            self.overlay_container.visible = True
            self.web_view.visible = False
            self.image_container.visible = False

        # コントロールバー状態更新
        if hasattr(self, 'control_bar') and len(self.control_bar.controls) >= 1:
            reload_btn = self.control_bar.controls[0]
            reload_btn.disabled = (self.current_state == LargePreviewState.EMPTY)

    async def load_pdf(self, file_info: Dict[str, Any], blob_data: Optional[bytes] = None):
        """PDF読み込みメイン処理（V2版）"""
        try:
            # 初期状態
            self._set_state_and_rebuild(LargePreviewState.LOADING)
            
            if blob_data is None:
                # DBからblob_dataを取得
                from app.core.db_simple import fetch_one
                db_result = fetch_one(
                    "SELECT blob_data FROM files_blob WHERE id = %s",
                    (file_info.get('blob_id', file_info.get('id')),)
                )
                if not db_result or 'blob_data' not in db_result:
                    raise ValueError("PDFデータが見つかりません")
                blob_data = db_result['blob_data']

            pdf_size = len(blob_data)
            logger.info(f"[V2-PDF] PDF読み込み開始: サイズ={pdf_size}bytes")

            # サイズに応じた処理分岐
            await self._handle_pdf_by_size_v2(file_info, blob_data, pdf_size)

        except Exception as e:
            logger.error(f"[V2-PDF] PDF読み込みエラー: {e}")
            self._set_state_and_rebuild(LargePreviewState.ERROR, str(e))

    async def _handle_pdf_by_size_v2(self, file_info: Dict[str, Any], blob_data: bytes, pdf_size: int):
        """サイズに応じたPDF処理（V2版）"""
        try:
            if self._force_image_mode:
                # 画像モード強制
                await self._handle_image_mode_v2(file_info, blob_data)
            elif pdf_size < PDFSizeThreshold.SMALL_PDF:
                # 小サイズ: data:URL
                await self._handle_data_url_mode(file_info, blob_data)
            elif pdf_size < PDFSizeThreshold.LARGE_PDF:
                # 中サイズ: HTTPストリーミング（V2）
                await self._handle_streaming_mode_v2(file_info, blob_data)
            else:
                # 大サイズ: 画像レンダリング
                await self._handle_image_mode_v2(file_info, blob_data)

        except Exception as e:
            logger.error(f"[V2-PDF] PDF処理エラー: {e}")
            self._set_state_and_rebuild(LargePreviewState.ERROR, f"PDF処理エラー: {str(e)}")

    async def _handle_streaming_mode_v2(self, file_info: Dict[str, Any], blob_data: bytes):
        """HTTPストリーミングモード処理（V2版）"""
        try:
            logger.info(f"[V2-STREAM] ストリーミングモード開始")
            # ストリーミング準備状態
            self._set_state_and_rebuild(LargePreviewState.PREPARING_STREAM)
            
            # ファイルIDを生成またはシステムから取得
            file_id = file_info.get('id', str(uuid.uuid4()))
            self._current_file_id = file_id
            
            # V2 PDFストリーミングサーバにPDFを登録
            logger.info(f"[V2-STREAM] serve_pdf_from_bytes_v2呼出開始")
            pdf_url, server = await serve_pdf_from_bytes_v2(blob_data, file_id)
            self._pdf_url = pdf_url
            logger.info(f"[V2-STREAM] URL生成完了: {pdf_url}")
            
            # PDF.js ビューア用データURI作成
            viewer_html = self._pdf_viewer_html.replace("{{PDF_URL}}", quote(pdf_url, safe=''))
            viewer_html_b64 = base64.b64encode(viewer_html.encode('utf-8')).decode('utf-8')
            viewer_url = f"data:text/html;base64,{viewer_html_b64}"
            
            # WebViewにビューア読み込み
            self.web_view.url = viewer_url
            self.current_file_info = file_info
            
            # ストリーミング表示準備完了
            self._set_state_and_rebuild(LargePreviewState.STREAM_READY)
            
            logger.info(f"[V2-STREAM] ストリーミングモード準備完了: {pdf_url}")
            
        except Exception as e:
            logger.error(f"[V2-STREAM] ストリーミングモードエラー: {e}")
            self._set_state_and_rebuild(LargePreviewState.ERROR, f"ストリーミング準備エラー: {str(e)}")

    async def _handle_data_url_mode(self, file_info: Dict[str, Any], blob_data: bytes):
        """data:URLモード処理"""
        try:
            logger.info(f"[V2-DATA] data:URLモード開始")
            
            # Base64エンコード
            pdf_base64 = base64.b64encode(blob_data).decode('utf-8')
            data_url = f"data:application/pdf;base64,{pdf_base64}"
            
            # WebViewに直接設定
            self.web_view.url = data_url
            self.current_file_info = file_info
            
            # 表示準備完了
            self._set_state_and_rebuild(LargePreviewState.DATA_URL_READY)
            
            logger.info(f"[V2-DATA] data:URLモード準備完了")
            
        except Exception as e:
            logger.error(f"[V2-DATA] data:URLモードエラー: {e}")
            self._set_state_and_rebuild(LargePreviewState.ERROR, f"data:URL準備エラー: {str(e)}")

    async def _handle_image_mode_v2(self, file_info: Dict[str, Any], blob_data: bytes):
        """画像モード処理（V2版）"""
        try:
            logger.info(f"[V2-IMAGE] 画像モード開始")
            self._set_state_and_rebuild(LargePreviewState.IMAGE_RENDERING)
            
            # 画像レンダラ初期化
            if self._image_renderer is None:
                self._image_renderer = PDFImageRenderer()
            
            # PDF読み込みと画像表示
            await self._image_renderer.load_pdf_data(blob_data)
            
            # 画像コンテナに追加
            self.image_container.content = self._image_renderer
            self.current_file_info = file_info
            
            # 画像表示準備完了
            self._set_state_and_rebuild(LargePreviewState.IMAGE_READY)
            
            logger.info(f"[V2-IMAGE] 画像モード準備完了")
            
        except Exception as e:
            logger.error(f"[V2-IMAGE] 画像モードエラー: {e}")
            self._set_state_and_rebuild(LargePreviewState.ERROR, f"画像レンダリングエラー: {str(e)}")

    def clear_preview(self):
        """プレビュークリア"""
        logger.info("[V2-CLEAR] プレビュークリア")
        self.current_file_info = None
        self._current_file_id = None
        self._pdf_url = None
        self.web_view.url = "about:blank"
        self.image_container.content = None
        if self._image_renderer:
            self._image_renderer.clear_pdf()
        self._set_state_and_rebuild(LargePreviewState.EMPTY)

    def _on_reload_click(self, e):
        """再読み込みボタンクリック"""
        if self.current_file_info:
            # Fletでの正しい非同期実行方法
            if hasattr(e, 'page') and e.page:
                e.page.run_task(self.load_pdf, self.current_file_info)
            elif hasattr(e, 'control') and hasattr(e.control, 'page') and e.control.page:
                e.control.page.run_task(self.load_pdf, self.current_file_info)

    def _on_image_mode_toggle(self, e):
        """画像モード切替ボタンクリック"""
        self._force_image_mode = not self._force_image_mode
        if self.current_file_info:
            # Fletでの正しい非同期実行方法
            if hasattr(e, 'page') and e.page:
                e.page.run_task(self.load_pdf, self.current_file_info)
            elif hasattr(e, 'control') and hasattr(e.control, 'page') and e.control.page:
                e.control.page.run_task(self.load_pdf, self.current_file_info)

    def _on_load_started(self, e):
        """WebView読み込み開始"""
        logger.debug("[V2-WEB] WebView読み込み開始")

    def _on_load_ended(self, e):
        """WebView読み込み完了"""
        logger.debug("[V2-WEB] WebView読み込み完了")

    def _on_load_error(self, e):
        """WebView読み込みエラー"""
        logger.error(f"[V2-WEB] WebView読み込みエラー: {e}")


def create_large_pdf_preview_v2() -> LargePDFPreviewV2:
    """大容量PDF対応プレビューコンポーネント作成（V2版）"""
    return LargePDFPreviewV2()
