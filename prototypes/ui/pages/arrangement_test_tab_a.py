"""配置テスト - タブA: 4ペイン分割レイアウト（backup復元版）"""

from nicegui import ui

class ArrangementTestTabA:
    """タブA: 4ペイン分割UI（simple_test.py完全再現）"""
    
    def __init__(self):
        self.users_data = self._create_sample_users()
        self.current_page = 1
        self.rows_per_page = 15
        self.total_pages = (len(self.users_data) - 1) // self.rows_per_page + 1
    
    def render(self):
        """タブAのレイアウトを描画"""
        # 完全な4ペイン分割
        with ui.element('div').style(
            'width: 100%; height: 100%; '
            'display: flex; margin: 0; padding: 0;'
        ).props('id="main-container"'):
            
            # 左側エリア（50%）
            with ui.element('div').style(
                'width: 50%; height: 100%; '
                'display: flex; flex-direction: column; '
                'margin: 0; padding: 0;'
            ).props('id="left-pane"'):
                
                # 左上ペイン
                self._create_left_top_pane()
                
                # 横スプリッター（左）
                self._create_horizontal_splitter_left()
                
                # 左下ペイン
                self._create_left_bottom_pane()
            
            # 縦スプリッター
            self._create_vertical_splitter()
            
            # 右側エリア（50%）
            self._create_right_area()
        
        # スプリッターJavaScript
        self._add_splitter_js()
        
        # ページネーションJavaScript
        self._add_pagination_js()
        
        # テーブルスクロールバー固定余白方式（JavaScript不要）
        # self._add_table_scrollbar_js()  # 固定余白方式では不要
        
        # ページネーションCSS調整（直接inputタグ使用で不要）
        # self._add_pagination_css()
    
    def _create_left_top_pane(self):
        """左上ペイン - データ分析"""
        with ui.element('div').style(
            'width: 100%; height: 50%; '
            'margin: 0; padding: 4px; '
            'box-sizing: border-box; overflow: hidden;'
        ).props('id="left-top-pane"'):
            with ui.element('div').style(
                'width: 100%; height: 100%; '
                'background: white; border-radius: 12px; '
                'box-shadow: 0 2px 8px rgba(0,0,0,0.15); '
                'border: 1px solid #e5e7eb; '
                'display: flex; flex-direction: column; '
                'overflow: hidden;'
            ):
                # ヘッダー（拡張サイズ）
                with ui.element('div').style(
                    'background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); '
                    'color: white; padding: 8px 12px; height: 32px; '
                    'display: flex; align-items: center; justify-content: space-between; '
                    'box-sizing: border-box; flex-shrink: 0;'
                ):
                    ui.label('📊 データ分析').style('font-weight: bold; font-size: 14px;')
                    with ui.element('div').style('display: flex; gap: 2px;'):
                        ui.button('📈', color='white').style(
                            'padding: 1px 4px; font-size: 9px; width: 20px !important; '
                            'height: 20px !important; margin: 0; line-height: 1; '
                            'min-width: 20px !important; max-width: 20px !important;'
                        )
                        ui.button('⚙️', color='white').style(
                            'padding: 1px 4px; font-size: 9px; width: 20px; '
                            'height: 20px; margin: 0; line-height: 1;'
                        )
                
                # コンテンツ
                with ui.element('div').style('flex: 1; padding: 8px; overflow: auto;'):
                    # チャート表示エリア
                    chart_options = {
                        'title': {'text': 'データ分析結果', 'left': 'center', 'textStyle': {'fontSize': 12}},
                        'xAxis': {'type': 'category', 'data': ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']},
                        'yAxis': {'type': 'value'},
                        'series': [{
                            'data': [120, 200, 150, 80, 70, 110, 130], 
                            'type': 'line',
                            'smooth': True
                        }]
                    }
                    ui.echart(chart_options).style('height: 150px; width: 100%;')
                
                # フッター
                with ui.element('div').style(
                    'height: 32px; background: #f8f9fa; '
                    'border-top: 1px solid #e5e7eb; '
                    'display: flex; align-items: center; '
                    'justify-content: space-between; '
                    'padding: 0 12px; font-size: 11px; '
                    'color: #6b7280; flex-shrink: 0;'
                ):
                    ui.label('📊 データ更新: 2024-01-15 15:30')
    
    def _create_horizontal_splitter_left(self):
        """横スプリッター（左）"""
        with ui.element('div').style(
            'width: 100%; height: 6px; '
            'background: #e5e7eb; '
            'cursor: row-resize; margin: 0; padding: 0; '
            'display: flex; align-items: center; justify-content: center; '
            'transition: background 0.2s ease;'
        ).props('id="horizontal-splitter-left" class="splitter"'):
            ui.label('⋮⋮⋮').style('color: #9ca3af; font-size: 8px; transform: rotate(90deg); transition: color 0.2s ease;').classes('splitter-dots')
    
    def _create_left_bottom_pane(self):
        """左下ペイン - ユーザー管理テーブル"""
        from ui.components.common import UserManagementPanel
        
        with ui.element('div').style(
            'width: 100%; height: 50%; '
            'margin: 0; padding: 4px; '
            'box-sizing: border-box; overflow: hidden;'
        ).props('id="left-bottom-pane"'):
            # 共通コンポーネントを使用
            panel = UserManagementPanel(
                users_data=self.users_data,
                on_add_user=lambda: ui.notify('ユーザー追加'),
                on_edit_user=lambda: ui.notify('ユーザー編集'),
                width="100%",
                height="100%"
            )
            panel.render()
    
    def _create_vertical_splitter(self):
        """縦スプリッター"""
        with ui.element('div').style(
            'width: 6px; height: 100%; '
            'background: #e5e7eb; '
            'cursor: col-resize; margin: 0; padding: 0; '
            'display: flex; align-items: center; justify-content: center; '
            'transition: background 0.2s ease;'
        ).props('id="vertical-splitter" class="splitter"'):
            ui.label('⋮⋮⋮').style('color: #9ca3af; font-size: 8px; transition: color 0.2s ease;').classes('splitter-dots')
    
    def _create_right_area(self):
        """右側エリア"""
        with ui.element('div').style(
            'width: 50%; height: 100%; '
            'display: flex; flex-direction: column; '
            'margin: 0; padding: 0;'
        ).props('id="right-pane"'):
            
            # 右上ペイン
            self._create_right_top_pane()
            
            # 横スプリッター（右）
            self._create_horizontal_splitter_right()
            
            # 右下ペイン
            self._create_right_bottom_pane()
    
    def _create_right_top_pane(self):
        """右上ペイン - タスク管理"""
        with ui.element('div').style(
            'width: 100%; height: 50%; '
            'margin: 0; padding: 4px; '
            'box-sizing: border-box; overflow: hidden;'
        ).props('id="right-top-pane"'):
            with ui.element('div').style(
                'width: 100%; height: 100%; '
                'background: white; border-radius: 12px; '
                'box-shadow: 0 2px 8px rgba(0,0,0,0.15); '
                'border: 1px solid #e5e7eb; '
                'display: flex; flex-direction: column; '
                'overflow: hidden;'
            ):
                # ヘッダー
                with ui.element('div').style(
                    'background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); '
                    'color: white; padding: 8px 12px; height: 32px; '
                    'display: flex; align-items: center; justify-content: space-between; '
                    'box-sizing: border-box; flex-shrink: 0;'
                ):
                    ui.label('📝 タスク管理').style('font-weight: bold; font-size: 14px;')
                    with ui.element('div').style('display: flex; gap: 2px;'):
                        ui.button('✅', color='white').style('padding: 1px 4px; font-size: 9px; width: 20px; height: 20px; margin: 0; line-height: 1;')
                        ui.button('🔄', color='white').style('padding: 1px 4px; font-size: 9px; width: 20px; height: 20px; margin: 0; line-height: 1;')
                
                # タスクリスト
                with ui.element('div').style('flex: 1; padding: 8px; overflow: auto;'):
                    tasks = [
                        ('UI設計完了', '完了', '#10b981'),
                        ('バックエンド実装', '進行中', '#f59e0b'),
                        ('テスト実行', '待機', '#6b7280'),
                        ('デプロイ準備', '待機', '#6b7280'),
                        ('ドキュメント更新', '進行中', '#f59e0b'),
                        ('レビュー依頼', '待機', '#6b7280')
                    ]
                    for task, status, color in tasks:
                        with ui.element('div').style(
                            'display: flex; justify-content: space-between; '
                            'align-items: center; padding: 4px 0; '
                            'border-bottom: 1px solid #f3f4f6;'
                        ):
                            ui.label(task).style('font-size: 12px;')
                            with ui.element('span').style(
                                f'background: {color}; color: white; '
                                f'padding: 2px 6px; border-radius: 3px; '
                                f'font-size: 9px;'
                            ):
                                ui.label(status)
                
                # フッター
                with ui.element('div').style(
                    'height: 32px; background: #f8f9fa; '
                    'border-top: 1px solid #e5e7eb; '
                    'display: flex; align-items: center; '
                    'justify-content: space-between; '
                    'padding: 0 12px; font-size: 11px; '
                    'color: #6b7280; flex-shrink: 0;'
                ):
                    ui.label('📝 6件のタスク')
                    ui.label('更新: 15:32')
    
    def _create_horizontal_splitter_right(self):
        """横スプリッター（右）"""
        with ui.element('div').style(
            'width: 100%; height: 6px; '
            'background: #e5e7eb; '
            'cursor: row-resize; margin: 0; padding: 0; '
            'display: flex; align-items: center; justify-content: center; '
            'transition: background 0.2s ease;'
        ).props('id="horizontal-splitter-right" class="splitter"'):
            ui.label('⋮⋮⋮').style('color: #9ca3af; font-size: 8px; transform: rotate(90deg); transition: color 0.2s ease;').classes('splitter-dots')
    
    def _create_right_bottom_pane(self):
        """右下ペイン - システムログ"""
        with ui.element('div').style(
            'width: 100%; height: 50%; '
            'margin: 0; padding: 4px; '
            'box-sizing: border-box; overflow: hidden;'
        ).props('id="right-bottom-pane"'):
            with ui.element('div').style(
                'width: 100%; height: 100%; '
                'background: white; border-radius: 12px; '
                'box-shadow: 0 2px 8px rgba(0,0,0,0.15); '
                'border: 1px solid #e5e7eb; '
                'display: flex; flex-direction: column; '
                'overflow: hidden;'
            ):
                # ヘッダー
                with ui.element('div').style(
                    'background: linear-gradient(135deg, #fa709a 0%, #fee140 100%); '
                    'color: white; padding: 8px 12px; height: 32px; '
                    'display: flex; align-items: center; justify-content: space-between; '
                    'box-sizing: border-box; flex-shrink: 0;'
                ):
                    ui.label('💬 システムログ').style('font-weight: bold; font-size: 14px;')
                    with ui.element('div').style('display: flex; gap: 2px;'):
                        ui.button('🔄', color='white').style('padding: 1px 4px; font-size: 9px; width: 20px; height: 20px; margin: 0; line-height: 1;')
                        ui.button('🗑️', color='white').style('padding: 1px 4px; font-size: 9px; width: 20px; height: 20px; margin: 0; line-height: 1;')
                
                # ログ表示
                with ui.element('div').style(
                    'flex: 1; padding: 8px; overflow: auto; '
                    'font-family: monospace; background: #1f2937; color: #e5e7eb;'
                ):
                    logs = [
                        ('[2024-01-15 15:30:10]', 'INFO:', 'User login successful', '#10b981'),
                        ('[2024-01-15 15:31:11]', 'WARN:', 'Database connection established', '#f59e0b'),
                        ('[2024-01-15 15:32:12]', 'ERROR:', 'Cache miss for key: user_123', '#ef4444'),
                        ('[2024-01-15 15:33:13]', 'DEBUG:', 'API request processed in 245ms', '#6b7280'),
                        ('[2024-01-15 15:34:14]', 'INFO:', 'Memory usage: 75%', '#10b981'),
                        ('[2024-01-15 15:35:15]', 'WARN:', 'Backup completed successfully', '#f59e0b')
                    ]
                    for timestamp, level, message, color in logs:
                        with ui.element('div').style('margin-bottom: 2px; font-size: 10px; line-height: 1.4;'):
                            ui.label(timestamp).style('color: #9ca3af; display: inline; margin-right: 4px;')
                            ui.label(level).style(f'color: {color}; font-weight: bold; display: inline; margin-right: 4px;')
                            ui.label(message).style('color: #e5e7eb; display: inline;')
                
                # フッター
                with ui.element('div').style(
                    'height: 32px; background: #374151; '
                    'border-top: 1px solid #e5e7eb; '
                    'display: flex; align-items: center; '
                    'justify-content: space-between; '
                    'padding: 0 12px; font-size: 11px; '
                    'color: #9ca3af; flex-shrink: 0;'
                ):
                    ui.label('💬 ログ: 6件')
                    ui.label('最新: 15:35')
    
    def _create_user_table_old(self):
        """ユーザーテーブル作成（ヘッダー固定・スクロールバー対応）"""
        # 現在ページのデータ
        start_idx = (self.current_page - 1) * self.rows_per_page
        end_idx = start_idx + self.rows_per_page
        current_page_data = self.users_data[start_idx:end_idx]
        
        # ヘッダー固定テーブルコンテナ（完全オーバーレイ方式）
        with ui.element('div').style(
            'width: 100%; height: 100%; '
            'display: flex; flex-direction: column; '
            'overflow: hidden; position: relative; '
            'margin: 0; padding: 0; box-sizing: border-box;'
        ).props('id="table-container"'):
            
            # ヘッダー（スクロールバー分padding追加）
            with ui.element('div').style(
                'flex-shrink: 0; background: #3b82f6; '
                'color: white; font-weight: bold; '
                'font-size: 11px; border-bottom: 1px solid #e5e7eb; '
                'padding-right: 17px; margin: 0; box-sizing: border-box; '
                'width: 100%; position: relative;'
            ).props('id="table-header"'):
                with ui.element('div').style(
                    'display: grid; '
                    'grid-template-columns: 60px 1fr 2fr 100px 100px 160px; '
                    'gap: 0; padding: 0;'
                ):
                    headers = ['ID', '名前', 'メール', '役割', 'ステータス', '最終ログイン']
                    for i, header in enumerate(headers):
                        # 最後のヘッダー（最終ログイン）は境界線なし
                        border_style = 'border-right: 1px solid rgba(255,255,255,0.2);' if i < len(headers) - 1 else ''
                        with ui.element('div').style(
                            f'padding: 6px 8px; '
                            f'{border_style} '
                            f'text-align: center; '
                            f'background: #3b82f6;'
                        ).classes(f'header-cell header-cell-{i}'):
                            ui.label(header)
            
            # テーブル本体（完全オーバーレイスクロール方式）
            with ui.element('div').style(
                'flex: 1; overflow-y: overlay; overflow-x: hidden; '
                'border: 1px solid #e5e7eb; margin: 0; padding: 0; '
                'scrollbar-width: thin; scrollbar-color: #cbd5e0 #f7fafc; '
                'box-sizing: border-box;'
            ).props(
                'id="table-body" '
                'tabindex="0" '
                'role="region" '
                'aria-label="ユーザーデータテーブル（スクロール可能）"'
            ):
                for row in current_page_data:
                    self._create_table_row_old(row)
    
    def _create_table_row_old(self, row):
        """テーブル行作成"""
        with ui.element('div').style(
            'display: grid; '
            'grid-template-columns: 60px 1fr 2fr 100px 100px 160px; '
            'gap: 0; padding: 0; '
            'border-bottom: 1px solid #f3f4f6; '
            'transition: background 0.2s; '
            'min-height: 28px;'
        ).props('onmouseover="this.style.background=\'#f8f9fa\'" onmouseout="this.style.background=\'white\'"'):
            
            # ID
            with ui.element('div').style(
                'padding: 4px 8px; border-right: 1px solid #f3f4f6; '
                'text-align: center; font-size: 11px; '
                'display: flex; align-items: center; justify-content: center;'
            ):
                ui.label(str(row['id']))
            
            # 名前
            with ui.element('div').style(
                'padding: 4px 8px; border-right: 1px solid #f3f4f6; '
                'font-size: 11px; display: flex; align-items: center;'
            ):
                ui.label(row['name'])
            
            # メール
            with ui.element('div').style(
                'padding: 4px 8px; border-right: 1px solid #f3f4f6; '
                'font-size: 11px; display: flex; align-items: center;'
            ):
                ui.label(row['email'])
            
            # 役割
            with ui.element('div').style(
                'padding: 4px 8px; border-right: 1px solid #f3f4f6; '
                'text-align: center; font-size: 11px; '
                'display: flex; align-items: center; justify-content: center;'
            ):
                role_colors = {'管理者': '#ef4444', 'エディター': '#f59e0b', 'ユーザー': '#6b7280'}
                with ui.element('span').style(
                    f'background: {role_colors.get(row["role"], "#6b7280")}; '
                    f'color: white; padding: 1px 6px; border-radius: 3px; '
                    f'font-size: 9px;'
                ):
                    ui.label(row['role'])
            
            # ステータス
            with ui.element('div').style(
                'padding: 4px 8px; border-right: 1px solid #f3f4f6; '
                'text-align: center; font-size: 11px; '
                'display: flex; align-items: center; justify-content: center;'
            ):
                status_colors = {'アクティブ': '#10b981', '保留': '#f59e0b', '無効': '#ef4444'}
                with ui.element('span').style(
                    f'background: {status_colors.get(row["status"], "#6b7280")}; '
                    f'color: white; padding: 1px 6px; border-radius: 3px; '
                    f'font-size: 9px;'
                ):
                    ui.label(row['status'])
            
            # 最終ログイン
            with ui.element('div').style(
                'padding: 4px 8px; '
                'text-align: center; font-size: 11px; '
                'display: flex; align-items: center; justify-content: center;'
            ):
                ui.label(row['last_login'])
    
    def _create_pagination_old(self):
        """ページネーション作成"""
        with ui.element('div').style(
            'height: 32px; background: #f8f9fa; '
            'border-top: 1px solid #e5e7eb; '
            'display: flex; align-items: center; '
            'justify-content: space-between; '
            'padding: 0 12px; font-size: 11px; '
            'color: #374151; flex-shrink: 0;'
        ).props('id="pagination-container"'):
            with ui.element('div').props('id="pagination-info"'):
                ui.label('1-15 of 20 users')
            
            with ui.element('div').style('display: flex; gap: 4px; align-items: center;').props('id="pagination-buttons"'):
                # 前ページボタン
                ui.button('◀', color='grey').style(
                    'padding: 1px 6px; font-size: 10px; width: 20px; height: 20px;'
                ).props('id="prev-btn" onclick="changePage(-1)"')
                
                # ページ入力・表示エリア新（直接inputタグ使用）
                with ui.element('div').style(
                    'display: flex; align-items: center; gap: 4px; '
                    'height: 20px;'
                ):
                    # 直接inputタグを使用（NiceGUIのui.input()を回避）
                    ui.element('input').style(
                        'width: 40px; height: 20px; font-size: 10px; '
                        'text-align: center; border: 1px solid #d1d5db; '
                        'border-radius: 3px; padding: 1px; '
                        'margin: 0; box-sizing: border-box; '
                        'outline: none; background: white;'
                    ).props(
                        'id="page-input" '
                        'type="text" '
                        'value="1" '
                        'onchange="goToPageFromInput()" '
                        'onkeypress="handlePageInputEnter(event)"'
                    )
                    
                    ui.label('/').style(
                        'font-size: 10px; color: #6b7280; '
                        'line-height: 20px; margin: 0;'
                    )
                    
                    ui.label('2').style(
                        'font-size: 10px; color: #374151; font-weight: bold; '
                        'line-height: 20px; margin: 0;'
                    ).props('id="max-pages"')
                
                # 次ページボタン
                ui.button('▶', color='grey').style(
                    'padding: 1px 6px; font-size: 10px; width: 20px; height: 20px;'
                ).props('id="next-btn" onclick="changePage(1)"')
    
    def _create_sample_users(self):
        """サンプルユーザーデータ作成"""
        return [
            {'id': 1, 'name': '田中太郎', 'email': 'tanaka@example.com', 'role': '管理者', 'status': 'アクティブ', 'last_login': '2024-01-15 14:30'},
            {'id': 2, 'name': '佐藤花子', 'email': 'sato@example.com', 'role': 'ユーザー', 'status': 'アクティブ', 'last_login': '2024-01-15 13:45'},
            {'id': 3, 'name': '鈴木一郎', 'email': 'suzuki@example.com', 'role': 'ユーザー', 'status': '保留', 'last_login': '2024-01-14 16:20'},
            {'id': 4, 'name': '高橋美咲', 'email': 'takahashi@example.com', 'role': 'エディター', 'status': 'アクティブ', 'last_login': '2024-01-15 12:15'},
            {'id': 5, 'name': '山田次郎', 'email': 'yamada@example.com', 'role': 'ユーザー', 'status': '無効', 'last_login': '2024-01-10 09:30'},
            {'id': 6, 'name': '伊藤誠', 'email': 'ito@example.com', 'role': 'ユーザー', 'status': 'アクティブ', 'last_login': '2024-01-15 11:45'},
            {'id': 7, 'name': '渡辺美香', 'email': 'watanabe@example.com', 'role': 'エディター', 'status': 'アクティブ', 'last_login': '2024-01-15 10:30'},
            {'id': 8, 'name': '中村健太', 'email': 'nakamura@example.com', 'role': 'ユーザー', 'status': 'アクティブ', 'last_login': '2024-01-15 15:00'},
            {'id': 9, 'name': '小林さくら', 'email': 'kobayashi@example.com', 'role': 'ユーザー', 'status': '保留', 'last_login': '2024-01-13 14:20'},
            {'id': 10, 'name': '加藤大輔', 'email': 'kato@example.com', 'role': 'ユーザー', 'status': 'アクティブ', 'last_login': '2024-01-15 09:15'},
            {'id': 11, 'name': '吉田優子', 'email': 'yoshida@example.com', 'role': 'エディター', 'status': 'アクティブ', 'last_login': '2024-01-15 13:20'},
            {'id': 12, 'name': '田村秀人', 'email': 'tamura@example.com', 'role': 'ユーザー', 'status': 'アクティブ', 'last_login': '2024-01-15 08:45'},
            {'id': 13, 'name': '松本理恵', 'email': 'matsumoto@example.com', 'role': 'ユーザー', 'status': '無効', 'last_login': '2024-01-12 16:30'},
            {'id': 14, 'name': '橋本直樹', 'email': 'hashimoto@example.com', 'role': 'ユーザー', 'status': 'アクティブ', 'last_login': '2024-01-15 12:00'},
            {'id': 15, 'name': '井上美穂', 'email': 'inoue@example.com', 'role': 'エディター', 'status': 'アクティブ', 'last_login': '2024-01-15 14:15'},
            {'id': 16, 'name': '木村雅彦', 'email': 'kimura@example.com', 'role': 'ユーザー', 'status': 'アクティブ', 'last_login': '2024-01-15 11:30'},
            {'id': 17, 'name': '林真奈美', 'email': 'hayashi@example.com', 'role': 'ユーザー', 'status': '保留', 'last_login': '2024-01-14 10:45'},
            {'id': 18, 'name': '清水浩司', 'email': 'shimizu@example.com', 'role': 'ユーザー', 'status': 'アクティブ', 'last_login': '2024-01-15 15:30'},
            {'id': 19, 'name': '山口恵子', 'email': 'yamaguchi@example.com', 'role': 'エディター', 'status': 'アクティブ', 'last_login': '2024-01-15 13:50'},
            {'id': 20, 'name': '森川太一', 'email': 'morikawa@example.com', 'role': 'ユーザー', 'status': 'アクティブ', 'last_login': '2024-01-15 12:30'}
        ]
    
    def _add_splitter_js(self):
        """スプリッターJavaScript"""
        ui.add_head_html('''
        <style>
        /* スプリッター基本スタイル・ホバー効果 */
        .splitter:hover {
            background: linear-gradient(135deg, #3b82f6, #1d4ed8) !important;
        }
        .splitter:hover .splitter-dots {
            color: white !important;
        }
        .splitter.dragging {
            background: linear-gradient(135deg, #1d4ed8, #1e40af) !important;
        }
        .splitter.dragging .splitter-dots {
            color: white !important;
        }
        </style>
        <script>
        function initSplitters() {
            setTimeout(() => {
                const vSplitter = document.getElementById('vertical-splitter');
                const leftPane = document.getElementById('left-pane');
                const rightPane = document.getElementById('right-pane');
                
                const hSplitterLeft = document.getElementById('horizontal-splitter-left');
                const leftTopPane = document.getElementById('left-top-pane');
                const leftBottomPane = document.getElementById('left-bottom-pane');
                
                const hSplitterRight = document.getElementById('horizontal-splitter-right');
                const rightTopPane = document.getElementById('right-top-pane');
                const rightBottomPane = document.getElementById('right-bottom-pane');
                
                let isDragging = false;
                let currentSplitter = null;
                
                // 縦スプリッター（左右分割）
                if (vSplitter && leftPane && rightPane) {
                    vSplitter.addEventListener('mousedown', (e) => {
                        isDragging = true;
                        currentSplitter = 'vertical';
                        vSplitter.classList.add('dragging');
                        document.body.style.userSelect = 'none';
                        document.body.style.cursor = 'col-resize';
                        e.preventDefault();
                    });
                }
                
                // 横スプリッター（左上下分割）
                if (hSplitterLeft && leftTopPane && leftBottomPane) {
                    hSplitterLeft.addEventListener('mousedown', (e) => {
                        isDragging = true;
                        currentSplitter = 'horizontal-left';
                        hSplitterLeft.classList.add('dragging');
                        document.body.style.userSelect = 'none';
                        document.body.style.cursor = 'row-resize';
                        e.preventDefault();
                    });
                }
                
                // 横スプリッター（右上下分割）
                if (hSplitterRight && rightTopPane && rightBottomPane) {
                    hSplitterRight.addEventListener('mousedown', (e) => {
                        isDragging = true;
                        currentSplitter = 'horizontal-right';
                        hSplitterRight.classList.add('dragging');
                        document.body.style.userSelect = 'none';
                        document.body.style.cursor = 'row-resize';
                        e.preventDefault();
                    });
                }
                
                // マウス移動処理
                document.addEventListener('mousemove', (e) => {
                    if (!isDragging || !currentSplitter) return;
                    
                    if (currentSplitter === 'vertical') {
                        const container = document.getElementById('main-container');
                        const rect = container.getBoundingClientRect();
                        const x = e.clientX - rect.left;
                        const percentage = Math.max(20, Math.min(80, (x / rect.width) * 100));
                        
                        leftPane.style.width = percentage + '%';
                        rightPane.style.width = (100 - percentage) + '%';
                    } else if (currentSplitter === 'horizontal-left') {
                        const leftPaneRect = leftPane.getBoundingClientRect();
                        const y = e.clientY - leftPaneRect.top;
                        const topPercent = Math.max(20, Math.min(80, (y / leftPaneRect.height) * 100));
                        
                        leftTopPane.style.height = topPercent + '%';
                        leftBottomPane.style.height = (100 - topPercent) + '%';
                    } else if (currentSplitter === 'horizontal-right') {
                        const rightPaneRect = rightPane.getBoundingClientRect();
                        const y = e.clientY - rightPaneRect.top;
                        const topPercent = Math.max(20, Math.min(80, (y / rightPaneRect.height) * 100));
                        
                        rightTopPane.style.height = topPercent + '%';
                        rightBottomPane.style.height = (100 - topPercent) + '%';
                    }
                });
                
                // ドラッグ終了
                document.addEventListener('mouseup', () => {
                    if (isDragging) {
                        // ドラッグクラス削除
                        document.querySelectorAll('.splitter').forEach(splitter => {
                            splitter.classList.remove('dragging');
                        });
                        
                        isDragging = false;
                        currentSplitter = null;
                        document.body.style.userSelect = '';
                        document.body.style.cursor = '';
                    }
                });
                
                console.log('All splitters initialized successfully');
            }, 500);
        }
        
        setTimeout(initSplitters, 100);
        </script>
        ''')
    
    def _add_pagination_js(self):
        """ページネーションJavaScript"""
        ui.add_head_html('''
        <script>
        // ページネーション用グローバル変数
        let currentPage = 1;
        let totalPages = 2;
        let rowsPerPage = 15;
        
        // 全データ
        const allUsersData = [
            {'id': 1, 'name': '田中太郎', 'email': 'tanaka@example.com', 'role': '管理者', 'status': 'アクティブ', 'last_login': '2024-01-15 14:30'},
            {'id': 2, 'name': '佐藤花子', 'email': 'sato@example.com', 'role': 'ユーザー', 'status': 'アクティブ', 'last_login': '2024-01-15 13:45'},
            {'id': 3, 'name': '鈴木一郎', 'email': 'suzuki@example.com', 'role': 'ユーザー', 'status': '保留', 'last_login': '2024-01-14 16:20'},
            {'id': 4, 'name': '高橋美咲', 'email': 'takahashi@example.com', 'role': 'エディター', 'status': 'アクティブ', 'last_login': '2024-01-15 12:15'},
            {'id': 5, 'name': '山田次郎', 'email': 'yamada@example.com', 'role': 'ユーザー', 'status': '無効', 'last_login': '2024-01-10 09:30'},
            {'id': 6, 'name': '伊藤誠', 'email': 'ito@example.com', 'role': 'ユーザー', 'status': 'アクティブ', 'last_login': '2024-01-15 11:45'},
            {'id': 7, 'name': '渡辺美香', 'email': 'watanabe@example.com', 'role': 'エディター', 'status': 'アクティブ', 'last_login': '2024-01-15 10:30'},
            {'id': 8, 'name': '中村健太', 'email': 'nakamura@example.com', 'role': 'ユーザー', 'status': 'アクティブ', 'last_login': '2024-01-15 15:00'},
            {'id': 9, 'name': '小林さくら', 'email': 'kobayashi@example.com', 'role': 'ユーザー', 'status': '保留', 'last_login': '2024-01-13 14:20'},
            {'id': 10, 'name': '加藤大輔', 'email': 'kato@example.com', 'role': 'ユーザー', 'status': 'アクティブ', 'last_login': '2024-01-15 09:15'},
            {'id': 11, 'name': '吉田優子', 'email': 'yoshida@example.com', 'role': 'エディター', 'status': 'アクティブ', 'last_login': '2024-01-15 13:20'},
            {'id': 12, 'name': '田村秀人', 'email': 'tamura@example.com', 'role': 'ユーザー', 'status': 'アクティブ', 'last_login': '2024-01-15 08:45'},
            {'id': 13, 'name': '松本理恵', 'email': 'matsumoto@example.com', 'role': 'ユーザー', 'status': '無効', 'last_login': '2024-01-12 16:30'},
            {'id': 14, 'name': '橋本直樹', 'email': 'hashimoto@example.com', 'role': 'ユーザー', 'status': 'アクティブ', 'last_login': '2024-01-15 12:00'},
            {'id': 15, 'name': '井上美穂', 'email': 'inoue@example.com', 'role': 'エディター', 'status': 'アクティブ', 'last_login': '2024-01-15 14:15'},
            {'id': 16, 'name': '木村雅彦', 'email': 'kimura@example.com', 'role': 'ユーザー', 'status': 'アクティブ', 'last_login': '2024-01-15 11:30'},
            {'id': 17, 'name': '林真奈美', 'email': 'hayashi@example.com', 'role': 'ユーザー', 'status': '保留', 'last_login': '2024-01-14 10:45'},
            {'id': 18, 'name': '清水浩司', 'email': 'shimizu@example.com', 'role': 'ユーザー', 'status': 'アクティブ', 'last_login': '2024-01-15 15:30'},
            {'id': 19, 'name': '山口恵子', 'email': 'yamaguchi@example.com', 'role': 'エディター', 'status': 'アクティブ', 'last_login': '2024-01-15 13:50'},
            {'id': 20, 'name': '森川太一', 'email': 'morikawa@example.com', 'role': 'ユーザー', 'status': 'アクティブ', 'last_login': '2024-01-15 12:30'}
        ];
        
        function updateUserTable(data) {
            const tableBody = document.getElementById('table-body');
            if (!tableBody) return;
            
            // テーブル本体をクリア（ヘッダー以外）
            tableBody.innerHTML = '';
            
            data.forEach(row => {
                const rowElement = document.createElement('div');
                rowElement.style.cssText = 'display: grid; grid-template-columns: 60px 1fr 2fr 100px 100px 160px; gap: 0; padding: 0; border-bottom: 1px solid #f3f4f6; transition: background 0.2s; min-height: 28px;';
                rowElement.onmouseover = () => rowElement.style.background = '#f8f9fa';
                rowElement.onmouseout = () => rowElement.style.background = 'white';
                
                // セル作成
                const cells = [
                    { content: row.id, style: 'text-align: center;' },
                    { content: row.name, style: '' },
                    { content: row.email, style: '' },
                    { content: row.role, style: 'text-align: center;', isRole: true },
                    { content: row.status, style: 'text-align: center;', isStatus: true },
                    { content: row.last_login, style: 'text-align: center;' }
                ];
                
                cells.forEach((cell, index) => {
                    const cellDiv = document.createElement('div');
                    cellDiv.style.cssText = `padding: 4px 8px; border-right: 1px solid #f3f4f6; font-size: 11px; display: flex; align-items: center; ${cell.style}`;
                    if (cell.style.includes('center')) {
                        cellDiv.style.justifyContent = 'center';
                    }
                    
                    if (cell.isRole) {
                        const roleColors = {'管理者': '#ef4444', 'エディター': '#f59e0b', 'ユーザー': '#6b7280'};
                        const span = document.createElement('span');
                        span.style.cssText = `background: ${roleColors[cell.content] || '#6b7280'}; color: white; padding: 1px 6px; border-radius: 3px; font-size: 9px;`;
                        span.textContent = cell.content;
                        cellDiv.appendChild(span);
                    } else if (cell.isStatus) {
                        const statusColors = {'アクティブ': '#10b981', '保留': '#f59e0b', '無効': '#ef4444'};
                        const span = document.createElement('span');
                        span.style.cssText = `background: ${statusColors[cell.content] || '#6b7280'}; color: white; padding: 1px 6px; border-radius: 3px; font-size: 9px;`;
                        span.textContent = cell.content;
                        cellDiv.appendChild(span);
                    } else {
                        cellDiv.textContent = cell.content;
                    }
                    
                    rowElement.appendChild(cellDiv);
                });
                
                tableBody.appendChild(rowElement);
            });
        }
        
        function updatePaginationInfo() {
            const startIdx = (currentPage - 1) * rowsPerPage + 1;
            const endIdx = Math.min(currentPage * rowsPerPage, allUsersData.length);
            const infoElement = document.querySelector('#pagination-info label');
            if (infoElement) {
                infoElement.textContent = `${startIdx}-${endIdx} of ${allUsersData.length} users`;
            }
        }
        
        function updatePaginationButtons() {
            // ページ入力フィールド更新
            const pageInput = document.getElementById('page-input');
            if (pageInput) {
                pageInput.value = currentPage;
            }
            
            // 最大ページ数表示更新
            const maxPagesLabel = document.querySelector('#max-pages');
            if (maxPagesLabel) {
                maxPagesLabel.textContent = totalPages;
            }
            
            // 前ページボタン
            const prevBtn = document.getElementById('prev-btn');
            if (prevBtn) {
                if (currentPage === 1) {
                    prevBtn.classList.remove('bg-primary');
                    prevBtn.classList.add('bg-grey-5');
                    prevBtn.style.opacity = '0.5';
                } else {
                    prevBtn.classList.remove('bg-grey-5');
                    prevBtn.classList.add('bg-primary');
                    prevBtn.style.opacity = '1';
                }
            }
            
            // 次ページボタン
            const nextBtn = document.getElementById('next-btn');
            if (nextBtn) {
                if (currentPage === totalPages) {
                    nextBtn.classList.remove('bg-primary');
                    nextBtn.classList.add('bg-grey-5');
                    nextBtn.style.opacity = '0.5';
                } else {
                    nextBtn.classList.remove('bg-grey-5');
                    nextBtn.classList.add('bg-primary');
                    nextBtn.style.opacity = '1';
                }
            }
        }
        
        function changePage(direction) {
            const newPage = currentPage + direction;
            if (newPage >= 1 && newPage <= totalPages) {
                currentPage = newPage;
                const startIdx = (currentPage - 1) * rowsPerPage;
                const endIdx = startIdx + rowsPerPage;
                const pageData = allUsersData.slice(startIdx, endIdx);
                
                updateUserTable(pageData);
                updatePaginationInfo();
                updatePaginationButtons();
                
                console.log(`Changed to page ${currentPage}`);
            }
        }
        
        function goToPage(page) {
            if (page >= 1 && page <= totalPages && page !== currentPage) {
                currentPage = page;
                const startIdx = (currentPage - 1) * rowsPerPage;
                const endIdx = startIdx + rowsPerPage;
                const pageData = allUsersData.slice(startIdx, endIdx);
                
                updateUserTable(pageData);
                updatePaginationInfo();
                updatePaginationButtons();
                
                console.log(`Went to page ${currentPage}`);
            }
        }
        
        // ページ入力からの移動
        function goToPageFromInput() {
            const pageInput = document.getElementById('page-input');
            if (pageInput) {
                const inputPage = parseInt(pageInput.value);
                if (!isNaN(inputPage) && inputPage >= 1 && inputPage <= totalPages) {
                    goToPage(inputPage);
                } else {
                    // 無効な値の場合、現在ページに戻す
                    pageInput.value = currentPage;
                }
            }
        }
        
        // Enter キー押下時の処理
        function handlePageInputEnter(event) {
            if (event.key === 'Enter') {
                goToPageFromInput();
            }
        }
        
        // 初期化
        setTimeout(() => {
            updatePaginationButtons();
            console.log('Pagination initialized');
        }, 500);
        </script>
        
        <style>
        /* スクロール領域のアクセシビリティ対応 */
        [role="region"][aria-label][tabindex]:focus {
            outline: 2px solid #3b82f6;
            outline-offset: 2px;
        }
        
        /* スクロールバーオーバーレイ方式（ヘッダー余白削除） */
        #table-header {
            padding-right: 0 !important;
            box-sizing: border-box !important;
        }
        
        /* テーブルコンテナでスクロールバーオーバーレイを制御 */
        #table-container {
            position: relative;
            overflow: hidden;
        }
        
        #table-body {
            position: relative;
            overflow-y: auto;
            overflow-x: hidden;
            /* スクロールバーのカスタマイズ (Webkit系ブラウザ) */
            scrollbar-width: thin;
            scrollbar-color: #cbd5e0 #f7fafc;
        }
        
        /* Webkit系ブラウザ向けスクロールバースタイリング */
        #table-body::-webkit-scrollbar {
            width: 12px;
            background-color: transparent;
        }
        
        #table-body::-webkit-scrollbar-track {
            background: rgba(247, 250, 252, 0.8);
            border-radius: 6px;
            margin: 2px;
        }
        
        #table-body::-webkit-scrollbar-thumb {
            background: #cbd5e0;
            border-radius: 6px;
            border: 2px solid transparent;
            background-clip: padding-box;
        }
        
        #table-body::-webkit-scrollbar-thumb:hover {
            background: #9ca3af;
        }
        
        #table-body::-webkit-scrollbar-thumb:active {
            background: #6b7280;
        }
        
        /* スクロールバーのオーバーレイ効果を強化 */
        #table-body {
            /* スクロールバーがコンテンツの上に表示されるように設定 */
            scrollbar-gutter: stable;
        }
        
        /* ホバー時のスクロールバー表示強化 */
        #table-body:hover::-webkit-scrollbar {
            opacity: 1;
        }
        
        /* スクロールバーがヘッダーやフッターに重ならないように高さ調整 */
        #table-body {
            margin-top: 0;
            margin-bottom: 0;
        }
        
        /* テーブル行のグリッドレイアウトをヘッダーと完全一致させる */
        #table-body > div {
            display: grid;
            grid-template-columns: 60px 1fr 2fr 100px 100px 160px;
            gap: 0;
            padding: 0;
        }
        
        /* パネルボタンのmargin強制適用 */
        .nicegui-button {
            margin: 0 !important;
        }
        
        /* ドロップダウンアイコンの文字化問題を修正 */
        .q-select .q-field__append {
            display: none !important;
        }
        
        .q-select::after {
            content: '▼';
            position: absolute;
            right: 12px;
            top: 50%;
            transform: translateY(-50%);
            font-size: 12px;
            color: #6b7280;
            pointer-events: none;
        }
        
        .q-select .q-field__control::before {
            display: none !important;
        }
        
        .q-select .q-field__control::after {
            display: none !important;
        }
        </style>
        ''')
    
    # スクロールバーオーバーレイ方式採用：
    # - スクロールバーをテーブルコンテンツの上にオーバーレイ表示
    # - ヘッダーの余白調整が不要（境界位置ズレなし）
    # - スクロールバーの有無に関係なく一定の表示
    # - CSSのみで実現、JavaScript不要
    # - ヘッダーとデータ行の境界位置が完全一致
    
    # ページネーションは直接inputタグ使用でシンプル化済み
    # オーバーレイ方式でスクロールバー位置問題を根本解決