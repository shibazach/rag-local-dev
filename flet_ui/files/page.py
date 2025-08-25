#!/usr/bin/env python3
"""
Flet RAGシステム - ファイル管理ページ（完全共通コンポーネント版）
全コンポーネントを共通化設計に統一
"""

import flet as ft
from .table import FilesTable
from ..shared.pdf_preview import PDFPreview
from ..shared.panel_components import create_panel, create_files_panel_config
from ..shared.style_constants import CommonComponents, PageStyles, SLIDER_RATIOS


def show_files_page(page=None):
    """ファイル管理ページのメインコンテンツ（共通コンポーネント統一版）"""
    if page:
        PageStyles.set_page_background(page)
    
    files_page = FilesPage()
    files_page.page = page  # Page参照を設定
    layout = files_page.create_main_layout()
    files_page.load_files()
    return layout


class FilesPage:
    """ファイル管理ページ（完全共通コンポーネント版）"""

    def __init__(self):
        self.files_table = FilesTable(on_file_select_callback=self.on_file_selected)
        self.pdf_preview = PDFPreview()
        self.page = None

        # 5段階比率: 独自設定（0:4 ～ 4:0）
        self.level = 3  # 初期値は2:2
        self.ratios = {
            1: (0, 4),  # 0:4
            2: (1, 3),  # 1:3  
            3: (2, 2),  # 2:2
            4: (3, 1),  # 3:1
            5: (4, 0),  # 4:0
        }

        # UI参照
        self.main_container: ft.Container | None = None
        self.left_container: ft.Container | None = None
        self.right_container: ft.Container | None = None
        self.width_slider: ft.Slider | None = None

    def _apply_ratios(self):
        """expand比率反映（比率0の場合は最小幅制御）"""
        if not self.left_container or not self.right_container:
            return
        left_expand, right_expand = self.ratios[self.level]
        
        # 比率0の場合は最小幅で表示（完全非表示回避）
        if left_expand == 0:
            self.left_container.expand = None
            self.left_container.width = 1  # 最小可視幅
        else:
            self.left_container.expand = left_expand
            self.left_container.width = None
            
        if right_expand == 0:
            self.right_container.expand = None
            self.right_container.width = 1  # 最小可視幅
        else:
            self.right_container.expand = right_expand
            self.right_container.width = None
            
        # ページに追加済みの場合のみ更新
        try:
            if self.left_container.page:
                self.left_container.update()
            if self.right_container.page:
                self.right_container.update()
        except Exception as e:
            # Container update error occurred
            pass

    def create_main_layout(self):
        """メインレイアウト作成（共通コンポーネント統一版）"""
        try:
            # FilesTableにpage参照を設定
            self.files_table.page = self.page
            
            # 左ペイン：ファイル一覧（FilesTable内で既にcreate_panel使用済み）
            left_pane = self.files_table.create_table_widget()
            
            # 右ペイン：PDFプレビュー
            right_pane = self.pdf_preview

            # 左右コンテナ（expandで比率制御、共通設計準拠）
            left_expand, right_expand = self.ratios[self.level]
            self.left_container = ft.Container(
                content=left_pane,
                expand=left_expand,
            )
            self.right_container = ft.Container(
                content=right_pane,
                expand=right_expand
            )

            # 5段階スライダー（共通コンポーネント使用）
            self.width_slider = CommonComponents.create_horizontal_slider(
                self.level, self.on_slider_change
            )

            # 上段：左右Row（共通コンポーネント使用）
            top_row = CommonComponents.create_main_layout_row(
                self.left_container, self.right_container
            )

            # 完全レイアウト（上部コンテンツ + 下部スライダーバー）
            self.main_container = PageStyles.create_complete_layout_with_slider(
                top_row, self.width_slider
            )
            
        except Exception as ex:
            import traceback
            traceback.print_exc()
            self.main_container = PageStyles.create_error_container(
                f"レイアウト作成エラー: {str(ex)}"
            )

        return self.main_container

    def on_slider_change(self, e: ft.ControlEvent):
        """スライダ変更時に比率を更新"""
        try:
            self.level = int(float(e.control.value))
        except Exception:
            pass
        self._apply_ratios()

    def load_files(self):
        """ファイル一覧のロード"""
        self.files_table.load_files()

    def on_file_selected(self, file_id):
        """ファイル選択時のプレビュー表示"""
        if file_id:
            file_info = self.files_table.get_selected_file()
            self.pdf_preview.show_pdf_preview(file_info)
        else:
            self.pdf_preview.show_empty_preview()