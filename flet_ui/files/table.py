import flet as ft
from typing import Dict, List, Optional, Any
import math
from .api_client import FilesDBClient


class FilesTable:
    """ファイル一覧テーブル（独立コンポーネント）"""
    
    def __init__(self, on_file_select_callback=None):
        # APIクライアント
        self.api_client = FilesDBClient()
        
        # コールバック
        self.on_file_select = on_file_select_callback
        
        # データ状態
        self.files_data = []
        self.selected_file_id = None
        self.current_page = 1
        self.per_page = 20
        self.search_term = ""
        self.status_filter = ""
        self.total_pages = 1
        
        # ページネーション用UI要素
        self.page_input = None
        self.per_page_dropdown = None
        
        # UI要素参照（情報密度向上のため行高さを削減）
        self.files_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("ファイル名"), numeric=False),
                ft.DataColumn(ft.Text("サイズ"), numeric=False),
                ft.DataColumn(ft.Text("ステータス"), numeric=False),
                ft.DataColumn(ft.Text("登録日"), numeric=False),
            ],
            data_row_min_height=32,
            data_row_max_height=32,
            heading_row_height=40,
            horizontal_margin=0,
            column_spacing=6,
            show_checkbox_column=False
        )
        self.pagination_container = ft.Container()
        
        # テーブルコンテナ（Qiita記事準拠、幅制御改善）
        self.table_container = ft.Container(
            content=ft.Column(
                controls=[self.files_table],
                scroll=ft.ScrollMode.ALWAYS,
                expand=True,
                spacing=0
            ),
            expand=True,
            padding=ft.padding.all(0),
            margin=ft.margin.all(0)
        )
    
    def create_table_widget(self):
        """テーブルウィジェット作成"""
        # 検索・フィルターUI
        search_input = ft.TextField(
            label="ファイル名で検索",
            on_change=self.on_search,
            width=200
        )
        
        status_dropdown = ft.Dropdown(
            label="ステータス",
            options=[
                ft.dropdown.Option("全て"),
                ft.dropdown.Option("処理完了"),
                ft.dropdown.Option("処理中"), 
                ft.dropdown.Option("未処理"),
                ft.dropdown.Option("未整形"),
                ft.dropdown.Option("未ベクトル化"),
                ft.dropdown.Option("エラー"),
            ],
            value="全て",
            on_change=self.on_status_filter_change,
            width=120
        )
        
        return ft.Container(
            content=ft.Column([
                # パネルヘッダー（水平レイアウト）
                ft.Container(
                    content=ft.Row([
                        ft.Text("📁 ファイル一覧", size=16, weight=ft.FontWeight.BOLD),
                        status_dropdown,
                        search_input
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    bgcolor=ft.Colors.GREY_100,
                    padding=ft.padding.all(8),
                    border=ft.border.only(bottom=ft.border.BorderSide(1, ft.Colors.GREY_300))
                ),
                # ファイル一覧テーブル
                ft.Container(
                    content=self.table_container,
                    expand=True,
                    padding=ft.padding.all(8)
                ),
                # ページネーション
                ft.Container(
                    content=self.pagination_container,
                    padding=ft.padding.all(8),
                    border=ft.border.only(top=ft.border.BorderSide(1, ft.Colors.GREY_300))
                )
            ], spacing=0),
            bgcolor=ft.Colors.WHITE,
            border=ft.border.all(1, ft.Colors.GREY_300),
            border_radius=8
        )
    
    def load_files(self):
        """ファイル一覧を読み込み"""
        try:
            response = self.api_client.get_files_list(
                page=self.current_page,
                page_size=self.per_page,
                status=self.status_filter,
                search=self.search_term
            )
            
            if response and response.get("status") == "success":
                self.files_data = response
                self.update_files_table()
                self.update_pagination()
                self.safe_update_ui()
            else:
                print(f"ファイル読み込みエラー: {response.get('error', '不明なエラー')}")
                self.files_data = {"files": [], "pagination": {}}
                self.update_files_table()
                self.update_pagination()
                
        except Exception as e:
            print(f"ファイル読み込み例外: {e}")
            self.files_data = {"files": [], "pagination": {}}
            self.update_files_table()
            self.update_pagination()
    
    def update_files_table(self):
        """ファイル一覧テーブルの表示を更新"""
        if not self.files_data or not self.files_data.get('files'):
            self.files_table.rows = []
            return
        
        # テーブル行
        table_rows = []
        for file_info in self.files_data['files']:
            # ステータス変換とバッジ
            status_raw = file_info.get('status', 'unknown')
            
            status_display_map = {
                'processed': '処理完了',
                'processing': '処理中',
                'pending': '未処理',
                'text_extracted': '未整形',
                'text_refined': '未ベクトル化',
                'error': 'エラー'
            }
            status_display = status_display_map.get(status_raw, status_raw)
            
            status_colors = {
                '処理完了': ft.Colors.GREEN,
                '処理中': ft.Colors.BLUE,
                '未処理': ft.Colors.ORANGE,
                '未整形': ft.Colors.PURPLE,
                '未ベクトル化': ft.Colors.TEAL,
                'エラー': ft.Colors.RED
            }
            
            status_badge = ft.Container(
                content=ft.Text(
                    status_display,
                    color=ft.Colors.WHITE,
                    size=10
                ),
                bgcolor=status_colors.get(status_display, ft.Colors.GREY),
                padding=ft.padding.symmetric(horizontal=6, vertical=2),
                border_radius=8
            )
            
            # ファイルサイズフォーマット
            size = file_info.get('file_size', 0)
            if size > 1024*1024:
                size_str = f"{size/(1024*1024):.1f} MB"
            elif size > 1024:
                size_str = f"{size/1024:.1f} KB"
            else:
                size_str = f"{size} B"
            
            # 日付フォーマット
            created_at = file_info.get('created_at', '')
            if 'T' in created_at:
                created_at = created_at.split('T')[0]
            
            # テーブル行
            row = ft.DataRow(
                cells=[
                    ft.DataCell(ft.Text(
                        file_info.get('file_name', 'unknown'),
                        size=11,
                        overflow=ft.TextOverflow.ELLIPSIS
                    )),
                    ft.DataCell(ft.Text(size_str, size=11)),
                    ft.DataCell(status_badge),
                    ft.DataCell(ft.Text(created_at, size=11)),
                ],
                selected=file_info['id'] == self.selected_file_id,
                on_select_changed=lambda e, fid=file_info['id']: self.on_row_select(fid)
            )
            table_rows.append(row)
        
        self.files_table.rows = table_rows
    
    def update_pagination(self):
        """ページネーション表示更新"""
        if not self.files_data:
            return
        
        pagination = self.files_data.get('pagination', {})
        current_page = pagination.get('current_page', self.current_page)
        total_pages = pagination.get('total_pages', 1)
        total_count = pagination.get('total_count', 0)
        
        self.total_pages = total_pages
        
        # ページ入力フィールド（手入力可能）
        if not self.page_input:
            self.page_input = ft.TextField(
                value=str(current_page),
                width=60,
                text_align=ft.TextAlign.CENTER,
                on_submit=self.on_page_input_submit,
                input_filter=ft.NumbersOnlyInputFilter()
            )
        else:
            self.page_input.value = str(current_page)
        
        # Records per pageドロップダウン
        if not self.per_page_dropdown:
            self.per_page_dropdown = ft.Dropdown(
                options=[
                    ft.dropdown.Option("10"),
                    ft.dropdown.Option("20"),
                    ft.dropdown.Option("50"),
                    ft.dropdown.Option("100"),
                ],
                value=str(self.per_page),
                width=60,
                on_change=self.on_per_page_change
            )
        else:
            self.per_page_dropdown.value = str(self.per_page)
        
        pagination_controls = [
            ft.IconButton(
                ft.Icons.ARROW_BACK,
                disabled=current_page <= 1,
                on_click=lambda _: self.change_page(current_page - 1)
            ),
            self.page_input,
            ft.Text("/", size=14),
            ft.Text(str(total_pages), size=14),
            ft.IconButton(
                ft.Icons.ARROW_FORWARD,
                disabled=current_page >= total_pages,
                on_click=lambda _: self.change_page(current_page + 1)
            ),
            ft.Container(expand=True),
            ft.Text("表示件数:", size=12, color=ft.Colors.GREY_600),
            self.per_page_dropdown,
            ft.Text(f"全 {total_count} 件", size=12, color=ft.Colors.GREY_600)
        ]
        
        self.pagination_container.content = ft.Row(
            pagination_controls, 
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=10
        )
    
    def on_row_select(self, file_id):
        """行選択処理"""
        if self.selected_file_id == file_id:
            self.selected_file_id = None
        else:
            self.selected_file_id = file_id
        
        self.update_files_table()
        self.safe_update_ui()
        
        # 外部コールバック呼び出し
        if self.on_file_select:
            self.on_file_select(self.selected_file_id)
    
    def on_search(self, e):
        """検索処理"""
        new_search = e.control.value if e.control.value else ""
        if new_search != self.search_term:
            self.search_term = new_search
            self.current_page = 1
            self.load_files()
    
    def on_status_filter_change(self, e):
        """ステータスフィルター変更"""
        selected_value = e.control.value
        
        status_value_map = {
            "全て": "",
            "処理完了": "processed",
            "処理中": "processing",
            "未処理": "pending",
            "未整形": "text_extracted",
            "未ベクトル化": "text_refined",
            "エラー": "error"
        }
        
        new_filter = status_value_map.get(selected_value, "")
        if new_filter != self.status_filter:
            self.status_filter = new_filter
            self.current_page = 1
            self.load_files()
    
    def change_page(self, new_page):
        """ページ変更"""
        if new_page != self.current_page:
            self.current_page = new_page
            self.load_files()
    
    def on_page_input_submit(self, e):
        """ページ番号手入力処理"""
        try:
            page_num = int(e.control.value)
            if 1 <= page_num <= self.total_pages:
                self.change_page(page_num)
            else:
                e.control.value = str(self.current_page)
        except ValueError:
            e.control.value = str(self.current_page)
    
    def on_per_page_change(self, e):
        """表示件数変更処理"""
        try:
            new_per_page = int(e.control.value)
            if new_per_page != self.per_page:
                self.per_page = new_per_page
                self.current_page = 1
                self.load_files()
        except ValueError:
            pass
    
    def safe_update_ui(self):
        """安全なUI更新"""
        try:
            # テーブルコンテナを更新
            if self.table_container and hasattr(self.table_container, 'page') and self.table_container.page:
                self.table_container.update()
            
            # ページネーションコンテナを更新
            if self.pagination_container and hasattr(self.pagination_container, 'page') and self.pagination_container.page:
                self.pagination_container.update()
        except Exception as e:
            pass  # エラーを無視
    
    def get_selected_file(self):
        """選択されたファイル情報を取得"""
        if not self.selected_file_id or not self.files_data.get('files'):
            return None
        
        for file_info in self.files_data['files']:
            if file_info['id'] == self.selected_file_id:
                return file_info
        return None
