#!/usr/bin/env python3
"""
PDF画像レンダリングコンポーネント
超大容量PDF対応・低メモリ環境向けフォールバック
"""

import flet as ft
from typing import Optional, Dict, Any, List
import base64
import asyncio
import io
import logging
from enum import Enum
from concurrent.futures import ThreadPoolExecutor
import tempfile
import os

logger = logging.getLogger(__name__)

# PDF処理ライブラリのインポート（優先順位付き）
PDF_LIBRARY = None
try:
    import pypdfium2 as pdfium
    PDF_LIBRARY = "pypdfium2"
    logger.info("Using pypdfium2 for PDF rendering")
except ImportError:
    try:
        import fitz  # PyMuPDF
        PDF_LIBRARY = "pymupdf"
        logger.info("Using PyMuPDF for PDF rendering")
    except ImportError:
        try:
            from pdf2image import convert_from_bytes
            PDF_LIBRARY = "pdf2image"
            logger.info("Using pdf2image for PDF rendering")
        except ImportError:
            logger.warning("No PDF rendering library available. Install pypdfium2, PyMuPDF, or pdf2image")
            PDF_LIBRARY = None


class ImageRendererState(Enum):
    """画像レンダラーの状態"""
    EMPTY = "empty"
    LOADING = "loading"
    RENDERING = "rendering"
    READY = "ready"
    ERROR = "error"


