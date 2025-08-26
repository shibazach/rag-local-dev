#!/usr/bin/env python3
"""
Flet RAGシステム - ファイル選択ダイアログコンポーネント
OCR調整ページ等で使用するファイル選択用の大きなダイアログ
"""

import flet as ft
from typing import Optional, Callable, Dict, Any
from ..files.table import FilesTable
from ..shared.pdf_preview import PDFPreview
from ..shared.style_constants import CommonComponents


class FileSelectionDialog:
    """ファイル選択用ダイアログコンポーネント"""
    
    def __init__(self, page: ft.Page, on_file_selected: Optional[Callable] = None):
        self.page = page
        self.on_file_selected = on_file_selected
        
        # コンパクト版FilesTable（ダイアログ用スタイル）
        self.files_table = FilesTable(on_file_select_callback=self._on_table_file_select)
        
        # PDFプレビュー（小さめ）
        self.pdf_preview = PDFPreview()
        
        # 選択されたファイル情報
        self.selected_file_info: Optional[Dict[str, Any]] = None
        
        # ダイアログ参照
        self.dialog: Optional[ft.AlertDialog] = None
        
        # レイアウト比率（2:1で左側テーブル重視）
        self.left_expand = 2
        self.right_expand = 1

    def _on_table_file_select(self, file_info: Dict[str, Any]):
        """テーブルからのファイル選択イベント"""
        self.selected_file_info = file_info
        
        # PDFプレビューを更新
        if file_info and file_info.get("filename", "").lower().endswith(".pdf"):
            self.pdf_preview.load_file(file_info.get("file_path", ""))
    
    def _on_select_click(self, e):
        """選択ボタンクリック"""
        if self.selected_file_info and self.on_file_selected:
            self.on_file_selected(self.selected_file_info)
        
        # ダイアログを閉じる
        self._close_dialog()
    
    def _on_cancel_click(self, e):
        """キャンセルボタンクリック"""
        self.selected_file_info = None
        self._close_dialog()
    
    def _close_dialog(self):
        """ダイアログを閉じる"""
        if self.dialog:
            self.dialog.open = False
            self.page.update()

    def _create_compact_files_content(self) -> ft.Control:
        """コンパクト版ファイル選択コンテンツ作成"""
        # FilesTableのコンパクト版を作成（スタイル調整）
        self._apply_compact_table_style()
        
        # テーブルウィジェット取得
        table_widget = self.files_table.create_table_widget()
        
        # 左右コンテンツ
        left_content = ft.Container(
            content=table_widget,
            expand=self.left_expand,
            padding=ft.padding.all(4)  # コンパクト化
        )
        
        right_content = ft.Container(
            content=self.pdf_preview,
            expand=self.right_expand,
            padding=ft.padding.all(4)  # コンパクト化
        )
        
        # 左右分割レイアウト
        files_row = ft.Container(
            content=ft.Row([
                left_content,
                ft.VerticalDivider(width=1, thickness=1, color=ft.Colors.GREY_300),
                right_content
            ], spacing=0, expand=True),
            height=600,  # ダイアログ用の高さ（大きめ）
            width=1200   # ダイアログ用の幅（大きめ）
        )
        
        return files_row

    def _apply_compact_table_style(self):
        """テーブルにコンパクトスタイル適用（FlexibleDataTable用）"""
        # FilesTable内のFlexibleDataTableを取得してスタイル調整
        if hasattr(self.files_table, 'data_table') and self.files_table.data_table:
            table = self.files_table.data_table
            
            # ヘッダー行のスタイル調整（既存ヘッダーを再構築）
            self._update_header_style(table)
            
            # データ行は動的に作成されるため、作成後に調整される
            # update_rows時に適用されるスタイルを変更するためのフラグ設定
            table._compact_mode = True

    def _update_header_style(self, table):
        """ヘッダー行のスタイルをコンパクト化"""
        if hasattr(table, 'header_row') and table.header_row:
            # ヘッダー内のTextコンポーネントを取得して更新
            header_row_content = table.header_row.content
            if isinstance(header_row_content, ft.Row):
                for cell_container in header_row_content.controls:
                    if isinstance(cell_container, ft.Container) and hasattr(cell_container, 'content'):
                        text_content = cell_container.content
                        if isinstance(text_content, ft.Text):
                            text_content.size = 12  # ヘッダー文字サイズ縮小
                        # パディング縮小
                        cell_container.padding = ft.padding.symmetric(horizontal=8, vertical=4)

    def create_dialog(self) -> ft.AlertDialog:
        """ファイル選択ダイアログを作成"""
        # ファイル選択コンテンツ作成
        files_content = self._create_compact_files_content()
        
        # アクションボタン
        actions = [
            ft.TextButton("キャンセル", on_click=self._on_cancel_click),
            ft.ElevatedButton("選択", on_click=self._on_select_click),
        ]
        
        # ダイアログ作成（大きめサイズ）
        self.dialog = ft.AlertDialog(
            title=ft.Text("ファイル選択", size=16, weight=ft.FontWeight.BOLD),
            content=files_content,
            actions=actions,
            actions_alignment=ft.MainAxisAlignment.END,
            # 大きめサイズ設定
            modal=True,
            # Fletのダイアログサイズはコンテンツに依存するため、コンテンツ側でサイズ調整
        )
        
        return self.dialog

    def show_dialog(self):
        """ダイアログを表示"""
        # tab_a成功パターン適用: page.open()方式
        def close_dialog(e):
            self.page.close(dialog)
        
        dialog = self.create_dialog()
        # アクションのクローズ処理をシンプルに
        for action in dialog.actions:
            if hasattr(action, 'text') and 'キャンセル' in action.text:
                action.on_click = close_dialog
        
        # ファイル一覧をロード
        self.files_table.page = self.page
        self.files_table.load_files()
        
        # tab_a成功方式: page.open()
        self.page.open(dialog)

    def get_selected_file(self) -> Optional[Dict[str, Any]]:
        """選択されたファイル情報を取得"""
        return self.selected_file_info


def create_file_selection_dialog(page: ft.Page, on_file_selected: Optional[Callable] = None) -> FileSelectionDialog:
    """ファイル選択ダイアログ作成のヘルパー関数"""
    return FileSelectionDialog(page, on_file_selected)
