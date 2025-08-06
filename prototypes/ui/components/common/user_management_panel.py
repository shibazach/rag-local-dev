"""
ユーザー管理パネル
BaseTablePanelを継承した具体実装
"""
from nicegui import ui
from typing import List, Dict, Optional, Callable
from .table import BaseTablePanel
from ..base import BaseButton, CommonStyles, StyleBuilder


class UserManagementPanel(BaseTablePanel):
    """
    ユーザー管理専用テーブルパネル
    
    Usage:
        panel = UserManagementPanel(users_data=users)
        panel.render()
    """
    
    def __init__(
        self,
        users_data: List[Dict] = None,
        on_add_user: Optional[Callable] = None,
        on_edit_user: Optional[Callable] = None,
        **kwargs
    ):
        super().__init__(
            title="👥 ユーザー管理",
            rows_per_page=15,
            **kwargs
        )
        self.data = users_data or self._create_sample_users()
        self.on_add_user = on_add_user
        self.on_edit_user = on_edit_user
        
        # テーブルカラム定義
        self.columns = [
            {'field': 'id', 'label': 'ID', 'width': '60px', 'align': 'center'},
            {'field': 'name', 'label': '名前', 'width': '1fr', 'align': 'left'},
            {'field': 'email', 'label': 'メール', 'width': '2fr', 'align': 'left'},
            {'field': 'role', 'label': '役割', 'width': '100px', 'align': 'center'},
            {'field': 'status', 'label': 'ステータス', 'width': '100px', 'align': 'center'},
            {'field': 'last_login', 'label': '最終ログイン', 'width': '160px', 'align': 'center'}
        ]
        
    def _build_header_buttons(self):
        """ヘッダーボタン作成"""
        # NiceGUIのui.buttonをそのまま使用（制約は受け入れる）
        ui.button('➕', color='primary').style(
            'padding: 2px 6px; font-size: 12px; '
            'min-height: 24px; min-width: 24px;'
        ).on('click', self.on_add_user) if self.on_add_user else None
        
        ui.button('✏️', color='primary').style(
            'padding: 2px 6px; font-size: 12px; '
            'min-height: 24px; min-width: 24px;'
        ).on('click', self.on_edit_user) if self.on_edit_user else None
        
    def _build_table(self):
        """テーブル構築"""
        # 現在ページのデータ
        start_idx = (self.current_page - 1) * self.rows_per_page
        end_idx = start_idx + self.rows_per_page
        current_page_data = self.data[start_idx:end_idx]
        
        # テーブルコンテナ
        with ui.element('div').style(
            'width: 100%; height: 100%; '
            'display: flex; flex-direction: column; '
            'overflow: hidden; position: relative;'
        ):
            # ヘッダー（スクロールバー分padding追加）
            grid_columns = ' '.join([col['width'] for col in self.columns])
            with ui.element('div').style(
                f'flex-shrink: 0; background: {CommonStyles.COLOR_PRIMARY}; '
                f'color: white; font-weight: bold; '
                f'font-size: {CommonStyles.FONT_SIZE_XS}; '
                f'border-bottom: 1px solid {CommonStyles.COLOR_GRAY_200}; '
                'padding-right: 17px; margin: 0; box-sizing: border-box; '
                'width: 100%; position: relative;'
            ):
                with ui.element('div').style(
                    f'display: grid; '
                    f'grid-template-columns: {grid_columns}; '
                    'gap: 0; padding: 0;'
                ):
                    for i, col in enumerate(self.columns):
                        border_style = 'border-right: 1px solid rgba(255,255,255,0.2);' if i < len(self.columns) - 1 else ''
                        with ui.element('div').style(
                            f'padding: 6px 8px; '
                            f'{border_style} '
                            f'text-align: {col["align"]};'
                        ):
                            ui.label(col['label'])
            
            # テーブル本体
            with ui.element('div').style(
                'flex: 1; overflow-y: auto; overflow-x: hidden; '
                f'border: 1px solid {CommonStyles.COLOR_GRAY_200}; '
                'margin: 0; padding: 0; box-sizing: border-box;'
            ):
                for row in current_page_data:
                    self._create_table_row(row, grid_columns)
                    
    def _create_table_row(self, row: Dict, grid_columns: str):
        """テーブル行作成"""
        with ui.element('div').style(
            f'display: grid; '
            f'grid-template-columns: {grid_columns}; '
            'gap: 0; padding: 0; '
            f'border-bottom: 1px solid {CommonStyles.COLOR_GRAY_100}; '
            'transition: background 0.2s; min-height: 28px;'
        ).classes('hover:bg-gray-50'):
            # ID
            self._create_cell(str(row['id']), 'center')
            
            # 名前
            self._create_cell(row['name'], 'left')
            
            # メール
            self._create_cell(row['email'], 'left')
            
            # 役割
            role_colors = {
                '管理者': CommonStyles.COLOR_ERROR,
                'エディター': CommonStyles.COLOR_WARNING,
                'ユーザー': CommonStyles.COLOR_GRAY_600
            }
            self._create_badge_cell(row['role'], role_colors.get(row['role'], CommonStyles.COLOR_GRAY_600))
            
            # ステータス
            status_colors = {
                'アクティブ': CommonStyles.COLOR_SUCCESS,
                '保留': CommonStyles.COLOR_WARNING,
                '無効': CommonStyles.COLOR_ERROR
            }
            self._create_badge_cell(row['status'], status_colors.get(row['status'], CommonStyles.COLOR_GRAY_600))
            
            # 最終ログイン
            self._create_cell(row['last_login'], 'center')
            
    def _create_cell(self, text: str, align: str = 'left'):
        """通常セル作成"""
        with ui.element('div').style(
            f'padding: 4px 8px; '
            f'border-right: 1px solid {CommonStyles.COLOR_GRAY_100}; '
            f'text-align: {align}; '
            f'font-size: {CommonStyles.FONT_SIZE_XS}; '
            'display: flex; align-items: center; '
            f'justify-content: {"center" if align == "center" else "flex-start"};'
        ):
            ui.label(text)
            
    def _create_badge_cell(self, text: str, color: str):
        """バッジセル作成"""
        with ui.element('div').style(
            f'padding: 4px 8px; '
            f'border-right: 1px solid {CommonStyles.COLOR_GRAY_100}; '
            'text-align: center; '
            f'font-size: {CommonStyles.FONT_SIZE_XS}; '
            'display: flex; align-items: center; justify-content: center;'
        ):
            with ui.element('span').style(
                f'background: {color}; '
                'color: white; padding: 1px 6px; border-radius: 3px; '
                'font-size: 9px;'
            ):
                ui.label(text)
                
    def _build_footer_content(self):
        """フッターコンテンツ"""
        ui.label(f'👥 {len(self.data)}名のユーザー')
        ui.label('最終同期: 15:30')
        
    def _create_sample_users(self):
        """サンプルユーザーデータ作成"""
        return [
            {'id': 1, 'name': '田中太郎', 'email': 'tanaka@example.com', 'role': '管理者', 'status': 'アクティブ', 'last_login': '2024-01-15 14:30'},
            {'id': 2, 'name': '佐藤花子', 'email': 'sato@example.com', 'role': 'ユーザー', 'status': 'アクティブ', 'last_login': '2024-01-15 13:45'},
            {'id': 3, 'name': '鈴木一郎', 'email': 'suzuki@example.com', 'role': 'ユーザー', 'status': '保留', 'last_login': '2024-01-14 16:20'},
            {'id': 4, 'name': '高橋美咲', 'email': 'takahashi@example.com', 'role': 'エディター', 'status': 'アクティブ', 'last_login': '2024-01-15 12:15'},
            {'id': 5, 'name': '山田次郎', 'email': 'yamada@example.com', 'role': 'ユーザー', 'status': '無効', 'last_login': '2024-01-10 09:30'},
            {'id': 6, 'name': '伊藤三郎', 'email': 'ito@example.com', 'role': 'ユーザー', 'status': 'アクティブ', 'last_login': '2024-01-15 11:00'},
            {'id': 7, 'name': '渡辺四郎', 'email': 'watanabe@example.com', 'role': '管理者', 'status': 'アクティブ', 'last_login': '2024-01-15 10:45'},
            {'id': 8, 'name': '中村五郎', 'email': 'nakamura@example.com', 'role': 'エディター', 'status': 'アクティブ', 'last_login': '2024-01-14 18:30'},
            {'id': 9, 'name': '小林六子', 'email': 'kobayashi@example.com', 'role': 'ユーザー', 'status': '保留', 'last_login': '2024-01-13 09:15'},
            {'id': 10, 'name': '加藤七美', 'email': 'kato@example.com', 'role': 'ユーザー', 'status': 'アクティブ', 'last_login': '2024-01-15 15:20'},
            {'id': 11, 'name': '吉田八郎', 'email': 'yoshida@example.com', 'role': 'ユーザー', 'status': 'アクティブ', 'last_login': '2024-01-15 14:00'},
            {'id': 12, 'name': '山口九子', 'email': 'yamaguchi@example.com', 'role': 'エディター', 'status': '無効', 'last_login': '2024-01-12 16:45'},
            {'id': 13, 'name': '松本十郎', 'email': 'matsumoto@example.com', 'role': 'ユーザー', 'status': 'アクティブ', 'last_login': '2024-01-15 13:30'},
            {'id': 14, 'name': '井上十一', 'email': 'inoue@example.com', 'role': '管理者', 'status': 'アクティブ', 'last_login': '2024-01-15 12:50'},
            {'id': 15, 'name': '木村十二子', 'email': 'kimura@example.com', 'role': 'ユーザー', 'status': '保留', 'last_login': '2024-01-11 10:30'},
            {'id': 16, 'name': '林十三郎', 'email': 'hayashi@example.com', 'role': 'ユーザー', 'status': 'アクティブ', 'last_login': '2024-01-15 09:45'},
            {'id': 17, 'name': '清水十四', 'email': 'shimizu@example.com', 'role': 'エディター', 'status': 'アクティブ', 'last_login': '2024-01-15 08:30'},
            {'id': 18, 'name': '山崎十五子', 'email': 'yamazaki@example.com', 'role': 'ユーザー', 'status': '無効', 'last_login': '2024-01-08 17:00'},
            {'id': 19, 'name': '森十六', 'email': 'mori@example.com', 'role': 'ユーザー', 'status': 'アクティブ', 'last_login': '2024-01-15 07:15'},
            {'id': 20, 'name': '池田十七郎', 'email': 'ikeda@example.com', 'role': '管理者', 'status': 'アクティブ', 'last_login': '2024-01-15 06:00'}
        ]