"""
データ登録ページ - 3ペイン構成（2:3:5）+ 共通コンポーネント実装
"""
from nicegui import ui
from app.ui.components.layout import RAGHeader, RAGFooter, MainContentArea
from app.ui.components.elements import CommonPanel
from app.ui.components.common.layout import CommonSplitter
from app.ui.components.base.button import BaseButton
from app.ui.components.pdf_viewer import PDFViewer
from app.core.db_simple import get_file_list
from app.services.file_service import get_file_service
import logging

logger = logging.getLogger(__name__)

class DataRegistrationPage:
    """データ登録ページクラス - 3ペイン構成（2:3:5）+ 共通コンポーネント"""
    
    def __init__(self):
        """初期化"""
        self.selected_files = set()
        self.all_files = []
        self.filtered_files = []
        self.file_data = []  # files.pyと同じ
        self.original_data = []  # files.pyと同じ
        self.current_status_filter = ""
        self.current_search_term = ""
        self.data_grid = None
        self.pdf_viewer = None
        self.file_service = get_file_service()
        
    def render(self):
        """ページレンダリング"""
        from app.utils.auth import SimpleAuth
        
        if not SimpleAuth.is_authenticated():
            ui.navigate.to('/login')
            return
        
        # 共通ヘッダー
        RAGHeader(show_site_name=True, current_page="data-registration")
        
        # 全ページ共通メインコンテンツエリア
        with MainContentArea():
            self._create_main_layout()
        
        # 共通フッター
        RAGFooter()
    
    def _create_main_layout(self):
        """3ペイン構成（3:3:4）メインレイアウト + 共通スプリッター"""
        with ui.element('div').style(
            'width: 100%; height: 100%; '
            'display: flex; margin: 0; padding: 4px; gap: 4px;'
        ).props('id="data-reg-container"'):
            
            # 左ペイン: 処理設定（3fr）
            with ui.element('div').style('width: 30%; height: 100%;'):
                self._create_settings_pane()
            
            # 左スプリッター
            CommonSplitter.create_vertical(splitter_id="data-reg-splitter-1", width="4px")
            
            # 中央ペイン: 処理ログ（3fr）
            with ui.element('div').style('width: 30%; height: 100%;'):
                self._create_log_pane()
            
            # 右スプリッター
            CommonSplitter.create_vertical(splitter_id="data-reg-splitter-2", width="4px")
            
            # 右ペイン: ファイル選択とPDFプレビュー（4fr）
            with ui.element('div').style('width: 40%; height: 100%; display: flex; flex-direction: column; gap: 4px;'):
                # 上部: ファイル選択（60%）
                with ui.element('div').style('height: 60%;'):
                    self._create_file_selection_pane()
                
                # 水平スプリッター
                CommonSplitter.create_horizontal(splitter_id="data-reg-h-splitter", height="4px")
                
                # 下部: PDFプレビュー（40%）
                with ui.element('div').style('height: 40%;'):
                    self._create_pdf_preview_pane()
    
    def _create_settings_pane(self):
        """左ペイン: 処理設定（2fr）"""
        with CommonPanel(
            title="📋 処理設定",
            gradient="#334155",
            header_color="white",
            width="100%",
            height="100%"
        ) as panel:
            
            # ヘッダーにボタン配置
            with panel.header_element:
                with ui.element('div').style(
                    'display: flex; gap: 6px; margin-right: 8px;'
                ):
                    # 処理開始ボタン
                    self.start_btn = BaseButton.create_type_a(
                        "🚀 処理開始",
                        on_click=self._start_processing
                    )
                    
                    # 停止ボタン（初期非表示）
                    self.stop_btn = BaseButton.create_type_b(
                        "⏹️ 停止",
                        on_click=self._stop_processing
                    )
                    self.stop_btn.style('display: none;')
            
            # パネル内容
            panel.content_element.style('padding: 0; height: 100%;')
            
            with panel.content_element:
                with ui.element('div').style('padding: 4px; height: 100%; box-sizing: border-box; display: flex; flex-direction: column;'):
                    with ui.element('div').style('display: flex; flex-direction: column; gap: 12px; height: 100%;'):
                        
                        # 整形プロセスと使用モデル
                        with ui.element('div').style('display: flex; flex-direction: column; gap: 8px;'):
                            # 整形プロセス
                            with ui.element('div').style('display: flex; align-items: center; gap: 8px;'):
                                ui.label('整形プロセス').style('min-width: 80px; font-weight: 500; font-size: 13px;')
                                self.process_select = ui.select(
                                    options=['デフォルト (OCR + LLM整形)', 'マルチモーダル'],
                                    value='デフォルト (OCR + LLM整形)',
                                    on_change=self._on_process_change
                                ).style('flex: 1;').props('outlined dense')
                            
                            # 使用モデル表示
                            with ui.element('div').style('background: #f3f4f6; padding: 6px; border-radius: 4px;'):
                                with ui.element('div').style('display: flex; align-items: center; gap: 8px;'):
                                    ui.label('使用モデル:').style('font-weight: 600; font-size: 12px;')
                                    self.current_model_label = ui.label('Phi4-mini (CPU)').style('color: #6b7280; font-size: 12px;')
                        
                        # 埋め込みモデル
                        with ui.element('div').style('display: flex; flex-direction: column; gap: 6px;'):
                            ui.label('埋め込みモデル').style('font-weight: 500; font-size: 13px;')
                            with ui.element('div').style('display: flex; flex-direction: column; gap: 4px;'):
                                self.embedding_model_1 = ui.checkbox(
                                    'intfloat: all-MiniLM-L6-v2',
                                    value=True,
                                    on_change=self._update_process_button
                                ).style('font-size: 12px;')
                                self.embedding_model_2 = ui.checkbox(
                                    'nomic: nomic-embed-text-v1',
                                    value=False,
                                    on_change=self._update_process_button
                                ).style('font-size: 12px;')
                        
                        # 既存データ上書き
                        with ui.element('div').style('display: flex; align-items: center; gap: 8px;'):
                            ui.label('既存データ上書き').style('min-width: 120px; font-weight: 500; font-size: 13px;')
                            self.overwrite_checkbox = ui.checkbox(
                                '',
                                value=True
                            ).style('font-size: 12px;')
                        
                        # 品質しきい値
                        with ui.element('div').style('display: flex; align-items: center; gap: 8px;'):
                            ui.label('品質しきい値').style('min-width: 120px; font-weight: 500; font-size: 13px;')
                            self.quality_threshold = ui.number(
                                value=0.0,
                                min=0,
                                max=1,
                                step=0.1
                            ).style('width: 80px;').props('outlined dense')
                        
                        # LLMタイムアウト
                        with ui.element('div').style('display: flex; align-items: center; gap: 8px;'):
                            ui.label('LLMタイムアウト (秒)').style('min-width: 120px; font-weight: 500; font-size: 13px;')
                            self.llm_timeout = ui.number(
                                value=300,
                                min=30,
                                max=3600,
                                step=30
                            ).style('width: 80px;').props('outlined dense')
                        
                        # 区切り線
                        ui.element('div').style('border-top: 1px solid #e5e7eb; margin: 12px 0 8px 0;')
                        
                        # 自動スクロール設定
                        with ui.element('div').style('display: flex; align-items: center; gap: 8px;'):
                            ui.label('自動スクロール').style('min-width: 120px; font-weight: 500; font-size: 13px;')
                            self.auto_scroll_toggle = ui.checkbox(
                                '',
                                value=True,
                                on_change=self._toggle_auto_scroll
                            ).style('font-size: 12px;')
    
    def _create_log_pane(self):
        """中央ペイン: 処理ログ（3fr）"""
        with CommonPanel(
            title="📋 処理ログ",
            gradient="#334155",
            header_color="white",
            width="100%",
            height="100%"
        ) as panel:
            
            # ヘッダーにCSV出力ボタンのみ配置
            with panel.header_element:
                with ui.element('div').style(
                    'display: flex; gap: 6px; margin-right: 8px;'
                ):
                    # CSV出力ボタン
                    export_btn = BaseButton.create_type_a(
                        "📄 CSV出力",
                        on_click=self._export_csv
                    )
            
            # パネル内容
            panel.content_element.style('padding: 0; height: 100%;')
            
            with panel.content_element:
                with ui.element('div').style('padding: 4px; height: 100%; box-sizing: border-box; display: flex; flex-direction: column;'):
                    # 進捗表示エリア
                    self.progress_display = ui.element('div').style(
                        'background: #e3f2fd; border: 2px solid #2196f3; '
                        'border-radius: 6px; padding: 12px 16px; margin-bottom: 12px; '
                        'font-weight: bold; color: #1565c0; display: none;'
                    )
                    
                    with self.progress_display:
                        with ui.element('div').style('display: flex; justify-content: space-between; align-items: center;'):
                            self.progress_status = ui.label('待機中...').style('font-size: 14px;')
                            self.progress_elapsed = ui.label('処理時間: 0秒').style('color: #1976d2; font-weight: bold;')
                    
                    # ログコンテナ
                    self.log_container = ui.element('div').style(
                        'flex: 1; overflow-y: auto; '
                        'background: white; border: 1px solid #e5e7eb; border-radius: 4px; padding: 8px;'
                    )
                    
                    with self.log_container:
                        # 初期ログメッセージ
                        with ui.element('div').style('text-align: center; color: #9ca3af; padding: 20px;'):
                            ui.label('処理ログがここに表示されます').style('font-size: 14px;')
    
    def _create_pdf_preview_pane(self):
        """PDFプレビューペイン"""
        with CommonPanel(
            title="📄 PDFプレビュー",
            gradient="#334155",
            header_color="white",
            width="100%",
            height="100%",
            content_padding="0"
        ) as panel:
            # PDFビューアを配置
            self.pdf_viewer = PDFViewer(panel.content_element, height="100%", width="100%")
    
    def _create_file_selection_pane(self):
        """右ペイン: ファイル選択（5fr）- new/系準拠チェックボックス付き"""
        with CommonPanel(
            title="📁 ファイル選択",
            gradient="#334155",
            header_color="white",
            width="100%",
            height="100%",
            content_padding="0"  # paddingゼロに
        ) as panel:
            
            # ヘッダーにフィルター・検索・選択数表示
            with panel.header_element:
                with ui.element('div').style(
                    'display: flex; align-items: center; gap: 8px; flex: 1; min-width: 0;'
                ):
                    # ステータスフィルター（files.pyと同じ）
                    self.status_filter = ui.select(
                        options=[
                            '全て',
                            '処理完了',
                            '処理中', 
                            '未処理',
                            '未整形',
                            '未ベクトル化',
                            'エラー'
                        ],
                        value='全て',
                        on_change=self._filter_files
                    ).style(
                        'width: 120px; flex-shrink: 0; '
                        'background-color: white; color: black; '
                        'border-radius: 0;'
                    ).props('outlined dense square').classes('q-ma-none')
                    
                    # ファイル名検索（files.pyと同じ）
                    self.search_input = ui.input(
                        placeholder='ファイル名で検索...',
                        on_change=self._filter_files
                    ).style(
                        'flex: 1; min-width: 120px; '
                        'background-color: white; color: black; '
                        'border-radius: 0;'
                    ).props('outlined dense bg-white square').classes('q-ma-none')
                    
                    # 選択数表示
                    with ui.element('div').style(
                        'padding: 0; white-space: nowrap; flex-shrink: 0; display: flex; align-items: center;'
                    ):
                        ui.label('選択: ').style('color: white; font-size: 14px; font-weight: 500;')
                        self.selected_count_label = ui.label('0').style('color: white; font-size: 14px; font-weight: bold;')
                        ui.label('件').style('color: white; font-size: 14px; font-weight: 500;')
            
            # パネル内容
            panel.content_element.style('padding: 0; height: 100%;')
            
            with panel.content_element:
                self._setup_file_data_grid()
    
    def _setup_file_data_grid(self):
        """ファイル選択用ui.table設定"""
        # カラム定義（files.pyと同じ、ただしチェックボックス付き）
        columns = [
            {'name': 'filename', 'label': 'ファイル名', 'field': 'filename', 'sortable': True, 'align': 'left'},
            {'name': 'size', 'label': 'サイズ', 'field': 'size', 'sortable': True, 'align': 'right'},
            {'name': 'status', 'label': 'ステータス', 'field': 'status', 'sortable': True, 'align': 'center'},
            {'name': 'created_at', 'label': '作成日時', 'field': 'created_at', 'sortable': True, 'align': 'center'}
        ]
        
        # ui.table作成（files.pyと同じ仕様、チェックボックス付き）
        self.data_grid = ui.table(
            columns=columns,
            rows=[],  # 初期は空
            row_key='id',  # files.pyと同じ
            pagination=20,  # files.pyと同じ
            selection='multiple'  # 複数選択可能（チェックボックス機能）
        ).classes('w-full').style(
            'height: 100%; margin: 0;'
        ).props('dense flat virtual-scroll :virtual-scroll-sticky-size-start="48"')  # files.pyと同じ
        
        # 選択変更イベント
        self.data_grid.on('selection', self._handle_selection_change)
        
        # 行ダブルクリックイベント（PDFプレビュー）
        self.data_grid.on('row-dblclick', self._handle_row_double_click)
        
        # ファイルデータをロード
        self._load_file_data()
        
        # ui.tableでは選択機能が組み込まれているため、カスタムチェックボックスは不要
    
    def _add_header_checkbox(self):
        """ヘッダーに全選択チェックボックスを追加"""
        # ここではJavaScriptで実装（将来的にはBaseDataGridViewの機能拡張）
        ui.run_javascript('''
            // ヘッダーの最初のセルにチェックボックスを追加
            setTimeout(() => {
                const headerCell = document.querySelector('.base-data-grid th:first-child');
                if (headerCell && !headerCell.querySelector('input[type="checkbox"]')) {
                    headerCell.innerHTML = '<input type="checkbox" id="header-checkbox-data-reg" title="全選択/解除">';
                    
                    const headerCheckbox = document.getElementById('header-checkbox-data-reg');
                    if (headerCheckbox) {
                        headerCheckbox.addEventListener('change', () => {
                            // Pythonのメソッドを呼び出し
                            window.pyodide?.runPython(`
                                if hasattr(window, 'data_reg_page'):
                                    window.data_reg_page._toggle_all_files(${headerCheckbox.checked})
                            `);
                        });
                    }
                }
            }, 100);
        ''')
    
    def _load_file_data(self):
        """ファイルデータをロード - files.pyと同じ実装"""
        logger = logging.getLogger(__name__)
        try:
            # シンプルなDB接続でファイルリストを取得
            result = get_file_list(limit=1000, offset=0)
            if result and 'files' in result:
                self.file_data = []
                
                for file in result['files']:
                    # ステータス判定（files.pyと同じロジック）
                    if file.get('has_text', False):
                        if file.get('text_length', 0) > 0:
                            status = '処理完了'
                        else:
                            status = '処理中'
                    else:
                        status = '未処理'
                    
                    self.file_data.append({
                        'id': file['file_id'],  # ui.tableのrow-key用
                        'file_id': file['file_id'],  # 実際のファイルID
                        'filename': file['filename'],
                        'size': self._format_file_size(file.get('file_size', 0)),
                        'status': status,
                        'created_at': file.get('created_at').strftime('%Y-%m-%d %H:%M') if file.get('created_at') and hasattr(file.get('created_at'), 'strftime') else str(file.get('created_at', '')),
                        'raw_data': file  # 元のデータを保持
                    })
                
                logger.info(f"Loaded {len(self.file_data)} files")
                
                # 元データを保持（フィルタリング用）
                self.original_data = self.file_data.copy()
                self.all_files = self.file_data.copy()
                self.filtered_files = self.file_data.copy()
                
                # 各行にIDを追加（既に追加済みだが念のため）
                for idx, row in enumerate(self.file_data):
                    row['id'] = idx
                
                # ui.tableを更新
                self.data_grid.rows[:] = self.file_data
                self.data_grid.update()
                
                # デバッグ：最初の3行のデータ構造を確認  
                logger.info("=== Table data structure debug (data_registration) ===")
                for i, row in enumerate(self.file_data[:3]):
                    logger.info(f"Row {i}: {row}")
                    logger.info(f"Row {i} keys: {list(row.keys())}")
            else:
                logger.warning("No files data received from database")
                self.file_data = []
                self.original_data = []
                self.all_files = []
                self.filtered_files = []
        except Exception as e:
            logger.error(f"Error loading file data: {e}")
            self.file_data = []
            self.original_data = []
            self.all_files = []
            self.filtered_files = []
            ui.notify(f'ファイルデータの読み込みに失敗しました: {str(e)}', type='negative')
    
    # イベントハンドラー
    def _start_processing(self):
        """処理開始"""
        selected_count = len(self.selected_files)
        if selected_count == 0:
            ui.notify('ファイルを選択してください', type='warning')
            return
        
        # 埋め込みモデルチェック
        if not (self.embedding_model_1.value or self.embedding_model_2.value):
            ui.notify('埋め込みモデルを選択してください', type='warning')
            return
        
        # UI状態変更
        self.start_btn.style('display: none;')
        self.stop_btn.style('display: inline-flex;')
        self.progress_display.style('display: block;')
        
        ui.notify(f'{selected_count}ファイルの処理を開始します')
        self._add_log_entry('INFO', f'処理開始: {selected_count}ファイル選択済み')
    
    def _stop_processing(self):
        """処理停止"""
        self.start_btn.style('display: inline-flex;')
        self.stop_btn.style('display: none;')
        self.progress_display.style('display: none;')
        
        ui.notify('処理を停止しました')
        self._add_log_entry('WARNING', '処理が停止されました')
    
    def _on_process_change(self, e):
        """整形プロセス変更時"""
        if e.value == 'マルチモーダル':
            self.current_model_label.text = 'Qwen-VL 7B (GPU)'
        else:
            self.current_model_label.text = 'Phi4-mini (CPU)'
    
    def _update_process_button(self, e=None):
        """処理ボタンの有効/無効を更新"""
        selected_count = len(self.selected_files)
        has_model = self.embedding_model_1.value or self.embedding_model_2.value
        
        self.start_btn.props(f'disable={not (selected_count > 0 and has_model)}')
    
    def _toggle_auto_scroll(self, e):
        """自動スクロール切り替え"""
        ui.notify(f'自動スクロール: {"有効" if e.value else "無効"}')
    
    def _export_csv(self):
        """CSV出力"""
        ui.notify('処理ログをCSV出力します')
    
    def _filter_files(self, e=None):
        """フィルタを適用 - files.pyと同じロジック"""
        status_filter = self.status_filter.value if hasattr(self, 'status_filter') else ''
        search_query = self.search_input.value.lower() if hasattr(self, 'search_input') else ''
        
        filtered_data = []
        for row in self.original_data:
            # ステータスフィルタ
            if status_filter != '全て' and row['status'] != status_filter:
                continue
            
            # 検索フィルタ
            if search_query and search_query not in row['filename'].lower():
                continue
            
            filtered_data.append(row)
        
        # 各行のIDを再設定
        for idx, row in enumerate(filtered_data):
            row['id'] = idx
        
        self.filtered_files = filtered_data
        # ui.tableの行データを更新（NiceGUIの標準的な方法）
        if self.data_grid:
            self.data_grid.rows[:] = filtered_data
            self.data_grid.update()
        
        self._update_selection_count()
    
    def _format_file_size(self, size):
        """ファイルサイズをフォーマット - files.pyと同じロジック"""
        if size < 1024:
            return f"{size}B"
        elif size < 1024 * 1024:
            return f"{size / 1024:.1f}KB"  
        elif size < 1024 * 1024 * 1024:
            return f"{size / 1024 / 1024:.1f}MB"
        else:
            return f"{size / 1024 / 1024 / 1024:.1f}GB"
    
    def _handle_selection_change(self, e):
        """ui.tableの選択変更処理"""
        # 選択された行のfile_idを取得
        self.selected_files.clear()
        if e.args:
            # e.argsは選択された行のリスト
            selected_rows = e.args
            if isinstance(selected_rows, list):
                for row in selected_rows:
                    # rowが辞書型かチェック
                    if isinstance(row, dict):
                        file_id = row.get('file_id')
                        if file_id:
                            self.selected_files.add(file_id)
        
        self._update_selection_count()
        self._update_process_button()
    
    def _toggle_all_files(self, checked):
        """全選択/解除"""
        if checked:
            # 全選択
            for file_data in self.filtered_files:
                self.selected_files.add(file_data['file_id'])
                file_data['selected'] = True
        else:
            # 全解除
            for file_data in self.filtered_files:
                self.selected_files.discard(file_data['file_id'])
                file_data['selected'] = False
        
        # データグリッド更新
        if self.data_grid:
            self.data_grid.update_data(self.filtered_files)
        
        self._update_selection_count()
        self._update_process_button()
    
    async def _handle_row_double_click(self, e):
        """行ダブルクリック時の処理 - PDFプレビュー"""
        if e.args:
            # e.argsの構造をログに出力してデバッグ
            logger.info(f"Double click event args: {e.args}")
            
            # 最初の引数が行データ
            if len(e.args) > 0:
                row_data = e.args[0]
                logger.info(f"Row data type: {type(row_data)}")
                logger.info(f"Row data keys: {row_data.keys() if isinstance(row_data, dict) else 'Not a dict'}")
                logger.info(f"Row data: {row_data}")
                
                if isinstance(row_data, dict):
                    file_id = row_data.get('file_id')
                    filename = row_data.get('filename')
                    
                    logger.info(f"Extracted file_id: {file_id}, filename: {filename}")
                    
                    if file_id:
                        try:
                            # ファイル情報を取得してblobデータで判定
                            file_info = self.file_service.get_file_info(file_id)
                            if file_info:
                                blob_data = file_info.get('blob_data')
                                
                                # blobデータの内容でPDF判定
                                is_pdf = self.file_service.is_pdf_by_content(blob_data)
                                
                                logger.info(f"File: {filename}, ID: {file_id}, is_pdf_by_content: {is_pdf}")
                                
                                if is_pdf:
                                    if self.pdf_viewer:
                                        logger.info(f"Loading PDF preview for file: {filename} (ID: {file_id})")
                                        await self.pdf_viewer.load_pdf(file_id, self.file_service)
                                    else:
                                        logger.warning(f"PDF viewer not initialized")
                                        ui.notify("PDFプレビューの初期化に失敗しました", type='error')
                                else:
                                    ui.notify(f"このファイルはPDFではありません: {filename}", type='warning')
                            else:
                                ui.notify(f"ファイル情報を取得できませんでした", type='error')
                        except Exception as ex:
                            logger.error(f"Error checking PDF: {ex}")
                            ui.notify(f"エラーが発生しました: {str(ex)}", type='error')
                    else:
                        ui.notify("ファイルIDが見つかりません", type='error')
    
    def _update_selection_count(self):
        """選択数表示更新"""
        count = len(self.selected_files)
        if hasattr(self, 'selected_count_label'):
            self.selected_count_label.text = str(count)
    
    def _add_log_entry(self, level, message):
        """ログエントリ追加"""
        import datetime
        
        timestamp = datetime.datetime.now().strftime('%H:%M:%S')
        log_style = {
            'INFO': 'color: #2563eb;',
            'SUCCESS': 'color: #16a34a;',
            'WARNING': 'color: #d97706;',
            'ERROR': 'color: #dc2626;'
        }.get(level, 'color: #6b7280;')
        
        with self.log_container:
            with ui.element('div').style('margin-bottom: 4px; font-size: 12px;'):
                ui.label(f'[{timestamp}]').style('color: #9ca3af; margin-right: 8px;')
                ui.label(level).style(f'{log_style} font-weight: bold; margin-right: 8px;')
                ui.label(message).style('color: #374151;')