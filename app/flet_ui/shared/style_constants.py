#!/usr/bin/env python3
"""
Flet RAGシステム - 共通UI定数・コンポーネント
機能別クラス構成で使いやすさ向上
"""

import flet as ft
import math


class Sliders:
    """スライダー関連コンポーネント"""
    
    # スライダー比率設定（1:5 ～ 5:1の5段階）
    RATIOS = {1: (1, 5), 2: (2, 4), 3: (3, 3), 4: (4, 2), 5: (5, 1)}
    
    @staticmethod
    def create_horizontal(value: float, on_change) -> ft.Slider:
        """水平スライダー（1-5段階、200px）"""
        return ft.Slider(
            min=1, max=5, value=value, divisions=4, label="{value}",
            on_change=on_change, width=200
        )
    
    @staticmethod
    def create_vertical(value: float, on_change) -> ft.Container:
        """垂直スライダー（1-5段階、90度回転、デバッグ用赤枠付き）"""
        return ft.Container(
            width=200, height=200,
            content=ft.Slider(
                min=1, max=5, value=value, divisions=4,
                rotate=math.pi / 2, on_change=on_change, 
                width=200, height=30
            ),
            # デバッグ用：オーバーレイ範囲を可視化
            bgcolor=ft.Colors.TRANSPARENT,
            border=ft.border.all(2, ft.Colors.RED)
        )
    
    @staticmethod
    def create_overlay_elements(left_value: float, left_on_change, 
                              right_value: float, right_on_change) -> list:
        """縦スライダー部分オーバーレイ要素（レスポンシブ中央配置）"""
        left_vslider = Sliders.create_vertical(left_value, left_on_change)
        right_vslider = Sliders.create_vertical(right_value, right_on_change)
        
        # 四象限パネル基準の中央配置：25%-50%-25%（横スライダー32px除外）
        left_overlay = ft.Container(
            content=ft.Column([
                ft.Container(expand=1),  # 上部（25%）
                ft.Container(
                    content=left_vslider,
                    expand=2,  # 中央部分（50%）
                    alignment=ft.alignment.center,
                    bgcolor="#FFCCCC"  # デバッグ用
                ),
                ft.Container(expand=1),  # 下部（25%）
            ], spacing=0),
            left=-84,
            top=0, bottom=32,  # 32px = 横スライダー高さを除外
            width=200,
        )
        
        right_overlay = ft.Container(
            content=ft.Column([
                ft.Container(expand=1),  # 上部（25%）
                ft.Container(
                    content=right_vslider,
                    expand=2,  # 中央部分（50%）
                    alignment=ft.alignment.center,
                    bgcolor="#FFCCCC"  # デバッグ用
                ),
                ft.Container(expand=1),  # 下部（25%）
            ], spacing=0),
            right=-84,
            top=0, bottom=32,  # 32px = 横スライダー高さを除外
            width=200,
        )
        
        return [left_overlay, right_overlay]
    
    @staticmethod  
    def create_complete_layout(
        main_content: ft.Control,
        left_value: float, left_on_change,
        right_value: float, right_on_change,
        horizontal_value: float, horizontal_on_change
    ) -> ft.Container:
        """完全一体型レイアウト：ガイド+縦スライダー+横スライダー"""
        
        # 横スライダー
        horizontal_slider = Sliders.create_horizontal(horizontal_value, horizontal_on_change)
        
        # ガイドエリア付きメインコンテンツ（左右36pxエリア確保）
        main_with_guides = ft.Container(
            expand=True,
            content=ft.Row([
                ft.Container(width=36, disabled=True),
                ft.Container(content=main_content, expand=True),
                ft.Container(width=36, disabled=True),
            ], expand=True, spacing=0, vertical_alignment=ft.CrossAxisAlignment.STRETCH)
        )
        
        # 基本レイアウト（ガイド + 横スライダー）
        base_layer = Layouts.create_with_bottom_slider(main_with_guides, horizontal_slider)
        
        # 縦スライダーオーバーレイ
        overlay_elements = Sliders.create_overlay_elements(
            left_value, left_on_change, right_value, right_on_change
        )
        
        # Stack構成
        return ft.Container(
            content=ft.Stack(
                expand=True, clip_behavior=ft.ClipBehavior.NONE,
                controls=[base_layer] + overlay_elements
            ),
            expand=True
        )


