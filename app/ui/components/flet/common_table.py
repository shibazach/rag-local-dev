#!/usr/bin/env python3
"""
Flet共通テーブルコンポーネント
カラムヘッダー + データ行 + ページネーション のセット
"""

import flet as ft
from typing import List, Dict, Any, Callable, Optional

class CommonDataTable:
    """
    共通データテーブルコンポーネント
    
    Features:
    - カラムヘッダー（ソート可能）
    - データ行（選択・ダブルクリック対応）
    - ページネーション
    - 行密度調整
    """
    
    def __init__(self, 
                 page: ft.Page,
                 columns: List[Dict[str, Any]],
                 rows: List[Dict[str, Any]] = None,
                 on_row_select: Optional[Callable] = None,
                 on_row_double_click: Optional[Callable] = None,
                 rows_per_page: int = 20,
                 compact: bool = True):
        """
        初期化
        
        Args:
            page: Fletページインスタンス
            columns: カラム定義 [{"name": "col1", "label": "Column 1", "numeric": False}, ...]
            rows: 行データ [{"col1": "value1", "col2": "value2"}, ...]
            on_row_select: 行選択時コールバック
            on_row_double_click: 行ダブルクリック時コールバック
            rows_per_page: 1ページあたり行数
            compact: コンパクト表示（行高縮小）
        """
        self.page = page
        self.columns = columns
        self.rows = rows or []
        self.on_row_select = on_row_select
        self.on_row_double_click = on_row_double_click
        self.rows_per_page = rows_per_page
        self.compact = compact
        
        self.current_page = 0
        self.selected_rows = set()
        
        # UI要素
        self.data_table = None
        self.pagination_container = None
        
    def build(self) -> ft.Column:
        """テーブル全体を構築"""
        # データテーブル作成
        self.data_table = self._create_data_table()
        
        # ページネーション作成
        self.pagination_container = self._create_pagination()
        
        return ft.Column([
            # テーブル本体（全域拡張）
            ft.Container(
                content=self.data_table,
                expand=True,
                bgcolor=ft.Colors.WHITE,
                border=ft.border.all(1, ft.Colors.GREY_300),
                border_radius=4
            ),
            # ページネーション
            self.pagination_container
        ], spacing=0, expand=True)
    
    def _create_data_table(self) -> ft.DataTable:
        """データテーブル作成"""
        # カラム定義
        ft_columns = []
        for col in self.columns:
            ft_columns.append(
                ft.DataColumn(
                    label=ft.Text(
                        col["label"], 
                        size=12 if self.compact else 14,
                        weight=ft.FontWeight.BOLD
                    ),
                    numeric=col.get("numeric", False)
                )
            )
        
        # 現在ページの行データ
        start_idx = self.current_page * self.rows_per_page
        end_idx = start_idx + self.rows_per_page
        page_rows = self.rows[start_idx:end_idx]
        
        # 行作成
        ft_rows = []
        for idx, row in enumerate(page_rows):
            actual_idx = start_idx + idx
            
            cells = []
            for col in self.columns:
                col_name = col["name"]
                cell_value = row.get(col_name, "")
                
                # セル作成
                if col_name == "status" and isinstance(cell_value, str):
                    # ステータス列は特別処理（色付きバッジ）
                    cell_content = self._create_status_badge(cell_value)
                else:
                    cell_content = ft.Text(
                        str(cell_value), 
                        size=11 if self.compact else 12,
                        overflow=ft.TextOverflow.ELLIPSIS
                    )
                
                cells.append(ft.DataCell(cell_content))
            
            ft_rows.append(
                ft.DataRow(
                    cells=cells,
                    selected=actual_idx in self.selected_rows,
                    on_select_changed=lambda e, idx=actual_idx: self._handle_row_select(e, idx),
                    on_long_press=lambda e, idx=actual_idx: self._handle_row_double_click(idx)
                )
            )
        
        return ft.DataTable(
            columns=ft_columns,
            rows=ft_rows,
            border=ft.border.all(1, ft.Colors.GREY_300),
            border_radius=4,
            data_row_min_height=28 if self.compact else 40,
            data_row_max_height=32 if self.compact else 50,
            heading_row_color=ft.Colors.GREY_100,
            heading_row_height=36 if self.compact else 48,
            column_spacing=20
        )
    
    def _create_status_badge(self, status: str) -> ft.Container:
        """ステータスバッジ作成"""
        color_map = {
            "処理完了": ft.Colors.GREEN,
            "処理中": ft.Colors.ORANGE,
            "未処理": ft.Colors.GREY_600,
            "エラー": ft.Colors.RED
        }
        
        return ft.Container(
            content=ft.Text(
                status, 
                size=10 if self.compact else 12,
                color=ft.Colors.WHITE
            ),
            bgcolor=color_map.get(status, ft.Colors.GREY),
            padding=ft.padding.symmetric(horizontal=6, vertical=1),
            border_radius=3
        )
    
    def _create_pagination(self) -> ft.Container:
        """ページネーション作成"""
        total_pages = (len(self.rows) + self.rows_per_page - 1) // self.rows_per_page
        start_row = self.current_page * self.rows_per_page + 1
        end_row = min(start_row + self.rows_per_page - 1, len(self.rows))
        
        return ft.Container(
            content=ft.Row([
                ft.Text("Records per page:", size=11),
                ft.Container(
                    content=ft.Dropdown(
                        value=str(self.rows_per_page),
                        options=[
                            ft.dropdown.Option("10"),
                            ft.dropdown.Option("20"),
                            ft.dropdown.Option("50"),
                        ],
                        width=60,
                        text_size=10,
                        dense=True,
                        on_change=self._change_rows_per_page
                    ),
                    height=24
                ),
                ft.Container(expand=True),
                ft.Text(
                    f"{start_row}-{end_row} of {len(self.rows)}", 
                    size=11, 
                    color=ft.Colors.GREY_600
                ),
                ft.IconButton(
                    ft.Icons.CHEVRON_LEFT, 
                    icon_size=14,
                    tooltip="前のページ",
                    on_click=self._prev_page,
                    disabled=self.current_page == 0
                ),
                ft.IconButton(
                    ft.Icons.CHEVRON_RIGHT, 
                    icon_size=14,
                    tooltip="次のページ",
                    on_click=self._next_page,
                    disabled=self.current_page >= total_pages - 1
                )
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, tight=True),
            padding=ft.padding.symmetric(horizontal=8, vertical=4),
            height=32,
            bgcolor=ft.Colors.GREY_50
        )
    
    def _handle_row_select(self, e, row_index):
        """行選択処理"""
        if e.control.selected:
            self.selected_rows.add(row_index)
        else:
            self.selected_rows.discard(row_index)
        
        if self.on_row_select:
            self.on_row_select(e, row_index)
    
    def _handle_row_double_click(self, row_index):
        """行ダブルクリック処理"""
        if self.on_row_double_click:
            self.on_row_double_click(row_index)
    
    def _change_rows_per_page(self, e):
        """1ページあたり行数変更"""
        self.rows_per_page = int(e.control.value)
        self.current_page = 0  # 最初のページに戻る
        self._refresh_table()
    
    def _prev_page(self, e):
        """前のページ"""
        if self.current_page > 0:
            self.current_page -= 1
            self._refresh_table()
    
    def _next_page(self, e):
        """次のページ"""
        total_pages = (len(self.rows) + self.rows_per_page - 1) // self.rows_per_page
        if self.current_page < total_pages - 1:
            self.current_page += 1
            self._refresh_table()
    
    def _refresh_table(self):
        """テーブル再描画"""
        # 実装：テーブルとページネーションを更新
        # この部分は実際の使用時に実装
        pass
    
    def update_data(self, new_rows: List[Dict[str, Any]]):
        """データ更新"""
        self.rows = new_rows
        self.current_page = 0
        self.selected_rows.clear()
        self._refresh_table()
    
    def get_selected_count(self) -> int:
        """選択行数取得"""
        return len(self.selected_rows)
    
    def get_selected_data(self) -> List[Dict[str, Any]]:
        """選択行データ取得"""
        return [self.rows[i] for i in self.selected_rows if i < len(self.rows)]
