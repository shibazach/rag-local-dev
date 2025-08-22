#!/usr/bin/env python3
"""
Flet RAGシステム - アプリケーション状態管理
ページ遷移、認証状態等を管理
"""

import flet as ft
from ..auth.login import show_login_page
from ..home.page import show_home_page
from .menu import create_header
from .status_bar import create_status_bar
from .placeholder_page import show_placeholder_page


class AppState:
    """アプリケーションの状態管理クラス"""
    
    def __init__(self, page: ft.Page):
        self.page = page
        self.current_user = None
        self.current_page = "home"
        
        # ページ名マッピング
        self.page_names = {
            "chat": "チャット",
            "files": "ファイル管理", 
            "upload": "アップロード",
            "ocr": "OCR調整",
            "data": "データ登録",
            "arrangement_test": "配置テスト",
            "admin": "管理"
        }
    
    def show_login(self):
        """ログイン画面を表示"""
        show_login_page(self.page, self.on_login_success)
    
    def on_login_success(self, user_info):
        """ログイン成功時の処理"""
        self.current_user = user_info
        self.current_page = "home"
        self.show_main_content()
    
    def on_logout(self):
        """ログアウト処理"""
        self.current_user = None
        self.current_page = "home"
        self.show_login()
    
    def navigate_to(self, target_page):
        """ページ遷移処理"""
        self.current_page = target_page
        self.show_main_content()
    
    def navigate_to_home(self):
        """ホームページに遷移"""
        self.navigate_to("home")
    
    def show_page_content(self):
        """現在のページのコンテンツを表示"""
        if self.current_page == "home":
            return show_home_page()
        elif self.current_page == "files":
            # ファイル管理ページ（コンテンツのみ）
            from ..files.page import show_files_page
            return show_files_page(self.page)
        elif self.current_page == "upload":
            # アップロードページ（コンテンツのみ）
            from ..upload.page import show_upload_page
            return show_upload_page(self.page)
        elif self.current_page == "ocr":
            # OCR調整ページ（コンテンツのみ）
            from ..ocr_adjustment.page import show_ocr_adjustment_page
            return show_ocr_adjustment_page(self.page)
        elif self.current_page == "arrangement_test":
            # 配置テストページ（コンテンツのみ）
            from ..arrangement_test.page import show_arrangement_test_page
            return show_arrangement_test_page(self.page)
        else:
            # その他のページはプレースホルダー
            display_name = self.page_names.get(self.current_page, self.current_page)
            return show_placeholder_page(self.current_page, display_name, self.navigate_to_home)
    
    def show_main_content(self):
        """メインコンテンツエリアを表示"""
        self.page.controls.clear()
        
        self.page.add(
            ft.Column([
                create_header(
                    self.current_page, 
                    self.current_user, 
                    self.navigate_to, 
                    self.on_logout
                ),
                ft.Container(
                    content=self.show_page_content(),
                    expand=True
                ),
                # create_status_bar()  # REM: ステータスバー表示停止
            ], spacing=0, expand=True)
        )
        self.page.update()
