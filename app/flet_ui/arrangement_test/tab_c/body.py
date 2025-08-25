#!/usr/bin/env python3
"""
Flet RAGシステム - 配置テスト タブC (縦スライダーテスト)
動的調整可能な縦スライダーテスト
"""

import flet as ft
import math


class TabC:
    """タブC: 縦スライダーテスト"""
    
    def __init__(self):
        self.slider_width = 300
        self.slider_height = 30
        self.container_width = 60
        self.container_height = 400
        self.spacing = 20
    
    def create_content(self) -> ft.Control:
        """タブCコンテンツ作成"""
        # 縦スライダー作成
        self.left_slider = ft.Slider(
            min=0, max=100, value=30,
            width=self.slider_width,
            height=self.slider_height,
            rotate=math.pi / 2,
            expand=1
        )
        
        self.right_slider = ft.Slider(
            min=0, max=100, value=70,
            width=self.slider_width,
            height=self.slider_height,
            rotate=math.pi / 2,
            expand=1
        )
        
        # スライダーコンテナ
        self.left_container = ft.Container(
            content=ft.Column([self.left_slider], alignment=ft.MainAxisAlignment.CENTER, expand=True),
            width=self.container_width,
            height=self.container_height,
            bgcolor=ft.Colors.BLUE_50,
            border=ft.border.all(2, ft.Colors.BLUE_300),
            border_radius=8
        )
        
        self.right_container = ft.Container(
            content=ft.Column([self.right_slider], alignment=ft.MainAxisAlignment.CENTER, expand=True),
            width=self.container_width,
            height=self.container_height,
            bgcolor=ft.Colors.GREEN_50,
            border=ft.border.all(2, ft.Colors.GREEN_300),
            border_radius=8
        )
        
        # 中央エリア
        center_area = ft.Container(
            content=ft.Text("中央エリア", size=20, text_align=ft.TextAlign.CENTER),
            bgcolor=ft.Colors.GREY_100,
            alignment=ft.alignment.center,
            expand=True,
            border=ft.border.all(2, ft.Colors.GREY_400),
            border_radius=8
        )
        
        # スライダーレイアウト
        slider_layout = ft.Row([
            self.left_container,
            ft.Container(width=self.spacing),
            center_area,
            ft.Container(width=self.spacing),
            self.right_container
        ], alignment=ft.MainAxisAlignment.CENTER, expand=True)
        
        # 動的調整パネル
        control_panel = self._create_control_panel()
        
        # メインレイアウト
        main_layout = ft.Column([
            ft.Container(
                content=slider_layout,
                expand=True,
                padding=ft.padding.all(20)
            ),
            ft.Divider(height=1, thickness=1, color=ft.Colors.GREY_400),
            control_panel
        ], expand=True)
        
        return main_layout
    
    def _create_control_panel(self) -> ft.Container:
        """動的調整パネル作成"""
        # スライダー幅調整
        width_slider = ft.Slider(
            min=200, max=500, value=self.slider_width,
            label="幅: {value}px",
            on_change=self._on_width_change
        )
        
        # スライダー太さ調整
        height_slider = ft.Slider(
            min=20, max=50, value=self.slider_height,
            label="太さ: {value}px",
            on_change=self._on_height_change
        )
        
        # コンテナ幅調整
        container_width_slider = ft.Slider(
            min=40, max=100, value=self.container_width,
            label="コンテナ幅: {value}px",
            on_change=self._on_container_width_change
        )
        
        # コンテナ高さ調整
        container_height_slider = ft.Slider(
            min=300, max=600, value=self.container_height,
            label="コンテナ高さ: {value}px",
            on_change=self._on_container_height_change
        )
        
        # 間隔調整
        spacing_slider = ft.Slider(
            min=0, max=50, value=self.spacing,
            label="間隔: {value}px",
            on_change=self._on_spacing_change
        )
        
        control_content = ft.Column([
            ft.Text("動的調整パネル", size=16, weight=ft.FontWeight.BOLD),
            ft.Row([
                ft.Text("スライダー幅:", width=120),
                width_slider
            ]),
            ft.Row([
                ft.Text("スライダー太さ:", width=120),
                height_slider
            ]),
            ft.Row([
                ft.Text("コンテナ幅:", width=120),
                container_width_slider
            ]),
            ft.Row([
                ft.Text("コンテナ高さ:", width=120),
                container_height_slider
            ]),
            ft.Row([
                ft.Text("間隔:", width=120),
                spacing_slider
            ])
        ])
        
        return ft.Container(
            content=control_content,
            padding=ft.padding.all(16),
            bgcolor=ft.Colors.WHITE,
            border=ft.border.only(top=ft.BorderSide(1, ft.Colors.GREY_300))
        )
    
    def _on_width_change(self, e):
        """スライダー幅変更"""
        self.slider_width = int(e.control.value)
        self.left_slider.width = self.slider_width
        self.right_slider.width = self.slider_width
        self.left_slider.update()
        self.right_slider.update()
    
    def _on_height_change(self, e):
        """スライダー太さ変更"""
        self.slider_height = int(e.control.value)
        self.left_slider.height = self.slider_height
        self.right_slider.height = self.slider_height
        self.left_slider.update()
        self.right_slider.update()
    
    def _on_container_width_change(self, e):
        """コンテナ幅変更"""
        self.container_width = int(e.control.value)
        self.left_container.width = self.container_width
        self.right_container.width = self.container_width
        self.left_container.update()
        self.right_container.update()
    
    def _on_container_height_change(self, e):
        """コンテナ高さ変更"""
        self.container_height = int(e.control.value)
        self.left_container.height = self.container_height
        self.right_container.height = self.container_height
        self.left_container.update()
        self.right_container.update()
    
    def _on_spacing_change(self, e):
        """間隔変更"""
        self.spacing = int(e.control.value)
        # 間隔の更新は親レイアウトの再構築が必要
        print(f"間隔を{self.spacing}pxに変更（レイアウト再構築が必要）")

