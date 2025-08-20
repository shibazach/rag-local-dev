#!/usr/bin/env python3
"""
Flet RAGシステム - プレースホルダーページ（改良版）
まだ実装されていないページ用の統一テンプレート
"""

import flet as ft
from .menu import create_header
from .status_bar import create_status_bar


def create_placeholder_layout(page, current_page, current_user, page_name, display_name, navigate_callback, logout_callback, navigate_to_home_callback):
    """
    プレースホルダーページの完全なレイアウトを作成
    （メニュー・ステータスバー込み）
    
    Args:
        page (ft.Page): Fletページオブジェクト
        current_page (str): 現在のページ名
        current_user (dict): 現在のユーザー情報
        page_name (str): ページ名
        display_name (str): 表示名
        navigate_callback (function): ページ遷移コールバック
        logout_callback (function): ログアウトコールバック
        navigate_to_home_callback (function): ホームに戻るコールバック
    """
    page.controls.clear()
    
    page.add(
        ft.Column([
            # ヘッダー（共通メニュー）
            create_header(
                current_page, 
                current_user, 
                navigate_callback, 
                logout_callback
            ),
            # メインコンテンツエリア
            ft.Container(
                content=create_placeholder_content(page_name, display_name, navigate_to_home_callback),
                expand=True
            ),
            # ステータスバー
            create_status_bar()
        ], spacing=0, expand=True)
    )
    page.update()


def create_placeholder_content(page_name, display_name, navigate_to_home_callback):
    """
    プレースホルダーのメインコンテンツ部分を作成
    
    Args:
        page_name (str): ページ名
        display_name (str): 表示名
        navigate_to_home_callback (function): ホームに戻るコールバック
        
    Returns:
        ft.Container: プレースホルダーコンテンツコンテナ
    """
    return ft.Container(
        content=ft.Column([
            ft.Icon(
                ft.Icons.CONSTRUCTION,
                size=64,
                color=ft.Colors.ORANGE_600
            ),
            ft.Container(height=20),
            ft.Text(
                f"{display_name} ページ",
                size=32,
                weight=ft.FontWeight.BOLD,
                color=ft.Colors.BLUE_800,
                text_align=ft.TextAlign.CENTER
            ),
            ft.Container(height=10),
            ft.Text(
                "この機能は現在開発中です",
                size=16,
                color=ft.Colors.GREY_600,
                text_align=ft.TextAlign.CENTER
            ),
            ft.Container(height=30),
            ft.Row([
                ft.ElevatedButton(
                    "ホームに戻る",
                    on_click=lambda _: navigate_to_home_callback(),
                    bgcolor=ft.Colors.BLUE_600,
                    color=ft.Colors.WHITE,
                    width=200
                ),
                ft.Container(width=20),
                ft.OutlinedButton(
                    "機能一覧",
                    on_click=lambda _: navigate_to_home_callback(),
                    width=200
                )
            ], alignment=ft.MainAxisAlignment.CENTER),
            ft.Container(height=40),
            ft.Card(
                content=ft.Container(
                    content=ft.Column([
                        ft.Text(
                            "開発予定機能",
                            size=18,
                            weight=ft.FontWeight.BOLD,
                            color=ft.Colors.GREY_800
                        ),
                        ft.Container(height=10),
                        ft.Text(
                            f"• {display_name}の基本機能\n• データ処理・表示\n• ユーザーインターフェース\n• 設定・カスタマイズ",
                            size=14,
                            color=ft.Colors.GREY_700
                        )
                    ]),
                    padding=ft.padding.all(20),
                    width=400
                ),
                elevation=2
            )
        ], 
        alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        padding=ft.padding.all(40),
        alignment=ft.alignment.center,
        expand=True
    )


def show_placeholder_page(page_name, display_name, navigate_to_home_callback):
    """
    旧バージョン互換のプレースホルダーページ表示（コンテンツのみ）
    
    Args:
        page_name (str): ページ名
        display_name (str): 表示名
        navigate_to_home_callback (function): ホームに戻るコールバック
        
    Returns:
        ft.Container: プレースホルダーページコンテナ
    """
    return create_placeholder_content(page_name, display_name, navigate_to_home_callback)