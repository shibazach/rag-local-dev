#!/usr/bin/env python3
"""
Flet RAGシステム - ログインページコンポーネント
認証関連のUI処理
"""

import flet as ft
from flet_ui.shared.common_buttons import create_action_button


def show_login_page(page: ft.Page, on_login_success_callback):
    """
    ログイン画面を表示
    
    Args:
        page (ft.Page): Fletページオブジェクト
        on_login_success_callback (function): ログイン成功時のコールバック関数
    """
    page.controls.clear()
    
    username_field = ft.TextField(
        label="ユーザー名",
        hint_text="admin",
        width=300
    )
    
    password_field = ft.TextField(
        label="パスワード",
        hint_text="password", 
        password=True,
        width=300
    )
    
    message_text = ft.Text("", color=ft.Colors.RED)
    
    def handle_login(e):
        if username_field.value == "admin" and password_field.value == "password":
            # ログイン成功
            user_info = {"username": "admin"}
            on_login_success_callback(user_info)
        else:
            message_text.value = "ユーザー名またはパスワードが違います"
            message_text.color = ft.Colors.RED
            page.update()
    
    page.add(
        ft.Column([
            ft.Text(
                "RAG System",
                size=32,
                weight=ft.FontWeight.BOLD,
                color=ft.Colors.BLUE_800
            ),
            ft.Text(
                "ログイン",
                size=20,
                color=ft.Colors.GREY_600
            ),
            ft.Container(height=20),
            username_field,
            password_field,
            message_text,
            ft.Container(height=20),
            create_action_button(
                "ログイン",
                on_click=handle_login,
                width=300
            ),
        ], 
        alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER)
    )
    page.update()