class Layouts:
    """レイアウト関連コンポーネント"""
    
    @staticmethod
    def create_row(left: ft.Control, right: ft.Control, spacing: int = 0) -> ft.Row:
        """標準左右分割Row"""
        return ft.Row([left, right], spacing=spacing, expand=True, 
                     vertical_alignment=ft.CrossAxisAlignment.STRETCH)
    
    @staticmethod
    def create_column(*contents: ft.Control, spacing: int = 0) -> ft.Column:
        """標準縦配置Column"""
        return ft.Column(list(contents), spacing=spacing, expand=True)
    
    @staticmethod
    def create_container(content: ft.Control, expand: bool = True, 
                        padding: int = 8) -> ft.Container:
        """標準Container"""
        return ft.Container(content=content, expand=expand, 
                           padding=ft.padding.all(padding))
    
    @staticmethod
    def create_sidebar(content: ft.Control, position: str = "left") -> ft.Container:
        """サイドバー（36px幅、境界線付き）"""
        border = ft.border.only(right=ft.BorderSide(1, ft.Colors.GREY_300)) if position == "left" \
                 else ft.border.only(left=ft.BorderSide(1, ft.Colors.GREY_300))
        return ft.Container(content=content, width=36, bgcolor=ft.Colors.GREY_50, border=border)
    
    @staticmethod
    def create_bottombar(content: ft.Control) -> ft.Container:
        """ボトムバー（32px高さ、上境界線付き）"""
        return ft.Container(
            content=content, height=32, bgcolor=ft.Colors.GREY_50,
            border=ft.border.only(top=ft.BorderSide(1, ft.Colors.GREY_300))
        )
    
    @staticmethod
    def create_with_bottom_slider(top_content: ft.Control, slider: ft.Slider) -> ft.Container:
        """上部コンテンツ + 下部スライダー"""
        return ft.Container(
            content=ft.Column([
                ft.Container(content=top_content, expand=True),
                Layouts.create_bottombar(
                    ft.Row([slider], alignment=ft.MainAxisAlignment.CENTER)
                )
            ], spacing=0, expand=True),
            expand=True
        )
    
    @staticmethod  
    def create_spacing(size: int = 16) -> ft.Container:
        """縦間隔調整"""
        return ft.Container(height=size)
    
    @staticmethod
    def create_width_spacing(size: int = 8) -> ft.Container:
        """横間隔調整"""
        return ft.Container(width=size)


class Components:
    """基本UIコンポーネント"""
    
    @staticmethod
    def create_divider() -> ft.Divider:
        """水平区切り線"""
        return ft.Divider(height=1, thickness=1, color=ft.Colors.GREY_300)
    
    @staticmethod  
    def create_vertical_divider() -> ft.VerticalDivider:
        """垂直区切り線"""
        return ft.VerticalDivider(width=1, thickness=1, color=ft.Colors.GREY_300)
    
    @staticmethod
    def create_primary_button(text: str, on_click=None) -> ft.ElevatedButton:
        """プライマリボタン（青背景）"""
        return ft.ElevatedButton(
            text=text, on_click=on_click,
            bgcolor=ft.Colors.BLUE, color=ft.Colors.WHITE,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8))
        )
    
    @staticmethod
    def create_secondary_button(text: str, on_click=None) -> ft.ElevatedButton:
        """セカンダリボタン（グレー背景）"""
        return ft.ElevatedButton(
            text=text, on_click=on_click,
            bgcolor=ft.Colors.GREY_300, color=ft.Colors.BLACK,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8))
        )
    
    @staticmethod
    def create_text(text: str, center: bool = True) -> ft.Text:
        """標準テキスト"""
        return ft.Text(
            text, size=14, color=ft.Colors.GREY_600,
            text_align=ft.TextAlign.CENTER if center else ft.TextAlign.LEFT
        )
    
    @staticmethod
    def create_icon(icon: ft.Icon, size: int = 60) -> ft.Icon:
        """標準アイコン"""
        return ft.Icon(icon, size=size, color=ft.Colors.GREY_400)
    
    @staticmethod
    def create_panel_header_config(title: str, icon: ft.Icons) -> 'PanelHeaderConfig':
        """パネルヘッダー設定"""
        from .panel_components import PanelHeaderConfig
        return PanelHeaderConfig(
            title=title, title_icon=icon,
            bgcolor=ft.Colors.BLUE_GREY_800, text_color=ft.Colors.WHITE
        )


