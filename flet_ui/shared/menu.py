#!/usr/bin/env python3
"""
Flet RAGシステム - 共通メニューコンポーネント
メニューとヘッダー関連の再利用可能なコンポーネント
"""

import flet as ft


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
            ft.Icon(ft.Icons.PERSON, color=ft.Colors.WHITE, size=20),
            ft.Text(f"{current_user['username']}", color=ft.Colors.WHITE, size=14),
            ft.Icon(ft.Icons.ARROW_DROP_DOWN, color=ft.Colors.WHITE, size=16)
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
        bgcolor=ft.Colors.WHITE,  # 白背景に変更
        elevation=4,  # より明確な影
        shadow_color=ft.Colors.with_opacity(0.2, ft.Colors.BLACK)
    )
    return user_dropdown


def create_header(current_page, current_user, navigate_callback, logout_callback):
    """
    ヘッダー部分を作成（メニュー統合版）
    
    Args:
        current_page (str): 現在のページ名
        current_user (dict): 現在のユーザー情報
        navigate_callback (function): ページ遷移時のコールバック関数
        logout_callback (function): ログアウト時のコールバック関数
        
    Returns:
        ft.Container: ヘッダーコンテナ
    """
    # メニューボタンを直接作成
    menu_items = [
        {"name": "ホーム", "page": "home", "icon": "🏠"},
        {"name": "チャット", "page": "chat", "icon": "💬"},
        {"name": "ファイル", "page": "files", "icon": "📁"},
        {"name": "アップロード", "page": "upload", "icon": "📤"},
        {"name": "OCR調整", "page": "ocr", "icon": "🔄"},
        {"name": "データ登録", "page": "data", "icon": "⚙️"},
        {"name": "配置テスト", "page": "test", "icon": "🧪"},
        {"name": "管理", "page": "admin", "icon": "⚡"},
    ]
    
    menu_buttons = []
    for item in menu_items:
        is_current = current_page == item["page"]
        button = ft.TextButton(
            content=ft.Row([
                ft.Text(item["icon"], size=14),
                ft.Text(item["name"], size=12)
            ], spacing=2, tight=True),
            style=ft.ButtonStyle(
                color=ft.Colors.RED_400 if is_current else ft.Colors.WHITE,
                bgcolor={"": ft.Colors.with_opacity(0.1, ft.Colors.RED_400) if is_current else ft.Colors.TRANSPARENT},
                padding=ft.padding.all(6),
                shape=ft.RoundedRectangleBorder(radius=4)
            ),
            on_click=lambda _, page_name=item["page"]: navigate_callback(page_name)
        )
        menu_buttons.append(button)
    
    return ft.Container(
        content=ft.Row([
            # 左側：メニューボタン
            ft.Row(
                controls=menu_buttons,
                spacing=4,
                wrap=True
            ),
            # 右側に認証情報（ドロップダウン形式）
            create_user_menu(current_user, logout_callback)
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        bgcolor="#334155",
        padding=ft.padding.all(8),
        margin=ft.margin.all(0)
    )


# create_footer()はstatus_bar.pyに移動されました
# 互換性のためのインポート
from .status_bar import create_status_bar as create_footer
