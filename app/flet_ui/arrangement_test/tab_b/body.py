#!/usr/bin/env python3
"""
Flet RAGシステム - 配置テスト タブB (コンポーネント)
既存OCR調整ページコンポーネント厳格使用による新レイアウト実装
段階的実装：Phase 1 基本構造（左右パネル + 横スライダー）
"""

import flet as ft
from app.flet_ui.ocr_adjustment.page import OCRAdjustmentPage
from app.flet_ui.shared.panel_components import create_panel, PanelHeaderConfig, PanelConfig
from app.flet_ui.shared.style_constants import CommonComponents, PageStyles, SLIDER_RATIOS


class TabB:
    """タブB: 段階的実装による既存コンポーネント厳格使用"""
    
    def __init__(self):
        self.selected_tab = 0  # 0: 設定, 1: PDF
        self.page = None
        self.ocr_page = None
        
        # 共通比率テーブル使用（全ページ統一）
        self.horizontal_level = 3  # 中央（3:3）
        self.ratios = SLIDER_RATIOS
        
        # コンテナ参照（動的更新用）
        self.left_pane_container = None
        self.right_pane_container = None
        
    def create_content(self, page: ft.Page = None) -> ft.Control:
        """メインコンテンツ作成"""
        self.page = page
        if page:
            self.ocr_page = OCRAdjustmentPage(page)
        else:
            self.ocr_page = OCRAdjustmentPage()
        
        return self._create_basic_layout()
    
    def _create_basic_layout(self) -> ft.Control:
        """Phase 1: 基本レイアウト（左右パネル + 横スライダー）"""
        
        # 既存パターン適用: 初期比率取得
        left_ratio, right_ratio = self.ratios[self.horizontal_level]
        
        # 左ペイン（常にパネル構造、タブ内容で切り替え）
        self.left_pane_container = ft.Container(
            content=self._create_left_panel(),
            expand=left_ratio
        )
        
        # 右ペイン（統一パネル、既存パターン比率）
        self.right_pane_container = ft.Container(
            content=self._create_right_panel(),
            expand=right_ratio
        )
        
        # 横スライダー（filesページと完全統一）
        horizontal_slider = CommonComponents.create_horizontal_slider(
            self.horizontal_level, self._on_horizontal_change
        )
        
        # 左右レイアウト（既存Containerを直接使用）
        self.main_row = ft.Row([
            self.left_pane_container, 
            ft.VerticalDivider(),
            self.right_pane_container
        ], spacing=0, expand=True, vertical_alignment=ft.CrossAxisAlignment.STRETCH)
        
        # 初期比率適用（共通メソッド使用）
        CommonComponents.apply_slider_ratios_to_row(
            self.main_row, self.ratios, self.horizontal_level
        )
        
        # 全体レイアウト（filesページと完全統一）
        return PageStyles.create_complete_layout_with_slider(
            self.main_row, horizontal_slider
        )
    
    def _create_left_panel(self) -> ft.Control:
        """左ペイン: 共通パネル使用（統一形状）"""
        
        # パネル内容（実際のOCR設定内容 + 実行ボタン）
        panel_content = self._create_left_panel_content()
        
        # 共通パネル設定（右ペインと同じ形状、実行ボタン付き）
        header_config = PanelHeaderConfig(
            title="OCR設定",
            title_icon=ft.Icons.SETTINGS,
            bgcolor=ft.Colors.BLUE_GREY_800,
            text_color=ft.Colors.WHITE
        )
        
        panel_config = PanelConfig(header_config=header_config)
        
        # 統一パネル作成（右ペインと同じ形状）
        panel = create_panel(panel_config, panel_content)
        
        # パネルヘッダに実行ボタンを追加（既存OCR調整ページと同じパターン）
        from app.flet_ui.shared.common_buttons import create_action_button
        header_container = panel.content.controls[0]  # ヘッダー部分
        
        # 新しいヘッダー内容（タイトル + 右側の実行ボタン）
        new_header_content = ft.Row([
            # 左側：タイトル部分
            ft.Container(
                content=ft.Row([
                    ft.Icon(ft.Icons.SETTINGS, size=20, color=ft.Colors.WHITE),
                    ft.Text("OCR設定", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)
                ], spacing=8),
                expand=True
            ),
            # 右側：実行ボタン（▶アイコン1つだけ、既存と統一）
            create_action_button("実行", ft.Icons.PLAY_ARROW, self._execute_ocr_test)
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
        
        # ヘッダーコンテンツを置き換え
        header_container.content = new_header_content
        
        return panel
    
    def _create_right_panel(self) -> ft.Control:
        """右ペイン: 既存OCR結果パネル使用（統一形状）"""
        
        if self.ocr_page:
            # 既存OCR結果パネルをそのまま使用
            return self.ocr_page._create_ocr_results_pane()
        else:
            # フォールバック（共通パネル使用）
            panel_content = ft.Container(
                content=ft.Text("OCR結果パネルが利用できません", color=ft.Colors.RED),
                padding=ft.padding.all(8),
                expand=True
            )
            
            header_config = PanelHeaderConfig(
                title="OCR結果",
                title_icon=ft.Icons.TEXT_SNIPPET,
                bgcolor=ft.Colors.BLUE_GREY_800,
                text_color=ft.Colors.WHITE
            )
            
            panel_config = PanelConfig(header_config=header_config)
            return create_panel(panel_config, panel_content)
    
    def _create_left_panel_content(self) -> ft.Container:
        """左ペイン内容: 実際のOCR設定 + タブ + 実行ボタン"""
        if not self.ocr_page:
            return ft.Container(
                content=ft.Text("OCR設定が利用できません", color=ft.Colors.RED),
                padding=ft.padding.all(8),
                expand=True
            )
        
        # 既存OCR設定パネルの中身を取得
        ocr_settings_panel = self.ocr_page._create_ocr_settings_pane()
        ocr_settings_content = ocr_settings_panel.content.controls[1]  # 本体部分
        
        # 詳細設定（本物のアコーディオン）
        details_accordion = self._create_details_accordion()
        
        # 実行ボタン（共通ボタン使用、ヘッダーに配置予定のため削除）
        # execute_button = None  # パネルヘッダに移動
        
        # タブバー（動作版）
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
            # 設定タブ
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
        
        return ft.Container(
            content=ft.Column([
                tab_bar,
                tab_content
            ], spacing=0, expand=True, alignment=ft.MainAxisAlignment.START),
            expand=True
        )
    
    def _create_details_accordion(self) -> ft.Control:
        """詳細設定アコーディオン（本物）"""
        if not self.ocr_page or not self.page:
            return ft.Container(
                content=ft.Text("詳細設定が利用できません", color=ft.Colors.GREY_600),
                padding=ft.padding.all(8)
            )
        
        # 既存詳細設定パネルの中身を取得
        engine_details_panel = self.ocr_page._create_engine_details_pane()
        engine_details_content = engine_details_panel.content.controls[1]
        
        # 本物のアコーディオン
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
        if self.left_pane_container:
            new_content = self._create_left_panel()
            self.left_pane_container.content = new_content
            self.left_pane_container.update()
            print(f"⚡ tab_b タブ切り替え: {tab_index} ({'PDF' if tab_index == 1 else '設定'}タブ内容)")
    
    def _on_horizontal_change(self, e):
        """横スライダー変更（共通メソッド使用）"""
        self.horizontal_level = int(float(e.control.value))
        
        # 共通メソッドで0対策自動適用
        if hasattr(self, 'main_row') and self.main_row:
            CommonComponents.apply_slider_ratios_to_row(
                self.main_row, self.ratios, self.horizontal_level
            )
        
        print(f"横スライダー変更: レベル{self.horizontal_level}")

    def _execute_ocr_test(self, e):
        """OCR実行（プレースホルダー）"""
        print("🚀 OCR実行ボタンがクリックされました")
        # TODO: 実際のOCR実行処理を実装