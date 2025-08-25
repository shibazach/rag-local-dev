#!/usr/bin/env python3
"""
Flet RAGシステム - ファイル一覧テーブル
既存構成を完全保持 + 新共通コンポーネント内部使用版
"""

import flet as ft
from typing import Dict, List, Optional, Any
from .api_client import FletFilesClient
from ..shared.panel_components import (
    PanelHeaderConfig, PanelConfig, create_panel, create_files_panel_config
)
from ..shared.table_components import (
    TableColumnConfig, FlexibleDataTable, create_pagination_controls
)


class FilesTable:
    """ファイル一覧テーブル（既存インターフェース保持 + 新共通コンポーネント内部使用）"""

    def __init__(self, on_file_select_callback=None):
        # 既存インターフェース保持
        self.on_file_select_callback = on_file_select_callback
        self.files_data: Dict[str, Any] = {"files": [], "pagination": {}}
        self.current_page = 1
        self.per_page = 20
        self.total_pages = 1
        self.total_count = 0
        self.selected_file_id = None
        self.status_filter = "全て"
        self.search_text = ""
        
        # APIクライアント
        self.api_client = FletFilesClient()
        
        # ページネーション動的更新用の参照
        self.pagination_controls = None
        
        # ファイル一覧用カラム設定（新共通コンポーネント使用）
        self.column_configs = [
            TableColumnConfig(
                key="filename",
                title="ファイル名",
                column_type="text",
                width=None,  # 可変幅（残り幅使用）
                alignment="left"
            ),
            TableColumnConfig(
                key="file_size", 
                title="サイズ",
                column_type="size",
                width=100,
                alignment="right"
            ),
            TableColumnConfig(
                key="status",
                title="ステータス",
                column_type="status_badge",
                width=120,
                alignment="center"
            ),
            TableColumnConfig(
                key="created_at",
                title="登録日時",
                column_type="datetime",
                width=150,  # upload/page.pyと同様に調整
                alignment="right"  # 右寄せに変更
            )
        ]
        
        # 新共通コンポーネント使用
        self.data_table = FlexibleDataTable(
            column_configs=self.column_configs,
            row_click_handler=self._on_row_click
        )
        
        # 初期データでテーブル更新
        self.data_table.update_rows([], None)

    def create_table_widget(self):
        """ファイルテーブルウィジェット作成（既存メソッド名保持 + 新共通コンポーネント使用）"""

        
        try:
            # ページネーション作成（動的更新対応版）
            self.pagination_controls = self._create_pagination_controls()

            # パネル内コンテンツ（テーブル + ページネーション）
            panel_content = ft.Column([
                ft.Container(
                    content=self.data_table,
                    expand=True
                ),
                ft.Container(
                    content=self.pagination_controls,
                    padding=ft.padding.symmetric(horizontal=0, vertical=0),
                    border=ft.border.only(top=ft.border.BorderSide(1, ft.Colors.GREY_300))
                )
            ], spacing=0, expand=True)

            # 新共通コンポーネント使用でパネル作成
            panel_config = create_files_panel_config(
                title="ファイル一覧",
                title_icon="📁",
                show_status=True,
                show_search=True,
                status_callback=self._on_status_change,
                search_callback=self._on_search_change
            )

            
            return create_panel(panel_config, panel_content)

        except Exception as ex:
            import traceback
            traceback.print_exc()
            return ft.Container(
                content=ft.Text(f"エラー: {str(ex)}", color=ft.Colors.RED),
                padding=ft.padding.all(20),
            )

    def load_files(self):
        """既存メソッド名保持: ファイル一覧読み込み"""
        try:
            self.files_data = self.api_client.get_files_list(
                page=self.current_page,
                page_size=self.per_page,  # per_page → page_size (既存API仕様に合わせる)
                status=self.status_filter,
                search=self.search_text
            )
            
            # デバッグ: APIレスポンス確認

            
            # ページネーション情報更新
            pagination = self.files_data.get('pagination', {})
            self.total_pages = pagination.get('total_pages', 1)
            self.total_count = pagination.get('total_count', 0)
            self.current_page = pagination.get('current_page', self.current_page)
            
            # デバッグ: ページネーション情報確認

            print(f"  current_page: {self.current_page}")
            print(f"  files_count: {len(self.files_data.get('files', []))}")
            
            self._update_table_data()
            self._update_pagination()  # ページネーション動的更新
            
        except Exception as e:
            print(f"ファイル読み込み例外: {e}")
            self.files_data = {"files": [], "pagination": {}}
            self.total_pages = 1
            self.total_count = 0
            self._update_table_data()
            self._update_pagination()  # ページネーション動的更新

    def get_selected_file(self):
        """既存メソッド名保持: 選択されたファイル情報を取得"""
        if not self.selected_file_id or not self.files_data.get('files'):
            return None
            
        for file_info in self.files_data['files']:
            if file_info.get('id') == self.selected_file_id:
                return file_info
        return None

    def _update_table_data(self):
        """テーブルデータ更新（新共通コンポーネント使用）"""
        if not self.files_data or not self.files_data.get('files'):
            self.data_table.update_rows([], None)
            return
        
        # ファイルデータを新共通コンポーネント用の形式に変換
        rows_data = []
        for file_info in self.files_data['files']:
            # ステータス変換
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
            
            # 日付フォーマット（UTC+9日時表示）
            created_at = file_info.get('created_at', '')
            if 'T' in created_at:
                from datetime import datetime, timezone, timedelta
                try:
                    # ISO形式をパース
                    dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    # UTC+9に変換
                    jst = dt.astimezone(timezone(timedelta(hours=9)))
                    created_at = jst.strftime('%Y-%m-%d %H:%M:%S')  # upload/page.pyと同じフォーマット
                except:
                    # パースエラー時はフォールバック
                    date_part, time_part = created_at.split('T')
                    time_part = time_part.split('.')[0]
                    created_at = f"{date_part} {time_part}"
            
            # 新共通コンポーネント用の行データ
            row_data = {
                'id': file_info['id'],
                'filename': file_info.get('file_name', 'unknown'),
                'file_size': file_info.get('file_size', 0),
                'status': status_display,
                'created_at': created_at
            }
            rows_data.append(row_data)
        
        # 新共通コンポーネントでテーブル更新
        self.data_table.update_rows(rows_data, self.selected_file_id)

    def _on_row_click(self, row_id: str):
        """行クリック処理（既存コールバック保持）"""
        if self.selected_file_id == row_id:
            self.selected_file_id = None
        else:
            self.selected_file_id = row_id
        
        # テーブル再描画
        self._update_table_data()
        
        # コールバック呼び出し
        if self.on_file_select_callback:
            self.on_file_select_callback(self.selected_file_id)
        
        print(f"選択されたファイルID: {self.selected_file_id}")

    def _on_page_change(self, page: int):
        """ページ変更処理（新共通コンポーネント対応）"""
        if 1 <= page <= self.total_pages:
            self.current_page = page
            self.load_files()


    def _on_per_page_change(self, per_page: int):
        """1ページあたり件数変更処理（新共通コンポーネント対応）"""
        self.per_page = per_page
        self.current_page = 1
        self.load_files()


    def _on_status_change(self, e):
        """ステータス変更処理（新共通コンポーネント対応）"""
        self.status_filter = e.control.value
        self.current_page = 1
        self.load_files()
        print(f"ステータスフィルタ: {self.status_filter}")

    def _on_search_change(self, e):
        """検索変更処理（新共通コンポーネント対応）"""
        self.search_text = e.control.value
        self.current_page = 1
        self.load_files()
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
            
            # UI更新（ページに追加済みの場合のみ）
            try:
                if hasattr(self, 'page') and self.page and hasattr(self.pagination_controls, 'page'):
                    self.pagination_controls.update()
            except AssertionError as e:
                # Container がまだページに追加されていない場合はスキップ
                # Pagination update skipped: Container not yet added to page
                pass
            



# 既存の古いクラス・関数は完全削除（新共通コンポーネントに統合済み）