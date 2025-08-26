#!/usr/bin/env python3
"""
Flet RAGシステム - 共通テーブルコンポーネント
テーブル・ページネーション・カラム設定の統一実装
"""

import flet as ft
from dataclasses import dataclass
from typing import Dict, List, Optional, Callable, Any
from .panel_components import create_status_badge


@dataclass
class TableColumnConfig:
    """テーブルカラム設定クラス"""
    key: str
    title: str
    column_type: str  # "text", "size", "status_badge", "datetime", "checkbox"
    width: Optional[int] = None
    alignment: str = "left"  # "left", "center", "right"


class StandardColumns:
    """標準テーブルカラム設定"""
    
    @staticmethod
    def create_filename_column(width: Optional[int] = None, alignment: str = "left") -> TableColumnConfig:
        """ファイル名カラム（可変幅、省略表示対応）"""
        return TableColumnConfig(
            key="filename",
            title="ファイル名",
            column_type="text",
            width=width,
            alignment=alignment
        )
    
    @staticmethod
    def create_filesize_column(width: int = 100, alignment: str = "right") -> TableColumnConfig:
        """ファイルサイズカラム（MB/KB/B表示）"""
        return TableColumnConfig(
            key="file_size",
            title="サイズ",
            column_type="size",
            width=width,
            alignment=alignment
        )
    
    @staticmethod
    def create_status_column(width: int = 120, alignment: str = "center") -> TableColumnConfig:
        """ステータスカラム（バッジ表示）"""
        return TableColumnConfig(
            key="status",
            title="ステータス",
            column_type="status_badge",
            width=width,
            alignment=alignment
        )
    
    @staticmethod
    def create_datetime_column(width: int = 150, alignment: str = "center") -> TableColumnConfig:
        """日時カラム（yyyy-mm-dd hh:mm:ss形式）"""
        return TableColumnConfig(
            key="created_at",
            title="登録日時",
            column_type="datetime",
            width=width,
            alignment=alignment
        )
    
    @staticmethod
    def create_file_table_columns(datetime_alignment: str = "center") -> List[TableColumnConfig]:
        """ファイル管理用標準カラムセット"""
        return [
            StandardColumns.create_filename_column(),
            StandardColumns.create_filesize_column(),
            StandardColumns.create_status_column(),
            StandardColumns.create_datetime_column(alignment=datetime_alignment)
        ]
    
    @staticmethod
    def create_upload_table_columns() -> List[TableColumnConfig]:
        """アップロード用標準カラムセット（日時中央揃え）"""
        return StandardColumns.create_file_table_columns(datetime_alignment="center")
    
    @staticmethod
    def create_files_table_columns() -> List[TableColumnConfig]:
        """ファイル一覧用標準カラムセット（日時中央揃え）"""
        return StandardColumns.create_file_table_columns(datetime_alignment="center")


def create_simple_table(column_configs: List[TableColumnConfig], rows_data: List[Dict[str, Any]], selected_row_id: Optional[str] = None, row_click_handler: Optional[Callable] = None) -> ft.Column:
    """シンプルなテーブル作成"""
    
    # ヘッダー行作成
    header_cells = []
    for config in column_configs:
        cell = ft.Container(
            content=ft.Text(
                config.title,
                size=14,
                weight=ft.FontWeight.BOLD,
                color=ft.Colors.BLACK87,
                text_align=ft.TextAlign.LEFT if config.alignment == "left" else 
                          ft.TextAlign.CENTER if config.alignment == "center" else ft.TextAlign.RIGHT
            ),
            padding=ft.padding.symmetric(horizontal=12, vertical=8),
            width=config.width,
            expand=True if config.width is None else False
        )
        header_cells.append(cell)
    
    header_row = ft.Container(
        content=ft.Row(header_cells, spacing=0),
        bgcolor=ft.Colors.GREY_200,
        border=ft.border.only(bottom=ft.BorderSide(1, ft.Colors.GREY_300))
    )
    
    # データ行作成
    data_rows = []
    for row_data in rows_data:
        row_id = row_data.get('id', '')
        is_selected = (row_id == selected_row_id)
        
        row_cells = []
        for config in column_configs:
            cell_content = _create_cell_content(config, row_data)
            
            cell = ft.Container(
                content=cell_content,
                padding=ft.padding.symmetric(horizontal=12, vertical=8),
                width=config.width,
                expand=True if config.width is None else False
            )
            row_cells.append(cell)
        
        row_container = ft.Container(
            content=ft.Row(row_cells, spacing=0),
            bgcolor=ft.Colors.BLUE_50 if is_selected else ft.Colors.WHITE,
            border=ft.border.only(bottom=ft.BorderSide(1, ft.Colors.GREY_200)),
            on_click=lambda e, rid=row_id: row_click_handler(rid) if row_click_handler else None
        )
        data_rows.append(row_container)
    
    # テーブル全体
    table_content = [header_row] + data_rows
    
    return ft.Column(table_content, spacing=0, expand=True)


