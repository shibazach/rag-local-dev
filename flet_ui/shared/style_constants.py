#!/usr/bin/env python3
"""
Flet RAGシステム - 共通スタイル定数
全ページで使用するスタイル設定を統一管理
"""

import flet as ft
import math


# プロジェクト専用の組み込み設定のため、定数クラスは不要

# 共通スライダー設定
SLIDER_RATIOS = {1: (1, 5), 2: (2, 4), 3: (3, 3), 4: (4, 2), 5: (5, 1)}  # 1:5 ～ 5:1の5段階


class CommonComponents:
    """共通コンポーネント・スタイル定義"""
    
    @staticmethod
    def create_horizontal_divider() -> ft.Divider:
        """水平区切り線（プロジェクト標準設定済み）"""
        return ft.Divider(height=1, thickness=1, color=ft.Colors.GREY_300)
    
    @staticmethod  
    def create_vertical_divider() -> ft.VerticalDivider:
        """垂直区切り線（プロジェクト標準設定済み）"""
        return ft.VerticalDivider(width=1, thickness=1, color=ft.Colors.GREY_300)
    
    @staticmethod
    def create_horizontal_slider(value: float, on_change) -> ft.Slider:
        """水平スライダー（プロジェクト標準: 1-5段階、幅300px）"""
        return ft.Slider(
            min=1, max=5, value=value, divisions=4, label="{value}",
            on_change=on_change, width=300
        )
    
    @staticmethod
    def create_vertical_slider(value: float, on_change) -> ft.Container:
        """垂直スライダー（プロジェクト標準: 1-5段階、90度回転、赤枠付き）"""
        return ft.Container(
            width=200,         # 操作領域確保
            height=200,        # 操作領域確保
            content=ft.Slider(
                min=1, max=5, value=value, divisions=4,
                rotate=math.pi / 2, on_change=on_change, 
                width=200, height=30  # 回転時の実効サイズ
            ),
            # 赤枠でサイズ確認用
            border=ft.border.all(2, ft.Colors.RED),
            bgcolor=ft.Colors.TRANSPARENT
        )
    
    @staticmethod
    def create_vertical_slider_overlay_elements(left_value: float, left_on_change, 
                                              right_value: float, right_on_change) -> list:
        """縦スライダー部分オーバーレイ要素作成（左右端配置、中央エリア自由確保）"""
        left_vslider = CommonComponents.create_vertical_slider(left_value, left_on_change)
        right_vslider = CommonComponents.create_vertical_slider(right_value, right_on_change)
        
        return [
            # 左端オーバーレイ（-84pxはみ出し配置）
            ft.Container(
                content=left_vslider,
                left=-84, top=0, bottom=32,  # 下32px空けて横スライダーと重複回避
            ),
            # 右端オーバーレイ（-84pxはみ出し配置） 
            ft.Container(
                content=right_vslider,
                right=-84, top=0, bottom=32,  # 下32px空けて横スライダーと重複回避
            )
        ]
    
    @staticmethod
    def create_sidebar_container(content: ft.Control, position: str = "left") -> ft.Container:
        """サイドバーコンテナ（プロジェクト標準: 36px幅、灰色背景、境界線付き）"""
        border = ft.border.only(right=ft.BorderSide(1, ft.Colors.GREY_300)) if position == "left" \
                 else ft.border.only(left=ft.BorderSide(1, ft.Colors.GREY_300))
        return ft.Container(
            content=content, width=36, bgcolor=ft.Colors.GREY_50, border=border
        )
    
    @staticmethod
    def create_bottombar_container(content: ft.Control) -> ft.Container:
        """ボトムバーコンテナ（プロジェクト標準: 32px高さ、灰色背景、上境界線）"""
        return ft.Container(
            content=content, height=32, bgcolor=ft.Colors.GREY_50,
            border=ft.border.only(top=ft.BorderSide(1, ft.Colors.GREY_300))
        )
    
    @staticmethod
    def create_spacing_container(size: int = 16) -> ft.Container:
        """間隔調整用コンテナ（デフォルト16px）"""
        return ft.Container(height=size)
    
    @staticmethod
    def create_width_spacing_container(size: int = 8) -> ft.Container:
        """幅間隔調整用コンテナ（デフォルト8px）"""
        return ft.Container(width=size)
    
    @staticmethod
    def create_primary_button(text: str, on_click=None) -> ft.ElevatedButton:
        """プライマリボタン（プロジェクト標準: 200x36px、青色）"""
        return ft.ElevatedButton(
            text, width=200, height=36,
            bgcolor=ft.Colors.BLUE_600, color=ft.Colors.WHITE, on_click=on_click
        )
    
    @staticmethod
    def create_secondary_button(text: str, on_click=None) -> ft.ElevatedButton:
        """セカンダリボタン（プロジェクト標準: 200x36px、グレー）"""
        return ft.ElevatedButton(
            text, width=200, height=36, on_click=on_click
        )
    
    @staticmethod
    def create_standard_text(text: str, center: bool = True) -> ft.Text:
        """標準テキスト（プロジェクト標準: 14px、グレー色）"""
        return ft.Text(
            text, size=14, color=ft.Colors.GREY_600,
            text_align=ft.TextAlign.CENTER if center else None
        )
    
    @staticmethod
    def create_standard_icon(icon: ft.Icon, size: int = 60) -> ft.Icon:
        """標準アイコン（プロジェクト標準: 60px、グレー400色）"""
        return ft.Icon(icon, size=size, color=ft.Colors.GREY_400)
    
    @staticmethod
    def create_standard_panel_header_config(title: str, icon: ft.Icons) -> 'PanelHeaderConfig':
        """標準パネルヘッダー設定（プロジェクト標準: BLUE_GREY_800背景）"""
        from .panel_components import PanelHeaderConfig
        return PanelHeaderConfig(
            title=title, title_icon=icon,
            bgcolor=ft.Colors.BLUE_GREY_800, text_color=ft.Colors.WHITE
        )
    
    @staticmethod
    def create_main_layout_row(left_content: ft.Control, right_content: ft.Control, 
                              divider: bool = True) -> ft.Row:
        """メインレイアウト行（プロジェクト標準: 左右ペイン + 区切り線）"""
        controls = [left_content]
        if divider:
            controls.append(CommonComponents.create_vertical_divider())
        controls.append(right_content)
        return ft.Row(controls, spacing=0, expand=True, vertical_alignment=ft.CrossAxisAlignment.STRETCH)
    
    @staticmethod
    def create_main_layout_column(*contents: ft.Control) -> ft.Column:
        """メインレイアウト列（プロジェクト標準: spacing=0, expand=True）"""
        return ft.Column(list(contents), spacing=0, expand=True)
    
    @staticmethod
    def create_standard_column(contents: list, expand: bool = True) -> ft.Column:
        """標準カラム（プロジェクト標準: spacing=0）"""
        return ft.Column(contents, expand=expand, spacing=0)
    
    @staticmethod
    def create_standard_row(contents: list, expand: bool = True) -> ft.Row:
        """標準ロー（プロジェクト標準: spacing=0）"""
        return ft.Row(contents, expand=expand, spacing=0)
    
    @staticmethod
    def create_standard_container(content: ft.Control, expand: bool = True, 
                                 bgcolor: str = None) -> ft.Container:
        """標準コンテナ（プロジェクト標準設定）"""
        return ft.Container(
            content=content, expand=expand,
            bgcolor=bgcolor or ft.Colors.GREY_50
        )


