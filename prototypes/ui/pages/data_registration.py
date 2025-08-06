"""
データ登録ページ - 3ペイン構成（2:3:5）+ 共通コンポーネント実装
"""
from nicegui import ui
from ui.components.layout import RAGHeader, RAGFooter, MainContentArea
from ui.components.elements import CommonPanel
from ui.components.common.layout import CommonSplitter
from ui.components.base.button import BaseButton
from ui.components.common.data_grid import BaseDataGridView

class DataRegistrationPage:
    """データ登録ページクラス - 3ペイン構成（2:3:5）+ 共通コンポーネント"""
    
    def __init__(self):
        """初期化"""
        self.selected_files = set()
        self.all_files = []
        self.filtered_files = []
        self.current_status_filter = ""
        self.current_search_term = ""
        self.data_grid = None
        
    def render(self):
        """ページレンダリング"""
        from main import SimpleAuth
        
        if not SimpleAuth.is_authenticated():
            ui.navigate.to('/login')
            return
        
        # 共通ヘッダー
        RAGHeader(show_site_name=True, current_page="data-registration")
        
        # 全ページ共通メインコンテンツエリア
        with MainContentArea():
            # 共通スプリッタースタイル・JS追加
            CommonSplitter.add_splitter_styles()
            CommonSplitter.add_splitter_javascript()
            
            self._create_main_layout()
        
        # 共通フッター
        RAGFooter()
    
    def _create_main_layout(self):
        """3ペイン構成（2:3:5）メインレイアウト"""
        with ui.element('div').style(
            'width: 100%; height: 100%; '
            'display: grid; '
            'grid-template-columns: 2fr 3fr 5fr; '
            'gap: 4px; margin: 0; padding: 4px;'
        ).props('id="data-reg-container"'):
            
            # 左ペイン: 処理設定（2fr）
            self._create_settings_pane()
            
            # 中央ペイン: 処理ログ（3fr）
            self._create_log_pane()
            
            # 右ペイン: ファイル選択（5fr）
            self._create_file_selection_pane()
    
    def _create_settings_pane(self):
        """左ペイン: 処理設定（2fr）"""
        with CommonPanel(
            title="📋 処理設定",
            gradient="#f8f9fa",
            header_color="#374151",
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
                with ui.element('div').style('padding: 4px; height: 100%; box-sizing: border-box;'):
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
                                    self.current_model_label = ui.label('自動判定中...').style('color: #6b7280; font-size: 12px;')
                        
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
                        
                        # 設定オプション（横並び）
                        with ui.element('div').style('display: flex; align-items: center; gap: 16px;'):
                            # 既存データ上書き
                            self.overwrite_checkbox = ui.checkbox(
                                '既存データを上書き',
                                value=True
                            ).style('font-size: 12px;')
                            
                            # 品質しきい値
                            with ui.element('div').style('display: flex; align-items: center; gap: 6px;'):
                                ui.label('品質しきい値').style('font-weight: 500; font-size: 12px;')
                                self.quality_threshold = ui.number(
                                    value=0.0,
                                    min=0,
                                    max=1,
                                    step=0.1
                                ).style('width: 70px;').props('outlined dense')
                        
                        # LLMタイムアウト
                        with ui.element('div').style('display: flex; align-items: center; gap: 8px;'):
                            ui.label('LLMタイムアウト (秒)').style('min-width: 120px; font-weight: 500; font-size: 13px;')
                            self.llm_timeout = ui.number(
                                value=300,
                                min=30,
                                max=3600,
                                step=30
                            ).style('width: 80px;').props('outlined dense')
    
    def _create_log_pane(self):
        """中央ペイン: 処理ログ（3fr）"""
        with CommonPanel(
            title="📋 処理ログ",
            gradient="#f8f9fa",
            header_color="#374151",
            width="100%",
            height="100%"
        ) as panel:
            
            # ヘッダーにコントロール配置
            with panel.header_element:
                with ui.element('div').style(
                    'display: flex; gap: 12px; align-items: center; margin-right: 8px;'
                ):
                    # 自動スクロールトグル
                    with ui.element('div').style('display: flex; align-items: center; gap: 6px;'):
                        self.auto_scroll_toggle = ui.checkbox(
                            '自動スクロール',
                            value=True,
                            on_change=self._toggle_auto_scroll
                        ).style('color: white; font-size: 12px;')
                    
                    # CSV出力ボタン
                    export_btn = BaseButton.create_type_b(
                        "📄 CSV出力",
                        on_click=self._export_csv
                    )
            
            # パネル内容
            panel.content_element.style('padding: 0; height: 100%;')
            
            with panel.content_element:
                with ui.element('div').style('padding: 4px; height: 100%; box-sizing: border-box;'):
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
                        'height: calc(100% - 60px); overflow-y: auto; '
                        'background: white; border: 1px solid #e5e7eb; border-radius: 4px; padding: 8px;'
                    )
                    
                    with self.log_container:
                        # 初期ログメッセージ
                        with ui.element('div').style('text-align: center; color: #9ca3af; padding: 20px;'):
                            ui.label('処理ログがここに表示されます').style('font-size: 14px;')
    
    def _create_file_selection_pane(self):
        """右ペイン: ファイル選択（5fr）- new/系準拠チェックボックス付き"""
        with CommonPanel(
            title="📁 ファイル選択",
            gradient="#f8f9fa",
            header_color="#374151",
            width="100%",
            height="100%"
        ) as panel:
            
            # ヘッダーにフィルター・検索・選択数表示
            with panel.header_element:
                with ui.element('div').style(
                    'display: flex; align-items: center; gap: 8px; margin-right: 8px; flex: 1;'
                ):
                    # ステータスフィルター
                    self.status_filter = ui.select(
                        options=['すべてのステータス', '未処理', '処理中', '未整形', '未ベクトル化', '処理完了', 'エラー'],
                        value='すべてのステータス',
                        on_change=self._filter_files
                    ).style('width: 160px; flex-shrink: 0;').props('outlined dense')
                    
                    # ファイル名検索
                    self.search_input = ui.input(
                        placeholder='ファイル名で検索...',
                        on_change=self._filter_files
                    ).style('flex: 1; min-width: 0;').props('outlined dense')
                    
                    # 選択数表示
                    with ui.element('div').style(
                        'background: rgba(37, 99, 235, 0.1); padding: 4px 8px; '
                        'border-radius: 4px; white-space: nowrap;'
                    ):
                        ui.label('選択: ').style('color: white; font-size: 12px; font-weight: 500;')
                        self.selected_count_label = ui.label('0').style('color: white; font-size: 12px; font-weight: bold;')
                        ui.label('件').style('color: white; font-size: 12px; font-weight: 500;')
            
            # パネル内容
            panel.content_element.style('padding: 0; height: 100%;')
            
            with panel.content_element:
                self._setup_file_data_grid()
    
    def _setup_file_data_grid(self):
        """ファイル選択用データグリッド設定"""
        # カラム定義（チェックボックス付き）
        columns = [
            {
                'field': 'selected',
                'label': '',  # ヘッダーチェックボックスは別途追加
                'width': '40px',
                'align': 'center',
                'render_type': 'checkbox'
            },
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
                'align': 'center'
            },
            {
                'field': 'size',
                'label': 'サイズ',
                'width': '100px',
                'align': 'right'
            }
        ]
        
        self.data_grid = BaseDataGridView(
            columns=columns,
            height='100%',
            auto_rows=True,
            min_rows=10,
            default_rows_per_page=100,
            header_color='#2563eb'
        )
        
        # データグリッドのチェックボックスイベント
        self.data_grid.on_cell_click = self._handle_checkbox_click
        
        # サンプルデータ設定
        self._load_sample_data()
        
        # 全選択チェックボックスをヘッダーに追加
        self._add_header_checkbox()
    
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
    
    def _load_sample_data(self):
        """サンプルデータ読み込み"""
        sample_data = [
            {
                'selected': False,
                'filename': 'document1.pdf',
                'pages': 15,
                'status': '未処理',
                'size': '2.1 MB',
                'file_id': 1
            },
            {
                'selected': False,
                'filename': 'report2023.pdf',
                'pages': 42,
                'status': '処理完了',
                'size': '5.8 MB',
                'file_id': 2
            },
            {
                'selected': False,
                'filename': 'manual_v2.pdf',
                'pages': 128,
                'status': '未整形',
                'size': '12.3 MB',
                'file_id': 3
            },
            {
                'selected': False,
                'filename': 'contract_20241201.pdf',
                'pages': 8,
                'status': 'エラー',
                'size': '1.5 MB',
                'file_id': 4
            }
        ]
        
        self.all_files = sample_data
        self.filtered_files = sample_data.copy()
        self.data_grid.update_data(sample_data)
        
        # グローバル参照用
        ui.run_javascript('window.data_reg_page = pyodide.globals.get("data_reg_page");')
        
        self._update_selection_count()
    
    def _create_settings_panel(self):
        """設定パネル（左上）- new/系準拠"""
        with ui.element('div').style('''
            grid-row: 1 / 2;
            grid-column: 1 / 2;
            background: white;
            border: 1px solid #ddd;
            border-radius: 8px;
            display: flex;
            flex-direction: column;
            overflow: hidden;
        '''):
            # パネルヘッダー
            with ui.element('div').style('background:#f8f9fa;padding:8px 12px;border-bottom:1px solid #ddd;display:flex;justify-content:space-between;align-items:center;'):
                ui.label('📋 処理設定').style('font-size:16px;font-weight:600;margin:0;')
                with ui.row().classes('gap-1'):
                    ui.button('🚀 処理開始', on_click=lambda: ui.notify('処理開始')).props('size=sm color=primary').style('font-size:11px;')
                    ui.button('⏹️ 停止', on_click=lambda: ui.notify('停止')).props('size=sm color=secondary').style('font-size:11px;display:none;')
            
            # パネル内容
            with ui.element('div').style('flex:1;padding:8px;overflow-y:auto;'):
                # 整形プロセス
                ui.label('整形プロセス').style('font-weight:600;margin-bottom:6px;font-size:13px;')
                ui.select(['デフォルト (OCR + LLM整形)', 'マルチモーダル'], value='デフォルト (OCR + LLM整形)').props('outlined dense').style('width:100%;margin-bottom:16px;')
                
                # 埋め込みモデル
                ui.label('埋め込みモデル').style('font-weight:600;margin-bottom:6px;font-size:13px;')
                with ui.element('div').style('border:1px solid #eee;border-radius:4px;padding:8px;background:#fafafa;margin-bottom:16px;'):
                    ui.checkbox('intfloat/e5-large-v2: multilingual-e5-large', value=True).style('margin-bottom:3px;font-size:14px;')
                    ui.checkbox('intfloat/e5-small-v2: multilingual-e5-small').style('margin-bottom:3px;font-size:14px;')
                    ui.checkbox('nomic-embed-text: nomic-text-embed').style('margin-bottom:3px;font-size:14px;')
                
                # 横並び設定
                with ui.row().classes('gap-4 w-full'):
                    with ui.column():
                        ui.checkbox('既存データを上書き', value=True).style('margin-bottom:8px;')
                    with ui.column():
                        ui.label('品質しきい値').style('font-weight:600;margin-bottom:6px;font-size:13px;')
                        ui.number(value=0.0, min=0, max=1, step=0.1).props('outlined dense').style('width:80px;height:28px;font-size:11px;')
                
                # LLMタイムアウト
                ui.label('LLMタイムアウト (秒)').style('font-weight:600;margin-bottom:6px;font-size:13px;')
                ui.number(value=300, min=30, max=3600).props('outlined dense').style('width:120px;height:28px;font-size:11px;')

    def _create_log_panel(self):
        """処理ログパネル（中央全体）- new/系準拠"""
        with ui.element('div').style('''
            grid-row: 1 / 3;
            grid-column: 2 / 3;
            background: white;
            border: 1px solid #ddd;
            border-radius: 8px;
            display: flex;
            flex-direction: column;
            overflow: hidden;
        '''):
            # パネルヘッダー
            with ui.element('div').style('background:#f8f9fa;padding:8px 12px;border-bottom:1px solid #ddd;display:flex;justify-content:space-between;align-items:center;'):
                ui.label('📋 処理ログ').style('font-size:16px;font-weight:600;margin:0;')
                with ui.row().classes('items-center gap-2'):
                    ui.switch('自動スクロール', value=True).style('font-size:11px;')
                    ui.button('CSV出力').props('size=sm outline').style('font-size:11px;')
            
            # ログコンテナ
            with ui.element('div').style('flex:1;overflow-y:auto;padding:8px;font-family:"Courier New",monospace;font-size:11px;'):
                ui.label('処理ログはここに表示されます').style('color:#666;text-align:center;margin-top:4em;')

    def _create_file_panel(self):
        """ファイル選択パネル（右全体）- new/系準拠"""
        with ui.element('div').style('''
            grid-row: 1 / 3;
            grid-column: 3 / 4;
            background: white;
            border: 1px solid #ddd;
            border-radius: 8px;
            display: flex;
            flex-direction: column;
            overflow: hidden;
        '''):
            # パネルヘッダー（横並び）
            with ui.element('div').style('background:#f8f9fa;padding:8px 12px;border-bottom:1px solid #ddd;display:flex;justify-content:flex-start;align-items:center;gap:12px;'):
                ui.label('📁 ファイル選択').style('font-size:16px;font-weight:600;margin:0;flex-shrink:0;min-width:120px;')
                ui.select(['すべてのステータス', '未処理', '処理中', '処理完了'], value='すべてのステータス').props('outlined dense').style('min-width:180px;height:32px;font-size:12px;')
                ui.input(placeholder='ファイル名で検索...').props('outlined dense').style('flex:1;height:32px;font-size:12px;')
                ui.label('選択: 0件').style('font-size:12px;color:#666;flex-shrink:0;min-width:80px;text-align:right;')
            
            # ファイル一覧
            with ui.element('div').style('flex:1;overflow:hidden;padding:0;'):
                ui.label('ファイル一覧はここに表示されます').style('color:#666;text-align:center;margin-top:4em;padding:16px;')

    def _create_status_panel(self):
        """処理状況パネル（左下）- new/系準拠"""
        with ui.element('div').style('''
            grid-row: 2 / 3;
            grid-column: 1 / 2;
            background: white;
            border: 1px solid #ddd;
            border-radius: 8px;
            display: flex;
            flex-direction: column;
            overflow: hidden;
            margin-top: 6px;
        '''):
            # パネルヘッダー
            with ui.element('div').style('background:#f8f9fa;padding:8px 12px;border-bottom:1px solid #ddd;'):
                ui.label('📊 処理状況').style('font-size:16px;font-weight:600;margin:0;')
            
            # パネル内容
            with ui.element('div').style('flex:1;padding:8px;'):
                # 全体進捗
                ui.label('全体進捗').style('font-weight:600;font-size:13px;margin-bottom:6px;')
                ui.label('待機中').style('font-size:11px;color:#666;margin-bottom:6px;')
                with ui.element('div').style('height:16px;background:#e9ecef;border-radius:8px;overflow:hidden;margin-bottom:16px;'):
                    ui.element('div').style('height:100%;width:0%;background:linear-gradient(90deg,#007bff,#0056b3);')
                
                # 現在の処理
                ui.label('現在の処理').style('font-weight:600;font-size:13px;margin-bottom:6px;')
                ui.label('待機中...').style('font-size:12px;margin-bottom:16px;')
                
                # 統計（4個横並び）
                with ui.row().classes('gap-2 w-full'):
                    with ui.element('div').style('flex:1;text-align:center;padding:8px;background:#f8f9fa;border-radius:4px;'):
                        ui.label('0').style('font-size:16px;font-weight:700;color:#007bff;')
                        ui.label('総ファイル数').style('font-size:10px;color:#666;margin-top:2px;')
                    
                    with ui.element('div').style('flex:1;text-align:center;padding:8px;background:#f8f9fa;border-radius:4px;'):
                        ui.label('0').style('font-size:16px;font-weight:700;color:#007bff;')
                        ui.label('選択数').style('font-size:10px;color:#666;margin-top:2px;')

