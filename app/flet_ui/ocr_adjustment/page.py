#!/usr/bin/env python3
"""
Flet RAGシステム - OCR調整ページメイン
4分割レイアウト + 3つのスライダー制御
"""

import flet as ft
import math
from typing import Dict, Any, Optional
from app.flet_ui.shared.panel_components import create_panel, PanelHeaderConfig, PanelConfig
from app.flet_ui.shared.pdf_preview import PDFPreview
from app.flet_ui.shared.style_constants import CommonComponents, PageStyles, SLIDER_RATIOS
from app.flet_ui.shared.file_selection_dialog import create_file_selection_dialog
from .engines.easyocr_params import get_easyocr_parameters, create_easyocr_panel_content
from .engines.tesseract_params import get_tesseract_parameters, create_tesseract_panel_content
from .engines.paddleocr_params import get_paddleocr_parameters, create_paddleocr_panel_content
from .engines.ocrmypdf_params import get_ocrmypdf_parameters, create_ocrmypdf_panel_content
from .dictionary_manager import create_dictionary_buttons
from app.flet_ui.shared.common_buttons import create_light_button, create_dark_button, create_action_button

class OCRAdjustmentPage:
    """OCR調整ページ（4分割レイアウト + 3スライダー制御）"""
    
    def __init__(self, page: ft.Page = None):
        """初期化"""
        # ページ参照（アコーディオン用）
        self.page = page
        # 縦スライダー削除：2分割構造では横スライダーのみ
        self.horizontal_level = 3
        
        # tab_bパターン：タブ切り替え状態
        self.selected_tab = 0  # 0: 設定, 1: PDF
        
        # 共通比率テーブル使用
        self.ratios = SLIDER_RATIOS
        
        # 縦スライダー関連削除（2分割構造では不要）
        # self.left_split_level = 3
        # self.right_split_level = 3
        
        # 共通コンポーネントインスタンス
        self.pdf_preview = PDFPreview()
        
        # コンテナ参照（2分割構造）
        self.left_container = None
        self.right_container = None
        self.main_row = None
        
        # OCR関連状態
        self.selected_engine = "EasyOCR"  # 初期値
        self.engine_parameters = {}
        self.ocr_results = []  # OCR結果履歴
        self.results_container = None  # 結果表示コンテナ
        self.engine_details_container = None  # エンジン詳細コンテナ
        
        # ファイル選択関連
        self.selected_file_info: Optional[Dict[str, Any]] = None
        self.file_display_field: Optional[ft.TextField] = None  # ファイル表示フィールド
        self.file_selection_dialog = None  # ダイアログインスタンス

    def create_main_layout(self):
        """メインレイアウト作成（tab_b成功パターン適用：2分割構造）"""
        
        # 2分割メインコンテンツ作成（OCR機能保護、tab_b構造適用）
        main_2pane_content = self._create_2pane_layout()
        
        # 横スライダー（共通化済み）
        horizontal_slider = CommonComponents.create_horizontal_slider(
            self.horizontal_level, self.on_horizontal_change
        )
        
        # 基本レイアウト（横スライダー付き、縦スライダー不要）
        return PageStyles.create_complete_layout_with_slider(
            main_2pane_content, horizontal_slider
        )

    def _create_ocr_settings_pane(self):
        """左ペイン: OCR設定（tab_b完全パターン適用：タブ構造）"""
        
        # OCR設定基本内容（既存機能保護）
        ocr_settings_content = self._create_ocr_basic_settings()
        
        # 詳細設定アコーディオン（tab_bパターン適用）
        details_accordion = self._create_details_accordion_like_tab_b()
        
        # タブバー（tab_b完全パターン）
        tab_bar = ft.Container(
            content=ft.Row([
                ft.Container(
                    content=ft.Text("設定", size=12, weight=ft.FontWeight.BOLD,
                                   color=ft.Colors.BLUE_700 if self.selected_tab == 0 else ft.Colors.GREY_600),
                    padding=ft.padding.symmetric(horizontal=16, vertical=8),
                    bgcolor=ft.Colors.BLUE_50 if self.selected_tab == 0 else ft.Colors.GREY_100,
                    on_click=lambda e: self._switch_tab(0)
                ),
                ft.Container(
                    content=ft.Text("PDF", size=12, weight=ft.FontWeight.BOLD,
                                   color=ft.Colors.BLUE_700 if self.selected_tab == 1 else ft.Colors.GREY_600),
                    padding=ft.padding.symmetric(horizontal=16, vertical=8),
                    bgcolor=ft.Colors.BLUE_50 if self.selected_tab == 1 else ft.Colors.GREY_100,
                    on_click=lambda e: self._switch_tab(1)
                )
            ], spacing=2),
            padding=ft.padding.symmetric(horizontal=8, vertical=4),
            bgcolor=ft.Colors.GREY_50
        )
        
        # タブコンテンツ（動的切り替え）
        if self.selected_tab == 0:
            # 設定タブ：OCR設定 + 詳細設定アコーディオン
            tab_content = ft.Container(
                content=ft.Column([
                    ocr_settings_content,
                    details_accordion
                ], spacing=8, scroll=ft.ScrollMode.AUTO, expand=True),
                padding=ft.padding.all(4),
                expand=True
            )
        else:
            # PDFタブ：filesと同じメッセージを直接タブ内センタリング表示
            tab_content = ft.Container(
                content=ft.Column([
                    ft.Icon(ft.Icons.PICTURE_AS_PDF, size=80, color=ft.Colors.GREY_400),
                    ft.Container(height=16),
                    ft.Text("ファイルを選択すると\nPDFプレビューが表示されます", 
                           size=16, color=ft.Colors.GREY_600, text_align=ft.TextAlign.CENTER)
                ], 
                alignment=ft.MainAxisAlignment.CENTER, 
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=0),
                expand=True,
                padding=ft.padding.all(0),
                bgcolor=ft.Colors.WHITE,
                alignment=ft.alignment.center
            )
        
        # パネル作成（共通パネルコンポーネント使用、OCR実行ボタン付き）
        header_config = PanelHeaderConfig(
            title="OCR設定",
            title_icon=ft.Icons.SETTINGS,
            bgcolor=ft.Colors.BLUE_GREY_800,
            text_color=ft.Colors.WHITE
        )
        panel_config = PanelConfig(header_config=header_config)
        
        # タブ構造をパネルコンテンツとして使用
        tab_structure = ft.Container(
            content=ft.Column([
                tab_bar,
                tab_content
            ], spacing=0, expand=True, alignment=ft.MainAxisAlignment.START),
            expand=True
        )
        
        panel = create_panel(panel_config, tab_structure)
        
        # OCR実行ボタンをヘッダーに追加（既存パターン）
        from app.flet_ui.shared.common_buttons import create_action_button
        header_container = panel.content.controls[0]  # ヘッダー部分
        
        new_header_content = ft.Row([
            # 左側：タイトル部分
            ft.Container(
                content=ft.Row([
                    ft.Icon(ft.Icons.SETTINGS, size=20, color=ft.Colors.WHITE),
                    ft.Text("OCR設定", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)
                ], spacing=8),
                expand=True
            ),
            # 右側：実行ボタン（▶アイコン1つだけ）
            create_action_button("実行", ft.Icons.PLAY_ARROW, self._execute_ocr_test)
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
        
        header_container.content = new_header_content
        
        return panel
    
    def _create_details_accordion_like_tab_b(self):
        """詳細設定アコーディオン（tab_bと完全同一パターン）"""
        # OCR設定ページの既存詳細設定パネルから内容を取得
        if hasattr(self, '_create_engine_details_pane'):
            engine_details_panel = self._create_engine_details_pane()
            engine_details_content = engine_details_panel.content.controls[1]
        else:
            # フォールバック：基本的なプレースホルダー
            engine_details_content = ft.Container(
                content=ft.Text("詳細設定を読み込み中...", color=ft.Colors.GREY_600),
                padding=ft.padding.all(8)
            )
        
        # tab_bと完全同一のアコーディオン実装
        from app.flet_ui.shared.custom_accordion import make_accordion
        
        accordion = make_accordion(
            page=self.page,
            items=[
                ("🔧 詳細設定", engine_details_content, False)
            ],
            single_open=True,
            header_bg=ft.Colors.BLUE_50,
            body_bg=ft.Colors.WHITE,
            spacing=2,
            radius=0  # 角丸なし
        )
        
        return accordion
    
    def _switch_tab(self, tab_index: int):
        """タブ切り替え（正しい実装：パネル構造維持、タブ内容のみ切り替え）"""
        self.selected_tab = tab_index
        # 左ペイン内容を再作成して更新（パネル構造維持）
        if hasattr(self, 'left_container') and self.left_container:
            new_content = self._create_ocr_settings_pane()
            self.left_container.content = new_content
            self.left_container.update()
            print(f"⚡ OCR設定 タブ切り替え: {tab_index} ({'PDF' if tab_index == 1 else '設定'}タブ内容)")
    
    def _create_ocr_basic_settings(self):
        """OCR基本設定内容（既存機能保護）"""
        # パネル内容（実際のOCR設定項目）
        return ft.Container(
            content=ft.Column([
                # ファイル選択情報（統一レイアウト）
                ft.Row([
                    ft.Container(
                        content=ft.Text("ファイル:", weight=ft.FontWeight.BOLD, size=12),
                        width=120,  # 統一幅
                        alignment=ft.alignment.center_left
                    ),
                    self._create_file_display_field(),
                    ft.IconButton(
                        icon=ft.Icons.FOLDER_OPEN,
                        icon_size=20,
                        tooltip="ファイル選択",
                        on_click=self._on_file_select_click
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

    # _create_pdf_preview_pane() - 削除：PDFプレビューはPDFタブに統合
    
    def _create_2pane_layout(self) -> ft.Container:
        """2分割レイアウト作成（tab_b成功パターン適用、縦スライダー削除）"""
        
        # 左パネル：OCR設定（常にパネル構造、タブ内容で切り替え）
        self.left_container = ft.Container(
            content=self._create_ocr_settings_pane(),
            expand=1
        )
        
        # 右パネル：OCR結果
        self.right_container = ft.Container(
            content=self._create_ocr_results_pane(),
            expand=1
        )
        
        # 2分割メイン行作成（tab_b成功パターン）
        self.main_row = ft.Row([
            self.left_container,
            ft.VerticalDivider(width=1, thickness=1, color=ft.Colors.GREY_400),
            self.right_container
        ], spacing=0, expand=True)
        
        # 初期比率適用（共通メソッド使用）
        CommonComponents.apply_slider_ratios_to_row(
            self.main_row, self.ratios, self.horizontal_level
        )
        
        # 2分割部分のみ返す
        return ft.Container(content=self.main_row, expand=True)
    
    # 縦スライダー関連メソッドは削除（2分割構造では不要）
    
    # 縦スライダー関連メソッドは削除（2分割構造では不要）

    def on_horizontal_change(self, e):
        """左右分割スライダー変更（共通メソッド使用、OCR機能保護）"""
        try:
            self.horizontal_level = int(float(e.control.value))
        except ValueError:
            return
        
        # 共通メソッドで横比率適用（0対策自動適用）
        if hasattr(self, 'main_row') and self.main_row:
            CommonComponents.apply_slider_ratios_to_row(
                self.main_row, self.ratios, self.horizontal_level
            )
        
        print(f"⚡ OCR設定 横スライダー変更: レベル{self.horizontal_level}")
    
    # ========= ファイル選択機能 =========
    
    def _create_file_display_field(self) -> ft.TextField:
        """ファイル表示用テキストフィールド作成"""
        self.file_display_field = ft.TextField(
            hint_text="選択されたファイル名", 
            read_only=True,
            expand=True,
            height=40
        )
        return self.file_display_field
    
    def _on_file_select_click(self, e):
        """ファイル選択ボタンクリック"""
        print("ファイル選択がクリックされました")
        if not self.file_selection_dialog:
            self.file_selection_dialog = create_file_selection_dialog(
                page=self.page,
                on_file_selected=self._on_file_selected
            )
        
        self.file_selection_dialog.show_dialog()
    
    def _on_file_selected(self, file_info: Dict[str, Any]):
        """ファイル選択完了時の処理"""
        self.selected_file_info = file_info
        
        # ファイル表示フィールドに選択されたファイル名を表示
        if self.file_display_field and file_info:
            filename = file_info.get("filename", "")
            self.file_display_field.value = filename
            self.file_display_field.update()
            
            # OCR結果をクリア（新しいファイル選択時）
            self._clear_ocr_results()
            
            # ステータス表示等の更新
            self._update_file_selection_status(file_info)
    
    def _update_file_selection_status(self, file_info: Dict[str, Any]):
        """ファイル選択状態の更新"""
        # 後で拡張: ファイル情報表示、プレビューエリア更新等
        pass
    
    def _clear_ocr_results(self):
        """OCR結果をクリア"""
        if self.results_container:
            self.results_container.controls.clear()
            if self.results_container.page:
                self.results_container.update()
    
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
            # 専用レイアウトを使用（pageパラメータを渡す）
            content = engine_layout_functions[self.selected_engine](page=self.page)
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
    
    ocr_page = OCRAdjustmentPage(page=page)  # pageインスタンス渡し
    layout = ocr_page.create_main_layout()
    return layout

