"""
アップロードページ - new/系準拠実装（3ペイン構成）
"""
from nicegui import ui
from app.config import logger
from app.ui.components.layout import RAGHeader, RAGFooter, MainContentArea
from app.ui.components.elements import CommonPanel
from app.ui.components.common.layout import CommonSplitter
from app.ui.components.base.button import BaseButton
# from app.ui.components.common.data_grid import BaseDataGridView  # ui.tableに移行
from app.ui.components.upload_log_viewer import UploadLogViewer

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
        from app.auth.session import SessionManager
        
        current_user = SessionManager.get_current_user()
        if not current_user:
            ui.navigate.to('/login?redirect=/upload')
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

        # 外部JavaScript（/app-static/js/upload.js）を読み込む
        ui.run_javascript("""
            (function(){
              // 既に読み込み済みかチェック
              if (window.uploadScriptLoaded) {
                console.log('[upload] script already loaded');
                return;
              }
              const s = document.createElement('script');
              s.src = '/app-static/js/upload.js';
              s.defer = true;
              s.onload = () => {
                console.log('[upload] external script loaded');
                window.uploadScriptLoaded = true;
              };
              s.onerror = (e) => console.error('[upload] external script load error', e);
              document.head.appendChild(s);
            })();
        """)
        
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
            
            # ｒペイン：結果表示（70%幅）
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
                    # ファイル選択ボタンのみ（選択後即アップロード）
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
                            ).style('flex: 1;').props('outlined dense').props('id="folder-path-input"')
                            
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
            title="アップロードログ（リアルタイム）",
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
                            with ui.element('div').style('display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; gap: 20px;'):
                                ui.label('⏳ アップロード中...').style('font-weight: 600; font-size: 16px;')
                                with ui.element('div').props('id="progress-stats"').style('display: flex; align-items: center; white-space: nowrap;'):
                                    ui.label('処理中: ').style('color: #6b7280; font-size: 14px; margin: 0;')
                                    ui.element('span').props('id="progress-current"').style('color: #6b7280; font-weight: 600; margin: 0 4px;')
                                    ui.label(' / ').style('color: #6b7280; font-size: 14px; margin: 0;')
                                    ui.element('span').props('id="progress-total"').style('color: #6b7280; font-weight: 600; margin-left: 4px;')
                            
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
        """ログビューアーを作成"""
        # ログビューアーコンテナ
        log_container = ui.element('div').style('height: 100%; width: 100%;')
        
        # ログビューアーインスタンスを作成（初期は全体）
        self.log_viewer = UploadLogViewer(log_container)
        
        # 従来の結果表示用の隠しテーブル（互換性のため残す）
        self.data_grid = None
    
    def _filter_results(self, e=None):
        """結果をフィルタリング"""
        if not self.original_results:
            return
        
        status_filter = self.status_filter.value if self.status_filter else '全て'
        search_text = self.search_input.value.lower() if self.search_input else ''
        
        def map_status_to_label(status_code: str) -> str:
            code = (status_code or '').lower()
            if code in ('success', 'uploaded', 'new'):
                return '新規'
            if code in ('duplicate', 'existing'):
                return '既存'
            if code in ('error', 'failed', 'failure'):
                return 'エラー'
            return '不明'
        
        filtered_data = []
        for item in self.original_results:
            # ステータスフィルター（元のコード値から日本語ラベルに変換して比較）
            status_match = True
            if status_filter != '全て':
                label = map_status_to_label(item.get('status_code'))
                status_match = (label == status_filter)
            
            # ファイル名検索
            name_match = True
            if search_text:
                name_match = search_text in (item.get('file_name') or '').lower()
            
            if status_match and name_match:
                filtered_data.append(item)
        
        # ui.tableを更新
        if self.data_grid:
            self.data_grid.rows[:] = filtered_data
            self.data_grid.update()
    
    def _show_results(self, results_data):
        """結果をログビューアーで表示（旧互換性のため残す）"""
        # ログビューアーが自動的に更新するため、ここでは何もしない
        print(f"[DEBUG] _show_results called with {len(results_data) if isinstance(results_data, list) else 0} items")
        
        # ログビューアーを手動で更新
        if hasattr(self, 'log_viewer'):
            ui.run_javascript('window.uploadLogUpdated = true;')
        
        return
        
        # データを整形
        formatted_data = []
        for idx, result in enumerate(results_data):
            # ステータス表示の変換
            raw_status = (result.get('status') or '').lower()
            if raw_status in ('success', 'uploaded', 'new'):
                status_display = '🆕 新規'
            elif raw_status in ('duplicate', 'existing'):
                status_display = '📂 既存'
            elif raw_status in ('error', 'failed', 'failure'):
                status_display = '❌ エラー'
            else:
                status_display = '不明'
            
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
                'id': idx,  # 各行にIDを追加（files.pyと同じ）
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
            # 元のステータスコードを保持（表示用のstatusは維持）
            original_item['status_code'] = (result.get('status') or '').lower()
            self.original_results.append(original_item)
        
        # 待機メッセージを隠す
        ui.run_javascript('document.getElementById("upload-waiting").style.display = "none";')
        
        # データをui.tableに設定
        print(f"[DEBUG] Setting {len(formatted_data)} rows to data_grid")
        print(f"[DEBUG] Formatted data sample: {formatted_data[:1] if formatted_data else 'empty'}")
        
        # テーブルのデータを更新 - 新しいリストを設定
        self.data_grid.rows[:] = formatted_data
        
        # 強制的に更新
        self.data_grid.update()
        ui.update()  # UIの強制更新
        
        # JavaScriptでテーブルコンテナを表示（念のため遅延実行）
        ui.run_javascript('''
            setTimeout(() => {
                const table = document.getElementById("upload-results-table");
                if (table) {
                    table.style.display = "block";
                    console.log("[DEBUG] Table display set to block");
                }
                const waiting = document.getElementById("upload-waiting");
                if (waiting) {
                    waiting.style.display = "none";
                    console.log("[DEBUG] Waiting div hidden");
                }
            }, 100);
        ''')
        
        print(f"[DEBUG] data_grid updated with {len(self.data_grid.rows)} rows")
    
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
        # 注：現在は使用していないが、将来の互換性のため残す
        self._results_input = ui.input().props('id="results-input"').style('display: none;')
        self._results_input.on('value-change', lambda e: self._handle_results_change(e.value) if e.value else None)
        
        # フォルダパス更新用の隠しinput要素を作成
        self._folder_path_update = ui.input().props('id="folder-path-update"').style('display: none;')
        self._folder_path_update.on('value-change', lambda e: self._handle_folder_path_change(e.value))
        
        # JavaScript側に要素のIDを渡す
        ui.run_javascript(f'''
            window.resultsInputId = "results-input";
            window.folderPathUpdateId = "folder-path-input";  // 実際のフォルダ入力要素のIDに変更
        ''')
        
        # シンプルなアプローチ：JavaScriptからPythonを直接呼び出す
        def show_results_from_js(results_str: str) -> None:
            """JavaScript から直接呼び出される関数"""
            import json
            try:
                if results_str:
                    results = json.loads(results_str)
                    print(f"[DEBUG] show_results_from_js called with {len(results)} items")
                    self._show_results(results)
            except Exception as e:
                print(f"[ERROR] show_results_from_js error: {e}")
        
        # 関数を登録
        self._show_results_from_js = show_results_from_js
        
        # グローバル変数として公開
        ui.run_javascript(f'''
            window._pythonShowResults = function(results) {{
                console.log('[DEBUG] Setting results via Python callback');
                // 隠しinputを使った別の方法を試す
                const input = document.getElementById('results-input');
                if (input) {{
                    input.value = JSON.stringify(results);
                    // Vueの変更検知を強制的にトリガー
                    input.dispatchEvent(new Event('input', {{ bubbles: true }}));
                    // もう一度changeイベントも
                    const changeEvent = new Event('change', {{ bubbles: true }});
                    input.dispatchEvent(changeEvent);
                }}
            }};
        ''')
        


    
    def _handle_results_change(self, value):
        """結果データが更新されたときの処理"""
        print(f"[DEBUG] _handle_results_change called with value length: {len(value) if value else 0}")
        print(f"[DEBUG] Value type: {type(value)}, first 100 chars: {str(value)[:100] if value else 'None'}")
        if value:
            import json
            try:
                results = json.loads(value)
                print(f"[DEBUG] JSON parsed successfully: {len(results) if isinstance(results, list) else 0} items")
                # デバッグログ
                try:
                    from app.config import logger as _logger
                    count = len(results) if isinstance(results, list) else 0
                    statuses = [str(r.get('status')) for r in (results if isinstance(results, list) else [])][:5]
                    _logger.info(f"[UploadPage] 結果受信: {count}件, statuses(sample)={statuses}")
                except Exception:
                    pass
                self._show_results(results)
                # 処理後は値をクリア
                self._results_input.value = ''
            except json.JSONDecodeError:
                try:
                    from app.config import logger as _logger
                    _logger.error(f"[UploadPage] Invalid JSON in results: {value}")
                except Exception:
                    pass
    
    def _handle_folder_path_change(self, value):
        """フォルダパスが更新されたときの処理"""
        if value:
            self.folder_path_input.set_value(value)
            # 処理後は値をクリア
            self._folder_path_update.value = ''

    
    # イベントハンドラー
    def _open_file_dialog(self):
        """ファイル選択ダイアログを開く"""
        try:
            from app.config import logger as _logger
            _logger.info("[UploadPage] ファイル選択ボタン押下: input[type=file] をクリック")
        except Exception:
            pass

        ui.run_javascript('''
            const fi = document.getElementById("file-input");
            if (fi) {
                // フォルダモード属性を外し、値もクリア（再選択グレー対策）
                fi.removeAttribute('webkitdirectory');
                fi.removeAttribute('directory');
                delete fi.dataset.isFolderSelect;
                fi.value = '';
                fi.click();
            }
        ''')
        
        # シンプルなポーリング方式で結果とセッションIDを取得
        async def poll_results():
            """アップロード結果をポーリング"""
            import asyncio
            for _ in range(10):  # 最大5秒待機
                await asyncio.sleep(0.5)
                try:
                    # JavaScriptのグローバル変数を直接確認
                    has_results = await ui.run_javascript('window.latestUploadResults !== null && window.latestUploadResults !== undefined')
                    if has_results:
                        # 結果を取得
                        results_json = await ui.run_javascript('JSON.stringify(window.latestUploadResults)')
                        if results_json:
                            import json
                            results = json.loads(results_json)
                            print(f"[DEBUG] Got results via polling: {len(results)} items")
                            self._show_results(results)
                            # クリア
                            await ui.run_javascript('window.latestUploadResults = null')
                        # セッションIDを取得してログビューアーに適用
                        session_id = await ui.run_javascript('window.latestUploadSessionId || null')
                        if session_id and hasattr(self, 'log_viewer') and self.log_viewer:
                            self.log_viewer.session_id = session_id
                            await self.log_viewer.refresh_logs()
                            break
                except Exception as e:
                    print(f"[ERROR] poll_results error: {e}")
        
        # 1秒後にポーリング開始
        ui.timer(1.0, poll_results, once=True)

    def _start_file_upload(self):
        """選択済みファイルのアップロードを開始"""
        try:
            from app.config import logger as _logger
            _logger.info("[UploadPage] アップロード開始ボタン押下: JSのuploadFiles(window.selectedFiles)を起動")
        except Exception:
            pass
        ui.run_javascript('''
            if (window.selectedFiles && window.selectedFiles.length > 0) {
                window.uploadFiles(window.selectedFiles);
                // 送信後はキューをクリア
                window.selectedFiles = null;
            } else {
                alert('先にファイルを選択してください');
            }
        ''')
    
    def _upload_folder(self):
        """フォルダアップロード実行"""
        upload_type = self.upload_type.value
        folder_path = self.folder_path_input.value
        include_subfolders = self.subfolder_checkbox.value
        try:
            from app.config import logger as _logger
            _logger.info(
                f"[UploadPage] フォルダアップロード要求: type={upload_type}, path={folder_path}, include_subfolders={include_subfolders}"
            )
        except Exception:
            pass
        
        if not folder_path:
            ui.notify('フォルダパスを指定してください', type='warning')
            return
        
        if upload_type == '💻 ローカル':
            # ローカルフォルダアップロード - JavaScript側で保存済みファイル情報をアップロード
            ui.run_javascript(f'''
                if (window.selectedFolderFiles && window.selectedFolderFiles.length > 0) {{
                    // 確認ダイアログを表示
                    const confirmMsg = window.selectedFolderFiles.length + '個のファイルをこのサイトにアップロードしますか？\\n「PDF」のすべてのファイルがアップロードされます。この操作は、サイトを信頼できる場合にのみ行ってください。';
                    if (confirm(confirmMsg)) {{
                        console.log('アップロード開始:', window.selectedFolderFiles.length + '個のファイル');
                        window.uploadFiles(window.selectedFolderFiles);
                        // アップロード後はリセット
                        window.selectedFolderFiles = null;
                    }}
                }} else {{
                    console.warn('フォルダが選択されていません');
                    alert('先にフォルダを選択してください');
                }}
            ''')
        else:  # サーバー
            # サーバーフォルダアップロード - APIを呼び出し
            ui.run_javascript(f'''
                // サーバーフォルダも確認ダイアログを表示
                const confirmMsg = 'サーバー上のフォルダ「{folder_path}」のファイルをアップロードしますか？' + ({str(include_subfolders).lower()} ? '\\nサブフォルダも含まれます。' : '');
                if (confirm(confirmMsg)) {{
                    window.uploadServerFolder("{folder_path}", {str(include_subfolders).lower()});
                }}
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
        try:
            from app.config import logger as _logger
            _logger.info(f"[UploadPage] フォルダ参照ボタン押下: mode={upload_type}")
        except Exception:
            pass
        
        # フォルダアップロード後も結果とセッションIDをポーリング
        async def poll_folder_results():
            """フォルダアップロード結果をポーリング"""
            import asyncio
            for _ in range(20):  # 最大10秒待機（フォルダは時間がかかる）
                await asyncio.sleep(0.5)
                try:
                    # JavaScriptのグローバル変数を直接確認
                    has_results = await ui.run_javascript('window.latestUploadResults !== null && window.latestUploadResults !== undefined')
                    if has_results:
                        # 結果を取得
                        results_json = await ui.run_javascript('JSON.stringify(window.latestUploadResults)')
                        if results_json:
                            import json
                            results = json.loads(results_json)
                            print(f"[DEBUG] Got folder upload results via polling: {len(results)} items")
                            self._show_results(results)
                            # クリア
                            await ui.run_javascript('window.latestUploadResults = null')
                        # セッションIDを取得し、ログビューアーをセッションモードに
                        session_id = await ui.run_javascript('window.latestUploadSessionId || null')
                        if session_id and hasattr(self, 'log_viewer') and self.log_viewer:
                            self.log_viewer.session_id = session_id
                            await self.log_viewer.refresh_logs()
                            break
                except Exception as e:
                    print(f"[ERROR] poll_folder_results error: {e}")
        
        # 3秒後にポーリング開始（フォルダ選択とアップロードに時間がかかるため）
        ui.timer(3.0, poll_folder_results, once=True)
        
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