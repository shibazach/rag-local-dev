#!/usr/bin/env python3
"""
大容量PDF対応プレビューコンポーネント
HTTPストリーミング + PDF.js + 画像フォールバック対応
"""

import flet as ft
from typing import Optional, Dict, Any, Callable
import base64
import asyncio
import uuid
import logging
from enum import Enum
from urllib.parse import quote
from app.services.file_service import get_file_service
from .pdf_stream_server import PDFStreamManager, serve_pdf_from_bytes
from .pdf_image_renderer import PDFImageRenderer

logger = logging.getLogger(__name__)


class LargePreviewState(Enum):
    """大容量PDFプレビューの状態"""
    EMPTY = "empty"              # ファイル未選択
    LOADING = "loading"          # PDF読み込み中
    PREPARING_STREAM = "prep"    # ストリーミング準備中
    STREAM_READY = "stream"      # ストリーミング表示準備完了
    IMAGE_MODE = "image"         # 画像レンダモード
    ERROR = "error"              # エラー状態


class PDFSizeThreshold:
    """PDFサイズ判定閾値"""
    SMALL_PDF = 1.5 * 1024 * 1024    # 1.5MB - data:URL方式
    LARGE_PDF = 20 * 1024 * 1024     # 20MB - HTTPストリーミング
    HUGE_PDF = 100 * 1024 * 1024     # 100MB - 画像レンダ推奨


