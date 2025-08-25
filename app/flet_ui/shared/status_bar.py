#!/usr/bin/env python3
"""
Flet RAGシステム - ステータスバー共通コンポーネント
システム状況表示用のステータスバー
"""

import flet as ft


def create_status_bar():
    """
    ステータスバー（フッター）部分を作成
    
    Returns:
        ft.Container: ステータスバーコンテナ
    """
    return ft.Container(
        content=ft.Row([
            ft.Text("システム正常稼働中", color=ft.Colors.WHITE),
            ft.Container(expand=True),
            ft.Text("接続 OK", color=ft.Colors.WHITE)
        ]),
        bgcolor="#334155",
        padding=ft.padding.all(10),
        width=float("inf")
    )


def create_custom_status_bar(left_text, right_text, bgcolor="#334155"):
    """
    カスタマイズ可能なステータスバーを作成
    
    Args:
        left_text (str): 左側のテキスト
        right_text (str): 右側のテキスト
        bgcolor (str): 背景色
        
    Returns:
        ft.Container: カスタムステータスバーコンテナ
    """
    return ft.Container(
        content=ft.Row([
            ft.Text(left_text, color=ft.Colors.WHITE),
            ft.Container(expand=True),
            ft.Text(right_text, color=ft.Colors.WHITE)
        ]),
        bgcolor=bgcolor,
        padding=ft.padding.all(10),
        width=float("inf")
    )