def _create_cell_content(config: TableColumnConfig, row_data: Dict[str, Any], compact_mode: bool = False) -> ft.Control:
    """セル内容作成（コンパクトモード対応）"""
    value = row_data.get(config.key, "")
    
    # コンパクトモード時のサイズ調整
    text_size = 11 if compact_mode else 14
    status_text_size = 10 if compact_mode else 12
    
    if config.column_type == "text":
        return ft.Text(
            str(value), 
            size=text_size, 
            color=ft.Colors.BLACK87,
            overflow=ft.TextOverflow.ELLIPSIS,  # 長いテキストを...で省略
            max_lines=1  # 1行に制限
        )
    
    elif config.column_type == "size":
        if isinstance(value, (int, float)) and value > 0:
            if value >= 1024 * 1024:
                size_text = f"{value / (1024 * 1024):.1f} MB"
            elif value >= 1024:
                size_text = f"{value / 1024:.1f} KB"
            else:
                size_text = f"{value} B"
        else:
            size_text = "-"
        text_align = ft.TextAlign.RIGHT if config.alignment == "right" else ft.TextAlign.LEFT
        return ft.Text(size_text, size=text_size, color=ft.Colors.BLACK87, text_align=text_align)
    
    elif config.column_type == "status_badge":
        return create_status_badge(str(value))
    
    elif config.column_type == "datetime":
        text_align = ft.TextAlign.RIGHT if config.alignment == "right" else \
                    ft.TextAlign.CENTER if config.alignment == "center" else ft.TextAlign.LEFT
        return ft.Text(str(value), size=status_text_size, color=ft.Colors.BLACK87, text_align=text_align)
    
    elif config.column_type == "checkbox":
        return ft.Checkbox(value=bool(value), disabled=True)
    
    else:
        return ft.Text(str(value), size=text_size, color=ft.Colors.BLACK87)


class FlexibleDataTable(ft.Column):
    """柔軟なデータテーブル（ヘッダー固定版）"""
    
    def __init__(self, column_configs: List[TableColumnConfig], row_click_handler: Optional[Callable] = None):
        super().__init__()
        self.column_configs = column_configs
        self.row_click_handler = row_click_handler
        self.rows_data = []
        self.selected_row_id = None
        self.expand = True
        
        # コンパクトモードフラグ（ダイアログ等での使用時）
        self._compact_mode = False
        
        # ヘッダー行作成
        self.header_row = self._create_header_row()
        
        # データ部分（スクロール可能）
        self.data_container = ft.Column([], spacing=0, scroll=ft.ScrollMode.AUTO, expand=True)
        
        # テーブル構造設定
        self.controls = [
            self.header_row,
            self.data_container
        ]
        self.spacing = 0
    
    def _create_header_row(self) -> ft.Container:
        """ヘッダー行作成"""
        header_cells = []
        for config in self.column_configs:
            # コンパクトモード対応（ヘッダー）
            header_size = 12 if self._compact_mode else 14
            header_padding = ft.padding.symmetric(horizontal=8, vertical=4) if self._compact_mode else ft.padding.symmetric(horizontal=12, vertical=8)
            
            cell = ft.Container(
                content=ft.Text(
                    config.title,
                    size=header_size,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.BLACK87,
                    text_align=ft.TextAlign.LEFT if config.alignment == "left" else 
                              ft.TextAlign.CENTER if config.alignment == "center" else ft.TextAlign.RIGHT
                ),
                padding=header_padding,
                width=config.width,
                expand=True if config.width is None else False
            )
            header_cells.append(cell)
        
        return ft.Container(
            content=ft.Row(header_cells, spacing=0),
            bgcolor=ft.Colors.GREY_200,
            border=ft.border.only(bottom=ft.BorderSide(1, ft.Colors.GREY_300))
        )
    
    def update_rows(self, rows_data: List[Dict[str, Any]], selected_row_id: Optional[str] = None):
        """行データ更新"""
        self.rows_data = rows_data
        self.selected_row_id = selected_row_id
        
        # データ行をクリア
        self.data_container.controls.clear()
        
        # 新しいデータ行を作成
        for row_data in rows_data:
            row_id = row_data.get('id', '')
            is_selected = (row_id == selected_row_id)
            
            row_cells = []
            for config in self.column_configs:
                cell_content = _create_cell_content(config, row_data, self._compact_mode)
                
                # セルの配置設定
                if config.alignment == "center":
                    alignment = ft.alignment.center
                elif config.alignment == "right":
                    alignment = ft.alignment.center_right
                else:
                    alignment = ft.alignment.center_left
                
                # コンパクトモード対応（データ行）
                data_padding = ft.padding.symmetric(horizontal=8, vertical=4) if self._compact_mode else ft.padding.symmetric(horizontal=12, vertical=8)
                
                cell = ft.Container(
                    content=cell_content,
                    padding=data_padding,
                    width=config.width,
                    expand=True if config.width is None else False,
                    alignment=alignment
                )
                row_cells.append(cell)
            
            row_container = ft.Container(
                content=ft.Row(row_cells, spacing=0),
                bgcolor=ft.Colors.BLUE_50 if is_selected else ft.Colors.WHITE,
                border=ft.border.only(bottom=ft.BorderSide(1, ft.Colors.GREY_200)),
                on_click=lambda e, rid=row_id: self.row_click_handler(rid) if self.row_click_handler else None
            )
            self.data_container.controls.append(row_container)
        
        # UI更新
        try:
            self.data_container.update()
        except AssertionError:
            # まだページに追加されていない場合はスキップ
            pass


