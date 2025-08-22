#!/usr/bin/env python3
"""
Flet RAGシステム - NavigationBar形式メニューコンポーネント
Flet公式サンプルを参考にしたNavigationBar実装
"""

import flet as ft


def create_navigation_bar(current_page, navigate_callback):
    """
    NavigationBar形式のメニューを作成
    参考: https://github.com/flet-dev/examples/blob/main/python/apps/controls-gallery/examples/navigation/navigationbar/01_navigationbar_example.py
    
    Args:
        current_page (str): 現在のページ名
        navigate_callback (function): ページ遷移時のコールバック関数
        
    Returns:
        ft.NavigationBar: NavigationBarコンポーネント
    """
    # ページ名とインデックスのマッピング
    page_mapping = {
        "home": 0,
        "chat": 1, 
        "files": 2,
        "upload": 3,
        "ocr": 4,
        "data": 5,
        "arrangement_test": 6,
        "admin": 7,
    }
    
    # 現在のページのインデックスを取得
    selected_index = page_mapping.get(current_page, 0)
    
    def on_destination_change(e):
        """NavigationBar選択時のコールバック"""
        index = e.control.selected_index
        page_names = list(page_mapping.keys())
        if 0 <= index < len(page_names):
            navigate_callback(page_names[index])
    
    # カスタムボタンでNavigationBarを作成（グラデーション無し、間隔調整）
    nav_buttons = []
    for i, (page_name, destination) in enumerate(zip(page_mapping.keys(), [
        {"icon": ft.Icons.HOME_OUTLINED, "selected_icon": ft.Icons.HOME, "label": "ホーム"},
        {"icon": ft.Icons.CHAT_OUTLINED, "selected_icon": ft.Icons.CHAT, "label": "チャット"},
        {"icon": ft.Icons.FOLDER_OUTLINED, "selected_icon": ft.Icons.FOLDER, "label": "ファイル"},
        {"icon": ft.Icons.UPLOAD_OUTLINED, "selected_icon": ft.Icons.UPLOAD, "label": "アップロード"},
        {"icon": ft.Icons.SETTINGS_OUTLINED, "selected_icon": ft.Icons.SETTINGS, "label": "OCR調整"},
        {"icon": ft.Icons.STORAGE_OUTLINED, "selected_icon": ft.Icons.STORAGE, "label": "データ登録"},
        {"icon": ft.Icons.SCIENCE_OUTLINED, "selected_icon": ft.Icons.SCIENCE, "label": "配置テスト"},
        {"icon": ft.Icons.ADMIN_PANEL_SETTINGS_OUTLINED, "selected_icon": ft.Icons.ADMIN_PANEL_SETTINGS, "label": "管理"},
    ])):
        is_selected = i == selected_index
        icon_color = "#334155" if is_selected else ft.Colors.GREY_600  # ヒーロー色 vs ダークグレー
        text_color = "#334155" if is_selected else ft.Colors.GREY_600
        
        button = ft.Container(
            content=ft.Column([
                ft.Icon(
                    destination["selected_icon"] if is_selected else destination["icon"],
                    color=icon_color,
                    size=24  # 20 → 24に拡大
                ),
                ft.Container(height=2),  # アイコンと文字の間隔を縮小
                ft.Text(
                    destination["label"],
                    color=text_color,
                    size=12,  # 10 → 12に拡大
                    text_align=ft.TextAlign.CENTER
                )
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=0),
            padding=ft.padding.symmetric(horizontal=8, vertical=2),
            on_click=lambda _, page=page_name: navigate_callback(page),
            ink=False,  # リップル効果を無効化
        )
        nav_buttons.append(button)
    
    nav_bar = ft.Row(
        controls=nav_buttons,
        alignment=ft.MainAxisAlignment.SPACE_EVENLY,
        spacing=0,
    )
    
    # カスタムNavigationBarをコンテナでラップ
    return ft.Container(
        content=nav_bar,
        height=48,  # コンパクト化
        alignment=ft.alignment.center,
    )


def create_user_menu(current_user, on_logout_callback):
    """
    ユーザーメニュー（ドロップダウン式）を作成
    
    Args:
        current_user (dict): 現在のユーザー情報
        on_logout_callback (function): ログアウト時のコールバック関数
        
    Returns:
        ft.PopupMenuButton: ユーザーメニューコンポーネント
    """
    user_dropdown = ft.PopupMenuButton(
        content=ft.Row([
            ft.Icon(ft.Icons.PERSON, color="#334155", size=20),
            ft.Text(f"{current_user['username']}", color="#334155", size=14),
            ft.Icon(ft.Icons.ARROW_DROP_DOWN, color="#334155", size=16)
        ], spacing=5),
        items=[
            ft.PopupMenuItem(
                content=ft.Row([
                    ft.Icon(ft.Icons.LOGOUT, color=ft.Colors.GREY_800, size=16),
                    ft.Text("ログアウト", color=ft.Colors.GREY_800, size=14, weight=ft.FontWeight.BOLD)
                ], spacing=8),
                on_click=lambda _: on_logout_callback()
            )
        ],
        bgcolor=ft.Colors.WHITE,
        elevation=4,
        shadow_color=ft.Colors.with_opacity(0.2, ft.Colors.BLACK)
    )
    return user_dropdown


def create_header(current_page, current_user, navigate_callback, logout_callback):
    """
    ヘッダー部分を作成（NavigationBar + ユーザーメニュー）
    
    Args:
        current_page (str): 現在のページ名
        current_user (dict): 現在のユーザー情報
        navigate_callback (function): ページ遷移時のコールバック関数
        logout_callback (function): ログアウト時のコールバック関数
        
    Returns:
        ft.Container: ヘッダーコンテナ
    """
    return ft.Container(
        content=ft.Row([
            # 左側：NavigationBar（expandで幅を取る）
            ft.Container(
                content=create_navigation_bar(current_page, navigate_callback),
                expand=True
            ),
            # 右側：少しスペースを開けてユーザーメニュー
            ft.Container(width=16),  # スペース
            create_user_menu(current_user, logout_callback)
        ], alignment=ft.MainAxisAlignment.START),
        bgcolor=ft.Colors.GREY_50,  # 全ページ統一背景色
        padding=ft.padding.symmetric(horizontal=8, vertical=4),
        margin=ft.margin.all(0)
    )


# create_footer()はstatus_bar.pyに移動されました
# 互換性のためのインポート
from .status_bar import create_status_bar as create_footer