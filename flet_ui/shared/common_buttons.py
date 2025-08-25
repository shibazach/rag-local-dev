#!/usr/bin/env python3
"""
共通ボタンコンポーネント - 統一されたスタイル
"""
import flet as ft

def create_light_button(text: str, icon=None, on_click=None, width: int = None) -> ft.ElevatedButton:
    """淡い系ボタン（読込系操作用）"""
    return ft.ElevatedButton(
        text=text,
        icon=icon,
        on_click=on_click,
        width=width,
        bgcolor=ft.Colors.BLUE_GREY_100,
        color=ft.Colors.BLUE_GREY_800,
    )

def create_dark_button(text: str, icon=None, on_click=None, width: int = None) -> ft.ElevatedButton:
    """濃い系ボタン（保存系操作用）"""
    return ft.ElevatedButton(
        text=text,
        icon=icon,
        on_click=on_click,
        width=width,
        bgcolor=ft.Colors.BLUE_GREY_800,
        color=ft.Colors.WHITE,
    )

def create_action_button(text: str, icon=None, on_click=None, width: int = None) -> ft.ElevatedButton:
    """アクション系ボタン（実行系操作用）"""
    return ft.ElevatedButton(
        text=text,
        icon=icon,
        on_click=on_click,
        width=width,
        bgcolor=ft.Colors.BLUE_GREY_600,
        color=ft.Colors.WHITE,
    )
