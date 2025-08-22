#!/usr/bin/env python3
"""
Flet RAGシステム - PDFプレビューコンポーネント（根本設計見直し版）
レイアウト状態管理の完全分離アーキテクチャ
"""

import flet as ft
from typing import Optional, Dict, Any
import base64
from app.services.file_service import get_file_service
from enum import Enum
import asyncio


class PreviewState(Enum):
    """PDFプレビューの状態"""
    EMPTY = "empty"          # ファイル未選択
    LOADING = "loading"      # PDF読み込み中  
    PDF_READY = "pdf_ready"  # PDF表示準備完了
    ERROR = "error"          # エラー状態


class PDFPreview(ft.Container):
    """PDFプレビューコンポーネント（パネル構造+オーバーレイ設計）"""
    
    def __init__(self, file_path: Optional[str] = None):
        super().__init__()
        
        # 基本設定（パネルと同様の4pxマージン）
        self.file_path = file_path
        self.current_file_info = None
        self.expand = True
        self.margin = ft.margin.all(4)
        self.file_service = get_file_service()
        
        # 状態管理
        self._state = PreviewState.EMPTY
        self._error_message = ""
        
        # WebViewコンポーネント（単一インスタンス）
        self.web_view = ft.WebView(
            url="about:blank",
            expand=True,
            on_page_started=self._on_load_started,
            on_page_ended=self._on_load_ended
        )
        
        # 初期レイアウト構築
        self._rebuild_content()
    
    def _rebuild_content(self):
        """状態に応じてレイアウトを完全再構築（オーバーレイ版）"""
        # ベース：WebViewまたは白背景
        base_content = self.web_view if self._state == PreviewState.PDF_READY else ft.Container(
            expand=True, bgcolor=ft.Colors.WHITE
        )
        
        # オーバーレイ：状態別表示（PDF表示時は非表示）
        overlay_content = None
        if self._state == PreviewState.EMPTY:
            overlay_content = self._create_overlay_content(
                ft.Icons.PICTURE_AS_PDF, "ファイルを選択すると\nPDFプレビューが表示されます"
            )
        elif self._state == PreviewState.LOADING:
            overlay_content = self._create_loading_overlay()
        elif self._state == PreviewState.ERROR:
            overlay_content = self._create_overlay_content(
                ft.Icons.ERROR, f"PDF表示エラー\n{self._error_message}", ft.Colors.RED
            )
        
        # スタック構成：ベース + オーバーレイ
        stack_controls = [base_content]
        if overlay_content:
            stack_controls.append(overlay_content)
        
        # パネルと同様の構造（4pxマージン + 白背景 + 角丸 + ボーダー）
        self.content = ft.Container(
            content=ft.Container(
                content=ft.Stack(stack_controls, expand=True),
                border_radius=8,
                clip_behavior=ft.ClipBehavior.ANTI_ALIAS
            ),
            expand=True,
            bgcolor=ft.Colors.WHITE,
            border_radius=8,
            border=ft.border.all(1, ft.Colors.GREY_300)
        )
    
    def _create_overlay_content(self, icon: ft.Icons, text: str, color: str = ft.Colors.GREY_400) -> ft.Container:
        """オーバーレイコンテンツ作成（Qiita記事理論: Stack内はContainer.alignment）"""
        return ft.Container(
            content=ft.Column([
                ft.Icon(icon, size=80, color=color),
                ft.Container(height=16),
                ft.Text(text, size=16, color=ft.Colors.GREY_600, text_align=ft.TextAlign.CENTER)
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, tight=True),
            alignment=ft.alignment.center,  # Stack内要素のセンタリング（記事準拠）
            expand=True,
            bgcolor="#FFFFFF"
        )
    
    def _create_loading_overlay(self) -> ft.Container:
        """ローディングオーバーレイ（Qiita記事理論: Stack内はContainer.alignment）"""
        return ft.Container(
            content=ft.Column([
                ft.ProgressRing(width=50, height=50),
                ft.Container(height=8),
                ft.Text("PDFを読み込み中...", size=14, color=ft.Colors.GREY_600)
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, tight=True),
            alignment=ft.alignment.center,  # Stack内要素のセンタリング（記事準拠）
            expand=True,
            bgcolor="#FFFFFF"
        )
    
    def _set_state_and_rebuild(self, new_state: PreviewState, error_message: str = ""):
        """状態変更とレイアウト再構築"""
        self._state = new_state
        self._error_message = error_message
        self._rebuild_content()
        try:
            self.update()
        except:
            pass
    
    async def load_pdf(self, file_info: Dict[str, Any]):
        """PDFを実際に読み込んで表示（状態管理版）"""
        if not file_info:
            self.show_empty_preview()
            return
        
        try:
            file_id = file_info.get('id', '')
            file_name = file_info.get('file_name', 'unknown')
            
            print(f"[DEBUG] PDF読み込み開始: {file_name} (ID: {file_id})")
            
            # 1. ローディング状態に変更
            self._set_state_and_rebuild(PreviewState.LOADING)
            
            # 2. ファイルデータを取得
            file_data = self.file_service.get_file_info(file_id)
            
            if file_data and file_data.get('blob_data'):
                blob_data = file_data['blob_data']
                
                # 3. Base64エンコード
                pdf_base64 = base64.b64encode(blob_data).decode('utf-8')
                pdf_url = f'data:application/pdf;base64,{pdf_base64}'
                
                # 4. WebViewにPDF URL設定
                self.web_view.url = pdf_url
                self.current_file_info = file_info
                self.file_path = file_name
                
                # 5. PDF表示状態に変更
                self._set_state_and_rebuild(PreviewState.PDF_READY)
                
                # 6. タイムアウト対策（3秒後に状態確認）
                asyncio.create_task(self._verify_load_completion())
                
                print(f"[DEBUG] PDF表示完了: {file_name}")
            else:
                # エラー状態に変更
                self._set_state_and_rebuild(PreviewState.ERROR, f"PDFデータを取得できませんでした: {file_name}")
                
        except Exception as e:
            print(f"[DEBUG] PDF読み込みエラー: {str(e)}")
            self._set_state_and_rebuild(PreviewState.ERROR, f"PDF読み込みエラー: {str(e)}")
    
    def show_pdf_preview(self, file_info):
        """PDFプレビュー表示（同期インターフェース）"""
        print(f"[DEBUG] PDFプレビュー表示: {file_info}")
        if file_info:
            try:
                loop = asyncio.get_event_loop()
                loop.create_task(self.load_pdf(file_info))
            except RuntimeError:
                asyncio.run(self.load_pdf(file_info))
        else:
            print("[DEBUG] プレビューをクリア")
            self.show_empty_preview()
    
    def show_empty_preview(self):
        """空のプレビュー表示"""
        self.current_file_info = None
        self.file_path = None
        self.web_view.url = "about:blank"
        self._set_state_and_rebuild(PreviewState.EMPTY)
    
    def _on_load_started(self, e):
        """PDF読み込み開始時（WebViewイベント）"""
        print(f"[DEBUG] WebView読み込み開始")
        # PDF_READY状態でもWebViewの読み込みが開始される場合がある
        # 状態はPDF_READYのまま維持
    
    def _on_load_ended(self, e):
        """PDF読み込み完了時（WebViewイベント）"""
        print(f"[DEBUG] WebView読み込み完了")
        # PDF_READY状態を維持（ローディング状態は既に解除済み）
    
    async def _verify_load_completion(self, delay_seconds: int = 3):
        """読み込み完了確認（タイムアウト対策）"""
        await asyncio.sleep(delay_seconds)
        print(f"[DEBUG] PDF読み込み確認（{delay_seconds}秒経過）")
        # PDF_READY状態であることを確認（既に正しい状態のはず）
        if self._state == PreviewState.PDF_READY:
            print("[DEBUG] PDF表示状態確認OK")


def create_pdf_preview(file_path: Optional[str] = None) -> PDFPreview:
    """PDFプレビュー作成関数"""
    return PDFPreview(file_path)