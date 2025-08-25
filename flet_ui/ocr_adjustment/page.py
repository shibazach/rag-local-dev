#!/usr/bin/env python3
"""
Flet RAGシステム - OCR調整ページメイン
4分割レイアウト + 3つのスライダー制御
"""

import flet as ft
import math
from ..shared.panel_components import create_panel, PanelHeaderConfig, PanelConfig
from ..shared.pdf_preview import PDFPreview
from ..shared.style_constants import CommonComponents, PageStyles, SLIDER_RATIOS

class OCRAdjustmentPage:
    """OCR調整ページ（4分割レイアウト + 3スライダー制御）"""
    
    def __init__(self):
        """初期化"""
        self.left_split_level = 3
        self.right_split_level = 3
        self.horizontal_level = 3
        
        # 共通比率テーブル使用
        self.ratios = SLIDER_RATIOS
        
        # 共通コンポーネントインスタンス
        self.pdf_preview = PDFPreview()
        
        # コンテナ参照（tab_d.py パターン適用）
        self.top_left_container = None
        self.bottom_left_container = None
        self.top_right_container = None
        self.bottom_right_container = None
        self.left_column = None
        self.right_column = None
        self.left_container = None
        self.right_container = None
        self.main_row = None

    def create_main_layout(self):
        """メインレイアウト作成（tab_d.py構造適用: ft.Stack + 部分オーバーレイ）"""
        
        # ===== 下層: 本体レイアウト =====
        base_layer = self._create_base_layout()
        
        # ===== 上層: 部分オーバーレイ（左右端の縦スライダーのみ） =====
        overlay_elements = self._create_overlay_layer()
        
        # 初期レイアウト適用（コンテナ作成後）
        self._update_layout()
        
        # ===== ルート: 部分オーバーレイでStack構成 =====
        main_content = ft.Stack(
            expand=True,
            clip_behavior=ft.ClipBehavior.NONE,  # 画面端からのはみ出し許可
            controls=[base_layer] + overlay_elements,  # 背景 + 左右端オーバーレイ
        )
        
        return ft.Container(
            content=main_content,
            expand=True
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
    
    def _create_base_layout(self) -> ft.Container:
        """本体レイアウト: 4分割ペイン + 下部横スライダー（tab_d.py構造準拠）"""
        
        # 4つのペインコンテナ作成
        self.top_left_container = ft.Container(expand=1)
        self.bottom_left_container = ft.Container(expand=1)
        self.top_right_container = ft.Container(expand=1)
        self.bottom_right_container = ft.Container(expand=1)
        
        # 左右カラム作成
        self.left_column = ft.Column([
            self.top_left_container,
            ft.Divider(height=1, thickness=1, color=ft.Colors.GREY_400),
            self.bottom_left_container
        ], spacing=0, expand=True)
        
        self.right_column = ft.Column([
            self.top_right_container,
            ft.Divider(height=1, thickness=1, color=ft.Colors.GREY_400),
            self.bottom_right_container
        ], spacing=0, expand=True)
        
        # Container参照保持（files/page.pyパターン適用）
        self.left_container = ft.Container(content=self.left_column, expand=1)
        self.right_container = ft.Container(content=self.right_column, expand=1)
        
        # メイン行作成（中央4分割）
        self.main_row = ft.Row([
            self.left_container,
            ft.VerticalDivider(width=1, thickness=1, color=ft.Colors.GREY_400),
            self.right_container
        ], spacing=0, expand=True)
        
        # 横スライダー作成
        horizontal_slider = CommonComponents.create_horizontal_slider(
            self.horizontal_level, self.on_horizontal_change
        )
        
        # メインコンテンツ部分（左右ガイド + 中央4分割）
        main_content = ft.Container(
            expand=True,
            content=ft.Row([
                # 左ガイド（青枠）純粋36px
                ft.Container(width=36, bgcolor=ft.Colors.BLUE_50,
                            border=ft.border.all(1, ft.Colors.BLUE_300),
                            disabled=True),
                # 中央領域（4分割パネル）
                ft.Container(content=self.main_row, expand=True),
                # 右ガイド（青枠）純粋36px
                ft.Container(width=36, bgcolor=ft.Colors.BLUE_50,
                            border=ft.border.all(1, ft.Colors.BLUE_300),
                            disabled=True),
            ], expand=True, spacing=0, vertical_alignment=ft.CrossAxisAlignment.STRETCH)
        )
        
        # 完全レイアウト（共通スタイル適用）
        return PageStyles.create_complete_layout_with_slider(
            main_content, horizontal_slider
        )
    
    def _create_overlay_layer(self):
        """部分オーバーレイ: 共通コンポーネント使用"""
        return CommonComponents.create_vertical_slider_overlay_elements(
            self.left_split_level, self.on_left_split_change,
            self.right_split_level, self.on_right_split_change
        )
    
    def _update_layout(self):
        """レイアウトを実際に更新（4分割版）"""
        # 比率計算
        left_top_ratio, left_bottom_ratio = self.ratios[self.left_split_level]
        right_top_ratio, right_bottom_ratio = self.ratios[self.right_split_level]
        left_ratio, right_ratio = self.ratios[self.horizontal_level]
        
        # ペイン内容更新
        self.top_left_container.content = self._create_ocr_settings_pane()
        self.bottom_left_container.content = self._create_ocr_results_pane()
        self.top_right_container.content = self._create_engine_details_pane()
        self.bottom_right_container.content = self._create_pdf_preview_pane()
        
        # 比率適用
        self.top_left_container.expand = left_top_ratio
        self.bottom_left_container.expand = left_bottom_ratio
        self.top_right_container.expand = right_top_ratio
        self.bottom_right_container.expand = right_bottom_ratio
        
        # 左右比率（files/page.pyパターン適用：Container直接更新）
        self.left_container.expand = left_ratio
        self.right_container.expand = right_ratio
        
        # UI更新（Container直接更新）
        try:
            if hasattr(self, 'left_container') and self.left_container.page:
                self.left_container.update()
            if hasattr(self, 'right_container') and self.right_container.page:
                self.right_container.update()
        except:
            pass

    def on_left_split_change(self, e):
        """左ペイン分割スライダー変更"""
        self.left_split_level = int(float(e.control.value))
        self._update_layout()

    def on_right_split_change(self, e):
        """右ペイン分割スライダー変更"""
        self.right_split_level = int(float(e.control.value))
        self._update_layout()

    def on_horizontal_change(self, e):
        """左右分割スライダー変更"""
        self.horizontal_level = int(float(e.control.value))
        self._update_layout()


def show_ocr_adjustment_page(page: ft.Page = None):
    """OCR調整ページ表示関数"""
    if page:
        PageStyles.set_page_background(page)
    
    ocr_page = OCRAdjustmentPage()
    layout = ocr_page.create_main_layout()
    return layout

