#!/usr/bin/env python3
"""
Flet RAGシステム - OCR調整ページメイン
4分割レイアウト + 3つのスライダー制御
"""

import flet as ft
import math
from app.flet_ui.shared.panel_components import create_panel, PanelHeaderConfig, PanelConfig
from app.flet_ui.shared.pdf_preview import PDFPreview
from app.flet_ui.shared.style_constants import CommonComponents, PageStyles, SLIDER_RATIOS
from .engines.easyocr_params import get_easyocr_parameters, create_easyocr_panel_content
from .engines.tesseract_params import get_tesseract_parameters, create_tesseract_panel_content
from .engines.paddleocr_params import get_paddleocr_parameters, create_paddleocr_panel_content
from .engines.ocrmypdf_params import get_ocrmypdf_parameters, create_ocrmypdf_panel_content
from .dictionary_manager import create_dictionary_buttons
from app.flet_ui.shared.common_buttons import create_light_button, create_dark_button, create_action_button

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
        
        # OCR関連状態
        self.selected_engine = "EasyOCR"  # 初期値
        self.engine_parameters = {}
        self.ocr_results = []  # OCR結果履歴
        self.results_container = None  # 結果表示コンテナ
        self.engine_details_container = None  # エンジン詳細コンテナ

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
                # ファイル選択情報（統一レイアウト）
                ft.Row([
                    ft.Container(
                        content=ft.Text("ファイル:", weight=ft.FontWeight.BOLD, size=12),
                        width=120,  # 統一幅
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
                
                # OCRエンジン選択（統一レイアウト、余計なContainer削除）
                ft.Row([
                    ft.Container(
                        content=ft.Text("OCRエンジン:", weight=ft.FontWeight.BOLD, size=12),
                        width=120,  # 統一幅
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
                        width=200,
                        on_change=self._on_engine_change
                    )
                ], alignment=ft.MainAxisAlignment.START),
                
                # 処理ページ（統一レイアウト）
                ft.Row([
                    ft.Container(
                        content=ft.Text("処理ページ:", weight=ft.FontWeight.BOLD, size=12),
                        width=120,  # 統一幅
                        alignment=ft.alignment.center_left
                    ),
                    ft.TextField(
                        value="1",
                        width=80,
                        height=40,
                        text_align=ft.TextAlign.CENTER,
                        keyboard_type=ft.KeyboardType.NUMBER,
                        input_filter=ft.NumbersOnlyInputFilter(),
                    ),
                    ft.Text("0=全て", size=10, color=ft.Colors.GREY_600)
                ], spacing=8, alignment=ft.MainAxisAlignment.START),
                
                # 誤字修正（統一レイアウト）
                ft.Row([
                    ft.Container(
                        content=ft.Text("誤字修正:", weight=ft.FontWeight.BOLD, size=12),
                        width=120,  # 統一幅
                        alignment=ft.alignment.center_left
                    ),
                    ft.Switch(
                        value=True,
                        scale=0.8,
                        active_color=ft.Colors.BLUE_600,
                        active_track_color=ft.Colors.BLUE_200
                    )
                ], spacing=8, alignment=ft.MainAxisAlignment.START),
                

                
                # 辞書ボタン（横並び、予備は除く）
                ft.Container(
                    content=ft.Row(create_dictionary_buttons(), wrap=True, spacing=6),
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
                create_action_button("実行", ft.Icons.PLAY_ARROW, self._execute_ocr_test)
            ], spacing=6)
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
        
        # ヘッダーコンテンツを置き換え
        header_container.content = new_header_content
        
        return panel

    def _create_engine_details_pane(self):
        """右上: エンジン詳細設定ペイン（共通コンポーネント版）"""
        # エンジン詳細コンテナ（動的更新用）
        self.engine_details_container = ft.Column(
            controls=[],
            expand=True,
            scroll=ft.ScrollMode.AUTO,
            spacing=8
        )
        
        # 初期エンジン設定を表示
        self._update_engine_details()
        
        # パネル内容
        panel_content = ft.Container(
            content=self.engine_details_container,
            expand=True,
            padding=ft.padding.all(8)
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
                create_light_button("読込", ft.Icons.UPLOAD_FILE),
                create_action_button("保存", ft.Icons.SAVE_ALT)
            ], spacing=6)
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
        
        # ヘッダーコンテンツを置き換え
        header_container.content = new_header_content
        
        return panel

    def _create_ocr_results_pane(self):
        """左下: OCR結果ペイン（共通コンポーネント版）"""
        # 結果表示コンテナ（動的更新用）
        self.results_container = ft.Column(
            controls=[],
            expand=True,
            scroll=ft.ScrollMode.AUTO,
            spacing=8
        )
        
        # 初期状態は空のコンテナ
        
        # パネル内容
        panel_content = ft.Container(
            content=self.results_container,
            expand=True,
            padding=ft.padding.all(8)
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
                create_light_button("クリア", on_click=self._clear_results),
                create_action_button("出力", on_click=self._export_results)
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
    
    # ========= OCR機能 =========
    def _update_engine_details(self):
        """エンジン詳細設定を更新（専用レイアウト使用）"""
        if not self.engine_details_container:
            return
        
        # エンジンごとの専用レイアウト表示メソッドを呼び出し
        engine_layout_functions = {
            "EasyOCR": create_easyocr_panel_content,
            "Tesseract": create_tesseract_panel_content,
            "PaddleOCR": create_paddleocr_panel_content,
            "OCRMyPDF": create_ocrmypdf_panel_content
        }
        
        if self.selected_engine in engine_layout_functions:
            # 専用レイアウトを使用
            content = engine_layout_functions[self.selected_engine]()
        else:
            # フォールバック表示
            content = ft.Container(
                content=ft.Text(
                    f"{self.selected_engine} の設定項目は未定義です",
                    size=14,
                    color=ft.Colors.GREY_600,
                    text_align=ft.TextAlign.CENTER
                ),
                alignment=ft.alignment.center,
                expand=True
            )
        
        self.engine_details_container.controls = [content]

    def _on_engine_change(self, e):
        """OCRエンジン変更イベント"""
        self.selected_engine = e.control.value
        self._update_engine_details()
        if hasattr(self, 'engine_details_container') and self.engine_details_container.page:
            self.engine_details_container.update()
    
    
    def _create_retractable_section(self, result_data: dict) -> ft.Control:
        """リトラクタブルな結果セクションを作成"""
        timestamp = result_data.get("timestamp", "Unknown")
        engine = result_data.get("engine", "Unknown")
        page_count = result_data.get("page_count", 1)
        text_content = result_data.get("text", "")
        
        # 展開状態管理
        is_expanded = True
        
        # ヘッダー部分
        def toggle_expand(e):
            nonlocal is_expanded
            is_expanded = not is_expanded
            content_container.visible = is_expanded
            toggle_icon.name = ft.Icons.EXPAND_LESS if is_expanded else ft.Icons.EXPAND_MORE
            if content_container.page:
                content_container.update()
                toggle_icon.update()
        
        toggle_icon = ft.Icon(
            ft.Icons.EXPAND_LESS if is_expanded else ft.Icons.EXPAND_MORE,
            size=20,
            color=ft.Colors.GREY_600
        )
        
        header = ft.Container(
            content=ft.Row([
                toggle_icon,
                ft.Text(f"{timestamp} - {engine} ({page_count}ページ)", 
                       size=13, weight=ft.FontWeight.W_500),
                ft.IconButton(
                    icon=ft.Icons.DELETE,
                    icon_size=16,
                    tooltip="削除",
                    on_click=lambda e: self._remove_result_section(e, section_container)
                )
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            bgcolor=ft.Colors.BLUE_GREY_50,
            padding=ft.padding.all(8),
            border_radius=ft.border_radius.only(top_left=8, top_right=8),
            on_click=toggle_expand
        )
        
        # コンテンツ部分
        content_container = ft.Container(
            content=ft.Column([
                ft.Container(
                    content=ft.Text(
                        text_content,
                        size=12,
                        selectable=True,
                        color=ft.Colors.BLACK87
                    ),
                    bgcolor=ft.Colors.WHITE,
                    padding=ft.padding.all(12),
                    border_radius=ft.border_radius.only(bottom_left=8, bottom_right=8),
                    border=ft.border.all(1, ft.Colors.GREY_300)
                )
            ]),
            visible=is_expanded
        )
        
        # セクション全体
        section_container = ft.Column([
            header,
            content_container
        ], spacing=0)
        
        return ft.Container(
            content=section_container,
            margin=ft.margin.only(bottom=8)
        )
    
    def _remove_result_section(self, e, section_container):
        """結果セクションを削除"""
        if not self.results_container:
            return
        
        # セクションを削除
        for control in self.results_container.controls:
            if control.content == section_container:
                self.results_container.controls.remove(control)
                break
        
        # 結果が空の場合は空のまま
        
        if self.results_container.page:
            self.results_container.update()

    def _execute_ocr_test(self, e):
        """OCR実行（プレースホルダー）"""
        pass

    def _clear_results(self, e):
        """OCR結果をクリア（プレースホルダー）"""
        pass

    def _export_results(self, e):
        """OCR結果を出力（プレースホルダー）"""
        pass


def show_ocr_adjustment_page(page: ft.Page = None):
    """OCR調整ページ表示関数"""
    if page:
        PageStyles.set_page_background(page)
    
    ocr_page = OCRAdjustmentPage()
    layout = ocr_page.create_main_layout()
    return layout