class Styles:
    """ページスタイル・テーマ管理"""
    
    @staticmethod
    def set_page_background(page: ft.Page):
        """ページ背景設定"""
        page.bgcolor = ft.Colors.GREY_50
        page.padding = 0
    
    @staticmethod
    def create_main_container(content: ft.Control) -> ft.Container:
        """メインコンテナ（統一背景）"""
        return ft.Container(content=content, expand=True, bgcolor=ft.Colors.GREY_50)
    
    @staticmethod
    def create_error_container(error_message: str) -> ft.Container:
        """エラー表示コンテナ"""
        return ft.Container(
            content=ft.Column([
                ft.Icon(ft.Icons.ERROR, size=64, color=ft.Colors.RED),
                ft.Text(f"エラー: {error_message}", size=16, color=ft.Colors.RED)
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            alignment=ft.alignment.center, expand=True,
            bgcolor=ft.Colors.RED_50, padding=20
        )


# 後方互換性エイリアス（完全版）
class CommonComponents:
    """統合コンポーネントクラス（全機能アクセス）"""
    
    # Sliders
    create_horizontal_slider = staticmethod(Sliders.create_horizontal)
    create_vertical_slider = staticmethod(Sliders.create_vertical)
    create_vertical_slider_overlay_elements = staticmethod(Sliders.create_overlay_elements)
    create_complete_layout_with_full_sliders = staticmethod(Sliders.create_complete_layout)
    
    # Layouts
    create_main_layout_row = staticmethod(Layouts.create_row)
    create_main_layout_column = staticmethod(Layouts.create_column)
    create_sidebar_container = staticmethod(Layouts.create_sidebar)
    create_bottombar_container = staticmethod(Layouts.create_bottombar)
    create_spacing_container = staticmethod(Layouts.create_spacing)
    create_width_spacing_container = staticmethod(Layouts.create_width_spacing)
    create_standard_container = staticmethod(Layouts.create_container)
    
    @staticmethod
    def create_standard_column(contents: list, expand: bool = True) -> ft.Column:
        """標準Column（リスト引数版）"""
        return ft.Column(contents, expand=expand, spacing=0)
    
    @staticmethod  
    def create_standard_row(contents: list, expand: bool = True) -> ft.Row:
        """標準Row（リスト引数版）"""
        return ft.Row(contents, expand=expand, spacing=0)
    
    # Components
    create_horizontal_divider = staticmethod(Components.create_divider)
    create_vertical_divider = staticmethod(Components.create_vertical_divider)
    create_primary_button = staticmethod(Components.create_primary_button)
    create_secondary_button = staticmethod(Components.create_secondary_button)
    create_standard_text = staticmethod(Components.create_text)
    create_standard_icon = staticmethod(Components.create_icon)
    create_standard_panel_header_config = staticmethod(Components.create_panel_header_config)


class PageStyles:
    """ページスタイル統合クラス"""
    
    set_page_background = staticmethod(Styles.set_page_background)
    create_main_layout_container = staticmethod(Styles.create_main_container)
    create_complete_layout_with_slider = staticmethod(Layouts.create_with_bottom_slider)
    create_error_container = staticmethod(Styles.create_error_container)


# 定数エイリアス
SLIDER_RATIOS = Sliders.RATIOS