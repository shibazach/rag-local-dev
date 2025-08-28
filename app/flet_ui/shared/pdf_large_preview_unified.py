#!/usr/bin/env python3
"""
V5統合PDF大容量プレビューコンポーネント
V1 (WebView) + V4 (画像変換) の透明フォールバック対応

主要機能:
- サイズ決め打ち自動選択：≤1.2MB=V1 WebView / >1.2MB=V4 画像変換
- V4 UI維持：既存V4の操作感を完全保持
- 透明フォールバック：ユーザーは戦略を意識しない
- 統一インターフェース：単一APIでV1/V4を内部選択

使用例:
```python
pdf_preview = PDFPreviewV5(page)
await pdf_preview.load_pdf("path/to/file.pdf")
```

戦略ロジック:
- ≤1.2MB: V1方式 (data:URL + WebView表示)
- >1.2MB: V4方式 (PyMuPDF画像変換表示)
- UI統一: すべてV4スタイルで表示（内部戦略は透明）
"""

import flet as ft
import asyncio
import logging
import os
from typing import Optional, Dict, Any

from .pdf_preview import PDFPreview  # V1コンポーネント
from .pdf_large_preview_v4 import PDFImagePreviewV4  # V4コンポーネント

logger = logging.getLogger(__name__)

# サイズ閾値設定（1.2MB）
SIZE_THRESHOLD_BYTES = int(1.2 * 1024 * 1024)


