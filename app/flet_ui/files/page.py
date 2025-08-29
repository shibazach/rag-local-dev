#!/usr/bin/env python3
"""
Flet RAGシステム - ファイル管理ページ（完全共通コンポーネント版）
全コンポーネントを共通化設計に統一
"""

import flet as ft
from .table import FilesTable
from app.flet_ui.shared.pdf_preview import PDFPreview
from app.flet_ui.shared.panel_components import create_panel, create_files_panel_config
from app.flet_ui.shared.style_constants import CommonComponents, PageStyles, SLIDER_RATIOS


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
        self.pdf_preview = None  # V5は後でpage参照と共に初期化
        self.page = None

        # 共通比率テーブル使用（全ページ統一）
        from app.flet_ui.shared.style_constants import SLIDER_RATIOS
        self.level = 3  # 初期値は2:2
        self.ratios = SLIDER_RATIOS

        # UI参照
        self.main_container: ft.Container | None = None
        self.left_container: ft.Container | None = None
        self.right_container: ft.Container | None = None
        self.width_slider: ft.Slider | None = None

    def _apply_ratios(self):
        """expand比率反映（共通メソッド使用）"""
        if hasattr(self, 'main_row') and self.main_row:
            CommonComponents.apply_slider_ratios_to_row(
                self.main_row, self.ratios, self.level
            )

    def create_main_layout(self):
        """メインレイアウト作成（共通コンポーネント統一版）"""
        try:
            # FilesTableにpage参照を設定
            self.files_table.page = self.page
            
            # 元の動作するPDFプレビュー初期化
            self.pdf_preview = PDFPreview(self.page)
            
            # 左ペイン：ファイル一覧（FilesTable内で既にcreate_panel使用済み）
            left_pane = self.files_table.create_table_widget()
            
            # 右ペイン：元の動作するPDFプレビュー
            right_pane = ft.Container(
                content=self.pdf_preview,
                expand=True,
                alignment=ft.alignment.center,
                bgcolor=ft.Colors.WHITE
            )

            # 5段階スライダー（共通コンポーネント使用）
            self.width_slider = CommonComponents.create_horizontal_slider(
                self.level, self.on_slider_change
            )

            # 上段：左右Row（共通コンポーネント使用、0対策自動適用）
            self.main_row = CommonComponents.create_main_layout_row(
                left_pane, right_pane
            )
            
            # 初期比率適用（共通メソッド使用）
            CommonComponents.apply_slider_ratios_to_row(
                self.main_row, self.ratios, self.level
            )
            
            # 後方互換性：個別コンテナ参照を保持
            self.left_container = self.main_row.controls[0]
            self.right_container = self.main_row.controls[1]

            # 完全レイアウト（上部コンテンツ + 下部スライダーバー）
            self.main_container = PageStyles.create_complete_layout_with_slider(
                self.main_row, self.width_slider
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
        """ファイル選択時のPDFプレビュー表示（元の動作版）"""
        if file_id and self.pdf_preview:
            file_info = self.files_table.get_selected_file()
            if file_info and file_info.get('file_name', '').lower().endswith('.pdf'):
                try:
                    # 元のシンプルなPDFプレビュー表示
                    from app.services.file_service import get_file_service
                    file_service = get_file_service()
                    file_data = file_service.get_file_info(file_info['id'])
                    
                    if file_data and file_data.get('blob_data'):
                        # 元の動作するPDFプレビュー表示
                        self.pdf_preview.show_pdf_preview(file_info)
                        print(f"[INFO] PDF読み込み完了: {file_info['file_name']}")
                    else:
                        print(f"[ERROR] PDFデータ取得失敗: {file_info.get('file_name', 'unknown')}")
                except Exception as e:
                    print(f"[ERROR] PDFファイル処理エラー: {e}")
        elif self.pdf_preview:
            # PDFファイル以外またはfile_idなしの場合はクリア
            self.pdf_preview.show_empty_preview()