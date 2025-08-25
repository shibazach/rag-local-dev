#!/usr/bin/env python3
"""
Flet RAGシステム - 配置テスト タブA (レイアウト)
4分割レイアウトテスト
"""

import flet as ft
from ..shared.style_constants import CommonComponents


class TabA:
    """タブA: レイアウトテスト"""
    
    def __init__(self):
        pass
    
    def create_content(self) -> ft.Control:
        """タブAコンテンツ作成"""
        # 4つのペイン作成
        
        # 横スライダーテスト用ハンドラー
        def on_slider_change(e):
            print(f"スライダー値: {e.control.value}")
        
        # 共通コンポーネント横スライダーをテスト配置
        test_slider = CommonComponents.create_horizontal_slider(3, on_slider_change)
        
        top_left = ft.Container(
            content=ft.Column([
                ft.Text("左上 - 横スライダーテスト", size=16, text_align=ft.TextAlign.CENTER),
                test_slider
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            bgcolor=ft.Colors.RED_100,
            alignment=ft.alignment.center,
            expand=True,
            border=ft.border.all(2, ft.Colors.RED_300),
            padding=ft.padding.all(10)
        )
        
        bottom_left = ft.Container(
            content=ft.Text("左下", size=20, text_align=ft.TextAlign.CENTER),
            bgcolor=ft.Colors.BLUE_100,
            alignment=ft.alignment.center,
            expand=True,
            border=ft.border.all(2, ft.Colors.BLUE_300)
        )
        
        top_right = ft.Container(
            content=ft.Text("右上", size=20, text_align=ft.TextAlign.CENTER),
            bgcolor=ft.Colors.GREEN_100,
            alignment=ft.alignment.center,
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