class PDFPreviewV5(ft.Container):
    """V5統合PDFプレビューコンポーネント（透明フォールバック）"""

    def __init__(self, page: Optional[ft.Page] = None):
        super().__init__()
        
        # 基本設定
        self.page = page
        self.expand = True
        self.bgcolor = ft.Colors.WHITE
        self.border_radius = 8
        self.padding = ft.padding.all(4)
        
        # 状態管理
        self._file_path: Optional[str] = None
        self._file_size: Optional[int] = None
        self._current_strategy: Optional[str] = None
        self._current_file_id: Optional[str] = None
        
        # 子コンポーネント（どちらか一方のみ使用）
        self._v1_component: Optional[PDFPreview] = None
        self._v4_component: Optional[PDFImagePreviewV4] = None
        self._active_component: Optional[ft.Control] = None
        
        # UI初期化
        self._init_ui()

    def _init_ui(self):
        """UI要素初期化"""
        
        # 初期状態表示
        self._empty_state = ft.Column([
            ft.Icon(ft.Icons.PICTURE_AS_PDF, size=80, color=ft.Colors.GREY_400),
            ft.Container(height=16),
            ft.Text("PDF未選択", size=16, color=ft.Colors.GREY_600),
            ft.Text("V5統合表示 - 自動最適化", size=12, color=ft.Colors.GREY_500)
        ], 
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        alignment=ft.MainAxisAlignment.CENTER,
        spacing=0)
        
        # 読み込み状態表示
        self._loading_state = ft.Column([
            ft.ProgressRing(width=40, height=40, color=ft.Colors.BLUE_400),
            ft.Container(height=16),
            ft.Text("PDF読み込み中...", size=16, color=ft.Colors.BLUE_600),
            ft.Text("最適表示方式を自動選択中", size=12, color=ft.Colors.BLUE_500)
        ], 
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        alignment=ft.MainAxisAlignment.CENTER,
        spacing=0)
        
        # エラー状態表示
        self._error_state = ft.Column([
            ft.Icon(ft.Icons.ERROR_OUTLINE, size=64, color=ft.Colors.RED_400),
            ft.Container(height=16),
            ft.Text("読み込みエラー", size=16, color=ft.Colors.RED_600),
            ft.Text("ファイルを確認してください", size=12, color=ft.Colors.RED_500)
        ], 
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        alignment=ft.MainAxisAlignment.CENTER,
        spacing=0)
        
        # デフォルト状態
        self.content = ft.Container(
            content=self._empty_state,
            alignment=ft.alignment.center,
            expand=True
        )

    async def load_pdf(self, file_path: str):
        """PDF読み込み（統合版）"""
        try:
            logger.info(f"[V5] PDF読み込み開始: {file_path}")
            
            # ファイル存在確認
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"PDF file not found: {file_path}")
            
            self._file_path = file_path
            self._file_size = os.path.getsize(file_path)
            
            # 読み込み状態表示
            self._show_loading()
            
            # サイズベース戦略決定
            if self._file_size <= SIZE_THRESHOLD_BYTES:
                self._current_strategy = "webview"
                logger.info(f"[V5] V1戦略選択 - サイズ: {self._file_size/1024/1024:.2f}MB")
                await self._load_with_v1(file_path)
            else:
                self._current_strategy = "image"
                logger.info(f"[V5] V4戦略選択 - サイズ: {self._file_size/1024/1024:.2f}MB")
                await self._load_with_v4(file_path)
            
        except Exception as e:
            logger.error(f"[V5] PDF読み込みエラー: {e}")
            self._show_error()

    async def load_pdf_from_bytes(self, pdf_data: bytes, filename: str = "document.pdf", file_id: str = None):
        """PDFバイト読み込み（統合版）"""
        try:
            logger.info(f"[V5] バイト読み込み開始: {filename}")
            
            self._file_size = len(pdf_data)
            self._current_file_id = file_id  # file_idを保存
            
            # 読み込み状態表示
            self._show_loading()
            
            # サイズベース戦略決定
            if self._file_size <= SIZE_THRESHOLD_BYTES:
                self._current_strategy = "webview"
                logger.info(f"[V5] V1戦略選択 - サイズ: {self._file_size/1024/1024:.2f}MB")
                await self._load_v1_from_bytes(pdf_data, filename, file_id)
            else:
                self._current_strategy = "image"
                logger.info(f"[V5] V4戦略選択 - サイズ: {self._file_size/1024/1024:.2f}MB")
                await self._load_v4_from_bytes(pdf_data, filename, file_id)
            
        except Exception as e:
            logger.error(f"[V5] バイト読み込みエラー: {e}")
            self._show_error()

    async def _load_with_v1(self, file_path: str):
        """V1 WebView方式で読み込み"""
        try:
            # V1コンポーネント作成
            self._v1_component = PDFPreview(self.page)
            
            # PDFデータ読み込み
            with open(file_path, "rb") as f:
                pdf_data = f.read()
            
            # V1で読み込み
            await self._v1_component.load_pdf_from_bytes(pdf_data)
            
            # 表示切り替え
            self._active_component = self._v1_component
            self.content = self._v1_component
            self.update()
            
            logger.info("[V5] V1読み込み完了")
            
        except Exception as e:
            logger.error(f"[V5] V1読み込みエラー: {e}")
            # V1失敗時はV4にフォールバック
            logger.info("[V5] V4にフォールバック実行")
            await self._load_with_v4(file_path)

    async def _load_with_v4(self, file_path: str):
        """V4画像方式で読み込み"""
        try:
            # V4コンポーネント作成
            self._v4_component = PDFImagePreviewV4(self.page)
            
            # PDFデータ読み込み
            with open(file_path, "rb") as f:
                pdf_data = f.read()
            
            # V4で読み込み
            await self._v4_component.load_pdf_from_bytes(pdf_data)
            
            # 表示切り替え
            self._active_component = self._v4_component
            self.content = self._v4_component
            self.update()
            
            logger.info("[V5] V4読み込み完了")
            
        except Exception as e:
            logger.error(f"[V5] V4読み込みエラー: {e}")
            self._show_error()

    async def _load_v1_from_bytes(self, pdf_data: bytes, filename: str, file_id: str = None):
        """V1でバイトデータ読み込み"""
        try:
            # V1コンポーネント作成
            self._v1_component = PDFPreview(self.page)
            
            # V1で読み込み（正しいfile_idを使用）
            if file_id:
                file_info = {
                    'id': file_id,
                    'file_name': filename
                }
            else:
                # file_idがない場合のフォールバック（V1スキップ）
                logger.warning("[V5] file_idなしでV1読み込みスキップ")
                self._show_error("V1: file_idが必要です")
                return
                
            self._v1_component.show_pdf_preview(file_info)
            
            # 表示切り替え
            self._active_component = self._v1_component
            self.content = self._v1_component
            self.update()
            
            logger.info("[V5] V1バイト読み込み完了")
            
        except Exception as e:
            logger.error(f"[V5] V1バイト読み込みエラー: {e}")
            # V1失敗時はV4にフォールバック
            logger.info("[V5] V4にフォールバック実行")
            await self._load_v4_from_bytes(pdf_data, filename)

    async def _load_v4_from_bytes(self, pdf_data: bytes, filename: str, file_id: str = None):
        """V4でバイトデータ読み込み"""
        try:
            # V4コンポーネント作成
            self._v4_component = PDFImagePreviewV4(self.page)
            
            # V4で読み込み（file_idは使用しない）
            file_info = {
                'id': file_id if file_id else 'v4_unified_preview',
                'file_name': filename
            }
            await self._v4_component.load_pdf(file_info, pdf_data)
            
            # 表示切り替え
            self._active_component = self._v4_component
            self.content = self._v4_component
            self.update()
            
            logger.info("[V5] V4バイト読み込み完了")
            
        except Exception as e:
            logger.error(f"[V5] V4バイト読み込みエラー: {e}")
            self._show_error()

    def _show_loading(self):
        """読み込み状態表示"""
        self.content = ft.Container(
            content=self._loading_state,
            alignment=ft.alignment.center,
            expand=True
        )
        if hasattr(self, 'page') and self.page:
            self.update()

    def _show_error(self):
        """エラー状態表示"""
        self.content = ft.Container(
            content=self._error_state,
            alignment=ft.alignment.center,
            expand=True
        )
        if hasattr(self, 'page') and self.page:
            self.update()

    def clear_preview(self):
        """プレビュークリア"""
        logger.info("[V5] プレビュークリア")
        
        self._file_path = None
        self._file_size = None
        self._current_strategy = None
        
        # 子コンポーネントクリア
        if self._v1_component:
            try:
                self._v1_component.clear_preview()
            except Exception as e:
                logger.warning(f"[V5] V1クリアエラー: {e}")
        if self._v4_component:
            try:
                self._v4_component.clear_preview()
            except Exception as e:
                logger.warning(f"[V5] V4クリアエラー: {e}")
        
        self._v1_component = None
        self._v4_component = None
        self._active_component = None
        
        # 初期状態に戻す
        self.content = ft.Container(
            content=self._empty_state,
            alignment=ft.alignment.center,
            expand=True
        )
        if hasattr(self, 'page') and self.page:
            self.update()

    def get_current_strategy(self) -> Optional[str]:
        """現在の戦略取得"""
        return self._current_strategy

    def get_file_info(self) -> Dict[str, Any]:
        """ファイル情報取得"""
        return {
            "file_path": self._file_path,
            "file_size": self._file_size,
            "strategy": self._current_strategy,
            "threshold_mb": 1.2,  # 固定値として返す
            "active_component": "v1" if self._v1_component == self._active_component else "v4" if self._v4_component == self._active_component else None
        }


# ---------------------------
# ファクトリ関数
# ---------------------------

def create_pdf_preview_unified(page: Optional[ft.Page] = None) -> PDFPreviewV5:
    """V5統合PDFプレビュー作成"""
    return PDFPreviewV5(page)


def create_large_pdf_preview(page: Optional[ft.Page] = None) -> PDFPreviewV5:
    """大容量PDFプレビュー作成（互換性ラッパー）"""
    return create_pdf_preview_unified(page)


# V5エイリアス
PDFPreviewUnified = PDFPreviewV5
create_pdf_preview_v5 = create_pdf_preview_unified


if __name__ == "__main__":
    # テスト用
    import sys
    
    def main():
        if len(sys.argv) < 2:
            print("Usage: python pdf_large_preview_unified.py <pdf_path>")
            return
        
        pdf_path = sys.argv[1]
        
        def test_app(page: ft.Page):
            page.title = "V5統合PDF表示テスト"
            page.theme_mode = ft.ThemeMode.LIGHT
            
            pdf_preview = create_pdf_preview_v5(page)
            
            async def load_test():
                await pdf_preview.load_pdf(pdf_path)
            
            page.run_task(load_test)
            page.add(pdf_preview)
        
        ft.app(target=test_app)
    
    main()