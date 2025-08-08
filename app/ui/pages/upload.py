"""
アップロードページ - new/系準拠実装（3ペイン構成）
"""
from nicegui import ui
from app.ui.components.layout import RAGHeader, RAGFooter, MainContentArea
from app.ui.components.elements import CommonPanel
from app.ui.components.common.layout import CommonSplitter
from app.ui.components.base.button import BaseButton
# from app.ui.components.common.data_grid import BaseDataGridView  # ui.tableに移行

class UploadPage:
    """アップロードページクラス - new/系準拠3ペイン構成"""
    
    def __init__(self):
        """初期化"""
        self.uploaded_files = []
        self.upload_results = []
        self.original_results = []  # フィルタリング用のオリジナルデータ
        self.is_uploading = False
        self.folder_path = "/workspace/ignored/input_files"
        self.include_subfolders = False
        self.data_grid = None  # BaseDataGridViewインスタンス
        self.status_filter = None  # ステータスフィルター
        self.search_input = None  # 検索入力
    
    def render(self):
        """ページレンダリング"""
        from app.utils.auth import SimpleAuth
        
        if not SimpleAuth.is_authenticated():
            ui.navigate.to('/login')
            return
        
        # 共通ヘッダー
        RAGHeader(show_site_name=True, current_page="upload")
        
        # 全ページ共通メインコンテンツエリア
        with MainContentArea():
            # 共通スプリッタースタイル・JS追加
            CommonSplitter.add_splitter_styles()
            CommonSplitter.add_splitter_javascript()
            
            self._create_main_layout()
        
        # 共通フッター
        RAGFooter()
        
        # JavaScript機能追加（new/系移植版）
        self._add_upload_javascript()
        
        # グローバル参照の設定（Python側メソッド呼び出し用）
        ui.run_javascript(f'window.uploadPageInstance = {{id: "{id(self)}"}};')
        
        # NiceGUIのJavaScript連携のための設定
        self._setup_js_callbacks()
    
    def _create_main_layout(self):
        """メインレイアウト作成"""
        with ui.element('div').style(
            'width: 100%; height: 100%; '
            'display: flex; margin: 0; padding: 4px; gap: 4px;'
        ).props('id="upload-main-container"'):
            
            # 左ペイン：アップロード機能（30%幅）
            with ui.element('div').style(
                'width: 30%; height: 100%; '
                'display: flex; flex-direction: column; '
                'margin: 0; padding: 0; gap: 4px;'
            ).props('id="upload-left-pane"'):
                self._create_file_upload_pane()
                CommonSplitter.create_horizontal(splitter_id="upload-hsplitter", height="4px")
                self._create_folder_upload_pane()
            
            # 縦スプリッター
            CommonSplitter.create_vertical(splitter_id="upload-vsplitter", width="4px")
            
            # 右ペイン：結果表示（70%幅）
            with ui.element('div').style(
                'width: 70%; height: 100%; '
                'display: flex; flex-direction: column; '
                'margin: 0; padding: 0;'
            ).props('id="upload-right-pane"'):
                self._create_result_pane()
    
    def _create_file_upload_pane(self):
        """左上: ファイルアップロードペイン"""
        with CommonPanel(
            title="ファイルアップロード",
            gradient="#334155",
            header_color="white",
            width="100%",
            height="50%"
        ) as panel:
            
            # ヘッダーにボタン配置
            with panel.header_element:
                with ui.element('div').style(
                    'display: flex; gap: 6px; margin-right: 8px;'
                ):
                    # ファイル選択ボタン
                    select_btn = BaseButton.create_type_a(
                        "📁 ファイル選択",
                        on_click=self._open_file_dialog
                    )
            
            # パネル内容: ドラッグ&ドロップエリア
            panel.content_element.style('padding: 0; height: 100%;')
            
            with panel.content_element:
                with ui.element('div').style('padding: 4px; height: 100%; box-sizing: border-box;'):
                    # ドラッグ&ドロップエリア（ID変更）
                    with ui.element('div').props('id="upload-box"').style(
                        'width: 100%; height: 80%; '
                        'border: 2px dashed #d1d5db; border-radius: 8px; '
                        'background: #f9fafb; display: flex; flex-direction: column; '
                        'align-items: center; justify-content: center; '
                        'text-align: center; cursor: pointer; transition: 0.2s;'
                    ):
                        ui.icon('cloud_upload', size='3em', color='grey-5').style('margin-bottom: 16px;')
                        ui.label('ファイルをドラッグ&ドロップ').style('font-size: 18px; margin-bottom: 8px; font-weight: 500;')
                        ui.label('または上のボタンでファイルを選択').style('color: #6b7280; font-size: 14px;')
                    
                    # 対応形式表示
                    with ui.element('div').style('margin-top: 8px; padding: 8px; background: #f3f4f6; border-radius: 4px;'):
                        ui.label('対応形式: PDF, DOCX, TXT, CSV, JSON, EML').style('font-size: 12px; color: #4b5563;')
                        ui.label('最大サイズ: 100MB').style('font-size: 12px; color: #4b5563;')
                    
                    # 隠しファイル入力（ID追加）
                    self.file_input = ui.element('input').props(
                        'type="file" multiple accept=".pdf,.docx,.txt,.csv,.json,.eml,.png,.jpg,.jpeg" style="display: none;" id="file-input"'
                    )
    
    def _create_folder_upload_pane(self):
        """左下: フォルダアップロードペイン"""
        with CommonPanel(
            title="フォルダアップロード",
            gradient="#334155",
            header_color="white",
            width="100%",
            height="50%"
        ) as panel:
            
            # ヘッダーはタイトルのみ（ボタンなし）
            
            # パネル内容
            panel.content_element.style('padding: 0; height: 100%;')
            
            with panel.content_element:
                with ui.element('div').style('padding: 8px; height: 100%; box-sizing: border-box; display: flex; flex-direction: column; gap: 12px;'):
                    
                    # ラジオボタンでローカル/サーバー選択
                    with ui.element('div').style('margin-bottom: 8px;'):
                        ui.label('アップロード方式').style('font-weight: 600; font-size: 14px; margin-bottom: 6px;')
                        self.upload_type = ui.radio(
                            ['💻 ローカル', '🖥️ サーバー'], 
                            value='💻 ローカル',
                            on_change=self._on_upload_type_change
                        ).style('display: flex; gap: 16px;')
                    
                    # 共通フォルダ操作エリア
                    with ui.element('div').style('display: flex; flex-direction: column; gap: 8px; flex: 1;'):
                        
                        # フォルダパス入力行
                        with ui.element('div').style('display: flex; align-items: center; gap: 8px;'):
                            self.folder_path_input = ui.input(
                                placeholder='フォルダパスまたはフォルダ選択'
                            ).style('flex: 1;').props('outlined dense')
                            
                            self.folder_btn = ui.button('📂', on_click=self._open_folder_dialog).style(
                                'min-width: 40px; padding: 8px;'
                            ).props('color=primary flat')
                        
                        # オプション行
                        with ui.element('div').style('display: flex; align-items: center; gap: 12px;'):
                            self.subfolder_checkbox = ui.checkbox(
                                'サブフォルダも含める',
                                value=self.include_subfolders
                            )
                            
                            # アップロードボタンを右端に配置
                            upload_btn = BaseButton.create_type_a(
                                "🚀 アップロード",
                                on_click=self._upload_folder
                            )
                        
                        # 説明エリア
                        with ui.element('div').style('background: #f8f9fa; padding: 12px; border-radius: 6px; border-left: 4px solid #2563eb; flex: 1;'):
                            self.description_label = ui.label('💻 ローカルフォルダアップロード').style('font-weight: 600; font-size: 14px; margin-bottom: 6px;')
                            self.description_list = ui.element('div')
                            self._update_description()
                            # ブラウザ制限の注記
                            ui.label('※ ブラウザの仕様上、フォルダ選択ダイアログのタイトルは「ファイルを開く」と表示されます').style(
                                'font-size: 12px; color: #6b7280; margin-top: 8px;'
                            )
                    
                    # 既存のfile-inputを動的に切り替えて使用（webkitdirectory属性をJavaScriptで制御）
    
    def _create_result_pane(self):
        """右: 結果表示ペイン（BaseDataGridView使用）"""
        with CommonPanel(
            title="アップロード結果",
            gradient="#334155",
            header_color="white",
            width="100%",
            height="100%",
            content_padding="0"  # paddingゼロに
        ) as panel:
            
            # ヘッダーにフィルター機能とボタン配置
            with panel.header_element:
                with ui.element('div').style(
                    'display: flex; align-items: center; gap: 8px; flex: 1; min-width: 0;'
                ):
                    # ステータスフィルター（files.pyと同じ仕様）
                    self.status_filter = ui.select(
                        options=[
                            '全て',
                            '新規',
                            '既存',
                            'エラー'
                        ],
                        value='全て',
                        on_change=self._filter_results
                    ).style(
                        'width: 100px; flex-shrink: 0; '
                        'background-color: white; color: black; '
                        'border-radius: 0;'
                    ).props('outlined dense square').classes('q-ma-none')
                    
                    # ファイル名検索（files.pyと同じ仕様）
                    self.search_input = ui.input(
                        placeholder='ファイル名で検索...',
                        on_change=self._filter_results
                    ).style(
                        'flex: 1; min-width: 120px; '
                        'background-color: white; color: black; '
                        'border-radius: 0;'
                    ).props('outlined dense bg-white square').classes('q-ma-none')
                    
                    # 管理画面へボタン
                    manage_btn = BaseButton.create_type_b(
                        "📁 ファイル管理",
                        on_click=lambda: ui.navigate.to('/files')
                    )
            
            # パネル内容
            panel.content_element.style('padding: 0; height: 100%;')
            
            with panel.content_element:
                with ui.element('div').style('height: 100%; display: flex; flex-direction: column;'):
                    # プログレスエリア（初期非表示）
                    with ui.element('div').props('id="upload-progress"').style('display: none; margin: 8px; margin-bottom: 16px;'):
                        with ui.element('div').style('background: #f3f4f6; padding: 16px; border-radius: 8px;'):
                            with ui.element('div').style('display: flex; justify-content: space-between; margin-bottom: 12px;'):
                                ui.label('⏳ アップロード中...').style('font-weight: 600; font-size: 16px;')
                                with ui.element('div').props('id="progress-stats"'):
                                    ui.label('処理中: ').style('color: #6b7280; font-size: 14px;')
                                    ui.element('span').props('id="progress-current"').style('color: #6b7280; font-weight: 600;')
                                    ui.label(' / ').style('color: #6b7280; font-size: 14px;')
                                    ui.element('span').props('id="progress-total"').style('color: #6b7280; font-weight: 600;')
                            
                            # プログレスバー
                            with ui.element('div').style(
                                'width: 100%; height: 8px; background: #e5e7eb; border-radius: 4px; overflow: hidden;'
                            ):
                                ui.element('div').props('id="progress-fill"').style(
                                    'height: 100%; background: #3b82f6; width: 0%; transition: width 0.3s ease;'
                                )
                            
                            ui.element('div').props('id="progress-text"').style('text-align: center; margin-top: 8px; font-weight: 600;')
                            ui.element('div').props('id="progress-details"').style('margin-top: 12px; color: #6b7280; font-size: 14px;')
                    
                    # 結果グリッド表示エリア
                    with ui.element('div').props('id="upload-results"').style('flex: 1; min-height: 0; padding: 4px;'):
                        self._create_results_grid()
    
    def _create_results_grid(self):
        """結果表示グリッドを作成"""
        # 初期状態メッセージ
        with ui.element('div').props('id="upload-waiting"').style(
            'height: 100%; display: flex; align-items: center; justify-content: center; '
            'color: #9ca3af; text-align: center;'
        ):
            with ui.element('div'):
                ui.icon('cloud_upload', size='4em').style('margin-bottom: 16px; opacity: 0.5;')
                ui.label('ファイルまたはフォルダをアップロードすると').style('font-size: 16px; margin-bottom: 4px;')
                ui.label('ここに結果が表示されます').style('font-size: 16px;')
        
        # ui.table定義（初期は空データ）
        columns = [
            {'name': 'status', 'label': 'ステータス', 'field': 'status', 'sortable': True, 'align': 'center'},
            {'name': 'file_name', 'label': 'ファイル名', 'field': 'file_name', 'sortable': True, 'align': 'left'},
            {'name': 'size', 'label': 'サイズ', 'field': 'size', 'sortable': True, 'align': 'right'},
            {'name': 'created_at', 'label': '日時', 'field': 'created_at', 'sortable': True, 'align': 'center'},
            {'name': 'message', 'label': 'メッセージ', 'field': 'message', 'sortable': False, 'align': 'left'}
        ]
        
        # ui.table作成（files.pyと同じ仕様）
        self.data_grid = ui.table(
            columns=columns,
            rows=[],  # 初期は空
            row_key='file_name',
            pagination=20
        ).classes('w-full').style(
            'height: 100%; margin: 0; display: none;'  # 初期非表示
        ).props('dense flat').props('id="upload-results-table"')
    
    def _filter_results(self, e=None):
        """結果をフィルタリング"""
        if not self.original_results:
            return
        
        status_filter = self.status_filter.value if self.status_filter else '全て'
        search_text = self.search_input.value.lower() if self.search_input else ''
        
        filtered_data = []
        for item in self.original_results:
            # ステータスフィルター
            status_match = True
            if status_filter != '全て':
                # ステータス表示文字列でフィルタリング
                if status_filter == '新規' and '新規' not in item.get('status', ''):
                    status_match = False
                elif status_filter == '既存' and '既存' not in item.get('status', ''):
                    status_match = False
                elif status_filter == 'エラー' and 'エラー' not in item.get('status', ''):
                    status_match = False
            
            # ファイル名検索
            name_match = True
            if search_text:
                name_match = search_text in item['file_name'].lower()
            
            if status_match and name_match:
                filtered_data.append(item)
        
        # ui.tableを更新
        if self.data_grid:
            self.data_grid.rows[:] = filtered_data
            self.data_grid.update()
    
    def _show_results(self, results_data):
        """結果をグリッドに表示"""
        # データを整形
        formatted_data = []
        for result in results_data:
            # ステータス表示の変換
            status_display = {
                'uploaded': '✅ 完了',
                'duplicate': '🔄 重複',
                'error': '❌ エラー'
            }.get(result.get('status'), result.get('status', '不明'))
            
            # サイズの表示
            size_display = self._format_file_size(result.get('size', 0))
            
            # 日時の表示
            created_at = result.get('created_at')
            if created_at:
                if isinstance(created_at, str):
                    # ISO形式の場合
                    date_display = created_at[:16].replace('T', ' ')
                else:
                    # datetimeオブジェクトの場合
                    date_display = created_at.strftime('%Y-%m-%d %H:%M')
            else:
                date_display = '-'
            
            formatted_data.append({
                'status': status_display,
                'file_name': result.get('file_name', ''),
                'size': size_display,
                'created_at': date_display,
                'message': result.get('message', '')
            })
        
        # オリジナルデータを保存（フィルタリング用）
        self.original_results = []
        for i, result in enumerate(results_data):
            original_item = formatted_data[i].copy()
            original_item['status'] = result.get('status')  # 元のステータス値を保持
            self.original_results.append(original_item)
        
        # 待機メッセージを隠してグリッドを表示
        ui.run_javascript('document.getElementById("upload-waiting").style.display = "none";')
        ui.run_javascript('document.getElementById("upload-results-table").style.display = "block";')
        
        # データをui.tableに設定
        self.data_grid.rows[:] = formatted_data
        self.data_grid.update()
    
    def _format_file_size(self, size_bytes):
        """ファイルサイズをフォーマット"""
        if size_bytes == 0:
            return "0 B"
        size_names = ["B", "KB", "MB", "GB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1
        return f"{size_bytes:.1f} {size_names[i]}"
    
    def _set_folder_path(self, path):
        """フォルダパスを設定（JavaScriptから呼び出される）"""
        self.folder_path_input.value = path
        self.folder_path_input.update()
    
    def _setup_js_callbacks(self):
        """JavaScriptから呼び出し可能なコールバックを設定"""
        # 結果表示用の隠しinput要素を作成（JavaScript→Python通信用）
        self._results_input = ui.input().style('display: none;')
        self._results_input.on('value-change', lambda e: self._handle_results_change(e.value))
        
        # フォルダパス更新用の隠しinput要素を作成
        self._folder_path_update = ui.input().style('display: none;')
        self._folder_path_update.on('value-change', lambda e: self._handle_folder_path_change(e.value))
        
        # JavaScript側に要素のIDを渡す
        ui.run_javascript(f'''
            window.resultsInputId = "{self._results_input.id}";
            window.folderPathUpdateId = "{self._folder_path_update.id}";
        ''')
    
    def _handle_results_change(self, value):
        """結果データが更新されたときの処理"""
        if value:
            import json
            try:
                results = json.loads(value)
                self._show_results(results)
                # 処理後は値をクリア
                self._results_input.value = ''
            except json.JSONDecodeError:
                print(f"Invalid JSON in results: {value}")
    
    def _handle_folder_path_change(self, value):
        """フォルダパスが更新されたときの処理"""
        if value:
            self.folder_path_input.value = value
            # 処理後は値をクリア
            self._folder_path_update.value = ''
    
    # イベントハンドラー
    def _open_file_dialog(self):
        """ファイル選択ダイアログを開く"""
        ui.run_javascript('document.getElementById("file-input").click()')
    
    def _upload_folder(self):
        """フォルダアップロード実行"""
        upload_type = self.upload_type.value
        folder_path = self.folder_path_input.value
        include_subfolders = self.subfolder_checkbox.value
        
        if not folder_path:
            ui.notify('フォルダパスを指定してください', type='warning')
            return
        
        if upload_type == '💻 ローカル':
            # ローカルフォルダアップロード - JavaScript側で保存済みファイル情報をアップロード
            ui.run_javascript(f'''
                if (window.selectedFolderFiles && window.selectedFolderFiles.length > 0) {{
                    console.log('アップロード開始:', window.selectedFolderFiles.length + '個のファイル');
                    uploadFiles(window.selectedFolderFiles);
                    // アップロード後はリセット
                    window.selectedFolderFiles = null;
                }} else {{
                    console.warn('フォルダが選択されていません');
                    alert('先にフォルダを選択してください');
                }}
            ''')
        else:  # サーバー
            # サーバーフォルダアップロード - APIを呼び出し
            ui.run_javascript(f'''
                uploadServerFolder("{folder_path}", {str(include_subfolders).lower()});
            ''')
    
    def _on_upload_type_change(self, e):
        """アップロード方式変更時の処理"""
        # フォルダパスをリセット
        self.folder_path_input.value = ''
        # 説明文を更新
        self._update_description()
    
    def _open_folder_dialog(self):
        """フォルダダイアログを開く"""
        upload_type = self.upload_type.value
        
        if upload_type == '💻 ローカル':
            # ローカルフォルダ選択（既存のfile-inputにwebkitdirectory属性を追加してクリック）
            # 注意：ブラウザのネイティブダイアログのタイトルは「ファイルを開く」と表示されますが、
            # 実際にはフォルダ選択ダイアログです。タイトルはブラウザ依存で変更できません。
            ui.run_javascript('''
                const fileInput = document.getElementById("file-input");
                if (fileInput) {
                    // webkitdirectory属性を追加（フォルダ選択モード）
                    fileInput.setAttribute("webkitdirectory", "");
                    fileInput.setAttribute("directory", "");
                    // フォルダ選択フラグを設定
                    fileInput.dataset.isFolderSelect = "true";
                    fileInput.click();
                }
            ''')
        else:
            # サーバーフォルダブラウザ
            ui.run_javascript('''
                console.log("Button clicked - about to call openFolderBrowser");
                if (typeof window.openFolderBrowser === 'function') {
                    window.openFolderBrowser();
                } else {
                    console.error("openFolderBrowser function not found");
                    alert("フォルダブラウザ機能が読み込まれていません。ページを再読み込みしてください。");
                }
            ''')
    
    def _update_description(self):
        """説明文を更新"""
        upload_type = self.upload_type.value
        
        if upload_type == '💻 ローカル':
            self.description_label.text = '💻 ローカルフォルダアップロード'
            self.description_list.clear()
            with self.description_list:
                ui.label('• ブラウザでフォルダを選択してアップロード').style('font-size: 12px; color: #4b5563; margin: 2px 0;')
                ui.label('• 対応ファイルを自動検出・処理').style('font-size: 12px; color: #4b5563; margin: 2px 0;')
                ui.label('• 重複ファイルは自動スキップ').style('font-size: 12px; color: #4b5563; margin: 2px 0;')
        else:
            self.description_label.text = '🖥️ サーバーフォルダアップロード'
            self.description_list.clear()
            with self.description_list:
                ui.label('• サーバー上のフォルダパスを指定').style('font-size: 12px; color: #4b5563; margin: 2px 0;')
                ui.label('• 対応ファイルを自動検出・処理').style('font-size: 12px; color: #4b5563; margin: 2px 0;')
                ui.label('• 重複ファイルは自動スキップ').style('font-size: 12px; color: #4b5563; margin: 2px 0;')
    
    def _add_upload_javascript(self):
        """アップロード機能のJavaScript追加（new/系移植版）"""
        # Python側のメソッドを呼び出すための関数を登録
        upload_page_id = id(self)
        
        # JavaScriptコードを通常の文字列として定義（中括弧のエスケープ不要）
        js_code = '''
// Python側のインスタンスIDを保存
window.uploadPageId = "''' + str(upload_page_id) + '''";

// アップロード機能 - new/系移植版（app/系API対応）

// サーバーフォルダブラウザ機能を最初に定義（即座実行）
(function() {
    console.log('Defining openFolderBrowser function');
    
    window.openFolderBrowser = function() {
        console.log('openFolderBrowser called');
        
        // モーダルHTML構造をPythonで作成してもらう（NiceGUIのDOMに追加）
        const overlay = document.createElement('div');
        overlay.id = 'folder-browser-overlay';
        overlay.style.cssText = 
            'position: fixed;' +
            'top: 0;' +
            'left: 0;' +
            'width: 100%;' +
            'height: 100%;' +
            'background: rgba(0, 0, 0, 0.5);' +
            'z-index: 9999;' +
            'display: flex;' +
            'align-items: center;' +
            'justify-content: center;';
    
        const modal = document.createElement('div');
        modal.id = 'folder-browser-modal';
        modal.style.cssText = 
            'background: white;' +
            'border-radius: 8px;' +
            'box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);' +
            'width: 600px;' +
            'max-height: 80vh;' +
            'display: flex;' +
            'flex-direction: column;';
    
        modal.innerHTML = 
            '<div style="padding: 16px; border-bottom: 1px solid #e5e7eb; display: flex; justify-content: space-between; align-items: center;">' +
                '<h3 style="margin: 0; font-size: 18px; font-weight: 600;">📂 フォルダを選択</h3>' +
                '<button id="close-folder-browser" style="background: none; border: none; font-size: 24px; cursor: pointer; color: #6b7280;">&times;</button>' +
            '</div>' +
            '<div style="padding: 16px; flex: 1; overflow-y: auto;">' +
                '<div id="folder-breadcrumbs" style="background: #f3f4f6; padding: 8px 12px; border-radius: 4px; margin-bottom: 12px; font-family: monospace; font-size: 14px;"></div>' +
                '<ul id="folder-list" style="list-style: none; margin: 0; padding: 0; max-height: 300px; overflow-y: auto; border: 1px solid #e5e7eb; border-radius: 4px;"></ul>' +
            '</div>' +
            '<div style="padding: 16px; border-top: 1px solid #e5e7eb; display: flex; gap: 8px; justify-content: flex-end;">' +
                '<button id="cancel-folder-selection" style="padding: 8px 16px; border: 1px solid #d1d5db; background: white; border-radius: 4px; cursor: pointer;">キャンセル</button>' +
                '<button id="confirm-folder-selection" style="padding: 8px 16px; background: #2563eb; color: white; border: none; border-radius: 4px; cursor: pointer;">✅ 決定</button>' +
            '</div>';
    
        overlay.appendChild(modal);
        document.body.appendChild(overlay);
        
        // イベントリスナー
        document.getElementById('close-folder-browser').onclick = closeFolderBrowser;
        document.getElementById('cancel-folder-selection').onclick = closeFolderBrowser;
        overlay.onclick = (e) => { if (e.target === overlay) closeFolderBrowser(); };
        
        document.getElementById('confirm-folder-selection').onclick = () => {
            if (window.currentFolderPath) {
                selectFolder(window.currentFolderPath);
            } else {
                closeFolderBrowser();
            }
        };
        
        // 初期フォルダをロード
        loadFolders('ignored/input_files');
    };
    
    // フォルダブラウザ関連関数を定義
    window.loadFolders = async function(path) {
        try {
            const response = await fetch('/api/list-folders?path=' + encodeURIComponent(path));
            
            if (!response.ok) {
                throw new Error('HTTP ' + response.status);
            }
            
            const data = await response.json();
            
            if (data.error) {
                throw new Error(data.error);
            }
            
            // パンくずリストを更新
            const breadcrumbs = document.getElementById('folder-breadcrumbs');
            breadcrumbs.textContent = '/workspace/' + (path || '');
            
            // フォルダリストを更新
            const folderList = document.getElementById('folder-list');
            folderList.innerHTML = '';
            
            // 現在のパスを保存
            window.currentFolderPath = path;
            
            // 上に戻るリンク
            if (path && path !== '') {
                const upItem = document.createElement('li');
                upItem.innerHTML = '🔙 上へ';
                upItem.style.cssText = 
                    'padding: 12px;' +
                    'border-bottom: 1px solid #f3f4f6;' +
                    'cursor: pointer;' +
                    'font-weight: 500;' +
                    'color: #2563eb;';
                upItem.onclick = () => {
                    const parentPath = path.split('/').slice(0, -1).join('/');
                    loadFolders(parentPath);
                };
                upItem.onmouseover = () => upItem.style.background = '#f3f4f6';
                upItem.onmouseout = () => upItem.style.background = 'white';
                folderList.appendChild(upItem);
            }
            
            // フォルダ一覧
            data.folders.forEach(folderName => {
                const item = document.createElement('li');
                item.innerHTML = '📁 ' + folderName;
                item.style.cssText = 
                    'padding: 12px;' +
                    'border-bottom: 1px solid #f3f4f6;' +
                    'cursor: pointer;' +
                    'font-size: 14px;';
                item.onclick = () => {
                    const newPath = path ? path + '/' + folderName : folderName;
                    loadFolders(newPath);
                };
                item.ondblclick = () => {
                    const newPath = path ? path + '/' + folderName : folderName;
                    selectFolder(newPath);
                };
                item.onmouseover = () => item.style.background = '#f3f4f6';
                item.onmouseout = () => item.style.background = 'white';
                folderList.appendChild(item);
            });
            
        } catch (error) {
            console.error('フォルダ読み込みエラー:', error);
            const folderList = document.getElementById('folder-list');
            folderList.innerHTML = '<li style="padding: 12px; color: #dc2626; text-align: center;">❌ ' + error.message + '</li>';
        }
    };

    window.selectFolder = function(path) {
        const fullPath = '/workspace/' + path;
        
        // 隠しinput要素経由でPython側にフォルダパスを送信
        if (window.folderPathUpdateId) {
            const folderPathInput = document.getElementById(window.folderPathUpdateId);
            if (folderPathInput) {
                folderPathInput.value = fullPath;
                // changeイベントを発火してNiceGUIに通知
                folderPathInput.dispatchEvent(new Event('input', { bubbles: true }));
            }
        }
        
        closeFolderBrowser();
    };

    window.closeFolderBrowser = function() {
        const overlay = document.getElementById('folder-browser-overlay');
        if (overlay) {
            overlay.remove();
        }
    };
})();

// ドラッグ&ドロップの設定
document.addEventListener('DOMContentLoaded', function() {
    const uploadBox = document.getElementById('upload-box');
    const fileInput = document.getElementById('file-input');
    
    if (!uploadBox || !fileInput) return;
    
    // デフォルトのドラッグ&ドロップ動作を無効化（ブラウザでファイルが開くのを防ぐ）
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        document.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
        }, false);
    });
    
    // ドラッグ&ドロップイベント
    uploadBox.addEventListener('dragover', (e) => {
        e.preventDefault();
        e.stopPropagation();
        uploadBox.style.borderColor = '#3b82f6';
        uploadBox.style.backgroundColor = '#eff6ff';
    });
    
    uploadBox.addEventListener('dragleave', (e) => {
        e.preventDefault();
        e.stopPropagation();
        uploadBox.style.borderColor = '#d1d5db';
        uploadBox.style.backgroundColor = '#f9fafb';
    });
    
    uploadBox.addEventListener('drop', (e) => {
        e.preventDefault();
        e.stopPropagation();
        uploadBox.style.borderColor = '#d1d5db';
        uploadBox.style.backgroundColor = '#f9fafb';
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            handleFiles(files);
        }
    });
    
    // ファイル選択イベント（フォルダ選択かファイル選択かを判定）
    fileInput.addEventListener('change', (e) => {
        const files = Array.from(e.target.files);
        if (files.length === 0) return;
        
        // フォルダ選択モードかチェック
        if (e.target.dataset.isFolderSelect === "true") {
            // フォルダ選択の場合
            console.log('フォルダ選択:', files.length + '個のファイル');
            
            // フォルダパスを表示用の入力欄に設定（最初のファイルのパスから推定）
            if (files[0] && files[0].webkitRelativePath) {
                const folderPath = files[0].webkitRelativePath.split('/')[0];
                
                // 隠しinput要素経由でPython側にフォルダパスを送信
                if (window.folderPathUpdateId) {
                    const folderPathInput = document.getElementById(window.folderPathUpdateId);
                    if (folderPathInput) {
                        folderPathInput.value = folderPath;
                        folderPathInput.dispatchEvent(new Event('input', { bubbles: true }));
                    }
                }
            }
            
            // ファイル情報をグローバル変数に保存（アップロードボタン押下時まで待機）
            window.selectedFolderFiles = files;
            
            // 待機状態表示
            const waitingDiv = document.getElementById('upload-waiting');
            if (waitingDiv) {
                waitingDiv.innerHTML = `
                    <div style="text-align: center; color: #10b981;">
                        <div style="font-size: 48px; margin-bottom: 16px;">✅</div>
                        <div style="font-weight: 600; font-size: 18px; margin-bottom: 8px;">フォルダ選択完了</div>
                        <div style="color: #6b7280; margin-bottom: 12px;">${files.length}個のファイルが選択されました</div>
                        <div style="color: #374151; font-size: 14px;">「🚀 アップロード」ボタンを押して開始してください</div>
                    </div>
                `;
            }
            
            // webkitdirectory属性を削除してリセット
            e.target.removeAttribute("webkitdirectory");
            e.target.removeAttribute("directory");
            delete e.target.dataset.isFolderSelect;
        } else {
            // 通常のファイル選択の場合
            console.log('ファイル選択:', files.length + '個のファイル');
            handleFiles(files);
            // inputをリセット（次回も選択できるように）
            e.target.value = '';
        }
    });
    
    // クリックでファイル選択
    uploadBox.addEventListener('click', () => {
        fileInput.click();
    });

});

// ファイル処理
function handleFiles(files) {
    if (files.length === 0) return;
    
    // ファイルサイズチェック（100MB制限）
    const maxSize = 100 * 1024 * 1024; // 100MB
    const validFiles = Array.from(files).filter(file => {
        if (file.size > maxSize) {
            // NiceGUIのnotify機能を使用
            window.pywebview && window.pywebview.api ? 
                window.pywebview.api.notify(`ファイルサイズが大きすぎます: ${file.name}`, 'error') :
                console.warn(`ファイルサイズが大きすぎます: ${file.name}`);
            return false;
        }
        return true;
    });
    
    if (validFiles.length === 0) return;
    
    uploadFiles(validFiles);
}

// ファイルアップロード（app/系API対応）
async function uploadFiles(files) {
    const progressContainer = document.getElementById('upload-progress');
    const progressFill = document.getElementById('progress-fill');
    const progressText = document.getElementById('progress-text');
    const progressCurrent = document.getElementById('progress-current');
    const progressTotal = document.getElementById('progress-total');
    const progressDetails = document.getElementById('progress-details');
    const resultsContainer = document.getElementById('upload-results');
    const waitingContainer = document.getElementById('upload-waiting');
    const resultsShowContainer = document.getElementById('results-container');
    
    // プログレスバーを表示
    progressContainer.style.display = 'block';
    waitingContainer.style.display = 'none';
    resultsShowContainer.style.display = 'none';
    progressTotal.textContent = files.length;
    progressCurrent.textContent = '0';
    
    // 全ファイルを一度に送信するためのFormDataを作成
    const formData = new FormData();
    for (let i = 0; i < files.length; i++) {
        formData.append('files', files[i]);
    }
    
    let results = [];
    
    try {
        // プログレス更新 - アップロード段階
        progressFill.style.width = '50%';
        progressText.textContent = '50%';
        progressCurrent.textContent = files.length;
        progressDetails.innerHTML = `
            <p>📤 ファイルをアップロード中...</p>
            <p style="color: #6b7280; font-size: 12px;">📄 OCR処理は後で実行されます</p>
            <p style="color: #6b7280; font-size: 12px;">🧠 ベクトル化は後で実行されます</p>
        `;
        
        const response = await fetch('/api/upload/batch', {
            method: 'POST',
            body: formData
        });
        
        if (response.ok) {
            const result = await response.json();
            
            // プログレス100%表示
            progressFill.style.width = '100%';
            progressText.textContent = '100%';
            progressDetails.innerHTML = `
                <p>✅ アップロード完了！</p>
                <p style="color: #6b7280; font-size: 12px;">📄 OCR処理と🧠ベクトル化はバックグラウンドで続行されます</p>
            `;
            
            // app/系APIのレスポンス形式に対応
            results = result.results || [];
            
        } else {
            const error = await response.json();
            // エラーの場合、全ファイルを失敗として扱う
            for (let i = 0; i < files.length; i++) {
                results.push({
                    file_name: files[i].name,
                    status: 'error',
                    message: error.detail || 'アップロードに失敗しました'
                });
            }
        }
    } catch (error) {
        console.error('Error uploading files:', error);
        // エラーの場合、全ファイルを失敗として扱う
        for (let i = 0; i < files.length; i++) {
            results.push({
                file_name: files[i].name,
                status: 'error',
                message: 'ネットワークエラーが発生しました'
            });
        }
    }
    
    // 少し待機してから結果を表示
    setTimeout(() => {
        displayResults(results);
        progressContainer.style.display = 'none';
        waitingContainer.style.display = 'none';
        resultsShowContainer.style.display = 'block';
    }, 1500);
}

// 結果を表示（隠しinput経由でPython側に送信）
function displayResults(results) {
    // 配列でない場合のエラーハンドリング
    if (!Array.isArray(results)) {
        console.error('displayResults: results is not an array', results);
        return;
    }
    
    console.log('displayResults called with:', results);
    
    // 隠しinput要素経由でPython側に結果を送信
    if (window.resultsInputId) {
        const resultsInput = document.getElementById(window.resultsInputId);
        if (resultsInput) {
            // JSON文字列として値を設定
            resultsInput.value = JSON.stringify(results);
            // changeイベントを発火してNiceGUIに通知
            resultsInput.dispatchEvent(new Event('input', { bubbles: true }));
        } else {
            console.error('Results input element not found');
        }
    } else {
        console.error('resultsInputId not set');
    }
}

// ファイルサイズのフォーマット
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// サーバーフォルダアップロード（new/系移植版）
async function uploadServerFolder(folderPath, includeSubfolders) {
    const progressContainer = document.getElementById('upload-progress');
    const progressFill = document.getElementById('progress-fill');
    const progressText = document.getElementById('progress-text');
    const progressCurrent = document.getElementById('progress-current');
    const progressTotal = document.getElementById('progress-total');
    const progressDetails = document.getElementById('progress-details');
    const resultsContainer = document.getElementById('results-container');
    const waitingDiv = document.getElementById('upload-waiting');
    
    // UI状態変更
    if (waitingDiv) waitingDiv.style.display = 'none';
    if (progressContainer) progressContainer.style.display = 'block';
    if (resultsContainer) resultsContainer.style.display = 'none';
    
    // プログレス初期化
    if (progressTotal) progressTotal.textContent = '?';
    if (progressCurrent) progressCurrent.textContent = '0';
    if (progressFill) progressFill.style.width = '30%';
    if (progressText) progressText.textContent = '30%';
    if (progressDetails) {
        progressDetails.innerHTML = 
            '<p>📂 サーバーフォルダをスキャン中...</p>' +
            '<p class="text-muted">対応ファイルを検索しています</p>';
    }
    
    try {
        const formData = new FormData();
        formData.append('folder_path', folderPath);
        formData.append('include_subfolders', includeSubfolders);
        
        const response = await fetch('/api/upload/folder', {
            method: 'POST',
            body: formData
        });
        
        if (response.ok) {
            const result = await response.json();
            console.log('サーバーフォルダアップロード結果:', result);
            
            // プログレス更新 - 完了
            if (progressFill) progressFill.style.width = '100%';
            if (progressText) progressText.textContent = '100%';
            if (progressDetails) {
                progressDetails.innerHTML = 
                    '<p>✅ フォルダアップロード完了</p>' +
                    '<p class="text-muted">結果を表示しています</p>';
            }
            
            // 少し待ってから結果表示
            setTimeout(() => {
                if (progressContainer) progressContainer.style.display = 'none';
                if (resultsContainer) resultsContainer.style.display = 'block';
                
                // サーバーフォルダアップロードのレスポンス形式に対応
                const resultsData = result.results || result;
                console.log('displayResults に渡すデータ:', resultsData);
                console.log('resultsData is Array:', Array.isArray(resultsData));
                displayResults(resultsData);
            }, 1000);
            
        } else {
            throw new Error('サーバーエラー: ' + response.status);
        }
        
    } catch (error) {
        console.error('サーバーフォルダアップロードエラー:', error);
        
        // エラー表示
        if (progressContainer) progressContainer.style.display = 'none';
        if (resultsContainer) resultsContainer.style.display = 'block';
        
        const summaryDiv = document.getElementById('results-summary');
        if (summaryDiv) {
            summaryDiv.innerHTML = 
                '<div style="background: #fef2f2; border: 1px solid #fecaca; border-radius: 6px; padding: 12px; margin-bottom: 16px;">' +
                    '<div style="font-weight: 600; color: #dc2626; margin-bottom: 4px;">❌ フォルダアップロードエラー</div>' +
                    '<div style="color: #6b7280; font-size: 14px;">' + error.message + '</div>' +
                '</div>';
        }
        
        const listDiv = document.getElementById('results-list');
        if (listDiv) {
            listDiv.innerHTML = '';
        }
    }
});
        '''
        ui.run_javascript(js_code)