class PageStyles:
    """ページレイアウト統一設定"""
    
    @staticmethod
    def set_page_background(page: ft.Page):
        """ページ背景色統一設定（プロジェクト標準: GREY_50）"""
        if page:
            page.bgcolor = ft.Colors.GREY_50
    
    @staticmethod
    def create_main_layout_container(content: ft.Control) -> ft.Container:
        """メインレイアウトコンテナ（プロジェクト標準: expand + GREY_50背景）"""
        return ft.Container(content=content, expand=True, bgcolor=ft.Colors.GREY_50)
    
    @staticmethod 
    def create_complete_layout_with_slider(top_content: ft.Control, slider: ft.Slider) -> ft.Container:
        """完全レイアウト（プロジェクト標準: 上部コンテンツ + 下部スライダーバー）"""
        bottom_bar = CommonComponents.create_bottombar_container(
            ft.Row([slider], alignment=ft.MainAxisAlignment.CENTER)
        )
        return ft.Container(
            content=ft.Column([top_content, bottom_bar], spacing=0, expand=True),
            expand=True
        )
    
    @staticmethod
    def create_error_container(error_message: str) -> ft.Container:
        """エラー表示コンテナ（プロジェクト標準: 赤色テキスト、20pxパディング）"""
        return ft.Container(
            content=ft.Text(error_message, color=ft.Colors.RED),
            padding=ft.padding.all(20)
        )
