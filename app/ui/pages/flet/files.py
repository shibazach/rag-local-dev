#!/usr/bin/env python3
"""
Flet RAGシステム - ファイル管理ページ
flet_ui/files/page.py をベースとした統合版
"""

import flet as ft
from typing import List, Dict, Any, Optional
from app.core.db_simple import get_file_list

# 共通設定
BOTTOM_BAR_H = 32
OUTER_PAD = 8


class FilesTableComponent:
    """ファイルテーブルコンポーネント（縦スライダー付き）"""

    def __init__(self, on_file_select_callback=None):
        # データ管理
        self.all_files = []
        self.filtered_files = []
        self.selected_file_id = None
        self.on_file_select_callback = on_file_select_callback
        
        # フィルター状態
        self.status_filter = "全て"
        self.search_text = ""
        
        # ページネーション
        self.current_page = 1
        self.page_size = 20
        
        # UI参照（後で設定）
        self.page: ft.Page | None = None
        self.data_table: ft.DataTable | None = None
        self.status_dropdown: ft.Dropdown | None = None
        self.search_field: ft.TextField | None = None
        self.pagination_info: ft.Text | None = None

    def create_table_widget(self) -> ft.Container:
        """テーブルウィジェット作成"""
        try:
            # フィルターコンポーネント
            self.status_dropdown = ft.Dropdown(
                options=[
                    ft.dropdown.Option("全て"),
                    ft.dropdown.Option("処理完了"),
                    ft.dropdown.Option("処理中"),
                    ft.dropdown.Option("未処理"),
                    ft.dropdown.Option("未整形"),
                    ft.dropdown.Option("未ベクトル化"),
                    ft.dropdown.Option("エラー")
                ],
                value=self.status_filter,
                width=120,
                filled=True,
                bgcolor=ft.Colors.WHITE,
                on_change=self.on_status_change
            )
            
            self.search_field = ft.TextField(
                hint_text="ファイル名で検索",
                width=200,
                filled=True,
                bgcolor=ft.Colors.WHITE,
                on_change=self.on_search_change
            )
            
            # フィルターバー
            filter_bar = ft.Container(
                content=ft.Row([
                    ft.Text("ステータス:", size=14, color=ft.Colors.BLACK87),
                    self.status_dropdown,
                    ft.Container(width=20),
                    self.search_field,
                    ft.Container(expand=True)
                ], spacing=8),
                padding=ft.padding.all(8),
                bgcolor=ft.Colors.GREY_100,
                border=ft.border.only(bottom=ft.BorderSide(1, ft.Colors.GREY_300))
            )
            
            # データテーブル
            self.data_table = ft.DataTable(
                columns=[
                    ft.DataColumn(ft.Text("ファイル名", weight=ft.FontWeight.BOLD)),
                    ft.DataColumn(ft.Text("サイズ", weight=ft.FontWeight.BOLD)),
                    ft.DataColumn(ft.Text("ステータス", weight=ft.FontWeight.BOLD)),
                    ft.DataColumn(ft.Text("作成日時", weight=ft.FontWeight.BOLD))
                ],
                rows=[],
                show_checkbox_column=False,
                data_row_min_height=40,
                heading_row_height=45,
                column_spacing=20,
                horizontal_lines=ft.BorderSide(1, ft.Colors.GREY_200)
            )
            
            # テーブルコンテナ（スクロール対応）
            table_container = ft.Container(
                content=ft.Column([self.data_table], scroll=ft.ScrollMode.AUTO),
                expand=True,
                bgcolor=ft.Colors.WHITE,
                border=ft.border.all(1, ft.Colors.GREY_300)
            )
            
            # ページネーション
            self.pagination_info = ft.Text("0 件", size=14, color=ft.Colors.BLACK87)
            
            pagination_bar = ft.Container(
                content=ft.Row([
                    ft.Text("1ページ表示件数:", size=14, color=ft.Colors.BLACK87),
                    ft.Dropdown(
                        options=[
                            ft.dropdown.Option("10"),
                            ft.dropdown.Option("20"),
                            ft.dropdown.Option("50")
                        ],
                        value=str(self.page_size),
                        width=80,
                        bgcolor=ft.Colors.WHITE,
                        on_change=self.on_page_size_change
                    ),
                    ft.Container(expand=True),
                    self.pagination_info,
                    ft.Container(width=20),
                    ft.IconButton(
                        icon=ft.Icons.CHEVRON_LEFT,
                        on_click=self.prev_page
                    ),
                    ft.IconButton(
                        icon=ft.Icons.CHEVRON_RIGHT,
                        on_click=self.next_page
                    )
                ], spacing=8, alignment=ft.MainAxisAlignment.START),
                height=50,
                padding=ft.padding.symmetric(horizontal=12, vertical=8),
                bgcolor=ft.Colors.GREY_100,
                border=ft.border.only(top=ft.BorderSide(1, ft.Colors.GREY_300))
            )
            
            # 全体をパネルとして結合
            panel_content = ft.Column([
                filter_bar,
                table_container,
                pagination_bar
            ], spacing=0, expand=True)
            
            return ft.Container(
                content=panel_content,
                expand=True,
                margin=ft.margin.all(4),
                padding=ft.padding.all(0),
                bgcolor=ft.Colors.WHITE,
                border_radius=8,
                border=ft.border.all(1, ft.Colors.GREY_300)
            )
            
        except Exception as ex:
            import traceback
            traceback.print_exc()
            return ft.Container(
                content=ft.Text(f"テーブル作成エラー: {str(ex)}", color=ft.Colors.RED),
                padding=ft.padding.all(20)
            )

    def load_files(self):
        """ファイル一覧読み込み"""
        try:
            self.all_files = get_file_list()
            self.apply_filters()
            print(f"[DEBUG] Loaded {len(self.all_files)} files")
        except Exception as ex:
            print(f"[ERROR] Failed to load files: {ex}")
            self.all_files = []
            self.filtered_files = []
            self.update_table()

    def apply_filters(self):
        """フィルター適用"""
        filtered = self.all_files.copy()
        
        # ステータスフィルター
        if self.status_filter != "全て":
            filtered = [f for f in filtered if f.get('status', '') == self.status_filter]
        
        # 検索フィルター
        if self.search_text:
            filtered = [f for f in filtered if self.search_text.lower() in f.get('file_name', '').lower()]
        
        self.filtered_files = filtered
        self.current_page = 1  # フィルター変更時は1ページ目に戻る
        self.update_table()

    def update_table(self):
        """テーブル更新"""
        if not self.data_table:
            return
            
        try:
            # ページネーション計算
            total_count = len(self.filtered_files)
            total_pages = max(1, (total_count + self.page_size - 1) // self.page_size)
            start_idx = (self.current_page - 1) * self.page_size
            end_idx = min(start_idx + self.page_size, total_count)
            current_page_files = self.filtered_files[start_idx:end_idx]
            
            # テーブル行作成
            rows = []
            for file_data in current_page_files:
                file_id = str(file_data.get('id', ''))
                is_selected = (file_id == self.selected_file_id)
                
                # ステータスバッジ作成
                status = file_data.get('status', '未処理')
                status_badge = self.create_status_badge(status)
                
                # サイズフォーマット
                file_size = file_data.get('file_size', 0)
                if file_size >= 1024 * 1024:
                    size_text = f"{file_size / (1024 * 1024):.1f} MB"
                elif file_size >= 1024:
                    size_text = f"{file_size / 1024:.1f} KB"
                else:
                    size_text = f"{file_size} B"
                
                row = ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(file_data.get('file_name', ''), size=14)),
                        ft.DataCell(ft.Text(size_text, size=14)),
                        ft.DataCell(status_badge),
                        ft.DataCell(ft.Text(file_data.get('created_at', ''), size=14))
                    ],
                    selected=is_selected,
                    on_select_changed=lambda e, fid=file_id, fdata=file_data: self.on_row_select(e, fid, fdata)
                )
                rows.append(row)
            
            self.data_table.rows = rows
            
            # ページネーション情報更新
            if self.pagination_info:
                self.pagination_info.value = f"{start_idx + 1}-{end_idx} / {total_count} 件 (ページ {self.current_page}/{total_pages})"
            
            # UI更新
            if self.page:
                self.data_table.update()
                if self.pagination_info:
                    self.pagination_info.update()
            
        except Exception as ex:
            print(f"[ERROR] Failed to update table: {ex}")

    def create_status_badge(self, status: str) -> ft.Container:
        """ステータスバッジ作成"""
        status_colors = {
            "処理完了": ft.Colors.GREEN,
            "処理中": ft.Colors.ORANGE,
            "未処理": ft.Colors.GREY,
            "未整形": ft.Colors.BLUE,
            "未ベクトル化": ft.Colors.PURPLE,
            "エラー": ft.Colors.RED
        }
        
        color = status_colors.get(status, ft.Colors.GREY)
        
        return ft.Container(
            content=ft.Text(status, color=ft.Colors.WHITE, size=12, weight=ft.FontWeight.BOLD),
            padding=ft.padding.symmetric(horizontal=8, vertical=4),
            bgcolor=color,
            border_radius=12
        )

    def on_status_change(self, e):
        """ステータスフィルター変更"""
        self.status_filter = e.control.value
        self.apply_filters()

    def on_search_change(self, e):
        """検索テキスト変更"""
        self.search_text = e.control.value
        self.apply_filters()

    def on_page_size_change(self, e):
        """ページサイズ変更"""
        self.page_size = int(e.control.value)
        self.current_page = 1
        self.update_table()

    def prev_page(self, e):
        """前のページ"""
        if self.current_page > 1:
            self.current_page -= 1
            self.update_table()

    def next_page(self, e):
        """次のページ"""
        total_pages = max(1, (len(self.filtered_files) + self.page_size - 1) // self.page_size)
        if self.current_page < total_pages:
            self.current_page += 1
            self.update_table()

    def on_row_select(self, e, file_id: str, file_data: Dict[str, Any]):
        """行選択処理"""
        self.selected_file_id = file_id if e.control.selected else None
        self.update_table()
        
        if self.on_file_select_callback:
            self.on_file_select_callback(file_id if e.control.selected else None)

    def get_selected_file(self) -> Optional[Dict[str, Any]]:
        """選択されたファイル情報取得"""
        if not self.selected_file_id:
            return None
        
        for file_data in self.all_files:
            if str(file_data.get('id', '')) == self.selected_file_id:
                return file_data
        return None


class PDFPreviewComponent:
    """PDFプレビューコンポーネント"""

    def __init__(self):
        self.content_container: ft.Container | None = None

    def create_preview_widget(self) -> ft.Container:
        """プレビューウィジェット作成"""
        self.content_container = ft.Container(
            content=ft.Column([
                ft.Container(expand=True),
                ft.Icon(ft.Icons.PICTURE_AS_PDF, size=80, color=ft.Colors.GREY_400),
                ft.Text("PDFファイルを選択してください", size=16, color=ft.Colors.GREY_600),
                ft.Container(expand=True)
            ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            expand=True,
            bgcolor=ft.Colors.WHITE,
            border=ft.border.all(1, ft.Colors.GREY_300),
            border_radius=8,
            margin=ft.margin.all(4)
        )
        
        return self.content_container

    def show_pdf_preview(self, file_info: Dict[str, Any]):
        """PDFプレビュー表示"""
        if not self.content_container:
            return
            
        file_name = file_info.get('file_name', 'Unknown')
        file_size = file_info.get('file_size', 0)
        
        if file_size >= 1024 * 1024:
            size_text = f"{file_size / (1024 * 1024):.1f} MB"
        elif file_size >= 1024:
            size_text = f"{file_size / 1024:.1f} KB"
        else:
            size_text = f"{file_size} B"
        
        self.content_container.content = ft.Column([
            ft.Container(height=20),
            ft.Icon(ft.Icons.PICTURE_AS_PDF, size=60, color=ft.Colors.RED_400),
            ft.Text("PDFプレビュー", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.BLACK87),
            ft.Container(height=10),
            ft.Text(file_name, size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.BLACK87),
            ft.Text(f"サイズ: {size_text}", size=12, color=ft.Colors.GREY_600),
            ft.Container(height=20),
            ft.Text("※ プレビュー機能は未実装です", size=12, color=ft.Colors.ORANGE_600),
            ft.Container(expand=True)
        ], alignment=ft.MainAxisAlignment.START, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        
        try:
            self.content_container.update()
        except:
            pass

    def show_empty_preview(self):
        """空のプレビュー表示"""
        if not self.content_container:
            return
            
        self.content_container.content = ft.Column([
            ft.Container(expand=True),
            ft.Icon(ft.Icons.PICTURE_AS_PDF, size=80, color=ft.Colors.GREY_400),
            ft.Text("PDFファイルを選択してください", size=16, color=ft.Colors.GREY_600),
            ft.Container(expand=True)
        ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        
        try:
            self.content_container.update()
        except:
            pass


class FilesPage:
    """ファイル管理ページ（統合版）"""

    def __init__(self):
        # コンポーネント初期化
        self.files_table = FilesTableComponent(on_file_select_callback=self.on_file_selected)
        self.pdf_preview = PDFPreviewComponent()
        
        # ページ参照
        self.page: ft.Page | None = None

    def create_main_layout(self):
        """メインレイアウト作成"""
        try:
            # ページ参照設定
            self.files_table.page = self.page
            
            # 左：ファイル一覧テーブル
            left_pane = self.files_table.create_table_widget()
            
            # 右：PDFプレビュー
            right_pane = self.pdf_preview.create_preview_widget()
            
            # 左右分割レイアウト（1:1比率）
            main_row = ft.Row([
                ft.Container(content=left_pane, expand=1),
                ft.VerticalDivider(width=1, thickness=1, color=ft.Colors.GREY_300),
                ft.Container(content=right_pane, expand=1)
            ], spacing=0, expand=True, vertical_alignment=ft.CrossAxisAlignment.STRETCH)
            
            return ft.Container(
                content=main_row,
                padding=ft.padding.all(0),
                expand=True
            )
            
        except Exception as ex:
            import traceback
            traceback.print_exc()
            return ft.Container(
                content=ft.Text(f"レイアウト作成エラー: {str(ex)}", color=ft.Colors.RED),
                padding=ft.padding.all(20)
            )

    def load_files(self):
        """ファイル一覧読み込み"""
        self.files_table.load_files()

    def on_file_selected(self, file_id):
        """ファイル選択時のコールバック"""
        if file_id:
            file_info = self.files_table.get_selected_file()
            if file_info:
                self.pdf_preview.show_pdf_preview(file_info)
        else:
            self.pdf_preview.show_empty_preview()


def show_files_page(page: ft.Page = None):
    """ファイル管理ページ表示関数"""
    if page:
        page.bgcolor = ft.Colors.GREY_50
    
    files_page = FilesPage()
    files_page.page = page
    layout = files_page.create_main_layout()
    files_page.load_files()
    
    return layout