class LargePDFPreview(ft.Container):
    """大容量PDF対応プレビューコンポーネント"""
    
    def __init__(self, file_path: Optional[str] = None):
        super().__init__()
        
        # 基本設定
        self.file_path = file_path
        self.current_file_info = None
        self.expand = True
        self.margin = ft.margin.all(4)
        self.file_service = get_file_service()
        
        # 状態管理
        self._state = LargePreviewState.EMPTY
        self._error_message = ""
        self._current_file_id = None
        self._pdf_url = None
        self._force_image_mode = False
        
        # PDF.js viewer HTML content
        self._pdf_viewer_html = self._create_pdf_viewer_html()
        
        # WebViewコンポーネント（PDF.js用）
        self.web_view = ft.WebView(
            url="about:blank",
            expand=True,
            on_page_started=self._on_load_started,
            on_page_ended=self._on_load_ended
        )
        
        # 画像表示用コンポーネント（フォールバック）
        self.image_view = ft.Image(
            src="",
            fit=ft.ImageFit.CONTAIN,
            expand=True
        )
        
        # 画像レンダラー（超大容量PDF用）
        self.image_renderer = PDFImageRenderer()
        
        # コントロールバー
        self.control_bar = self._create_control_bar()
        
        # 初期レイアウト構築
        self._rebuild_content()
    
    def _create_pdf_viewer_html(self) -> str:
        """PDF.js ビューア用HTML生成"""
        return """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PDF Viewer</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.min.js"></script>
    <style>
        body {
            margin: 0;
            padding: 0;
            font-family: Arial, sans-serif;
            background: #f0f0f0;
        }
        #container {
            width: 100%;
            height: 100vh;
            display: flex;
            flex-direction: column;
        }
        #toolbar {
            background: #333;
            color: white;
            padding: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 10px;
        }
        #pdfViewer {
            flex: 1;
            overflow: auto;
            background: #525659;
            display: flex;
            flex-direction: column;
            align-items: center;
            padding: 20px;
        }
        .page {
            margin: 10px 0;
            background: white;
            box-shadow: 0 2px 5px rgba(0,0,0,0.3);
        }
        button {
            background: #4CAF50;
            color: white;
            border: none;
            padding: 8px 16px;
            cursor: pointer;
            border-radius: 4px;
        }
        button:hover {
            background: #45a049;
        }
        button:disabled {
            background: #666;
            cursor: not-allowed;
        }
        #pageInfo {
            color: #ccc;
        }
    </style>
</head>
<body>
    <div id="container">
        <div id="toolbar">
            <button onclick="zoomOut()">−</button>
            <span id="zoomLevel">100%</span>
            <button onclick="zoomIn()">+</button>
            <span>|</span>
            <button onclick="prevPage()">◀</button>
            <span id="pageInfo">1 / 1</span>
            <button onclick="nextPage()">▶</button>
        </div>
        <div id="pdfViewer"></div>
    </div>

    <script>
        let pdfDoc = null;
        let currentPage = 1;
        let scale = 1.0;
        
        const pdfViewer = document.getElementById('pdfViewer');
        const pageInfo = document.getElementById('pageInfo');
        const zoomLevel = document.getElementById('zoomLevel');
        
        function getURLParam(name) {
            const urlParams = new URLSearchParams(window.location.search);
            return urlParams.get(name);
        }
        
        function updatePageInfo() {
            if (pdfDoc) {
                pageInfo.textContent = `${currentPage} / ${pdfDoc.numPages}`;
            }
        }
        
        function updateZoomLevel() {
            zoomLevel.textContent = Math.round(scale * 100) + '%';
        }
        
        function zoomIn() {
            scale = Math.min(scale * 1.25, 3.0);
            renderCurrentPage();
            updateZoomLevel();
        }
        
        function zoomOut() {
            scale = Math.max(scale / 1.25, 0.25);
            renderCurrentPage();
            updateZoomLevel();
        }
        
        function nextPage() {
            if (pdfDoc && currentPage < pdfDoc.numPages) {
                currentPage++;
                renderCurrentPage();
                updatePageInfo();
            }
        }
        
        function prevPage() {
            if (pdfDoc && currentPage > 1) {
                currentPage--;
                renderCurrentPage();
                updatePageInfo();
            }
        }
        
        async function renderCurrentPage() {
            if (!pdfDoc) return;
            
            try {
                const page = await pdfDoc.getPage(currentPage);
                const viewport = page.getViewport({ scale: scale });
                
                const canvas = document.createElement('canvas');
                const context = canvas.getContext('2d');
                canvas.height = viewport.height;
                canvas.width = viewport.width;
                canvas.className = 'page';
                
                const renderContext = {
                    canvasContext: context,
                    viewport: viewport
                };
                
                await page.render(renderContext).promise;
                
                pdfViewer.innerHTML = '';
                pdfViewer.appendChild(canvas);
                
            } catch (error) {
                console.error('Error rendering page:', error);
                pdfViewer.innerHTML = '<div style="color: red; text-align: center; padding: 50px;">Error rendering PDF page</div>';
            }
        }
        
        async function loadPDF() {
            const pdfUrl = getURLParam('file');
            if (!pdfUrl) {
                pdfViewer.innerHTML = '<div style="color: red; text-align: center; padding: 50px;">No PDF URL provided</div>';
                return;
            }
            
            try {
                pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';
                
                const loadingTask = pdfjsLib.getDocument({
                    url: decodeURIComponent(pdfUrl),
                    cMapUrl: 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/cmaps/',
                    cMapPacked: true
                });
                
                pdfDoc = await loadingTask.promise;
                
                currentPage = 1;
                updatePageInfo();
                updateZoomLevel();
                await renderCurrentPage();
                
            } catch (error) {
                console.error('Error loading PDF:', error);
                pdfViewer.innerHTML = '<div style="color: red; text-align: center; padding: 50px;">Error loading PDF: ' + error.message + '</div>';
            }
        }
        
        // Initialize
        loadPDF();
    </script>
</body>
</html>"""
    
    def _create_control_bar(self) -> ft.Container:
        """コントロールバー作成"""
        return ft.Container(
            content=ft.Row([
                ft.IconButton(
                    icon=ft.Icons.REFRESH,
                    tooltip="再読み込み",
                    on_click=self._on_reload_click
                ),
                ft.IconButton(
                    icon=ft.Icons.IMAGE,
                    tooltip="画像モード切替",
                    on_click=self._on_image_mode_toggle
                ),
                ft.Text("", expand=True),  # spacer
                ft.Text(
                    "",
                    size=12,
                    color=ft.Colors.GREY_600,
                    data="file_info"
                )
            ]),
            height=40,
            padding=ft.padding.symmetric(horizontal=8, vertical=4),
            bgcolor=ft.Colors.GREY_50,
            border=ft.border.only(bottom=ft.BorderSide(1, ft.Colors.GREY_300))
        )
    
    def _rebuild_content(self):
        """状態に応じてレイアウトを完全再構築"""
        # メインコンテンツエリア
        if self._state == LargePreviewState.STREAM_READY:
            main_content = self.web_view
        elif self._state == LargePreviewState.IMAGE_MODE:
            main_content = self.image_renderer
        else:
            main_content = ft.Container(expand=True, bgcolor=ft.Colors.WHITE)
        
        # オーバーレイ表示
        overlay_content = None
        if self._state == LargePreviewState.EMPTY:
            overlay_content = self._create_overlay_content(
                ft.Icons.PICTURE_AS_PDF, "ファイルを選択すると\n大容量PDF対応プレビューが表示されます"
            )
        elif self._state == LargePreviewState.LOADING:
            overlay_content = self._create_loading_overlay("PDFを分析中...")
        elif self._state == LargePreviewState.PREPARING_STREAM:
            overlay_content = self._create_loading_overlay("ストリーミング準備中...")
        elif self._state == LargePreviewState.ERROR:
            overlay_content = self._create_overlay_content(
                ft.Icons.ERROR, f"PDF表示エラー\n{self._error_message}", ft.Colors.RED
            )
        
        # スタック構成
        stack_controls = [main_content]
        if overlay_content:
            stack_controls.append(overlay_content)
        
        # レイアウト構築
        content_area = ft.Stack(stack_controls, expand=True)
        
        # コントロールバーの表示制御
        show_controls = self._state in [LargePreviewState.STREAM_READY, LargePreviewState.IMAGE_MODE]
        
        if show_controls:
            main_layout = ft.Column([
                self.control_bar,
                ft.Container(content=content_area, expand=True)
            ], spacing=0, expand=True)
        else:
            main_layout = content_area
        
        # パネル構造
        self.content = ft.Container(
            content=ft.Container(
                content=main_layout,
                border_radius=8,
                clip_behavior=ft.ClipBehavior.ANTI_ALIAS
            ),
            expand=True,
            bgcolor=ft.Colors.WHITE,
            border_radius=8,
            border=ft.border.all(1, ft.Colors.GREY_300)
        )
    
    def _create_overlay_content(self, icon: ft.Icons, text: str, color: str = ft.Colors.GREY_400) -> ft.Container:
        """オーバーレイコンテンツ作成"""
        return ft.Container(
            content=ft.Column([
                ft.Icon(icon, size=80, color=color),
                ft.Container(height=16),
                ft.Text(text, size=16, color=ft.Colors.GREY_600, text_align=ft.TextAlign.CENTER)
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, tight=True),
            alignment=ft.alignment.center,
            expand=True,
            bgcolor="#FFFFFF"
        )
    
    def _create_loading_overlay(self, message: str) -> ft.Container:
        """ローディングオーバーレイ"""
        return ft.Container(
            content=ft.Column([
                ft.ProgressRing(width=50, height=50),
                ft.Container(height=8),
                ft.Text(message, size=14, color=ft.Colors.GREY_600)
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, tight=True),
            alignment=ft.alignment.center,
            expand=True,
            bgcolor="#FFFFFF"
        )
    
    def _set_state_and_rebuild(self, new_state: LargePreviewState, error_message: str = ""):
        """状態変更とレイアウト再構築"""
        self._state = new_state
        self._error_message = error_message
        self._rebuild_content()
        try:
            self.update()
        except:
            pass
    
    def _update_file_info_display(self, file_info: Dict[str, Any], pdf_size: int):
        """ファイル情報表示更新"""
        try:
            file_name = file_info.get('file_name', 'unknown')
            size_mb = pdf_size / (1024 * 1024)
            
            # 表示モード判定
            if self._force_image_mode or pdf_size > PDFSizeThreshold.HUGE_PDF:
                mode = "画像"
            elif pdf_size > PDFSizeThreshold.LARGE_PDF:
                mode = "ストリーミング"
            else:
                mode = "標準"
                
            info_text = f"{file_name} ({size_mb:.1f}MB, {mode}モード)"
            
            # コントロールバー内のファイル情報を更新
            for control in self._find_controls_with_data(self.control_bar, "file_info"):
                if isinstance(control, ft.Text):
                    control.value = info_text
                    
        except Exception as e:
            logger.warning(f"ファイル情報表示更新エラー: {e}")
    
    def _find_controls_with_data(self, container, data_value):
        """指定されたdataを持つコントロールを再帰的に検索"""
        results = []
        if hasattr(container, 'data') and container.data == data_value:
            results.append(container)
        if hasattr(container, 'content'):
            if isinstance(container.content, list):
                for child in container.content:
                    results.extend(self._find_controls_with_data(child, data_value))
            elif container.content:
                results.extend(self._find_controls_with_data(container.content, data_value))
        if hasattr(container, 'controls'):
            for child in container.controls:
                results.extend(self._find_controls_with_data(child, data_value))
        return results
    
    async def load_pdf(self, file_info: Dict[str, Any]):
        """PDFを実際に読み込んで表示（サイズ適応版）"""
        if not file_info:
            self.show_empty_preview()
            return
        
        try:
            file_id = file_info.get('id', '')
            file_name = file_info.get('file_name', 'unknown')
            
            # 1. ローディング状態に変更
            self._set_state_and_rebuild(LargePreviewState.LOADING)
            
            # 2. ファイルデータを取得
            file_data = self.file_service.get_file_info(file_id)
            
            if file_data and file_data.get('blob_data'):
                blob_data = file_data['blob_data']
                pdf_size = len(blob_data)
                
                logger.info(f"PDF読み込み開始: {file_name} ({pdf_size} bytes)")
                
                # 3. サイズに応じて表示方法を決定
                await self._handle_pdf_by_size(file_info, blob_data, pdf_size)
                
            else:
                # エラー状態に変更
                self._set_state_and_rebuild(LargePreviewState.ERROR, f"PDFデータを取得できませんでした: {file_name}")
                
        except Exception as e:
            logger.error(f"PDF読み込みエラー: {e}")
            self._set_state_and_rebuild(LargePreviewState.ERROR, f"PDF読み込みエラー: {str(e)}")
    
    async def _handle_pdf_by_size(self, file_info: Dict[str, Any], blob_data: bytes, pdf_size: int):
        """サイズに応じたPDF処理"""
        try:
            file_name = file_info.get('file_name', 'unknown')
            
            # サイズ判定とファイル情報表示更新
            self._update_file_info_display(file_info, pdf_size)
            
            if self._force_image_mode or pdf_size > PDFSizeThreshold.HUGE_PDF:
                # 超大容量または強制画像モード -> 画像レンダリング
                await self._handle_image_rendering(file_info, blob_data)
                
            elif pdf_size > PDFSizeThreshold.SMALL_PDF:
                # 大容量 -> HTTPストリーミング
                await self._handle_streaming_mode(file_info, blob_data)
                
            else:
                # 小容量 -> data:URL方式（従来通り）
                await self._handle_data_url_mode(file_info, blob_data)
                
        except Exception as e:
            logger.error(f"PDFサイズ処理エラー: {e}")
            self._set_state_and_rebuild(LargePreviewState.ERROR, f"PDF処理エラー: {str(e)}")
    
    async def _handle_streaming_mode(self, file_info: Dict[str, Any], blob_data: bytes):
        """HTTPストリーミングモード処理"""
        try:
            # ストリーミング準備状態
            self._set_state_and_rebuild(LargePreviewState.PREPARING_STREAM)
            
            # ファイルIDを生成またはシステムから取得
            file_id = file_info.get('id', str(uuid.uuid4()))
            self._current_file_id = file_id
            
            # PDFストリーミングサーバにPDFを登録
            pdf_url, server = await serve_pdf_from_bytes(blob_data, file_id)
            self._pdf_url = pdf_url
            
            # PDF.js ビューア用データURI作成
            viewer_html_b64 = base64.b64encode(self._pdf_viewer_html.encode('utf-8')).decode('utf-8')
            viewer_url = f"data:text/html;base64,{viewer_html_b64}?file={quote(pdf_url, safe='')}"
            
            # WebViewにビューア読み込み
            self.web_view.url = viewer_url
            self.current_file_info = file_info
            
            # ストリーミング表示準備完了
            self._set_state_and_rebuild(LargePreviewState.STREAM_READY)
            
            logger.info(f"ストリーミングモード準備完了: {pdf_url}")
            
        except Exception as e:
            logger.error(f"ストリーミングモードエラー: {e}")
            self._set_state_and_rebuild(LargePreviewState.ERROR, f"ストリーミング準備エラー: {str(e)}")
    
    async def _handle_data_url_mode(self, file_info: Dict[str, Any], blob_data: bytes):
        """data:URLモード処理（従来の小容量向け）"""
        try:
            # Base64エンコード
            pdf_base64 = base64.b64encode(blob_data).decode('utf-8')
            pdf_url = f'data:application/pdf;base64,{pdf_base64}'
            
            # WebViewにPDF URL設定
            self.web_view.url = pdf_url
            self.current_file_info = file_info
            
            # ストリーミング表示状態に設定（UIは同じ）
            self._set_state_and_rebuild(LargePreviewState.STREAM_READY)
            
            logger.info(f"data:URLモード準備完了")
            
        except Exception as e:
            logger.error(f"data:URLモードエラー: {e}")
            self._set_state_and_rebuild(LargePreviewState.ERROR, f"PDF表示エラー: {str(e)}")
    
    async def _handle_image_rendering(self, file_info: Dict[str, Any], blob_data: bytes):
        """画像レンダリングモード処理"""
        try:
            # 画像レンダラーでPDFを読み込み
            await self.image_renderer.load_pdf(file_info, blob_data)
            
            # 画像モード状態に設定
            self.current_file_info = file_info
            self._set_state_and_rebuild(LargePreviewState.IMAGE_MODE)
            
            logger.info(f"画像レンダリングモード準備完了")
            
        except Exception as e:
            logger.error(f"画像レンダリングエラー: {e}")
            self._set_state_and_rebuild(LargePreviewState.ERROR, f"画像レンダリングエラー: {str(e)}")
    
    def _on_reload_click(self, e):
        """再読み込みボタンクリック"""
        if self.current_file_info:
            asyncio.create_task(self.load_pdf(self.current_file_info))
    
    def _on_image_mode_toggle(self, e):
        """画像モード切替ボタンクリック"""
        self._force_image_mode = not self._force_image_mode
        if self.current_file_info:
            # Fletでの正しい非同期実行方法
            if hasattr(e, 'page') and e.page:
                e.page.run_task(self.load_pdf, self.current_file_info)
            elif hasattr(e, 'control') and hasattr(e.control, 'page') and e.control.page:
                e.control.page.run_task(self.load_pdf, self.current_file_info)
            else:
                # フォールバック
                import threading
                threading.Thread(target=lambda: asyncio.run(self.load_pdf(self.current_file_info))).start()
    
    def _on_load_started(self, e):
        """WebView読み込み開始"""
        logger.debug("WebView読み込み開始")
    
    def _on_load_ended(self, e):
        """WebView読み込み完了"""
        logger.debug("WebView読み込み完了")
    
    def show_pdf_preview(self, file_info):
        """PDFプレビュー表示（同期インターフェース）"""
        if file_info:
            try:
                loop = asyncio.get_event_loop()
                loop.create_task(self.load_pdf(file_info))
            except RuntimeError:
                asyncio.run(self.load_pdf(file_info))
        else:
            self.show_empty_preview()
    
    def show_empty_preview(self):
        """空のプレビュー表示"""
        self.current_file_info = None
        self.file_path = None
        self.web_view.url = "about:blank"
        self._current_file_id = None
        self._pdf_url = None
        
        # 画像レンダラーもリセット
        if self.image_renderer:
            self.image_renderer.show_empty_preview()
        
        self._set_state_and_rebuild(LargePreviewState.EMPTY)
    
    def cleanup(self):
        """リソース整理"""
        try:
            if self._current_file_id:
                # PDFストリーミングサーバからPDFを削除
                asyncio.create_task(self._cleanup_pdf_resources())
            
            # 画像レンダラーのクリーンアップ
            if self.image_renderer:
                self.image_renderer.cleanup()
                
        except Exception as e:
            logger.warning(f"クリーンアップエラー: {e}")
    
    async def _cleanup_pdf_resources(self):
        """PDF関連リソース整理"""
        try:
            if self._current_file_id:
                server = await PDFStreamManager.get_instance()
                server.unregister_pdf(self._current_file_id)
                self._current_file_id = None
                self._pdf_url = None
        except Exception as e:
            logger.warning(f"PDFリソース整理エラー: {e}")


def create_large_pdf_preview(file_path: Optional[str] = None) -> LargePDFPreview:
    """大容量PDF対応プレビュー作成関数"""
    return LargePDFPreview(file_path)
