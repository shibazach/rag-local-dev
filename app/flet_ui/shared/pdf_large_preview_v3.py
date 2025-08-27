#!/usr/bin/env python3
"""
大容量PDF対応プレビューコンポーネント（V3専用版）
完全HTTP統一方式・シンプル実装・実用優先

主要機能:
- V3サーバー専用（完全HTTP統一）
- data:URL完全廃止（WebView制限対応）
- 大容量PDFストリーミング表示
- 必要最小限のUI（実用重視）
- エラーハンドリング強化
"""

import flet as ft
import asyncio
import uuid
import logging
from typing import Dict, Any, Optional
from enum import Enum

# V3サーバーインポート
from .pdf_stream_server_v3 import PDFStreamManagerV3, serve_pdf_from_bytes_v3

logger = logging.getLogger(__name__)


class PreviewState(Enum):
    """プレビュー状態（シンプル版）"""
    EMPTY = "empty"
    LOADING = "loading" 
    STREAMING = "streaming"
    READY = "ready"
    ERROR = "error"


class LargePDFPreviewV3(ft.Container):
    """大容量PDF対応プレビューコンポーネント（V3専用・シンプル版）"""
    
    def __init__(self):
        super().__init__()
        
        # 状態管理
        self.state = PreviewState.EMPTY
        self.current_file_info: Optional[Dict[str, Any]] = None
        self.current_file_id: Optional[str] = None
        self.error_message = ""
        
        # UI要素初期化
        self._init_ui()
        
        # 初期レイアウト
        self._build_layout()

    def _init_ui(self):
        """UI要素初期化（最小構成）"""
        
        # WebView（HTTPストリーミング専用）
        self.web_view = ft.WebView(
            url="about:blank",
            expand=True,
            on_page_started=self._on_page_started,
            on_page_ended=self._on_page_ended,
            on_web_resource_error=self._on_page_error
        )
        
        # ステータス表示
        self.status_text = ft.Text(
            "PDFファイルを選択してください",
            size=14,
            color=ft.Colors.GREY_600,
            text_align=ft.TextAlign.CENTER
        )
        
        # コントロールボタン（最小限）
        self.reload_button = ft.ElevatedButton(
            text="🔄 再読み込み",
            on_click=self._on_reload,
            height=32,
            disabled=True
        )
        
        self.clear_button = ft.ElevatedButton(
            text="🗑️ クリア",
            on_click=self._on_clear,
            height=32
        )

    def _build_layout(self):
        """レイアウト構築（シンプル構成）"""
        
        # コントロールバー
        control_bar = ft.Row(
            controls=[
                self.reload_button,
                self.clear_button,
                ft.Container(expand=True),  # スペーサー
                self.status_text
            ],
            height=40,
            spacing=8
        )
        
        # メイン表示エリア
        main_area = ft.Stack(
            controls=[
                # WebView（バックグラウンド）
                self.web_view,
                # オーバーレイ（状態表示）
                ft.Container(
                    content=self._build_overlay(),
                    expand=True,
                    bgcolor=ft.Colors.with_opacity(0.9, ft.Colors.WHITE),
                    alignment=ft.alignment.center,
                    visible=True  # 初期状態は表示
                )
            ],
            expand=True
        )
        
        # 全体レイアウト
        self.content = ft.Column(
            controls=[
                ft.Container(
                    content=control_bar,
                    padding=ft.padding.all(8),
                    bgcolor=ft.Colors.GREY_50,
                    border=ft.border.only(bottom=ft.BorderSide(1, ft.Colors.GREY_300))
                ),
                main_area
            ],
            expand=True,
            spacing=0
        )
        
        # 外枠
        self.border = ft.border.all(1, ft.Colors.GREY_300)
        self.border_radius = 8
        self.expand = True

    def _build_overlay(self) -> ft.Control:
        """状態別オーバーレイ構築"""
        
        if self.state == PreviewState.EMPTY:
            return ft.Column(
                controls=[
                    ft.Icon(ft.Icons.PICTURE_AS_PDF, size=80, color=ft.Colors.GREY_400),
                    ft.Container(height=16),
                    ft.Text(
                        "V3版 大容量PDFプレビュー\n完全HTTP統一方式",
                        size=16,
                        color=ft.Colors.GREY_600,
                        text_align=ft.TextAlign.CENTER
                    )
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=0
            )
            
        elif self.state == PreviewState.LOADING:
            return ft.Column(
                controls=[
                    ft.ProgressRing(width=50, height=50),
                    ft.Container(height=16),
                    ft.Text("PDF読み込み中...", size=14, color=ft.Colors.BLUE_700)
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=0
            )
            
        elif self.state == PreviewState.STREAMING:
            return ft.Column(
                controls=[
                    ft.ProgressRing(width=50, height=50),
                    ft.Container(height=16),
                    ft.Text("ストリーミング準備中...", size=14, color=ft.Colors.GREEN_700)
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=0
            )
            
        elif self.state == PreviewState.ERROR:
            return ft.Column(
                controls=[
                    ft.Icon(ft.Icons.ERROR, size=64, color=ft.Colors.RED_400),
                    ft.Container(height=16),
                    ft.Text(
                        f"エラーが発生しました\n{self.error_message}",
                        size=14,
                        color=ft.Colors.RED_700,
                        text_align=ft.TextAlign.CENTER
                    )
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=0
            )
            
        # PreviewState.READYの場合はオーバーレイ非表示
        return ft.Container()

    def _update_ui(self):
        """UI更新（状態に応じた表示変更）"""
        
        # オーバーレイの表示/非表示
        if hasattr(self.content, 'controls') and len(self.content.controls) >= 2:
            main_area = self.content.controls[1]  # Stack
            if hasattr(main_area, 'controls') and len(main_area.controls) >= 2:
                overlay = main_area.controls[1]  # オーバーレイContainer
                
                if self.state == PreviewState.READY:
                    overlay.visible = False
                    self.web_view.visible = True
                else:
                    overlay.visible = True
                    overlay.content = self._build_overlay()
                    self.web_view.visible = False
        
        # ステータステキスト更新
        if self.current_file_info:
            file_name = self.current_file_info.get('file_name', 'unknown')
            self.status_text.value = f"📄 {file_name}"
        else:
            self.status_text.value = "PDFファイルを選択してください"
        
        # ボタン状態更新
        self.reload_button.disabled = (self.state == PreviewState.EMPTY)
        
        # UI更新
        try:
            self.update()
        except Exception as e:
            logger.warning(f"[V3-UI] UI更新エラー: {e}")

    def _set_state(self, new_state: PreviewState, error_msg: str = ""):
        """状態変更"""
        self.state = new_state
        self.error_message = error_msg
        logger.info(f"[V3-UI] 状態変更: {new_state.value}")
        self._update_ui()

    # ==================== 公開API ====================
    
    async def load_pdf(self, file_info: Dict[str, Any], blob_data: Optional[bytes] = None):
        """PDF読み込みメイン処理（V3版）"""
        try:
            logger.info(f"[V3-UI] PDF読み込み開始: {file_info}")
            self._set_state(PreviewState.LOADING)
            self.current_file_info = file_info
            
            # DBからblob_dataを取得（必要な場合）
            if blob_data is None:
                blob_data = await self._fetch_blob_data(file_info)
            
            pdf_size = len(blob_data)
            logger.info(f"[V3-UI] PDF読み込み: サイズ={pdf_size}bytes")
            
            # V3サーバーでHTTPストリーミング処理
            await self._handle_streaming_v3(file_info, blob_data)
            
        except Exception as e:
            logger.error(f"[V3-UI] PDF読み込みエラー: {e}")
            self._set_state(PreviewState.ERROR, str(e))

    async def _fetch_blob_data(self, file_info: Dict[str, Any]) -> bytes:
        """DBからblob_data取得"""
        from app.core.db_simple import fetch_one
        
        blob_id = file_info.get('blob_id', file_info.get('id'))
        if not blob_id:
            raise ValueError("blob_idが見つかりません")
        
        result = fetch_one(
            "SELECT blob_data FROM files_blob WHERE id = %s",
            (blob_id,)
        )
        
        if not result or 'blob_data' not in result:
            raise ValueError(f"PDFデータが見つかりません: blob_id={blob_id}")
        
        return result['blob_data']

    async def _handle_streaming_v3(self, file_info: Dict[str, Any], blob_data: bytes):
        """V3ストリーミング処理（完全HTTP統一）"""
        try:
            logger.info("[V3-UI] ストリーミング処理開始")
            self._set_state(PreviewState.STREAMING)
            
            # ファイルID生成
            file_id = file_info.get('id', str(uuid.uuid4()))
            self.current_file_id = file_id
            
            # V3サーバーにPDF登録
            logger.info("[V3-UI] V3サーバーでPDF登録...")
            pdf_url, server = await serve_pdf_from_bytes_v3(blob_data, file_id)
            logger.info(f"[V3-UI] PDF URL: {pdf_url}")
            
            # ビューアURL生成（V3の主要機能）
            viewer_url = server.get_viewer_url(pdf_url)
            logger.info(f"[V3-UI] Viewer URL: {viewer_url}")
            
            # WebViewにビューア読み込み（完全HTTP統一）
            self.web_view.url = viewer_url
            
            # 表示準備完了
            self._set_state(PreviewState.READY)
            logger.info("[V3-UI] ストリーミング表示準備完了")
            
        except Exception as e:
            logger.error(f"[V3-UI] ストリーミング処理エラー: {e}")
            self._set_state(PreviewState.ERROR, f"ストリーミング処理エラー: {str(e)}")

    def clear_preview(self):
        """プレビュークリア"""
        logger.info("[V3-UI] プレビュークリア")
        
        # V3サーバーからPDF登録解除
        if self.current_file_id:
            try:
                server = PDFStreamManagerV3.get_instance_sync()
                server.unregister_pdf(self.current_file_id)
                logger.info(f"[V3-UI] PDF登録解除: {self.current_file_id}")
            except Exception as e:
                logger.warning(f"[V3-UI] PDF登録解除エラー: {e}")
        
        # 状態リセット
        self.current_file_info = None
        self.current_file_id = None
        self.web_view.url = "about:blank"
        self._set_state(PreviewState.EMPTY)

    # ==================== イベントハンドラ ====================
    
    def _on_reload(self, e):
        """再読み込みボタン"""
        if self.current_file_info:
            if hasattr(e, 'page') and e.page:
                e.page.run_task(self.load_pdf, self.current_file_info)
            else:
                logger.warning("[V3-UI] page.run_task が利用できません")

    def _on_clear(self, e):
        """クリアボタン"""
        self.clear_preview()

    def _on_page_started(self, e):
        """WebView読み込み開始"""
        logger.debug("[V3-UI] WebView読み込み開始")

    def _on_page_ended(self, e):
        """WebView読み込み完了"""
        logger.info("[V3-UI] WebView読み込み完了")

    def _on_page_error(self, e):
        """WebView読み込みエラー"""
        logger.error(f"[V3-UI] WebView読み込みエラー: {e}")
        self._set_state(PreviewState.ERROR, f"WebView読み込みエラー: {str(e)}")

    # ==================== レガシーAPI互換 ====================
    
    def show_pdf_preview(self, file_info: Dict[str, Any]):
        """レガシーAPI互換用（V1/V2からの移行対応）"""
        if file_info:
            try:
                # 非同期実行
                import asyncio
                loop = asyncio.get_event_loop()
                loop.create_task(self.load_pdf(file_info))
            except RuntimeError:
                # イベントループが存在しない場合
                logger.warning("[V3-UI] イベントループが利用できません")
        else:
            self.clear_preview()

    def show_empty_preview(self):
        """空プレビュー表示（レガシーAPI互換）"""
        self.clear_preview()


# ==================== 作成関数 ====================

def create_large_pdf_preview_v3() -> LargePDFPreviewV3:
    """大容量PDF対応プレビューコンポーネント作成（V3版）"""
    return LargePDFPreviewV3()


# ==================== テスト・デバッグ用 ====================

if __name__ == "__main__":
    print("🚀 LargePDFPreviewV3 - V3専用大容量PDFプレビューコンポーネント")
    print("   - 完全HTTP統一方式")
    print("   - data:URL完全廃止") 
    print("   - V3サーバー専用")
    print("   - 必要最小限のUI")
