#!/usr/bin/env python3
"""
Flet RAGシステム - 配置テストページメイン
"""

import flet as ft
from .tab_a import TabA
from .tab_b import TabB
from .tab_c import TabC
from .tab_d import TabD
from .tab_e import TabE
from ..shared.style_constants import PageStyles


class ArrangementTestPage:
    """配置テストページ"""
    
    def __init__(self):
        self.current_tab = 0
        self.tab_content_container = ft.Container(expand=True)
        
        # タブインスタンス
        self.tab_a = TabA()
        self.tab_b = TabB()
        self.tab_c = TabC()
        self.tab_d = TabD()
        self.tab_e = TabE()
    
    def create_main_layout(self):
        """メインレイアウト作成"""
        # タブ作成
        tabs = ft.Tabs(
            selected_index=0,
            on_change=self.on_tab_change,
            tabs=[
                ft.Tab(text="レイアウト", icon=ft.Icons.GRID_VIEW),
                ft.Tab(text="コンポーネント", icon=ft.Icons.WIDGETS),
                ft.Tab(text="縦スライダーテスト", icon=ft.Icons.TUNE),
                ft.Tab(text="縦スライダーレイヤー検討", icon=ft.Icons.LAYERS),
                ft.Tab(text="総合展示", icon=ft.Icons.VIEW_MODULE)
            ]
        )
        
        # 初期タブコンテンツ設定
        self._create_tab_content(0)
        
        # メインレイアウト
        main_layout = ft.Column([
            tabs,
            self.tab_content_container
        ], expand=True, spacing=0)
        
        return ft.Container(
            content=main_layout,
            expand=True,
            bgcolor=ft.Colors.GREY_50
        )
    
    def on_tab_change(self, e):
        """タブ変更処理"""
        self.current_tab = e.control.selected_index
        self._create_tab_content(self.current_tab)
        self.tab_content_container.update()
    
    def _create_tab_content(self, tab_index: int):
        """タブコンテンツ作成"""
        if tab_index == 0:
            content = self.tab_a.create_content()
        elif tab_index == 1:
            content = self.tab_b.create_content()
        elif tab_index == 2:
            content = self.tab_c.create_content()
        elif tab_index == 3:
            content = self.tab_d.create_content()
        elif tab_index == 4:
            content = self.tab_e.create_content()
        else:
            content = ft.Text("不明なタブです", size=16)
        
        self.tab_content_container.content = content


def show_arrangement_test_page(page: ft.Page = None):
    """配置テストページ表示関数"""
    if page:
        PageStyles.set_page_background(page)
    
    arrangement_page = ArrangementTestPage()
    return arrangement_page.create_main_layout()
