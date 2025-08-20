#!/usr/bin/env python3
"""
Flet RAGシステム - ファイル管理ページ（NiceGUI版準拠）
- 左ペイン：ファイル一覧テーブル（チェックボックス付き）
- 右ペイン：プレビューエリア
"""

import flet as ft
from typing import Dict, List, Optional, Any
import math
from .api_client import FilesDBClient


def show_files_page():
    """ファイル管理ページのメインコンテンツ"""
    files_page = FilesPage()
    layout = files_page.create_main_layout()
    # レイアウト作成後に初期データ読み込み
    files_page.load_files()
    return layout


class FilesPage:
    """ファイル管理ページ（NiceGUI版準拠）"""
    
    def __init__(self):
        # APIクライアント（実DB接続版）
        self.api_client = FilesDBClient()
        
        # データ状態
        self.files_data = []
        self.selected_file_id = None  # 選択されたファイルID
        self.current_page = 1
        self.per_page = 20  # デフォルト20件
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
            horizontal_margin=0,     # マージンを0に
            column_spacing=8,        # カラム間スペースをさらに削減
            width=None               # テーブル幅を親コンテナに合わせる
        )
        self.pagination_container = ft.Container()
        self.preview_container = ft.Container()
        
        # スプリッター（50:50）
        self.left_width_ratio = 0.5  # 左ペインの幅（比率）
        self.min_width_ratio = 0.2   # 最小幅（20%）
        self.max_width_ratio = 0.8   # 最大幅（80%）
        
        # UI要素参照（スプリッター用）
        self.left_pane_container = None
        self.main_container = None
        self.table_container = None
    
    def create_main_layout(self):
        """メインレイアウト作成"""
        
        # 左ペイン（ファイル一覧）
        left_pane = self.create_files_list_pane()
        self.left_pane_container = left_pane  # 参照を保存
        
        # リサイズハンドル（スプリッター）
        resize_handle = ft.GestureDetector(
            content=ft.Container(
                width=8,
                bgcolor=ft.Colors.GREY_400,
                border_radius=4,
                content=ft.Container(
                    width=2,
                    bgcolor=ft.Colors.GREY_600,
                    margin=ft.margin.symmetric(horizontal=3)
                ),
                height=None  # 親の高さに合わせる
            ),
            on_pan_update=self.on_pan_update,
            mouse_cursor=ft.MouseCursor.RESIZE_COLUMN
        )
        
        # 右ペイン（プレビュー）
        right_pane = self.create_preview_pane()
        
        # 初期プレビュー設定
        self.preview_container.content = ft.Container(
            content=ft.Text("ファイルを選択してプレビューを表示", text_align=ft.TextAlign.CENTER),
            alignment=ft.alignment.center,
            expand=True
        )
        
        # メインレイアウト（8px padding、50:50比率）
        self.main_container = ft.Container(
            content=ft.Row([
                ft.Container(content=left_pane, expand=1),  # 50%
                resize_handle,
                ft.Container(content=right_pane, expand=1)  # 50%
            ], spacing=6),
            padding=ft.padding.all(8),
            expand=True
        )
        
        return self.main_container
    
    def create_files_list_pane(self):
        """ファイル一覧ペイン作成"""
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
        
        # テーブルコンテナを作成して参照を保存（Qiita記事準拠）
        self.table_container = ft.Column(
            controls=[self.files_table],
            scroll=ft.ScrollMode.ALWAYS,  # Qiita記事通りALWAYSを使用
            expand=True
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
                        # ファイル一覧テーブル（Containerで包む）
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
    
    def create_preview_pane(self):
        """プレビューペイン作成"""
        return ft.Container(
            content=self.preview_container,
            bgcolor=ft.Colors.WHITE,
            border=ft.border.all(1, ft.Colors.GREY_300),
            border_radius=8,
            padding=ft.padding.all(8),
            expand=True
        )
    
    def load_files(self):
        """ファイル一覧を読み込み"""
        try:
            response = self.api_client.get_files_list(
                page=self.current_page,
                page_size=self.per_page,
                search=self.search_term,
                status=self.status_filter
            )
            self.files_data = response
            self.update_files_table()
            self.update_pagination()
            
            # UIを更新（安全に）
            self.safe_update_ui()
                
        except Exception as e:
            print(f"ファイル読み込みエラー: {e}")
            # エラー時は空のテーブルを表示
            self.files_data = {"files": [], "pagination": {"current_page": 1, "total_pages": 1, "total_count": 0}}
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
            
            # 英語ステータスを日本語に変換
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
            
            # テーブル行（チェックボックス削除、行選択のみ）
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
    
    def safe_update_ui(self):
        """UIを安全に更新"""
        try:
            if self.table_container and hasattr(self.table_container, 'page') and self.table_container.page:
                self.table_container.update()
            if self.pagination_container and hasattr(self.pagination_container, 'page') and self.pagination_container.page:
                self.pagination_container.update()
        except Exception as e:
            print(f"UI更新エラー: {e}")  # デバッグ用
    
    def update_pagination(self):
        """ページネーション表示更新"""
        if not self.files_data:
            return
        
        pagination = self.files_data.get('pagination', {})
        current_page = pagination.get('current_page', self.current_page)
        total_pages = pagination.get('total_pages', 1)
        total_count = pagination.get('total_count', 0)
        
        # クラス変数を更新
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
                width=70,
                on_change=self.on_per_page_change
            )
        else:
            self.per_page_dropdown.value = str(self.per_page)
        
        pagination_controls = []
        
        # 前のページボタン
        prev_btn = ft.IconButton(
            ft.Icons.ARROW_BACK,
            disabled=current_page <= 1,
            on_click=lambda _: self.change_page(current_page - 1)
        )
        pagination_controls.append(prev_btn)
        
        # ページ入力 + 総ページ数
        pagination_controls.extend([
            self.page_input,
            ft.Text("/", size=14),
            ft.Text(str(total_pages), size=14),
        ])
        
        # 次のページボタン  
        next_btn = ft.IconButton(
            ft.Icons.ARROW_FORWARD,
            disabled=current_page >= total_pages,
            on_click=lambda _: self.change_page(current_page + 1)
        )
        pagination_controls.append(next_btn)
        
        # Records per page + 件数表示
        pagination_controls.extend([
            ft.Container(expand=True),
            ft.Text("表示件数:", size=12, color=ft.Colors.GREY_600),
            self.per_page_dropdown,
            ft.Text(f"全 {total_count} 件", size=12, color=ft.Colors.GREY_600)
        ])
        
        self.pagination_container.content = ft.Row(
            pagination_controls, 
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=10
        )
    
    def change_page(self, new_page):
        """ページ変更"""
        if new_page != self.current_page:
            self.current_page = new_page
            self.load_files()
    
    def on_row_select(self, file_id):
        """行選択処理"""
        # 既に選択されている場合は選択解除、そうでなければ選択
        if self.selected_file_id == file_id:
            self.selected_file_id = None
            # 選択解除時は空のプレビューを表示
            self.show_empty_preview()
        else:
            self.selected_file_id = file_id
            # PDFプレビューを表示
            self.show_pdf_preview(file_id)
        
        # テーブルを再描画して選択状態を反映
        self.update_files_table()
        # UIを更新
        self.safe_update_ui()
    
    def show_empty_preview(self):
        """空のプレビュー表示"""
        self.preview_container.content = ft.Container(
            content=ft.Text("ファイルを選択してプレビューを表示", text_align=ft.TextAlign.CENTER),
            alignment=ft.alignment.center,
            expand=True
        )
        try:
            if self.preview_container and hasattr(self.preview_container, 'page') and self.preview_container.page:
                self.preview_container.update()
        except:
            pass
    
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
        
        # 日本語表示名から英語DB値にマッピング
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
    
    def on_page_input_submit(self, e):
        """ページ番号手入力"""
        try:
            new_page = int(e.control.value)
            if 1 <= new_page <= self.total_pages:
                self.change_page(new_page)
            else:
                # 無効なページ番号の場合は現在ページに戻す
                e.control.value = str(self.current_page)
                e.control.update()
        except ValueError:
            # 無効な入力の場合は現在ページに戻す
            e.control.value = str(self.current_page)
            e.control.update()
    
    def on_per_page_change(self, e):
        """表示件数変更"""
        new_per_page = int(e.control.value)
        if new_per_page != self.per_page:
            self.per_page = new_per_page
            self.current_page = 1  # 1ページ目に戻る
            self.load_files()
    
    def show_pdf_preview(self, file_id):
        """PDFプレビュー表示（行選択時）"""
        # ファイル情報取得
        file_info = None
        for f in self.files_data.get('files', []):
            if f['id'] == file_id:
                file_info = f
                break
        
        if not file_info:
            return
        
        file_name = file_info.get('file_name', 'Unknown')
        
        # PDFプレビューコンテンツ（シンプル版）
        preview_content = ft.Container(
            content=ft.Column([
                # PDF表示領域（将来的に実際のPDF表示可能）
                ft.Container(
                    content=ft.Column([
                        ft.Icon(ft.Icons.PICTURE_AS_PDF, size=64, color=ft.Colors.RED),
                        ft.Container(height=20),
                        ft.Text(
                            file_name,
                            size=14,
                            weight=ft.FontWeight.BOLD,
                            text_align=ft.TextAlign.CENTER,
                            color=ft.Colors.GREY_700
                        ),
                        ft.Container(height=20),
                        ft.Container(
                            content=ft.Text(
                                "PDFプレビュー機能\n実装予定",
                                text_align=ft.TextAlign.CENTER,
                                size=12,
                                color=ft.Colors.GREY_500
                            ),
                            bgcolor=ft.Colors.GREY_100,
                            padding=ft.padding.all(20),
                            border_radius=8,
                            border=ft.border.all(1, ft.Colors.GREY_300)
                        )
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    alignment=ft.alignment.center,
                    expand=True
                )
            ], spacing=0, expand=True),
            alignment=ft.alignment.center,
            expand=True
        )
        
        self.preview_container.content = preview_content
        try:
            if self.preview_container and hasattr(self.preview_container, 'page') and self.preview_container.page:
                self.preview_container.update()
        except:
            pass
    
    def show_file_detail(self, file_id):
        """ファイル詳細ダイアログ表示"""
        print(f"ファイル詳細表示: {file_id}")
        # TODO: 詳細ダイアログの実装
    
    def download_file(self, file_id):
        """ファイルダウンロード"""
        print(f"ファイルダウンロード: {file_id}")
        # TODO: ダウンロード機能の実装
    
    def on_pan_update(self, e: ft.DragUpdateEvent):
        """スプリッターのドラッグ処理（50:50固定のため無効）"""
        # 50:50固定レイアウトのため、動的リサイズは無効
        pass