def create_pagination_controls(
    current_page: int,
    total_pages: int,
    total_count: int,
    page_size: int,
    on_page_change: Callable[[int], None],
    on_page_size_change: Callable[[int], None]
) -> ft.Container:
    """ページネーションコントロール作成"""
    
    # ページ入力
    page_input = ft.TextField(
        value=str(current_page),
        width=60,
        text_align=ft.TextAlign.CENTER,
        bgcolor=ft.Colors.WHITE,
        on_submit=lambda e: _on_page_input_submit(e, on_page_change, total_pages)
    )
    
    # 1ページあたり件数ドロップダウン
    per_page_dropdown = ft.Dropdown(
        options=[
            ft.dropdown.Option("10"),
            ft.dropdown.Option("20"),
            ft.dropdown.Option("50"),
            ft.dropdown.Option("100")
        ],
        value=str(page_size),
        width=90,  # 見切れ防止
        bgcolor=ft.Colors.WHITE,
        on_change=lambda e: on_page_size_change(int(e.control.value))
    )
    
    # 前へボタン
    prev_button = ft.IconButton(
        icon=ft.Icons.CHEVRON_LEFT,
        disabled=(current_page <= 1),
        on_click=lambda e: on_page_change(current_page - 1)
    )
    
    # 次へボタン
    next_button = ft.IconButton(
        icon=ft.Icons.CHEVRON_RIGHT,
        disabled=(current_page >= total_pages),
        on_click=lambda e: on_page_change(current_page + 1)
    )
    
    # ページネーション情報（カッコ削除、右側のみ表示）
    page_info = ft.Text(
        f"全 {total_count} 件",
        size=14,
        color=ft.Colors.BLACK87
    )
    
    # ページネーションレイアウト
    left_section = ft.Row([
        ft.Text("表示件数:", size=12, color=ft.Colors.BLACK87),
        per_page_dropdown,
    ], spacing=6, alignment=ft.MainAxisAlignment.START)
    
    center_section = ft.Row([
        prev_button,
        page_input,
        ft.Text(f"/{total_pages}", size=14, color=ft.Colors.BLACK87),
        next_button,
    ], spacing=4, alignment=ft.MainAxisAlignment.CENTER)
    
    right_section = ft.Container(
        content=page_info,
        alignment=ft.alignment.center_right
    )
    
    pagination_content = ft.Row([
        left_section,
        ft.Container(expand=True),
        center_section, 
        ft.Container(expand=True),
        right_section
    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER)
    
    return ft.Container(
        content=pagination_content,
        height=54,
        padding=ft.padding.symmetric(horizontal=12, vertical=0),
        bgcolor=ft.Colors.GREY_200
    )


def _on_page_input_submit(e, on_page_change: Callable[[int], None], total_pages: int):
    """ページ入力確定処理"""
    try:
        page = int(e.control.value)
        if 1 <= page <= total_pages:
            on_page_change(page)
        else:
            e.control.value = str(min(max(1, page), total_pages))
            e.control.update()
    except ValueError:
        e.control.value = "1"
        e.control.update()