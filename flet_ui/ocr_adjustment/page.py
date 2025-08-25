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
                                    expand=True,
                                    on_change=self._on_engine_change
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
                    height=32,
                    on_click=self._execute_ocr_test
                )
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
        # 結果表示コンテナ（動的更新用）
        self.results_container = ft.Column(
            controls=[],
            expand=True,
            scroll=ft.ScrollMode.AUTO,
            spacing=8
        )
        
        # 初期プレースホルダー表示
        self._show_results_placeholder()
        
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
                ft.ElevatedButton(
                    "クリア",
                    bgcolor=ft.Colors.GREY_600,
                    color=ft.Colors.WHITE,
                    height=32,
                    on_click=self._clear_results
                ),
                ft.ElevatedButton(
                    "出力",
                    bgcolor=ft.Colors.BLUE,
                    color=ft.Colors.WHITE,
                    height=32,
                    on_click=self._export_results
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
    
    # ========= OCR機能 =========
    def _on_engine_change(self, e):
        """OCRエンジン変更イベント"""
        self.selected_engine = e.control.value
        self._update_engine_details()
        if hasattr(self, 'engine_details_container') and self.engine_details_container.page:
            self.engine_details_container.update()
    
    def _show_results_placeholder(self):
        """OCR結果プレースホルダー表示"""
        if not self.results_container:
            return
        
        placeholder = ft.Container(
            content=ft.Column([
                ft.Icon(ft.Icons.TEXT_SNIPPET, size=64, color=ft.Colors.GREY_400),
                ft.Text("OCR実行すると", size=14, color=ft.Colors.GREY_600),
                ft.Text("結果がここに表示されます", size=14, color=ft.Colors.GREY_600),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            expand=True,
            alignment=ft.alignment.center
        )
        
        self.results_container.controls = [placeholder]
    
    def _update_engine_details(self):
        """エンジン詳細設定を更新"""
        if not self.engine_details_container:
            return
        
        # エンジン固有のパラメータを模擬実装（実際の実装では OCREngineFactory を使用）
        params = self._get_engine_parameters(self.selected_engine)
        
        controls = []
        for param in params:
            control_row = self._create_parameter_control(param)
            if control_row:
                controls.append(control_row)
        
        if not controls:
            controls.append(
                ft.Container(
                    content=ft.Text("このエンジンに設定項目はありません", 
                                   size=14, color=ft.Colors.GREY_600),
                    alignment=ft.alignment.center,
                    expand=True
                )
            )
        
        self.engine_details_container.controls = controls
    
    def _get_engine_parameters(self, engine_name: str) -> list:
        """エンジン別パラメータ定義（模擬実装）"""
        params_map = {
            "EasyOCR": [
                {
                    "name": "languages",
                    "label": "認識言語",
                    "type": "select",
                    "default": "日本語 + 英語",
                    "options": ["日本語のみ", "英語のみ", "日本語 + 英語", "中国語", "韓国語"],
                    "description": "OCR認識対象言語"
                },
                {
                    "name": "use_gpu",
                    "label": "GPU使用",
                    "type": "boolean",
                    "default": False,
                    "description": "GPU加速を使用（CUDA対応GPU必要）"
                },
                {
                    "name": "zoom_factor",
                    "label": "画像拡大倍率",
                    "type": "number",
                    "default": 2.0,
                    "min": 1.0,
                    "max": 4.0,
                    "step": 0.5,
                    "description": "画像の拡大倍率（高いほど精度向上、処理時間増加）"
                }
            ],
            "Tesseract": [
                {
                    "name": "psm",
                    "label": "ページセグメンテーションモード",
                    "type": "select",
                    "default": "6: 単一の均一テキストブロック",
                    "options": [
                        "3: 完全自動ページセグメンテーション",
                        "6: 単一の均一テキストブロック",
                        "7: 単一テキスト行",
                        "8: 単一単語"
                    ],
                    "description": "テキスト認識のセグメンテーション方法"
                },
                {
                    "name": "language",
                    "label": "認識言語",
                    "type": "select",
                    "default": "jpn+eng",
                    "options": ["jpn", "eng", "jpn+eng", "chi_sim", "kor"],
                    "description": "OCR認識対象言語"
                }
            ],
            "PaddleOCR": [
                {
                    "name": "lang",
                    "label": "認識言語",
                    "type": "select", 
                    "default": "japan",
                    "options": ["japan", "ch", "en", "korean", "french"],
                    "description": "OCR認識対象言語"
                },
                {
                    "name": "use_gpu",
                    "label": "GPU使用",
                    "type": "boolean",
                    "default": False,
                    "description": "GPU加速を使用"
                }
            ],
            "OCRMyPDF": [
                {
                    "name": "language",
                    "label": "認識言語",
                    "type": "select",
                    "default": "jpn+eng",
                    "options": ["jpn", "eng", "jpn+eng", "chi_sim", "kor"],
                    "description": "OCR認識対象言語"
                },
                {
                    "name": "dpi",
                    "label": "DPI設定",
                    "type": "number",
                    "default": 300,
                    "min": 150,
                    "max": 600,
                    "step": 50,
                    "description": "画像解像度（高いほど精度向上）"
                },
                {
                    "name": "optimize",
                    "label": "PDF最適化レベル",
                    "type": "select",
                    "default": "1: 軽度最適化（推奨）",
                    "options": [
                        "0: 最適化なし",
                        "1: 軽度最適化（推奨）",
                        "2: 中程度最適化",
                        "3: 高度最適化"
                    ],
                    "description": "出力PDFの最適化レベル"
                }
            ]
        }
        
        return params_map.get(engine_name, [])
    
    def _create_parameter_control(self, param: dict) -> ft.Control:
        """パラメータコントロールを作成"""
        param_name = param.get("name", "")
        param_label = param.get("label", param_name)
        param_type = param.get("type", "text")
        param_default = param.get("default")
        param_description = param.get("description", "")
        
        # ラベル部分
        label_container = ft.Container(
            content=ft.Text(f"{param_label}:", size=13, weight=ft.FontWeight.W_500),
            width=120,
            alignment=ft.alignment.center_left
        )
        
        # コントロール作成
        control_widget = None
        if param_type == "select":
            options = param.get("options", [])
            control_widget = ft.Dropdown(
                options=[ft.dropdown.Option(opt) for opt in options],
                value=param_default if param_default in options else None,
                expand=True
            )
        elif param_type == "number":
            control_widget = ft.TextField(
                value=str(param_default) if param_default is not None else "0",
                width=100,
                height=40,
                text_align=ft.TextAlign.CENTER,
                keyboard_type=ft.KeyboardType.NUMBER,
                input_filter=ft.NumbersOnlyInputFilter()
            )
        elif param_type == "boolean":
            control_widget = ft.Switch(value=bool(param_default))
        else:
            control_widget = ft.TextField(
                value=str(param_default) if param_default is not None else "",
                expand=True,
                height=40
            )
        
        # 説明部分（小さいテキスト）
        desc_text = ft.Text(
            param_description, 
            size=11, 
            color=ft.Colors.GREY_600,
            max_lines=2,
            overflow=ft.TextOverflow.ELLIPSIS
        ) if param_description else None
        
        # 行全体を作成
        row_content = [label_container, control_widget]
        
        return ft.Container(
            content=ft.Column([
                ft.Row(row_content, alignment=ft.MainAxisAlignment.START),
                desc_text
            ], spacing=4),
            padding=ft.padding.all(4)
        )
    
    def add_ocr_result(self, result_data: dict):
        """OCR結果をリトラクタブルセクションとして追加"""
        if not self.results_container:
            return
        
        # プレースホルダーがある場合は削除
        if (self.results_container.controls and 
            len(self.results_container.controls) == 1 and 
            isinstance(self.results_container.controls[0].content, ft.Column)):
            self.results_container.controls.clear()
        
        # 新しい結果セクションを作成して最上位に追加
        new_section = self._create_retractable_section(result_data)
        self.results_container.controls.insert(0, new_section)
        
        if self.results_container.page:
            self.results_container.update()
    
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
        
        # 結果が空の場合はプレースホルダーを表示
        if not self.results_container.controls:
            self._show_results_placeholder()
        
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

