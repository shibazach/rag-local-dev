"""
ファイル管理ページ - 共通コンポーネント活用版
"""
from nicegui import ui
from ui.components.layout import RAGHeader, RAGFooter, MainContentArea
from ui.components.elements import CommonPanel
from ui.components.common.layout import CommonSplitter
from ui.components.common.data_grid import BaseDataGridView
from app.services.file_service import FileService

class FilesPage:
    """ファイル管理ページクラス - 共通コンポーネント活用版"""
    
    def __init__(self):
        self.search_text = ""
        self.status_filter = "全て"
        self.data_grid = None
        self.search_input = None
        self.original_data = []
        
        # サービス初期化
        self.file_service = FileService()
        self.file_data = []
        
        # 実際のDBからファイルデータを取得
        self._load_file_data()
    
    def _load_file_data(self):
        """DBからファイルデータを取得"""
        try:
            # FileServiceを使ってファイル一覧を取得
            result = self.file_service.get_file_list(limit=1000, offset=0)
            
            if result and 'files' in result:
                self.file_data = []
                for file_info in result['files']:
                    # ステータス判定
                    status = '未処理'
                    if file_info.get('has_text', False):
                        if file_info.get('text_length', 0) > 0:
                            status = '処理完了'
                        else:
                            status = '処理中'
                    
                    # アクションボタンHTML（白系背景）
                    actions_html = f'<div style="display: flex; gap: 4px; justify-content: center;"><button onclick="previewFile(\'{file_info["file_id"]}\')" style="background: #f8f9fa; border: 1px solid #e9ecef; border-radius: 4px; padding: 4px 6px; cursor: pointer; font-size: 14px;" title="プレビュー">👁️</button><button onclick="showFileDetails(\'{file_info["file_id"]}\')" style="background: #f8f9fa; border: 1px solid #e9ecef; border-radius: 4px; padding: 4px 6px; cursor: pointer; font-size: 14px;" title="詳細情報">📝</button><button onclick="deleteFile(\'{file_info["file_id"]}\')" style="background: #fff5f5; border: 1px solid #fed7d7; border-radius: 4px; padding: 4px 6px; cursor: pointer; font-size: 14px;" title="削除">🗑️</button></div>'
                    
                    self.file_data.append({
                        'id': file_info['file_id'],
                        'filename': file_info['filename'],
                        'size': f"{file_info['file_size'] // 1024}KB" if file_info['file_size'] else 'N/A',
                        'content_type': file_info['content_type'],
                        'status': status,
                        'created_at': file_info['created_at'][:16].replace('T', ' ') if file_info.get('created_at') else 'N/A',
                        'actions': actions_html
                    })
                
                self.original_data = self.file_data.copy()
                print(f"ファイルデータ読み込み完了: {len(self.file_data)}件")
            else:
                print("ファイルデータが取得できませんでした")
                self.file_data = []
                self.original_data = []
                
        except Exception as e:
            print(f"ファイルデータ読み込みエラー: {e}")
            # エラー時はサンプルデータを使用
            self.file_data = [
                {
                    'id': 'sample-1',
                    'filename': 'サンプルファイル.pdf',
                    'size': '156KB',
                    'content_type': 'application/pdf',
                    'status': '処理完了',
                    'created_at': '2025-01-07 10:00',
                    'actions': '<div style="display: flex; gap: 4px; justify-content: center;"><button onclick="previewFile(\'sample-1\')" style="background: #f8f9fa; border: 1px solid #e9ecef; border-radius: 4px; padding: 4px 6px; cursor: pointer; font-size: 14px;" title="プレビュー">👁️</button><button onclick="showFileDetails(\'sample-1\')" style="background: #f8f9fa; border: 1px solid #e9ecef; border-radius: 4px; padding: 4px 6px; cursor: pointer; font-size: 14px;" title="詳細情報">📝</button><button onclick="deleteFile(\'sample-1\')" style="background: #fff5f5; border: 1px solid #fed7d7; border-radius: 4px; padding: 4px 6px; cursor: pointer; font-size: 14px;" title="削除">🗑️</button></div>'
                }
            ]
            self.original_data = self.file_data.copy()
    
    def render(self):
        """ページレンダリング"""
        from app.utils.auth import SimpleAuth
        
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
        
        # ファイル操作JavaScript追加
        self._add_file_actions_javascript()
    
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
            header_color="#6b7280",
            width="100%",
            height="100%"
        ) as panel:
            
            # ヘッダーにフィルターを追加
            with panel.header_element:
                with ui.element('div').style(
                    'display: flex; gap: 8px; align-items: center; flex: 1; min-width: 0;'
                ):
                    # ステータスフィルター（固定幅・ラベルなし）
                    status_select = ui.select(
                        options=[
                            '全て',
                            '未処理',
                            '処理中', 
                            '未整形',
                            '未ベクトル化',
                            '処理完了',
                            'エラー'
                        ],
                        value='全て'
                    ).style('width: 150px; height: 28px; min-height: 28px; flex-shrink: 0;').props('outlined dense')
                    
                    # 検索テキストボックス（レスポンシブ）
                    self.search_input = ui.input(
                        placeholder='ファイル名で検索...'
                    ).style('flex: 1; min-width: 120px; height: 28px; min-height: 28px;').props('outlined dense')
                    
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
                'field': 'size',
                'label': 'サイズ',
                'width': '80px',
                'align': 'center'
            },
            {
                'field': 'status',
                'label': 'ステータス',
                'width': '100px',
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
                'field': 'created_at',
                'label': '作成日時',
                'width': '130px',
                'align': 'center'
            },
            {
                'field': 'actions',
                'label': '操作',
                'width': '120px',
                'align': 'center',
                'render_type': 'html'
            }
        ]
        
        # データグリッド作成
        self.data_grid = BaseDataGridView(
            columns=columns,
            height='100%',
            auto_rows=True,
            min_rows=10,
            default_rows_per_page=20,
            header_color='#e5e7eb'
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
        if self.status_filter and self.status_filter != '全て':
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
    
    def _add_file_actions_javascript(self):
        """ファイル操作用JavaScript追加"""
        ui.add_head_html('''
        <script>
        // ファイルプレビュー機能（new/系移植版）
        async function previewFile(fileId) {
            try {
                const response = await fetch(`/api/files/${fileId}/preview`);
                
                if (response.ok) {
                    const contentType = response.headers.get('content-type');
                    
                    if (contentType && contentType.includes('application/pdf')) {
                        // PDFプレビュー
                        showPdfModal(fileId);
                    } else {
                        // テキストプレビュー
                        const data = await response.json();
                        if (data.type === 'text') {
                            showTextModal(data.content, data.filename);
                        } else {
                            alert('このファイル形式はプレビューできません');
                        }
                    }
                } else {
                    const errorData = await response.json();
                    alert(`プレビューエラー: ${errorData.detail}`);
                }
            } catch (error) {
                console.error('プレビューエラー:', error);
                alert(`プレビューエラー: ${error.message}`);
            }
        }
        
        // PDFモーダル表示
        function showPdfModal(fileId) {
            const overlay = document.createElement('div');
            overlay.style.cssText = `
                position: fixed; top: 0; left: 0; width: 100%; height: 100%;
                background: rgba(0, 0, 0, 0.8); z-index: 10000;
                display: flex; align-items: center; justify-content: center;
            `;
            
            const modal = document.createElement('div');
            modal.style.cssText = `
                background: white; border-radius: 8px; width: 90%; height: 90%;
                display: flex; flex-direction: column; box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
            `;
            
            modal.innerHTML = `
                <div style="padding: 16px; border-bottom: 1px solid #e5e7eb; display: flex; justify-content: space-between; align-items: center;">
                    <h3 style="margin: 0; font-size: 18px; font-weight: 600;">📄 PDFプレビュー</h3>
                    <button onclick="this.closest('.overlay').remove()" style="background: none; border: none; font-size: 24px; cursor: pointer; color: #6b7280;">&times;</button>
                </div>
                <div style="flex: 1; padding: 0;">
                    <iframe src="/api/files/${fileId}/preview" style="width: 100%; height: 100%; border: none;"></iframe>
                </div>
            `;
            
            overlay.className = 'overlay';
            overlay.appendChild(modal);
            overlay.onclick = (e) => { if (e.target === overlay) overlay.remove(); };
            document.body.appendChild(overlay);
        }
        
        // テキストモーダル表示
        function showTextModal(content, filename) {
            const overlay = document.createElement('div');
            overlay.style.cssText = `
                position: fixed; top: 0; left: 0; width: 100%; height: 100%;
                background: rgba(0, 0, 0, 0.8); z-index: 10000;
                display: flex; align-items: center; justify-content: center;
            `;
            
            const modal = document.createElement('div');
            modal.style.cssText = `
                background: white; border-radius: 8px; width: 80%; height: 80%;
                display: flex; flex-direction: column; box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
            `;
            
            modal.innerHTML = `
                <div style="padding: 16px; border-bottom: 1px solid #e5e7eb; display: flex; justify-content: space-between; align-items: center;">
                    <h3 style="margin: 0; font-size: 18px; font-weight: 600;">📄 ${filename || 'テキストファイル'}</h3>
                    <button onclick="this.closest('.overlay').remove()" style="background: none; border: none; font-size: 24px; cursor: pointer; color: #6b7280;">&times;</button>
                </div>
                <div style="flex: 1; padding: 16px; overflow-y: auto;">
                    <pre style="white-space: pre-wrap; font-family: monospace; font-size: 14px; line-height: 1.4; margin: 0;">${content}</pre>
                </div>
            `;
            
            overlay.className = 'overlay';
            overlay.appendChild(modal);
            overlay.onclick = (e) => { if (e.target === overlay) overlay.remove(); };
            document.body.appendChild(overlay);
        }
        
        // ファイル詳細情報表示
        function showFileDetails(fileId) {
            // TODO: ファイル詳細情報API実装後に追加
            alert(`ファイル詳細情報: ${fileId}`);
        }
        
        // ファイル削除
        async function deleteFile(fileId) {
            if (!confirm('このファイルを削除しますか？')) {
                return;
            }
            
            try {
                // TODO: ファイル削除API実装後に追加
                alert(`ファイル削除: ${fileId}`);
            } catch (error) {
                console.error('削除エラー:', error);
                alert(`削除エラー: ${error.message}`);
            }
        }
        </script>
        ''')