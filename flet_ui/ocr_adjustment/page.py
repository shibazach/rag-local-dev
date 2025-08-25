#!/usr/bin/env python3
"""
Flet RAGシステム - OCR調整ページメイン
4分割レイアウト + 3つのスライダー制御
"""

import flet as ft
import math
from flet_ui.shared.panel_components import create_panel, PanelHeaderConfig, PanelConfig
from flet_ui.shared.pdf_preview import PDFPreview
from flet_ui.shared.style_constants import CommonComponents, PageStyles, SLIDER_RATIOS

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
        """メインレイアウト作成（一体型コンポーネント適用）"""
        
        # 4分割メインコンテンツ作成
        main_4quad_content = self._create_4quad_layout()
        
        # 完全一体型レイアウト適用
        return CommonComponents.create_complete_layout_with_full_sliders(
            main_4quad_content,
            self.left_split_level, self.on_left_split_change,
            self.right_split_level, self.on_right_split_change, 
            self.horizontal_level, self.on_horizontal_change
        )

    def _create_ocr_settings_pane(self):
        """左上: OCR設定ペイン（共通コンポーネント版）"""
        # パネル内容（実際のOCR設定項目）
        panel_content = ft.Container(
            content=ft.Column([
                # ファイル選択情報
                ft.Container(
                    content=ft.Row([
                        ft.Container(
                            content=ft.Text("ファイル:", weight=ft.FontWeight.BOLD, size=12),
                            width=100,
                            alignment=ft.alignment.center_left
                        ),
                        ft.TextField(
                            hint_text="選択されたファイル名", 
                            read_only=True,
                            expand=True,
                            height=40
                        ),
                        ft.IconButton(
                            icon=ft.Icons.FOLDER_OPEN,
                            icon_size=20,
                            tooltip="ファイル選択"
                        )
                    ], alignment=ft.MainAxisAlignment.START),
                    padding=ft.padding.all(8),
                    bgcolor=ft.Colors.GREY_100,
                    border_radius=8
                ),
                
                # OCRエンジン選択
                ft.Container(
                    content=ft.Row([
                        ft.Container(
                            content=ft.Text("OCRエンジン:", size=13, weight=ft.FontWeight.W_500),
                            width=100,
                            alignment=ft.alignment.center_left
                        ),
                        ft.Dropdown(
                            options=[
                                ft.dropdown.Option("EasyOCR"),
                                ft.dropdown.Option("Tesseract"),
                                ft.dropdown.Option("PaddleOCR"),
                                ft.dropdown.Option("OCRMyPDF")
                            ],
                            value="EasyOCR",
                            expand=True
                        )
                    ]),
                    padding=ft.padding.all(4)
                ),
                
                # 処理ページと誤字修正（横並び）
                ft.Container(
                    content=ft.Row([
                        # 処理ページ
                        ft.Row([
                            ft.Container(
                                content=ft.Text("処理ページ:", size=13, weight=ft.FontWeight.W_500),
                                width=100,
                                alignment=ft.alignment.center_left
                            ),
                            ft.Container(
                                content=ft.TextField(
                                    value="1",
                                    width=80,
                                    height=40,
                                    text_align=ft.TextAlign.CENTER,
                                    keyboard_type=ft.KeyboardType.NUMBER,
                                    input_filter=ft.NumbersOnlyInputFilter()
                                ),
                                width=80
                            ),
                            ft.Text("0=全て", size=11, color=ft.Colors.GREY_600)
                        ], spacing=6),
                        
                        # 誤字修正
                        ft.Row([
                            ft.Switch(value=True),
                            ft.Text("誤字修正", size=13)
                        ], spacing=6)
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    padding=ft.padding.all(4)
                ),
                
                # 区切り線
                ft.Divider(height=1, color=ft.Colors.GREY_400),
                
                # 辞書ボタン（横並び、予備は除く）
                ft.Container(
                    content=ft.Row([
                        ft.ElevatedButton(
                            "一般用語", 
                            icon=ft.Icons.BOOK,
                            bgcolor=ft.Colors.GREY_300
                        ),
                        ft.ElevatedButton(
                            "専門用語", 
                            icon=ft.Icons.LIBRARY_BOOKS,
                            bgcolor=ft.Colors.GREY_300
                        ),
                        ft.ElevatedButton(
                            "誤字修正", 
                            icon=ft.Icons.CHECK_CIRCLE,
                            bgcolor=ft.Colors.GREY_300
                        ),
                        ft.ElevatedButton(
                            "ユーザー辞書", 
                            icon=ft.Icons.PERSON,
                            bgcolor=ft.Colors.GREY_300
                        )
                    ], wrap=True, spacing=6),
                    padding=ft.padding.all(4)
                )
            ], spacing=10, expand=True),
            padding=ft.padding.all(8),
            expand=True
        )
        
        # ヘッダー設定（ボタン付き）
        header_config = PanelHeaderConfig(
            title="OCR設定",
            title_icon=ft.Icons.SETTINGS,
            bgcolor=ft.Colors.BLUE_GREY_800,
            text_color=ft.Colors.WHITE
        )
        
        panel_config = PanelConfig(header_config=header_config)
        
        # パネル作成
        panel = create_panel(panel_config, panel_content)
        
        # ヘッダーにボタンを追加（手動で実装）
        header_container = panel.content.controls[0]  # ヘッダー部分
        
        # 既存のヘッダー内容を取得
        existing_content = header_container.content
        
        # 新しいヘッダー内容（タイトル + 右側のボタン群）
        new_header_content = ft.Row([
            # 左側：既存のタイトル部分
            ft.Container(
                content=ft.Row([
                    ft.Icon(ft.Icons.SETTINGS, size=20, color=ft.Colors.WHITE),
                    ft.Text("OCR設定", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)
                ], spacing=8),
                expand=True
            ),
            # 右側：ボタン群
            ft.Row([
                ft.ElevatedButton(
                    "実行",
                    icon=ft.Icons.PLAY_ARROW,
                    bgcolor=ft.Colors.GREEN,
                    color=ft.Colors.WHITE,
                    height=32
                )
            ], spacing=6)
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
        
        # ヘッダーコンテンツを置き換え
        header_container.content = new_header_content
        
        return panel

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
        
        # ヘッダー設定
        header_config = PanelHeaderConfig(
            title="詳細設定",
            title_icon=ft.Icons.BUILD,
            bgcolor=ft.Colors.BLUE_GREY_800,
            text_color=ft.Colors.WHITE
        )
        
        panel_config = PanelConfig(header_config=header_config)
        
        # パネル作成
        panel = create_panel(panel_config, panel_content)
        
        # ヘッダーにボタンを追加（右寄せ）
        header_container = panel.content.controls[0]  # ヘッダー部分
        
        # 新しいヘッダー内容（タイトル + 右側のボタン群）
        new_header_content = ft.Row([
            # 左側：タイトル部分
            ft.Container(
                content=ft.Row([
                    ft.Icon(ft.Icons.BUILD, size=20, color=ft.Colors.WHITE),
                    ft.Text("詳細設定", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)
                ], spacing=8),
                expand=True
            ),
            # 右側：ボタン群
            ft.Row([
                ft.ElevatedButton(
                    "読込",
                    icon=ft.Icons.UPLOAD_FILE,
                    bgcolor=ft.Colors.GREY_600,
                    color=ft.Colors.WHITE,
                    height=32
                ),
                ft.ElevatedButton(
                    "保存",
                    icon=ft.Icons.SAVE_ALT,
                    bgcolor=ft.Colors.BLUE,
                    color=ft.Colors.WHITE,
                    height=32
                )
            ], spacing=6)
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
        
        # ヘッダーコンテンツを置き換え
        header_container.content = new_header_content
        
        return panel

    def _create_ocr_results_pane(self):
        """左下: OCR結果ペイン（共通コンポーネント版）"""
        # パネル内容
        panel_content = ft.Container(
            content=ft.Column([
                # OCR実行前のプレースホルダー
                ft.Container(
                    content=ft.Column([
                        ft.Icon(ft.Icons.TEXT_SNIPPET, size=64, color=ft.Colors.GREY_400),
                        ft.Text("OCR実行すると", size=14, color=ft.Colors.GREY_600),
                        ft.Text("結果がここに表示されます", size=14, color=ft.Colors.GREY_600),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    expand=True,
                    alignment=ft.alignment.center
                )
            ], expand=True),
            expand=True
        )
        
        # ヘッダー設定
        header_config = PanelHeaderConfig(
            title="OCR結果",
            title_icon=ft.Icons.TEXT_SNIPPET,
            bgcolor=ft.Colors.BLUE_GREY_800,
            text_color=ft.Colors.WHITE
        )
        
        panel_config = PanelConfig(header_config=header_config)
        
        # パネル作成
        panel = create_panel(panel_config, panel_content)
        
        # ヘッダーにボタンを追加（右寄せ）
        header_container = panel.content.controls[0]  # ヘッダー部分
        
        # 新しいヘッダー内容（タイトル + 右側のボタン群）
        new_header_content = ft.Row([
            # 左側：タイトル部分
            ft.Container(
                content=ft.Row([
                    ft.Icon(ft.Icons.TEXT_SNIPPET, size=20, color=ft.Colors.WHITE),
                    ft.Text("OCR結果", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)
                ], spacing=8),
                expand=True
            ),
            # 右側：ボタン群
            ft.Row([
                ft.ElevatedButton(
                    "クリア",
                    bgcolor=ft.Colors.GREY_600,
                    color=ft.Colors.WHITE,
                    height=32
                ),
                ft.ElevatedButton(
                    "出力",
                    bgcolor=ft.Colors.BLUE,
                    color=ft.Colors.WHITE,
                    height=32
                )
            ], spacing=6)
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
        
        # ヘッダーコンテンツを置き換え
        header_container.content = new_header_content
        
        return panel

    def _create_pdf_preview_pane(self):
        """右下: PDFプレビューペイン（共通コンポーネント版）"""
        # 共通PDFプレビューコンポーネントを使用
        return ft.Container(
            content=self.pdf_preview,
            expand=True
            # marginは削除（PDFPreviewは全域使用）
        )
    
    def _create_4quad_layout(self) -> ft.Container:
        """4分割レイアウトのみ作成（ガイドエリア・スライダーは一体型コンポーネントが担当）"""
        
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
        
        # Container参照保持（比率更新用）
        self.left_container = ft.Container(content=self.left_column, expand=1)
        self.right_container = ft.Container(content=self.right_column, expand=1)
        
        # 4分割メイン行作成
        self.main_row = ft.Row([
            self.left_container,
            ft.VerticalDivider(width=1, thickness=1, color=ft.Colors.GREY_400),
            self.right_container
        ], spacing=0, expand=True)
        
        # 初期レイアウト適用
        self._update_layout()
        
        # 4分割部分のみ返す
        return ft.Container(content=self.main_row, expand=True)
    
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

