#!/usr/bin/env python3
"""
辞書管理機能 - ダイアログ表示とCRUD操作
"""
import flet as ft
from flet_ui.shared.common_buttons import create_light_button, create_dark_button

def create_dictionary_buttons() -> list[ft.Control]:
    """辞書ボタン一覧を作成"""
    buttons = [
        create_light_button("一般用語", ft.Icons.BOOK, _open_general_dictionary),
        create_light_button("専門用語", ft.Icons.LIBRARY_BOOKS, _open_technical_dictionary), 
        create_light_button("誤字修正", ft.Icons.SPELLCHECK, _open_spellcheck_dictionary),
        create_light_button("ユーザー辞書", ft.Icons.PERSON, _open_user_dictionary)
    ]
    return buttons

def _open_general_dictionary(e):
    """一般用語辞書ダイアログを表示"""
    _show_dictionary_dialog(e, "一般用語辞書", "general")

def _open_technical_dictionary(e):
    """専門用語辞書ダイアログを表示"""
    _show_dictionary_dialog(e, "専門用語辞書", "technical")

def _open_spellcheck_dictionary(e):
    """誤字修正辞書ダイアログを表示"""
    _show_dictionary_dialog(e, "誤字修正辞書", "spellcheck")

def _open_user_dictionary(e):
    """ユーザー辞書ダイアログを表示"""
    _show_dictionary_dialog(e, "ユーザー辞書", "user")

def _show_dictionary_dialog(e, title: str, dict_type: str):
    """辞書ダイアログを表示（プレースホルダー）"""
    # 今後実装予定：辞書編集ダイアログ
    dialog = ft.AlertDialog(
        title=ft.Text(title),
        content=ft.Text(f"{title}の管理機能は今後実装予定です。\n辞書タイプ: {dict_type}"),
        actions=[
            ft.TextButton("閉じる", on_click=lambda _: _close_dialog(e))
        ]
    )
    
    e.page.overlay.append(dialog)
    dialog.open = True
    e.page.update()

def _close_dialog(e):
    """ダイアログを閉じる"""
    if e.page.overlay:
        e.page.overlay[-1].open = False
        e.page.update()
