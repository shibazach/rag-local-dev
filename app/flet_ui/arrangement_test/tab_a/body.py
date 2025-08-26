#!/usr/bin/env python3
"""
Flet RAGシステム - 配置テスト タブA (レイアウト)
4分割レイアウトテスト
"""

import flet as ft


class TabA:
    """タブA: レイアウトテスト"""
    
    def __init__(self):
        pass
    
    def create_content(self, page: ft.Page = None) -> ft.Control:
        """タブAコンテンツ作成"""
        # 4つのペイン作成
        # 左上：日本語フォントテスト表示
        font_test_content = ft.Column([
            ft.Text("日本語フォント表示テスト", size=16, weight=ft.FontWeight.BOLD),
            ft.Divider(height=1, color=ft.Colors.GREY_300),
            
            # デフォルトフォント（2段階拡大+全黒色）
            ft.Text("デフォルト: 日本語テキスト（ひらがな・カタカナ・漢字）", size=16, color=ft.Colors.BLACK),
            ft.Text("Default: 这是中文文本", size=16, color=ft.Colors.BLACK),
            
            # font_family指定テスト（存在する場合）
            ft.Text("Arial指定: 日本語テキスト（ひらがな・カタカナ・漢字）", 
                   size=16, font_family="Arial", color=ft.Colors.BLACK),
            ft.Text("Helvetica指定: 日本語テキスト（ひらがな・カタカナ・漢字）", 
                   size=16, font_family="Helvetica", color=ft.Colors.BLACK),
            ft.Text("Courier指定: 日本語テキスト（ひらがな・カタカナ・漢字）", 
                   size=16, font_family="Courier New", color=ft.Colors.BLACK),
            
            # OCR詳細設定パネルと同じスタイルで表示（2段階拡大+全黒色）
            ft.Text("OCRパネル用統一スタイル:", size=14, color=ft.Colors.BLACK),
            ft.Text("認識言語:", size=18, weight=ft.FontWeight.W_500, color=ft.Colors.BLACK),
            ft.Text("簡易説明テキスト", size=15, color=ft.Colors.BLACK),
            
        ], spacing=4, scroll=ft.ScrollMode.AUTO, tight=True)
        
        top_left = ft.Container(
            content=font_test_content,
            bgcolor=ft.Colors.RED_100,
            padding=ft.padding.all(12),
            expand=True,
            border=ft.border.all(2, ft.Colors.RED_300)
        )
        
        bottom_left = ft.Container(
            content=ft.Text("左下", size=20, text_align=ft.TextAlign.CENTER),
            bgcolor=ft.Colors.BLUE_100,
            alignment=ft.alignment.center,
            expand=True,
            border=ft.border.all(2, ft.Colors.BLUE_300)
        )
        
        # 右上：自作アコーディオンテスト（関数型）
        from app.flet_ui.shared.custom_accordion import make_accordion
        
        # テスト用コンテンツ
        content1 = ft.Column([
            ft.Text("基本設定のテスト内容"),
            ft.TextField(label="テスト入力", width=200),
            ft.Switch(label="テストスイッチ")
        ])
        
        content2 = ft.Column([
            ft.Text("高精度設定のテスト内容"),
            ft.Slider(min=0, max=100, value=50, label="閾値"),
            ft.Dropdown(
                options=[ft.dropdown.Option("Option1"), ft.dropdown.Option("Option2")],
                value="Option1",
                width=150
            )
        ])
        
        content3 = ft.Column([
            ft.Text("詳細設定のテスト内容"),
            ft.Row([
                ft.Checkbox(label="チェック1"),
                ft.Checkbox(label="チェック2")
            ]),
            ft.ElevatedButton("テストボタン")
        ])
        
        # アコーディオン作成（関数型バージョン）
        # 実際のページインスタンスを使用
        if page is None:
            # フォールバック：ダミーページ（本来は避けるべき）
            test_page = ft.Page()
            test_page.update = lambda: None
            actual_page = test_page
        else:
            actual_page = page
        
        accordion = make_accordion(
            page=actual_page,
            items=[
                ("基本設定", content1, True),
                ("高精度設定", content2, False),
                ("詳細設定", content3, False),
            ],
            single_open=True,
            header_bg=ft.Colors.BLUE_50,
            body_bg=ft.Colors.BLUE_50,
            spacing=4
        )
        
        top_right = ft.Container(
            content=ft.Column([
                ft.Text("自作アコーディオンテスト", size=14, weight=ft.FontWeight.BOLD),
                accordion
            ], spacing=8),
            bgcolor=ft.Colors.GREEN_100,
            padding=ft.padding.all(8),
            expand=True,
            border=ft.border.all(2, ft.Colors.GREEN_300)
        )
        
        bottom_right = ft.Container(
            content=ft.Text("右下", size=20, text_align=ft.TextAlign.CENTER),
            bgcolor=ft.Colors.YELLOW_100,
            alignment=ft.alignment.center,
            expand=True,
            border=ft.border.all(2, ft.Colors.YELLOW_600)
        )
        
        # 左ペイン（上下分割）
        left_column = ft.Column([
            top_left,
            ft.Divider(height=1, thickness=1, color=ft.Colors.GREY_400),
            bottom_left
        ], expand=True, spacing=0)
        
        # 右ペイン（上下分割）
        right_column = ft.Column([
            top_right,
            ft.Divider(height=1, thickness=1, color=ft.Colors.GREY_400),
            bottom_right
        ], expand=True, spacing=0)
        
        # メインレイアウト（左右分割）
        main_layout = ft.Row([
            left_column,
            ft.VerticalDivider(width=1, thickness=1, color=ft.Colors.GREY_400),
            right_column
        ], spacing=0, expand=True)
        
        return ft.Container(
            content=main_layout,
            expand=True,
            padding=ft.padding.all(8)
        )