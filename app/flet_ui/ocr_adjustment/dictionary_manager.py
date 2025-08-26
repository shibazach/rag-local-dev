#!/usr/bin/env python3
"""
辞書管理機能 - ダイアログ表示とCRUD操作
"""
import flet as ft
from app.flet_ui.shared.common_buttons import create_light_button  # 辞書ボタンは淡い色使用
from app.flet_ui.shared.text_edit_dialog import show_text_edit_dialog
from app.services.dictionary_service import dictionary_service


def create_dictionary_buttons() -> list[ft.Control]:
    """辞書ボタン一覧を作成"""
    buttons = [
        create_light_button("一般用語", ft.Icons.BOOK, lambda e: _open_dictionary(e, "一般用語")),
        create_light_button("専門用語", ft.Icons.LIBRARY_BOOKS, lambda e: _open_dictionary(e, "専門用語")),
        create_light_button("誤字修正", ft.Icons.SPELLCHECK, lambda e: _open_dictionary(e, "誤字修正")),
        create_light_button("ユーザー辞書", ft.Icons.PERSON, lambda e: _open_dictionary(e, "ユーザー辞書"))
    ]
    return buttons


def _open_dictionary(e, dict_type: str):
    """指定した辞書の編集ダイアログを開く"""
    page = e.page
    
    try:
        # 現在の辞書内容を取得
        current_content = dictionary_service.get_dictionary_content(dict_type)
        title = dictionary_service.get_dictionary_title(dict_type)
        
        def on_save(new_content: str):
            """保存処理"""
            try:
                # 内容を検証
                if dictionary_service.validate_dictionary_content(dict_type, new_content):
                    # バックアップ作成
                    dictionary_service.backup_dictionary(dict_type)
                    
                    # 保存実行
                    dictionary_service.save_dictionary_content(dict_type, new_content)
                    
                    # 成功メッセージ表示
                    _show_success_message(page, f"{dict_type}辞書を保存しました")
                else:
                    # エラーメッセージ表示
                    _show_error_message(page, f"{dict_type}辞書の形式が正しくありません")
            except Exception as error:
                _show_error_message(page, f"保存エラー: {str(error)}")
        
        def on_cancel():
            """キャンセル処理"""
            # 特に何もしない（ダイアログが自動で閉じる）
            pass
        
        # テキスト編集ダイアログを表示（ユーザー辞書は大サイズ）
        if dict_type == "ユーザー辞書":
            dialog_width, dialog_height = 1400, 900  # 大サイズ
        else:
            dialog_width, dialog_height = 900, 700   # 標準サイズ
            
        show_text_edit_dialog(
            page=page,
            title=title,
            content=current_content,
            on_save=on_save,
            on_cancel=on_cancel,
            width=dialog_width,
            height=dialog_height
        )
        
    except Exception as error:
        _show_error_message(page, f"辞書読み込みエラー: {str(error)}")


def _show_success_message(page: ft.Page, message: str):
    """成功メッセージを表示"""
    snack_bar = ft.SnackBar(
        content=ft.Text(message, color=ft.Colors.WHITE),
        bgcolor=ft.Colors.GREEN_800,  # 統一色（濃い目）
        duration=3000
    )
    page.overlay.append(snack_bar)
    snack_bar.open = True
    page.update()


def _show_error_message(page: ft.Page, message: str):
    """エラーメッセージを表示"""
    snack_bar = ft.SnackBar(
        content=ft.Text(message, color=ft.Colors.WHITE),
        bgcolor=ft.Colors.RED_800,  # 統一色（濃い目）
        duration=5000
    )
    page.overlay.append(snack_bar)
    snack_bar.open = True
    page.update()