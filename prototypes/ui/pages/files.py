"""
ファイル管理ページ - 共通コンポーネント活用版
"""
from nicegui import ui
from ui.components.layout import RAGHeader, RAGFooter, MainContentArea
from ui.components.elements import CommonPanel
from ui.components.common.layout import CommonSplitter
from ui.components.common.data_grid import BaseDataGridView

class FilesPage:
    """ファイル管理ページクラス - 共通コンポーネント活用版"""
    
    def __init__(self):
        self.search_text = ""
        self.status_filter = "すべてのステータス"
        self.data_grid = None
        self.search_input = None
        self.original_data = []
        
        # サンプルデータ
        self.file_data = [
            {
                'id': 1,
                'filename': 'テストファイル1.pdf',
                'pages': 15,
                'status': '処理完了',
                'actions': '👁️ 表示'
            },
            {
                'id': 2,
                'filename': 'プレゼンテーション資料.pdf',
                'pages': 25,
                'status': '処理中',
                'actions': '👁️ 表示'
            },
            {
                'id': 3,
                'filename': '技術仕様書.pdf',
                'pages': 8,
                'status': '未処理',
                'actions': '👁️ 表示'
            },
            {
                'id': 4,
                'filename': 'ユーザーマニュアル.pdf',
                'pages': 42,
                'status': 'エラー',
                'actions': '👁️ 表示'
            },
            {
                'id': 5,
                'filename': '業務フロー図.pdf',
                'pages': 3,
                'status': '未ベクトル化',
                'actions': '👁️ 表示'
            }
        ]
    
    def render(self):
        """ページレンダリング"""
        from main import SimpleAuth
        
        if not SimpleAuth.is_authenticated():
            ui.navigate.to('/login')
            return
        
        # 共通ヘッダー
        RAGHeader(show_site_name=True, current_page="files")
        
        # 全ページ共通メインコンテンツエリア
        with MainContentArea():
            self._create_main_layout()
        
        # 共通フッター
        RAGFooter()
        
        # CommonSplitter初期化
        CommonSplitter.add_splitter_styles()
        CommonSplitter.add_splitter_javascript()
    
    def _create_main_layout(self):
        """メインレイアウト作成"""
        with ui.element('div').style(
            'width: 100%; height: 100%; '
            'display: flex; margin: 0; padding: 4px; gap: 4px;'
        ).props('id="files-main-container"'):
            
            # 左ペイン：ファイル一覧（50%幅）
            with ui.element('div').style(
                'width: 50%; height: 100%; '
                'display: flex; flex-direction: column; '
                'margin: 0; padding: 0;'
            ).props('id="files-left-pane"'):
                self._create_file_list_pane()
            
            # 縦スプリッター
            CommonSplitter.create_vertical(splitter_id="files-vsplitter", width="4px")
            
            # 右ペイン：PDFプレビュー（50%幅）
            with ui.element('div').style(
                'width: 50%; height: 100%; '
                'display: flex; flex-direction: column; '
                'margin: 0; padding: 0;'
            ).props('id="files-right-pane"'):
                self._create_pdf_preview_pane()
    
    def _create_file_list_pane(self):
        """ファイル一覧ペイン"""
        with CommonPanel(
            title="ファイル一覧",
            gradient="#f8f9fa",
            header_color="#374151",
            width="100%",
            height="100%"
        ) as panel:
            
            # ヘッダーにフィルターを追加
            with panel.header_element:
                with ui.element('div').style(
                    'display: flex; gap: 12px; align-items: center; margin-left: 16px; margin-right: 8px; width: calc(100% - 24px);'
                ):
                    # ステータスフィルター（適度な左寄せ）
                    status_select = ui.select(
                        options=[
                            'すべてのステータス',
                            '未処理',
                            '処理中', 
                            '未整形',
                            '未ベクトル化',
                            '処理完了',
                            'エラー'
                        ],
                        value='すべてのステータス',
                        label='ステータス'
                    ).style('width: 200px; flex-shrink: 0;').props('outlined dense')
                    
                    # 検索テキストボックス（右端まで拡張）
                    self.search_input = ui.input(
                        placeholder='ファイル名で検索...'
                    ).style('flex: 1; min-width: 0;').props('outlined dense')
                    
                    # イベントハンドラー設定
                    status_select.on('update:model-value', lambda e: self._filter_by_status(e.args))
                    self.search_input.on('update:model-value', lambda e: self._filter_by_search(e.args))
            
            # データグリッド配置
            panel.content_element.style('padding: 0; height: 100%;')
            
            with panel.content_element:
                self._setup_data_grid()
    
    def _setup_data_grid(self):
        """データグリッド設定"""
        # カラム定義
        columns = [
            {
                'field': 'filename',
                'label': 'ファイル名',
                'width': '1fr',
                'align': 'left'
            },
            {
                'field': 'pages',
                'label': '頁数',
                'width': '80px',
                'align': 'center'
            },
            {
                'field': 'status',
                'label': 'ステータス',
                'width': '120px',
                'align': 'center',
                'render_type': 'badge',
                'badge_colors': {
                    '処理完了': '#22c55e',
                    '処理中': '#3b82f6',
                    '未処理': '#6b7280',
                    '未整形': '#f59e0b',
                    '未ベクトル化': '#8b5cf6',
                    'エラー': '#ef4444'
                }
            },
            {
                'field': 'actions',
                'label': '操作',
                'width': '100px',
                'align': 'center',
                'render_type': 'button',
                'button_color': 'grey'
            }
        ]
        
        # データグリッド作成
        self.data_grid = BaseDataGridView(
            columns=columns,
            height='100%',
            auto_rows=True,
            min_rows=10,
            default_rows_per_page=20,
            header_color='#2563eb'
        )
        
        # セルクリックイベント設定（操作ボタン用）
        def handle_cell_click(field, row_data):
            if field == 'actions':
                self._preview_file(row_data)
        
        self.data_grid.on_cell_click = handle_cell_click
        
        # データ設定
        self.original_data = self.file_data.copy()
        self.data_grid.set_data(self.file_data)
        
        # レンダリング
        self.data_grid.render()
    
    def _create_pdf_preview_pane(self):
        """PDFプレビューペイン（chatの右下ペインと同構造）"""
        # ヘッダーなしの直接コンテンツ表示
        with ui.element('div').style(
            'width: 100%; height: 100%; '
            'background: white; border-radius: 12px; '
            'box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15); '
            'border: 1px solid #e5e7eb; '
            'display: flex; flex-direction: column; '
            'overflow: hidden;'
        ):
            # PDFビューアエリア
            with ui.element('div').style(
                'height: 100%; background: #f3f4f6; '
                'display: flex; align-items: center; justify-content: center;'
            ):
                with ui.element('div').style('text-align: center; color: #6b7280;'):
                    ui.icon('picture_as_pdf', size='48px').style('margin-bottom: 12px;')
                    ui.label('PDFプレビュー').style('font-size: 16px; font-weight: 500; margin-bottom: 4px;')
                    ui.label('ファイルを選択してプレビューを表示').style('font-size: 12px;')
    
    def _preview_file(self, row_data):
        """ファイルプレビュー"""
        ui.notify(f'{row_data["filename"]} をプレビュー表示します')
    
    def _view_file(self, row_data):
        """ファイル表示"""
        ui.notify(f'{row_data["filename"]} を新しいタブで開きます')
    
    def _filter_by_status(self, status_value):
        """ステータスによるフィルター処理"""
        self.status_filter = status_value
        self._apply_filters()
    
    def _filter_by_search(self, search_value):
        """検索テキストによるフィルター処理"""
        self.search_text = search_value if search_value else ""
        self._apply_filters()
    
    def _apply_filters(self):
        """フィルターを適用してデータグリッドを更新"""
        filtered_data = self.original_data.copy()
        
        # ステータスフィルター
        if self.status_filter and self.status_filter != 'すべてのステータス':
            filtered_data = [
                item for item in filtered_data 
                if item['status'] == self.status_filter
            ]
        
        # 検索テキストフィルター
        if self.search_text and self.search_text.strip():
            search_lower = self.search_text.strip().lower()
            filtered_data = [
                item for item in filtered_data
                if search_lower in item['filename'].lower()
            ]
        
        # データグリッドを更新
        if self.data_grid:
            self.data_grid.update_data(filtered_data)
            ui.notify(f'フィルター適用: {len(filtered_data)}件表示')