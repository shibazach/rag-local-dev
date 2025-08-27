#!/usr/bin/env python3
"""
大容量PDF対応プレビューコンポーネント（V3専用版）
右ペイン内表示・完全HTTP統一方式

主要機能:
- V3サーバー専用（完全HTTP統一）  
- 右ペイン内PDF表示（HTMLコントロール+iframe使用）
- WebView完全廃止（プラットフォーム統一）
- data:URL完全廃止（サイズ制限対応）
- 戻るボタン付きナビゲーション
"""

import flet as ft
import asyncio
import uuid
import logging
import sys
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


# プラットフォーム判定削除 - 全プラットフォームで右ペイン内表示統一


class LargePDFPreviewV3(ft.Container):
    """大容量PDF対応プレビューコンポーネント（V3版・右ペイン内表示）"""
    
    def __init__(self, page: Optional[ft.Page] = None):
        super().__init__()
        
        # ページ参照保持（右ペイン表示用）
        self.page = page
        
        # 状態管理
        self.state = PreviewState.EMPTY
        self.current_file_info: Optional[Dict[str, Any]] = None
        self.current_file_id: Optional[str] = None
        self.error_message = ""
        self._last_viewer_url: Optional[str] = None
        
        # UI要素初期化
        self._init_ui()
        
        # 初期レイアウト
        self._build_layout()

    def _init_ui(self):
        """UI要素初期化（外部ブラウザ統一版）"""
        
        # WebView完全廃止 - 全プラットフォーム外部ブラウザ統一
        
        # ステータス表示
        self.status_text = ft.Text(
            "PDFファイルを選択してください", 
            size=14, 
            color=ft.Colors.GREY_600,
            text_align=ft.TextAlign.CENTER
        )
        
        # コントロールボタン
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
        
        # 右ペイン内表示ボタン
        self.open_external_button = ft.ElevatedButton(
            text="📱 右ペインで表示", 
            on_click=self._show_in_right_pane, 
            height=32, 
            visible=False  # PDF準備完了時に表示
        )

    def _build_layout(self):
        """レイアウト構築（右ペイン表示特化）"""
        
        # コントロールバー
        control_bar = ft.Row(
            controls=[
                self.reload_button,
                self.clear_button,
                self.open_external_button,
                ft.Container(expand=True),  # スペーサー
                self.status_text
            ],
            height=40, 
            spacing=8
        )
        
        # メイン表示エリア（右ペイン専用）
        self._overlay_container = ft.Container(
            content=self._build_overlay(),
            expand=True,
            bgcolor=ft.Colors.WHITE,
            alignment=ft.alignment.center,
            visible=True
        )
        
        main_area = self._overlay_container  # シンプル化
        
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
        """状態別オーバーレイ構築（プラットフォーム適応版）"""
        
        if self.state == PreviewState.EMPTY:
            return ft.Column(
                controls=[
                    ft.Icon(ft.Icons.PICTURE_AS_PDF, size=80, color=ft.Colors.GREY_400),
                    ft.Container(height=16),
                    ft.Text(
                        "V3 大容量PDFプレビュー（HTTP統一・プラットフォーム適応）",
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
            
        elif self.state == PreviewState.READY:
            return ft.Column(
                controls=[
                    ft.Icon(ft.Icons.CHECK_CIRCLE, size=64, color=ft.Colors.GREEN_400),
                    ft.Container(height=16),
                    ft.Text("PDF表示準備完了", size=16, color=ft.Colors.GREEN_700, weight=ft.FontWeight.BOLD),
                    ft.Container(height=8),
                    ft.Text("「📱 右ペインで表示」ボタンを押してください", size=12, color=ft.Colors.GREY_600),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=0
            )
            
        # デフォルト
        return ft.Container()

    def _update_ui(self):
        """UI更新（右ペイン表示版）"""
        
        # オーバーレイ表示制御（常に表示・内容のみ切り替え）
        if self._overlay_container:
            self._overlay_container.visible = True
            self._overlay_container.content = self._build_overlay()
        
        # ステータステキスト更新
        if self.current_file_info:
            file_name = self.current_file_info.get('file_name', 'unknown')
            self.status_text.value = f"📄 {file_name}"
        else:
            self.status_text.value = "PDFファイルを選択してください"
        
        # ボタン状態更新
        self.reload_button.disabled = (self.state == PreviewState.EMPTY)
        # 右ペイン表示ボタンは、PDFが準備できた時のみ表示
        self.open_external_button.visible = (self.state == PreviewState.READY) and (self._last_viewer_url is not None)
        
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
        """V3ストリーミング処理（プラットフォーム適応版）"""
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
            
            # ビューアURLを保存（右ペイン表示用）
            self._last_viewer_url = viewer_url
            
            # 右ペイン表示準備完了
            logger.info("[V3-UI] 右ペイン表示準備完了")
            self._set_state(PreviewState.READY)
            self.open_external_button.visible = True  # 右ペイン表示ボタンを表示
            self.update()
            
        except Exception as e:
            logger.error(f"[V3-UI] ストリーミング処理エラー: {e}")
            self._set_state(PreviewState.ERROR, f"ストリーミング処理エラー: {str(e)}")

    def clear_preview(self):
        """プレビュークリア（プラットフォーム適応版）"""
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
        self._last_viewer_url = None
        self.open_external_button.visible = False
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

    # WebView関連イベントハンドラ削除（右ペイン表示統一のため）

    def _show_in_right_pane(self, e):
        """右ペイン内でPDFを表示"""
        if self._last_viewer_url:
            try:
                logger.info(f"[V3-UI] 右ペイン内PDF表示開始: {self._last_viewer_url}")
                
                # WebViewまたはURL表示でPDF表示（HTMLコントロール代替）
                # 方法1: WebViewを試行（可能な場合）
                try:
                    webview_control = ft.WebView(
                        url=self._last_viewer_url,
                        expand=True,
                        width=800,
                        height=600
                    )
                    pdf_display_control = webview_control
                    logger.info("[V3-UI] WebView使用でPDF表示")
                
                except Exception as webview_error:
                    logger.warning(f"[V3-UI] WebView失敗、URL表示にフォールバック: {webview_error}")
                    # 方法2: URL表示（フォールバック）
                    pdf_display_control = ft.Column(
                        controls=[
                            ft.Icon(ft.Icons.PICTURE_AS_PDF, size=80, color=ft.Colors.BLUE_400),
                            ft.Container(height=20),
                            ft.Text("PDF表示", size=20, color=ft.Colors.BLUE_700, weight=ft.FontWeight.BOLD),
                            ft.Container(height=16),
                            ft.Text("以下のURLで表示されています:", size=14, color=ft.Colors.GREY_700),
                            ft.Container(height=8),
                            ft.SelectableText(
                                value=self._last_viewer_url,
                                size=12,
                                color=ft.Colors.BLUE_600,
                                selectable=True
                            ),
                            ft.Container(height=20),
                            ft.Row(
                                controls=[
                                    ft.ElevatedButton(
                                        text="🌐 新しいタブで開く",
                                        on_click=lambda e: self._open_external_tab(),
                                        height=40
                                    ),
                                    ft.ElevatedButton(
                                        text="📋 URLコピー",
                                        on_click=lambda e: self._copy_url_to_clipboard(),
                                        height=40
                                    )
                                ],
                                alignment=ft.MainAxisAlignment.CENTER,
                                spacing=10
                            )
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=0,
                        expand=True,
                        scroll=ft.ScrollMode.AUTO
                    )
                
                # 右ペインにPDFビューア表示
                self._overlay_container.content = pdf_display_control
                self._overlay_container.alignment = None  # 中央寄せを解除
                self._overlay_container.bgcolor = ft.Colors.WHITE
                
                # ボタンを一時的に非表示
                self.open_external_button.visible = False
                
                # 戻るボタンを追加
                back_button = ft.ElevatedButton(
                    text="← 戻る",
                    on_click=self._back_to_preview,
                    height=32
                )
                
                # コントロールバーに戻るボタンを追加
                if len(self.content.controls) > 0 and hasattr(self.content.controls[0], 'content'):
                    control_bar = self.content.controls[0].content
                    if hasattr(control_bar, 'controls'):
                        # 戻るボタンを先頭に挿入
                        control_bar.controls.insert(0, back_button)
                
                self.update()
                logger.info("[V3-UI] 右ペイン内PDF表示完了")
                
            except Exception as ex:
                logger.error(f"[V3-UI] 右ペイン表示エラー: {ex}")
                self._set_state(PreviewState.ERROR, f"右ペイン表示エラー: {str(ex)}")
        else:
            self._set_state(PreviewState.ERROR, "表示するPDFがありません")
    
    def _back_to_preview(self, e):
        """PDFビューアから通常プレビューに戻る"""
        try:
            logger.info("[V3-UI] 通常プレビューに戻る")
            
            # オーバーレイを元に戻す
            self._overlay_container.content = self._build_overlay()
            self._overlay_container.alignment = ft.alignment.center
            self._overlay_container.bgcolor = ft.Colors.WHITE
            
            # 右ペイン表示ボタンを再表示
            self.open_external_button.visible = True
            
            # 戻るボタンをコントロールバーから削除
            if len(self.content.controls) > 0 and hasattr(self.content.controls[0], 'content'):
                control_bar = self.content.controls[0].content
                if hasattr(control_bar, 'controls') and len(control_bar.controls) > 0:
                    # 戻るボタン（先頭）を削除
                    if hasattr(control_bar.controls[0], 'text') and "戻る" in control_bar.controls[0].text:
                        control_bar.controls.pop(0)
            
            self.update()
            logger.info("[V3-UI] 通常プレビューに戻り完了")
            
        except Exception as ex:
            logger.error(f"[V3-UI] プレビュー戻りエラー: {ex}")
    
    def _open_external_tab(self):
        """外部タブでPDFを開く"""
        if self._last_viewer_url and self.page:
            try:
                logger.info(f"[V3-UI] 外部タブでPDF表示: {self._last_viewer_url}")
                self.page.launch_url(self._last_viewer_url)
            except Exception as ex:
                logger.error(f"[V3-UI] 外部タブ表示エラー: {ex}")
    
    def _copy_url_to_clipboard(self):
        """URLをクリップボードにコピー"""
        if self._last_viewer_url and self.page:
            try:
                logger.info("[V3-UI] URLクリップボードコピー")
                self.page.set_clipboard(self._last_viewer_url)
                # 成功通知（簡易版）
                logger.info("[V3-UI] URLコピー完了")
            except Exception as ex:
                logger.error(f"[V3-UI] URLコピーエラー: {ex}")
    
    # 削除：不要なメソッドを整理

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

def create_large_pdf_preview_v3(page: Optional[ft.Page] = None) -> LargePDFPreviewV3:
    """大容量PDF対応プレビューコンポーネント作成（V3版・プラットフォーム適応）"""
    return LargePDFPreviewV3(page)


# ==================== テスト・デバッグ用 ====================

if __name__ == "__main__":
    print("🚀 LargePDFPreviewV3 - V3専用大容量PDFプレビューコンポーネント")
    print("   - 完全HTTP統一方式")
    print("   - data:URL完全廃止") 
    print("   - V3サーバー専用")
    print("   - 必要最小限のUI")