class PDFImageRenderer(ft.Container):
    """PDF画像レンダリング表示コンポーネント"""
    
    def __init__(self, file_path: Optional[str] = None):
        super().__init__()
        
        # 基本設定
        self.file_path = file_path
        self.current_file_info = None
        self.expand = True
        self.margin = ft.margin.all(4)
        
        # レンダリング設定
        self.scale = 1.5  # デフォルトスケール
        self.current_page = 1
        self.total_pages = 0
        self.rendered_pages: Dict[int, str] = {}  # page_num -> base64_image
        self.cache_limit = 10  # 同時キャッシュページ数
        
        # 状態管理
        self._state = ImageRendererState.EMPTY
        self._error_message = ""
        self._pdf_data = None
        
        # スレッドプール（レンダリング用）
        self._executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="pdf_render")
        
        # UI コンポーネント
        self.image_display = ft.Image(
            src="",
            fit=ft.ImageFit.CONTAIN,
            expand=True
        )
        
        self.navigation_bar = self._create_navigation_bar()
        self.control_bar = self._create_control_bar()
        
        # 初期レイアウト構築
        self._rebuild_content()
    
    def _create_navigation_bar(self) -> ft.Container:
        """ページナビゲーションバー作成"""
        return ft.Container(
            content=ft.Row([
                ft.IconButton(
                    icon=ft.Icons.FIRST_PAGE,
                    tooltip="最初のページ",
                    on_click=self._on_first_page
                ),
                ft.IconButton(
                    icon=ft.Icons.CHEVRON_LEFT,
                    tooltip="前のページ",
                    on_click=self._on_prev_page
                ),
                ft.TextField(
                    value="1",
                    width=60,
                    text_align=ft.TextAlign.CENTER,
                    keyboard_type=ft.KeyboardType.NUMBER,
                    on_submit=self._on_page_input,
                    data="page_input"
                ),
                ft.Text("/", color=ft.Colors.GREY_600),
                ft.Text("1", color=ft.Colors.GREY_600, data="total_pages"),
                ft.IconButton(
                    icon=ft.Icons.CHEVRON_RIGHT,
                    tooltip="次のページ",
                    on_click=self._on_next_page
                ),
                ft.IconButton(
                    icon=ft.Icons.LAST_PAGE,
                    tooltip="最後のページ",
                    on_click=self._on_last_page
                ),
            ], alignment=ft.MainAxisAlignment.CENTER),
            height=50,
            padding=ft.padding.symmetric(horizontal=8, vertical=4),
            bgcolor=ft.Colors.GREY_100,
        )
    
    def _create_control_bar(self) -> ft.Container:
        """コントロールバー作成"""
        return ft.Container(
            content=ft.Row([
                ft.IconButton(
                    icon=ft.Icons.ZOOM_OUT,
                    tooltip="縮小",
                    on_click=self._on_zoom_out
                ),
                ft.Text("150%", size=12, color=ft.Colors.GREY_600, data="zoom_level"),
                ft.IconButton(
                    icon=ft.Icons.ZOOM_IN,
                    tooltip="拡大",
                    on_click=self._on_zoom_in
                ),
                ft.VerticalDivider(width=1),
                ft.IconButton(
                    icon=ft.Icons.REFRESH,
                    tooltip="再レンダリング",
                    on_click=self._on_refresh
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
        if self._state == ImageRendererState.READY:
            main_content = self.image_display
        else:
            main_content = ft.Container(expand=True, bgcolor=ft.Colors.WHITE)
        
        # オーバーレイ表示
        overlay_content = None
        if self._state == ImageRendererState.EMPTY:
            overlay_content = self._create_overlay_content(
                ft.Icons.IMAGE, "PDFを画像として表示します\n処理に時間がかかる場合があります"
            )
        elif self._state == ImageRendererState.LOADING:
            overlay_content = self._create_loading_overlay("PDFを読み込み中...")
        elif self._state == ImageRendererState.RENDERING:
            overlay_content = self._create_loading_overlay(f"ページ {self.current_page} をレンダリング中...")
        elif self._state == ImageRendererState.ERROR:
            overlay_content = self._create_overlay_content(
                ft.Icons.ERROR, f"レンダリングエラー\n{self._error_message}", ft.Colors.RED
            )
        
        # スタック構成
        stack_controls = [main_content]
        if overlay_content:
            stack_controls.append(overlay_content)
        
        content_area = ft.Stack(stack_controls, expand=True)
        
        # コントロールバーの表示制御
        show_controls = self._state == ImageRendererState.READY
        
        if show_controls:
            main_layout = ft.Column([
                self.control_bar,
                self.navigation_bar,
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
    
    def _set_state_and_rebuild(self, new_state: ImageRendererState, error_message: str = ""):
        """状態変更とレイアウト再構築"""
        self._state = new_state
        self._error_message = error_message
        self._rebuild_content()
        try:
            self.update()
        except:
            pass
    
    def _update_ui_controls(self):
        """UI コントロール更新"""
        try:
            # ページ情報更新
            for control in self._find_controls_with_data(self.navigation_bar, "page_input"):
                if isinstance(control, ft.TextField):
                    control.value = str(self.current_page)
            
            for control in self._find_controls_with_data(self.navigation_bar, "total_pages"):
                if isinstance(control, ft.Text):
                    control.value = str(self.total_pages)
            
            # ズームレベル更新
            zoom_percent = int(self.scale * 100)
            for control in self._find_controls_with_data(self.control_bar, "zoom_level"):
                if isinstance(control, ft.Text):
                    control.value = f"{zoom_percent}%"
            
            # ファイル情報更新
            if self.current_file_info:
                file_name = self.current_file_info.get('file_name', 'unknown')
                info_text = f"{file_name} (画像レンダリングモード)"
                for control in self._find_controls_with_data(self.control_bar, "file_info"):
                    if isinstance(control, ft.Text):
                        control.value = info_text
        except Exception as e:
            logger.warning(f"UI更新エラー: {e}")
    
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
    
    async def load_pdf(self, file_info: Dict[str, Any], pdf_data: bytes):
        """PDFデータから画像レンダリング開始"""
        if not pdf_data:
            self.show_empty_preview()
            return
        
        try:
            self.current_file_info = file_info
            self._pdf_data = pdf_data
            
            # ローディング状態
            self._set_state_and_rebuild(ImageRendererState.LOADING)
            
            # PDF情報取得
            await self._analyze_pdf()
            
            if self.total_pages > 0:
                self.current_page = 1
                await self._render_current_page()
            else:
                self._set_state_and_rebuild(ImageRendererState.ERROR, "PDFページが見つかりません")
                
        except Exception as e:
            logger.error(f"PDF読み込みエラー: {e}")
            self._set_state_and_rebuild(ImageRendererState.ERROR, f"PDF読み込みエラー: {str(e)}")
    
    async def _analyze_pdf(self):
        """PDF分析（ページ数取得）"""
        if PDF_LIBRARY is None:
            raise Exception("PDF処理ライブラリがインストールされていません")
        
        def _get_page_count():
            if PDF_LIBRARY == "pypdfium2":
                pdf = pdfium.PdfDocument(self._pdf_data)
                return len(pdf)
            elif PDF_LIBRARY == "pymupdf":
                bio = io.BytesIO(self._pdf_data)
                pdf = fitz.open(stream=bio, filetype="pdf")
                count = pdf.page_count
                pdf.close()
                return count
            elif PDF_LIBRARY == "pdf2image":
                # pdf2imageの場合、実際に変換しないとページ数がわからない
                # 一時的に最初のページのみ変換してページ数推定
                try:
                    images = convert_from_bytes(self._pdf_data, first_page=1, last_page=1)
                    # より正確なページ数取得のため、PyPDF2を使用
                    import PyPDF2
                    pdf_reader = PyPDF2.PdfReader(io.BytesIO(self._pdf_data))
                    return len(pdf_reader.pages)
                except:
                    return 1  # フォールバック
            else:
                raise Exception("サポートされていないPDF処理ライブラリ")
        
        # 別スレッドで実行
        loop = asyncio.get_event_loop()
        self.total_pages = await loop.run_in_executor(self._executor, _get_page_count)
        logger.info(f"PDF分析完了: {self.total_pages} ページ")
    
    async def _render_current_page(self):
        """現在ページのレンダリング"""
        if self.current_page in self.rendered_pages:
            # キャッシュされている場合
            self._display_cached_page()
            return
        
        try:
            # レンダリング状態
            self._set_state_and_rebuild(ImageRendererState.RENDERING)
            
            # 別スレッドでレンダリング実行
            loop = asyncio.get_event_loop()
            image_base64 = await loop.run_in_executor(
                self._executor, 
                self._render_page, 
                self.current_page
            )
            
            # キャッシュに保存
            self.rendered_pages[self.current_page] = image_base64
            self._cleanup_cache()
            
            # 画像表示
            self.image_display.src = f"data:image/png;base64,{image_base64}"
            
            # UI更新
            self._update_ui_controls()
            self._set_state_and_rebuild(ImageRendererState.READY)
            
        except Exception as e:
            logger.error(f"ページレンダリングエラー: {e}")
            self._set_state_and_rebuild(ImageRendererState.ERROR, f"レンダリングエラー: {str(e)}")
    
    def _render_page(self, page_num: int) -> str:
        """指定ページをPNG画像にレンダリング（同期処理）"""
        if PDF_LIBRARY == "pypdfium2":
            return self._render_with_pypdfium2(page_num)
        elif PDF_LIBRARY == "pymupdf":
            return self._render_with_pymupdf(page_num)
        elif PDF_LIBRARY == "pdf2image":
            return self._render_with_pdf2image(page_num)
        else:
            raise Exception("PDF処理ライブラリが利用できません")
    
    def _render_with_pypdfium2(self, page_num: int) -> str:
        """pypdfium2でレンダリング"""
        pdf = pdfium.PdfDocument(self._pdf_data)
        page = pdf[page_num - 1]  # 0ベースインデックス
        bitmap = page.render(scale=self.scale).to_pil()
        
        # PNG形式でBase64エンコード
        buffer = io.BytesIO()
        bitmap.save(buffer, format="PNG")
        return base64.b64encode(buffer.getvalue()).decode('utf-8')
    
    def _render_with_pymupdf(self, page_num: int) -> str:
        """PyMuPDFでレンダリング"""
        bio = io.BytesIO(self._pdf_data)
        pdf = fitz.open(stream=bio, filetype="pdf")
        page = pdf[page_num - 1]  # 0ベースインデックス
        
        # レンダリング設定
        mat = fitz.Matrix(self.scale, self.scale)
        pix = page.get_pixmap(matrix=mat)
        
        # PNG形式でBase64エンコード
        png_data = pix.pil_tobytes(format="PNG")
        pdf.close()
        
        return base64.b64encode(png_data).decode('utf-8')
    
    def _render_with_pdf2image(self, page_num: int) -> str:
        """pdf2imageでレンダリング"""
        dpi = int(72 * self.scale)  # スケールをDPIに変換
        images = convert_from_bytes(
            self._pdf_data, 
            first_page=page_num, 
            last_page=page_num,
            dpi=dpi
        )
        
        if not images:
            raise Exception(f"ページ {page_num} のレンダリングに失敗")
        
        # PNG形式でBase64エンコード
        buffer = io.BytesIO()
        images[0].save(buffer, format="PNG")
        return base64.b64encode(buffer.getvalue()).decode('utf-8')
    
    def _display_cached_page(self):
        """キャッシュされたページを表示"""
        if self.current_page in self.rendered_pages:
            image_base64 = self.rendered_pages[self.current_page]
            self.image_display.src = f"data:image/png;base64,{image_base64}"
            self._update_ui_controls()
            self._set_state_and_rebuild(ImageRendererState.READY)
    
    def _cleanup_cache(self):
        """キャッシュクリーンアップ（LRU的な処理）"""
        if len(self.rendered_pages) > self.cache_limit:
            # 現在のページから遠いページを削除
            pages_to_keep = set()
            for offset in range(-(self.cache_limit // 2), (self.cache_limit // 2) + 1):
                page = self.current_page + offset
                if 1 <= page <= self.total_pages:
                    pages_to_keep.add(page)
            
            pages_to_remove = [p for p in self.rendered_pages.keys() if p not in pages_to_keep]
            for page in pages_to_remove:
                del self.rendered_pages[page]
    
    # イベントハンドラー
    def _on_first_page(self, e):
        """最初のページへ"""
        if self.current_page != 1:
            self.current_page = 1
            asyncio.create_task(self._render_current_page())
    
    def _on_prev_page(self, e):
        """前のページへ"""
        if self.current_page > 1:
            self.current_page -= 1
            # Fletでの正しい非同期実行
            if hasattr(e, 'page') and e.page:
                e.page.run_task(self._render_current_page)
            elif hasattr(e, 'control') and hasattr(e.control, 'page') and e.control.page:
                e.control.page.run_task(self._render_current_page)
            else:
                import threading
                threading.Thread(target=lambda: asyncio.run(self._render_current_page())).start()
    
    def _on_next_page(self, e):
        """次のページへ"""
        if self.current_page < self.total_pages:
            self.current_page += 1
            # Fletでの正しい非同期実行
            if hasattr(e, 'page') and e.page:
                e.page.run_task(self._render_current_page)
            elif hasattr(e, 'control') and hasattr(e.control, 'page') and e.control.page:
                e.control.page.run_task(self._render_current_page)
            else:
                import threading
                threading.Thread(target=lambda: asyncio.run(self._render_current_page())).start()
    
    def _on_last_page(self, e):
        """最後のページへ"""
        if self.current_page != self.total_pages:
            self.current_page = self.total_pages
            asyncio.create_task(self._render_current_page())
    
    def _on_page_input(self, e):
        """ページ番号入力"""
        try:
            page_num = int(e.control.value)
            if 1 <= page_num <= self.total_pages:
                self.current_page = page_num
                asyncio.create_task(self._render_current_page())
            else:
                e.control.value = str(self.current_page)
                self.update()
        except ValueError:
            e.control.value = str(self.current_page)
            self.update()
    
    def _on_zoom_in(self, e):
        """拡大"""
        self.scale = min(self.scale * 1.25, 3.0)
        self.rendered_pages.clear()  # キャッシュクリア
        asyncio.create_task(self._render_current_page())
    
    def _on_zoom_out(self, e):
        """縮小"""
        self.scale = max(self.scale / 1.25, 0.5)
        self.rendered_pages.clear()  # キャッシュクリア
        asyncio.create_task(self._render_current_page())
    
    def _on_refresh(self, e):
        """再レンダリング"""
        self.rendered_pages.clear()  # キャッシュクリア
        if self._pdf_data:
            asyncio.create_task(self._render_current_page())
    
    def show_pdf_preview(self, file_info: Dict[str, Any], pdf_data: bytes):
        """PDFプレビュー表示（外部インターフェース）"""
        asyncio.create_task(self.load_pdf(file_info, pdf_data))
    
    def show_empty_preview(self):
        """空のプレビュー表示"""
        self.current_file_info = None
        self._pdf_data = None
        self.current_page = 1
        self.total_pages = 0
        self.rendered_pages.clear()
        self.image_display.src = ""
        self._set_state_and_rebuild(ImageRendererState.EMPTY)
    
    def cleanup(self):
        """リソース整理"""
        try:
            self.rendered_pages.clear()
            if self._executor:
                self._executor.shutdown(wait=False)
        except Exception as e:
            logger.warning(f"クリーンアップエラー: {e}")


def create_pdf_image_renderer(file_path: Optional[str] = None) -> PDFImageRenderer:
    """PDF画像レンダラー作成関数"""
    return PDFImageRenderer(file_path)
