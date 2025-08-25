#!/usr/bin/env python3
"""
共通テキスト編集ダイアログコンポーネント
将来的にLLMプロンプト編集にも使用可能
"""

import flet as ft
from typing import Callable, Optional
from .common_buttons import create_light_button, create_action_button


class TextEditDialog:
    """サイズ変更可能なテキスト編集ダイアログ"""
    
    def __init__(
        self,
        title: str,
        content: str = "",
        on_save: Optional[Callable[[str], None]] = None,
        on_cancel: Optional[Callable[[], None]] = None,
        width: int = 800,
        height: int = 600,
        resizable: bool = True
    ):
        """
        テキスト編集ダイアログを初期化
        
        Args:
            title (str): ダイアログタイトル
            content (str): 初期テキスト内容
            on_save (Callable): 保存時のコールバック
            on_cancel (Callable): キャンセル時のコールバック  
            width (int): 初期幅
            height (int): 初期高さ
            resizable (bool): サイズ変更可能か
        """
        self.title = title
        self.content = content
        self.on_save = on_save
        self.on_cancel = on_cancel
        self.width = width
        self.height = height
        self.resizable = resizable
        
        # UI要素
        self.text_field: Optional[ft.TextField] = None
        self.dialog: Optional[ft.AlertDialog] = None
        
    def _handle_save(self, e=None):
        """保存ボタン押下処理"""
        if self.text_field and self.on_save:
            self.on_save(self.text_field.value or "")
        self._close_dialog(e)
    
    def _handle_cancel(self, e=None):
        """キャンセルボタン押下処理"""
        if self.on_cancel:
            self.on_cancel()
        self._close_dialog(e)
    
    def _close_dialog(self, e=None):
        """ダイアログを閉じる"""
        if self.dialog:
            self.dialog.open = False
            # キーイベントハンドラーをクリア
            if hasattr(e, 'page') and e.page:
                e.page.on_keyboard_event = None
                e.page.update()
    
    def _create_dialog_content(self) -> ft.Container:
        """ダイアログ内容を作成"""
        
        # タイトル
        title_text = ft.Text(
            self.title,
            size=18,
            weight=ft.FontWeight.BOLD,
            color=ft.Colors.BLUE_800
        )
        
        # テキスト編集フィールド（ダイアログ下部まで最大拡張）
        self.text_field = ft.TextField(
            value=self.content,
            multiline=True,
            expand=True,  # 公式: expandでコンテナ内最大高さまで拡張
            min_lines=20,  # 最小行数増加
            max_lines=None,  # 無制限（expandで制限）
            border_color=ft.Colors.BLUE_200,
            focused_border_color=ft.Colors.BLUE_400,
            text_size=14,
            filled=True,
            fill_color=ft.Colors.GREY_50
        )
        
        # ボタン行
        button_row = ft.Row([
            create_light_button("キャンセル", on_click=self._handle_cancel),
            ft.Container(expand=True),  # スペーサー
            create_action_button("保存", ft.Icons.SAVE, on_click=self._handle_save)
                                                                                                                                                                                                                                                                                                                                                                                                                                                            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
        
        # メインコンテンツ（TextField最大高さまで拡張、公式仕様準拠）
        return ft.Container(
            content=ft.Column([
                title_text,
                ft.Divider(height=1, color=ft.Colors.BLUE_200),
                ft.Container(
                    content=self.text_field,
                    expand=True,  # 公式確認済み: AlertDialog内でも有効
                    padding=ft.padding.symmetric(vertical=2)
                ),
                button_row
            ], spacing=1, expand=True, tight=True),  # tight=Trueで最大拡張
            width=self.width,
            height=self.height,
            padding=ft.padding.all(8)
        )
    
    def show(self, page: ft.Page):
        """ダイアログを表示"""
        
        # Escapeキーイベントハンドラー
        def handle_key_event(e: ft.KeyboardEvent):
            if e.key == "Escape":
                self._close_dialog(e)
        
        # ダイアログ作成（Escapeキー対応付き）
        self.dialog = ft.AlertDialog(
            modal=True,
            content=self._create_dialog_content(),
            content_padding=0,
            actions=[],  # ボタンは content 内に配置
            actions_padding=0,
            shape=ft.RoundedRectangleBorder(radius=8),  # 角丸でモダンな見た目
            on_dismiss=self._handle_cancel  # Escapeや外側クリック時
        )
        
        # ページレベルでキーイベント監視
        page.on_keyboard_event = handle_key_event
        
        # ページに追加して表示
        page.overlay.append(self.dialog)
        self.dialog.open = True
        page.update()


def show_text_edit_dialog(
    page: ft.Page,
    title: str,
    content: str = "",
    on_save: Optional[Callable[[str], None]] = None,
    on_cancel: Optional[Callable[[], None]] = None,
    width: int = 800,
    height: int = 600
) -> None:
    """
    テキスト編集ダイアログを表示（簡易関数）
    
    Args:
        page (ft.Page): Fletページ
        title (str): ダイアログタイトル
        content (str): 初期テキスト内容
        on_save (Callable): 保存時のコールバック
        on_cancel (Callable): キャンセル時のコールバック
        width (int): ダイアログ幅
        height (int): ダイアログ高さ
    """
    dialog = TextEditDialog(
        title=title,
        content=content,
        on_save=on_save,
        on_cancel=on_cancel,
        width=width,
        height=height
    )
    dialog.show(page)
