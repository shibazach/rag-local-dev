#!/usr/bin/env python3
"""
Flet RAGシステム - 配置テスト タブB (コンポーネント)
各種コンポーネントテスト
"""

import flet as ft


class TabB:
    """タブB: コンポーネントテスト"""
    
    def __init__(self):
        pass
    
    def create_content(self) -> ft.Control:
        """タブBコンテンツ作成"""
        # ボタンテスト
        button_section = ft.Container(
            content=ft.Column([
                ft.Text("ボタンテスト", size=18, weight=ft.FontWeight.BOLD),
                ft.Row([
                    ft.ElevatedButton("標準ボタン"),
                    ft.OutlinedButton("アウトラインボタン"),
                    ft.TextButton("テキストボタン"),
                    ft.IconButton(icon=ft.Icons.FAVORITE, icon_color=ft.Colors.RED)
                ], wrap=True)
            ]),
            padding=ft.padding.all(16),
            bgcolor=ft.Colors.WHITE,
            border_radius=8,
            border=ft.border.all(1, ft.Colors.GREY_300)
        )
        
        # 入力コンポーネントテスト
        input_section = ft.Container(
            content=ft.Column([
                ft.Text("入力コンポーネントテスト", size=18, weight=ft.FontWeight.BOLD),
                ft.TextField(label="テキストフィールド", width=200),
                ft.Dropdown(
                    label="ドロップダウン",
                    options=[
                        ft.dropdown.Option("オプション1"),
                        ft.dropdown.Option("オプション2"),
                        ft.dropdown.Option("オプション3")
                    ],
                    width=200
                ),
                ft.Checkbox(label="チェックボックス"),
                ft.Switch(label="スイッチ"),
                ft.Slider(min=0, max=100, value=50, label="スライダー")
            ]),
            padding=ft.padding.all(16),
            bgcolor=ft.Colors.WHITE,
            border_radius=8,
            border=ft.border.all(1, ft.Colors.GREY_300)
        )
        
        # 表示コンポーネントテスト
        display_section = ft.Container(
            content=ft.Column([
                ft.Text("表示コンポーネントテスト", size=18, weight=ft.FontWeight.BOLD),
                ft.ProgressBar(value=0.7, width=200),
                ft.Icon(ft.Icons.STAR, color=ft.Colors.YELLOW, size=40),
                ft.Card(
                    content=ft.Container(
                        content=ft.Text("カードコンテンツ"),
                        padding=ft.padding.all(16)
                    ),
                    width=200
                )
            ]),
            padding=ft.padding.all(16),
            bgcolor=ft.Colors.WHITE,
            border_radius=8,
            border=ft.border.all(1, ft.Colors.GREY_300)
        )
        
        # メインレイアウト
        main_layout = ft.Column([
            button_section,
            ft.Container(height=16),
            input_section,
            ft.Container(height=16),
            display_section
        ], scroll=ft.ScrollMode.AUTO, expand=True)
        
        return ft.Container(
            content=main_layout,
            expand=True,
            padding=ft.padding.all(8)
        )

