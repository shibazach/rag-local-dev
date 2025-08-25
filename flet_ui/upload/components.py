#!/usr/bin/env python3
"""
Flet RAGシステム - アップロードページコンポーネント
ファイルアップロード・フォルダアップロード・リアルタイムログ
"""

import flet as ft
from typing import Dict, List, Any, Optional
from flet_ui.shared.panel_components import (
    PanelHeaderConfig, PanelConfig, create_panel, create_upload_panel_config
)
from flet_ui.shared.table_components import (
    TableColumnConfig, FlexibleDataTable, create_pagination_controls, StandardColumns
)


class FileUploadArea(ft.Container):
    """ファイルアップロードエリア"""
    
    def __init__(self):
        super().__init__()
        self.expand = True
        self._create_content()
    
    def _create_content(self):
        """コンテンツ作成"""
        # ドラッグ&ドロップエリア
        drop_area = ft.Container(
            content=ft.Column([
                ft.Icon(ft.Icons.CLOUD_UPLOAD, size=48, color=ft.Colors.GREY_400),
                ft.Container(height=12),
                ft.Text("ファイルをドラッグ&ドロップ", size=16, color=ft.Colors.GREY_600, text_align=ft.TextAlign.CENTER),
                ft.Text("または", size=14, color=ft.Colors.GREY_500, text_align=ft.TextAlign.CENTER),
                ft.Container(height=8),
                ft.ElevatedButton(
                    "ファイル選択",
                    icon=ft.Icons.FOLDER_OPEN,
                    on_click=self._on_file_select
                ),
                ft.Container(height=16),
                ft.Text("対応形式: PDF, DOCX, TXT, PNG, JPG", 
                       size=12, color=ft.Colors.GREY_500, text_align=ft.TextAlign.CENTER)
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            expand=True,
            alignment=ft.alignment.center,
            border=ft.border.all(2, ft.Colors.GREY_300),
            border_radius=8,
            bgcolor=ft.Colors.GREY_50,
            padding=ft.padding.all(20)
        )
        
        # パネル設定
        panel_config = create_upload_panel_config(
            title="ファイルアップロード",
            title_icon=ft.Icons.DESCRIPTION,
            show_file_select=True,
            file_select_callback=self._on_file_select
        )
        
        # パネル作成
        panel = create_panel(panel_config, drop_area)
        self.content = panel
    
    def _on_file_select(self, e=None):
        """ファイル選択処理"""
        print("ファイル選択がクリックされました")


class FolderUploadArea(ft.Container):
    """フォルダアップロードエリア"""
    
    def __init__(self):
        super().__init__()
        self.expand = True
        self._create_content()
    
    def _create_content(self):
        """コンテンツ作成"""
        # アップロード方式ラジオボタン
        upload_mode = ft.RadioGroup(
            content=ft.Column([
                ft.Radio(value="single", label="単一フォルダ"),
                ft.Radio(value="recursive", label="サブフォルダ含む")
            ]),
            value="single"
        )
        
        # フォルダ選択エリア
        folder_area = ft.Container(
            content=ft.Column([
                ft.Icon(ft.Icons.FOLDER, size=48, color=ft.Colors.GREY_400),
                ft.Container(height=12),
                ft.Text("フォルダをドラッグ&ドロップ", size=16, color=ft.Colors.GREY_600, text_align=ft.TextAlign.CENTER),
                ft.Text("または", size=14, color=ft.Colors.GREY_500, text_align=ft.TextAlign.CENTER),
                ft.Container(height=8),
                ft.ElevatedButton(
                    "フォルダ選択",
                    icon=ft.Icons.FOLDER_OPEN,
                    on_click=self._on_folder_select
                ),
                ft.Container(height=16),
                upload_mode,
                ft.Container(height=8),
                ft.Text("対応形式: PDF, DOCX, TXT, PNG, JPG", 
                       size=12, color=ft.Colors.GREY_500, text_align=ft.TextAlign.CENTER)
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            expand=True,
            alignment=ft.alignment.center,
            border=ft.border.all(2, ft.Colors.GREY_300),
            border_radius=8,
            bgcolor=ft.Colors.GREY_50,
            padding=ft.padding.all(20)
        )
        
        # パネル設定
        panel_config = create_upload_panel_config(
            title="フォルダアップロード",
            title_icon=ft.Icons.FOLDER,
            show_file_select=True,
            file_select_callback=self._on_folder_select
        )
        
        # パネル作成
        panel = create_panel(panel_config, folder_area)
        self.content = panel
    
    def _on_folder_select(self, e=None):
        """フォルダ選択処理"""
        print("フォルダ選択がクリックされました")


class RealTimeLogArea(ft.Container):
    """リアルタイムログエリア"""
    
    def __init__(self):
        super().__init__()
        self.expand = True
        self.current_page = 1
        self.per_page = 20
        self.total_pages = 2  # 31件 / 20件 = 2ページ
        self.total_count = 31
        self.status_filter = "全て"
        self.search_text = ""
        
        # ログデータ（サンプル）
        self.log_data = self._generate_sample_log_data()
        
        # テーブル設定（標準カラムセット使用）
        self.column_configs = StandardColumns.create_upload_table_columns()
        
        # テーブル作成
        self.data_table = FlexibleDataTable(
            column_configs=self.column_configs,
            row_click_handler=self._on_row_click
        )
        
        self._create_content()
    
    def _create_content(self):
        """コンテンツ作成"""
        # ページネーション作成
        self.pagination_controls = self._create_pagination_controls()
        
        # テーブル + ページネーション
        table_content = ft.Column([
            ft.Container(
                content=self.data_table,
                expand=True
            ),
            ft.Container(
                content=self.pagination_controls,
                padding=ft.padding.symmetric(horizontal=0, vertical=0),
                border=ft.border.only(top=ft.BorderSide(1, ft.Colors.GREY_300))
            )
        ], spacing=0, expand=True)
        
        # パネル設定
        panel_config = create_upload_panel_config(
            title="アップロードログ",
            title_icon=ft.Icons.LIST_ALT,
            show_status=True,
            show_search=True,
            status_callback=self._on_status_change,
            search_callback=self._on_search_change
        )
        
        # パネル作成
        panel = create_panel(panel_config, table_content)
        self.content = panel
        
        # 初期データ読み込み
        self._update_table_data()
    
    def _generate_sample_log_data(self) -> List[Dict[str, Any]]:
        """サンプルログデータ生成"""
        sample_data = []
        statuses = ["処理完了", "処理中", "未処理", "エラー"]
        
        for i in range(31):
            sample_data.append({
                "id": f"log_{i+1}",
                "filename": f"upload_file_{i+1:02d}.pdf",
                "file_size": 1024 * (100 + i * 50),
                "status": statuses[i % len(statuses)],
                "created_at": f"2025-01-{(i % 30) + 1:02d} 10:{i % 60:02d}:00"
            })
        
        return sample_data
    
    def _filter_data(self) -> List[Dict[str, Any]]:
        """データフィルタリング"""
        filtered_data = self.log_data
        
        # ステータスフィルタ
        if self.status_filter != "全て":
            filtered_data = [item for item in filtered_data if item["status"] == self.status_filter]
        
        # 検索フィルタ
        if self.search_text:
            filtered_data = [item for item in filtered_data if self.search_text.lower() in item["filename"].lower()]
        
        return filtered_data
    
    def _update_table_data(self):
        """テーブルデータ更新"""
        filtered_data = self._filter_data()
        
        # ページネーション計算
        start_idx = (self.current_page - 1) * self.per_page
        end_idx = start_idx + self.per_page
        page_data = filtered_data[start_idx:end_idx]
        
        # ページネーション情報更新
        self.total_count = len(filtered_data)
        self.total_pages = max(1, (self.total_count + self.per_page - 1) // self.per_page)
        
        # テーブル更新
        self.data_table.update_rows(page_data, None)
        
        # ページネーション更新
        self._update_pagination()
    
    def _on_row_click(self, row_id: str):
        """行クリック処理"""
        print(f"ログ行がクリックされました: {row_id}")
    
    def _on_page_change(self, page: int):
        """ページ変更処理"""
        if 1 <= page <= self.total_pages:
            self.current_page = page
            self._update_table_data()
    
    def _on_per_page_change(self, per_page: int):
        """1ページあたり件数変更処理"""
        self.per_page = per_page
        self.current_page = 1
        self._update_table_data()
    
    def _on_status_change(self, e):
        """ステータス変更処理"""
        self.status_filter = e.control.value
        self.current_page = 1
        self._update_table_data()
        print(f"ステータスフィルタ: {self.status_filter}")
    
    def _on_search_change(self, e):
        """検索変更処理"""
        self.search_text = e.control.value
        self.current_page = 1
        self._update_table_data()
        print(f"検索キーワード: {self.search_text}")
    
    def _create_pagination_controls(self):
        """ページネーションコントロール作成"""
        return create_pagination_controls(
            current_page=self.current_page,
            total_pages=self.total_pages,
            total_count=self.total_count,
            page_size=self.per_page,
            on_page_change=self._on_page_change,
            on_page_size_change=self._on_per_page_change
        )
    
    def _update_pagination(self):
        """ページネーション動的更新"""
        if self.pagination_controls:
            # 新しいページネーションコントロールを作成
            new_pagination = self._create_pagination_controls()
            
            # 既存のコントロールを置き換え
            self.pagination_controls.content = new_pagination.content
            
            # UI更新
            try:
                self.pagination_controls.update()
            except AssertionError:
                # まだページに追加されていない場合はスキップ
                pass