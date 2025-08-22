#!/usr/bin/env python3
"""
Flet RAGシステム - OCR調整ページメイン
4分割レイアウト + 3つのスライダー制御
"""

import flet as ft
import math
from ..shared.panel_components import create_panel, PanelHeaderConfig, PanelConfig
from ..shared.pdf_preview import PDFPreview
from ..shared.style_constants import CommonComponents, PageStyles

class OCRAdjustmentPage:
    """OCR調整ページ（4分割レイアウト + 3スライダー制御）"""
    
    def __init__(self):
        """初期化"""
        self.left_split_level = 3
        self.right_split_level = 3
        self.horizontal_level = 3
        
        # 共通コンポーネントインスタンス
        self.pdf_preview = PDFPreview()

    def create_main_layout(self):
        """メインレイアウト作成（4分割 + 3スライダー）"""
        print("[DEBUG] OCR Adjustment create_main_layout called")
        
        # 4つのペイン作成
        top_left = self._create_ocr_settings_pane()
        bottom_left = self._create_ocr_results_pane()
        top_right = self._create_engine_details_pane()
        bottom_right = self._create_pdf_preview_pane()
        
        # 左ペイン（上下分割）
        left_column = CommonComponents.create_main_layout_column(
            top_left, CommonComponents.create_horizontal_divider(), bottom_left
        )
        
        # 右ペイン（上下分割）
        right_column = CommonComponents.create_main_layout_column(
            top_right, CommonComponents.create_horizontal_divider(), bottom_right
        )
        
        # メインROW（左右分割）
        main_row = CommonComponents.create_main_layout_row(left_column, right_column)
        
        # 3つのスライダー作成（共通コンポーネント使用）
        left_slider = CommonComponents.create_vertical_slider(
            self.left_split_level, self.on_left_split_change
        )
        
        right_slider = CommonComponents.create_vertical_slider(
            self.right_split_level, self.on_right_split_change
        )
        
        horizontal_slider = CommonComponents.create_horizontal_slider(
            self.horizontal_level, self.on_horizontal_change
        )
        
        # 左右サイドバー（共通コンポーネント使用）
        left_sidebar = CommonComponents.create_sidebar_container(
            ft.Column([left_slider], alignment=ft.MainAxisAlignment.CENTER, expand=True),
            position="left"
        )
        
        right_sidebar = CommonComponents.create_sidebar_container(
            ft.Column([right_slider], alignment=ft.MainAxisAlignment.CENTER, expand=True),
            position="right"
        )
        
        # トップレベルROW
        top_row = ft.Row([
            left_sidebar,
            ft.Container(content=main_row, expand=True),
            right_sidebar
        ], spacing=0, expand=True)
        
        # 完全レイアウト（上部コンテンツ + 下部スライダーバー）
        return PageStyles.create_complete_layout_with_slider(
            ft.Container(content=top_row, expand=True), horizontal_slider
        )

    def _create_ocr_settings_pane(self):
        """左上: OCR設定ペイン（共通コンポーネント版）"""
        # パネル内容
        panel_content = ft.Container(
            content=ft.Column([
                CommonComponents.create_standard_text("ファイルをドラッグ&ドロップ\nまたはボタンで選択"),
                CommonComponents.create_spacing_container(),
                CommonComponents.create_secondary_button("📁 ファイル選択"),
                CommonComponents.create_spacing_container(),
                CommonComponents.create_primary_button("🚀 OCR実行")
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            expand=True, alignment=ft.alignment.center
        )
        
        # 共通パネル設定
        panel_config = PanelConfig(
            header_config=CommonComponents.create_standard_panel_header_config(
                "OCR設定", ft.Icons.SETTINGS
            )
        )
        
        return create_panel(panel_config, panel_content)

    def _create_engine_details_pane(self):
        """右上: エンジン詳細設定ペイン（共通コンポーネント版）"""
        # パネル内容
        panel_content = ft.Container(
            content=ft.Column([
                CommonComponents.create_standard_icon(ft.Icons.SETTINGS),
                CommonComponents.create_spacing_container(12),
                CommonComponents.create_standard_text("OCRエンジンを選択すると"),
                CommonComponents.create_standard_text("詳細設定が表示されます"),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            expand=True, alignment=ft.alignment.center
        )
        
        # 共通パネル設定
        panel_config = PanelConfig(
            header_config=CommonComponents.create_standard_panel_header_config(
                "詳細設定", ft.Icons.BUILD
            )
        )
        
        return create_panel(panel_config, panel_content)

    def _create_ocr_results_pane(self):
        """左下: OCR結果ペイン（共通コンポーネント版）"""
        # パネル内容
        panel_content = ft.Container(
            content=ft.Column([
                CommonComponents.create_standard_icon(ft.Icons.TEXT_SNIPPET),
                CommonComponents.create_spacing_container(12),
                CommonComponents.create_standard_text("OCR実行すると"),
                CommonComponents.create_standard_text("結果がここに表示されます"),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            expand=True, alignment=ft.alignment.center
        )
        
        # 共通パネル設定
        panel_config = PanelConfig(
            header_config=CommonComponents.create_standard_panel_header_config(
                "OCR結果", ft.Icons.TEXT_SNIPPET
            )
        )
        
        return create_panel(panel_config, panel_content)

    def _create_pdf_preview_pane(self):
        """右下: PDFプレビューペイン（共通コンポーネント版）"""
        # 共通PDFプレビューコンポーネントを使用
        return ft.Container(
            content=self.pdf_preview,
            expand=True
            # marginは削除（PDFPreviewは全域使用）
        )

    def on_left_split_change(self, e):
        """左ペイン分割スライダー変更"""
        self.left_split_level = int(float(e.control.value))
        print(f"[DEBUG] Left split level changed to: {self.left_split_level}")

    def on_right_split_change(self, e):
        """右ペイン分割スライダー変更"""
        self.right_split_level = int(float(e.control.value))
        print(f"[DEBUG] Right split level changed to: {self.right_split_level}")

    def on_horizontal_change(self, e):
        """左右分割スライダー変更"""
        self.horizontal_level = int(float(e.control.value))
        print(f"[DEBUG] Horizontal level changed to: {self.horizontal_level}")

def show_ocr_adjustment_page(page: ft.Page = None):
    """OCR調整ページ表示関数"""
    if page:
        PageStyles.set_page_background(page)
    
    ocr_page = OCRAdjustmentPage()
    layout = ocr_page.create_main_layout()
    return layout

