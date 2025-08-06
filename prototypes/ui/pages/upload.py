"""
アップロードページ - new/系準拠実装（3ペイン構成）
"""
from nicegui import ui
from ui.components.layout import RAGHeader, RAGFooter, MainContentArea
from ui.components.elements import CommonPanel
from ui.components.common.layout import CommonSplitter
from ui.components.base.button import BaseButton

class UploadPage:
    """アップロードページクラス - new/系準拠3ペイン構成"""
    
    def __init__(self):
        """初期化"""
        self.uploaded_files = []
        self.upload_results = []
        self.is_uploading = False
        self.folder_path = "/workspace/ignored/input_files"
        self.include_subfolders = False
    
    def render(self):
        """ページレンダリング"""
        from main import SimpleAuth
        
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
    
    def _create_main_layout(self):
        """メインレイアウト作成"""
        with ui.element('div').style(
            'width: 100%; height: 100%; '
            'display: flex; margin: 0; padding: 4px; gap: 4px;'
        ).props('id="upload-main-container"'):
            
            # 左ペイン：アップロード機能（50%幅）
            with ui.element('div').style(
                'width: 50%; height: 100%; '
                'display: flex; flex-direction: column; '
                'margin: 0; padding: 0; gap: 4px;'
            ).props('id="upload-left-pane"'):
                self._create_file_upload_pane()
                CommonSplitter.create_horizontal(splitter_id="upload-hsplitter", height="4px")
                self._create_folder_upload_pane()
            
            # 縦スプリッター
            CommonSplitter.create_vertical(splitter_id="upload-vsplitter", width="4px")
            
            # 右ペイン：結果表示（50%幅）
            with ui.element('div').style(
                'width: 50%; height: 100%; '
                'display: flex; flex-direction: column; '
                'margin: 0; padding: 0;'
            ).props('id="upload-right-pane"'):
                self._create_result_pane()
    
    def _create_file_upload_pane(self):
        """左上: ファイルアップロードペイン"""
        with CommonPanel(
            title="ファイルアップロード",
            gradient="#f8f9fa",
            header_color="#374151",
            width="100%",
            height="50%"
        ) as panel:
            
            # ヘッダーにボタン配置
            with panel.header_element:
                with ui.element('div').style(
                    'display: flex; gap: 6px; margin-right: 8px;'
                ):
                    # クリアボタン（左）
                    clear_btn = BaseButton.create_type_b(
                        "🗑️ クリア",
                        on_click=self._clear_files
                    )
                    
                    # 選択ボタン（右端）
                    select_btn = BaseButton.create_type_a(
                        "📁 ファイル選択",
                        on_click=self._open_file_dialog
                    )
            
            # パネル内容: ドラッグ&ドロップエリア
            panel.content_element.style('padding: 0; height: 100%;')
            
            with panel.content_element:
                with ui.element('div').style('padding: 4px; height: 100%; box-sizing: border-box;'):
                    # ドラッグ&ドロップエリア
                    with ui.element('div').props('id="file-drop-zone"').style(
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
                    
                    # 隠しファイル入力
                    self.file_input = ui.element('input').props(
                        'type="file" multiple accept=".pdf,.docx,.txt,.csv,.json,.eml" style="display: none;"'
                    )
    
    def _create_folder_upload_pane(self):
        """左下: フォルダアップロードペイン"""
        with CommonPanel(
            title="フォルダアップロード",
            gradient="#f8f9fa",
            header_color="#374151",
            width="100%",
            height="50%"
        ) as panel:
            
            # ヘッダーにボタン配置
            with panel.header_element:
                with ui.element('div').style(
                    'display: flex; gap: 6px; margin-right: 8px;'
                ):
                    # リセットボタン（左）
                    reset_btn = BaseButton.create_type_b(
                        "🔄 リセット",
                        on_click=self._reset_folder
                    )
                    
                    # アップロードボタン（右端）
                    upload_btn = BaseButton.create_type_a(
                        "🚀 アップロード",
                        on_click=self._upload_folder
                    )
            
            # パネル内容
            panel.content_element.style('padding: 0; height: 100%;')
            
            with panel.content_element:
                with ui.element('div').style('padding: 4px; height: 100%; box-sizing: border-box;'):
                    with ui.element('div').style('display: flex; flex-direction: column; gap: 8px; height: 100%;'):
                        
                        # タブ切り替え
                        with ui.element('div').style('display: flex; border-bottom: 1px solid #e5e7eb;'):
                            self.local_tab = ui.button('💻 ローカル', on_click=lambda: self._switch_folder_tab('local')).style(
                                'flex: 1; background: #2563eb; color: white; border: none; padding: 8px; border-radius: 0; cursor: pointer; font-weight: 600;'
                            )
                            self.server_tab = ui.button('🖥️ サーバー', on_click=lambda: self._switch_folder_tab('server')).style(
                                'flex: 1; background: transparent; color: #6b7280; border: none; padding: 8px; border-radius: 0; cursor: pointer; font-weight: 400;'
                            )
                        
                        # ローカルフォルダタブ
                        with ui.element('div').props('id="local-folder-content"').style('flex: 1; display: flex; flex-direction: column;'):
                            with ui.element('div').style(
                                'flex: 1; border: 2px dashed #d1d5db; border-radius: 8px; '
                                'background: #f9fafb; display: flex; flex-direction: column; '
                                'align-items: center; justify-content: center; text-align: center;'
                            ):
                                ui.icon('folder', size='2em', color='grey-5').style('margin-bottom: 12px;')
                                ui.label('フォルダを選択してアップロード').style('font-size: 16px; margin-bottom: 6px; font-weight: 500;')
                                ui.label('ブラウザのフォルダ選択で即座に開始').style('color: #6b7280; font-size: 12px;')
                            
                            # 隠しフォルダ入力
                            self.folder_input = ui.element('input').props(
                                'type="file" webkitdirectory directory multiple style="display: none;"'
                            )
                        
                        # サーバーフォルダタブ
                        with ui.element('div').props('id="server-folder-content"').style('flex: 1; display: none; flex-direction: column; gap: 8px;'):
                            # フォルダパス入力
                            with ui.element('div').style('display: flex; align-items: center; gap: 6px;'):
                                self.folder_path_input = ui.input(
                                    value=self.folder_path,
                                    placeholder='/workspace/ignored/input_files'
                                ).style('flex: 1;').props('outlined dense')
                                
                                browse_btn = ui.button('📂', on_click=self._browse_folder).style(
                                    'min-width: 40px; padding: 8px;'
                                ).props('color=grey-7 flat')
                            
                            # オプション
                            self.subfolder_checkbox = ui.checkbox(
                                'サブフォルダも含める',
                                value=self.include_subfolders
                            ).style('margin: 4px 0;')
                            
                            # 説明
                            with ui.element('div').style('background: #f3f4f6; padding: 8px; border-radius: 4px; flex: 1;'):
                                ui.label('📂 サーバーフォルダアップロード').style('font-weight: 600; font-size: 14px; margin-bottom: 4px;')
                                ui.label('• サーバー上のフォルダパスを指定').style('font-size: 12px; color: #4b5563;')
                                ui.label('• 対応ファイルを自動検出・処理').style('font-size: 12px; color: #4b5563;')
                                ui.label('• 重複ファイルは自動スキップ').style('font-size: 12px; color: #4b5563;')
    
    def _create_result_pane(self):
        """右: 結果表示ペイン"""
        with CommonPanel(
            title="アップロード結果",
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
                    # 管理画面へボタン
                    manage_btn = BaseButton.create_type_b(
                        "📁 ファイル管理",
                        on_click=lambda: ui.navigate.to('/files')
                    )
            
            # パネル内容
            panel.content_element.style('padding: 0; height: 100%;')
            
            with panel.content_element:
                with ui.element('div').style('padding: 4px; height: 100%; box-sizing: border-box;'):
                    # プログレスエリア（初期非表示）
                    with ui.element('div').props('id="upload-progress"').style('display: none; margin-bottom: 16px;'):
                        with ui.element('div').style('background: #f3f4f6; padding: 16px; border-radius: 8px;'):
                            with ui.element('div').style('display: flex; justify-content: space-between; margin-bottom: 12px;'):
                                ui.label('⏳ アップロード中...').style('font-weight: 600; font-size: 16px;')
                                self.progress_stats = ui.label('0 / 0').style('color: #6b7280;')
                            
                            # プログレスバー
                            with ui.element('div').style(
                                'width: 100%; height: 8px; background: #e5e7eb; border-radius: 4px; overflow: hidden;'
                            ):
                                self.progress_bar = ui.element('div').style(
                                    'height: 100%; background: #3b82f6; width: 0%; transition: width 0.3s ease;'
                                )
                            
                            self.progress_text = ui.label('0%').style('text-align: center; margin-top: 8px; font-weight: 600;')
                    
                    # 結果表示エリア
                    with ui.element('div').props('id="upload-results"').style('flex: 1; overflow-y: auto;'):
                        with ui.element('div').style(
                            'height: 100%; display: flex; align-items: center; justify-content: center; '
                            'color: #9ca3af; text-align: center;'
                        ):
                            with ui.element('div'):
                                ui.icon('cloud_upload', size='4em').style('margin-bottom: 16px; opacity: 0.5;')
                                ui.label('ファイルまたはフォルダをアップロードすると').style('font-size: 16px; margin-bottom: 4px;')
                                ui.label('ここに結果が表示されます').style('font-size: 16px;')
    
    # イベントハンドラー
    def _open_file_dialog(self):
        """ファイル選択ダイアログを開く"""
        ui.run_javascript('document.querySelector("input[type=file]").click()')
    
    def _clear_files(self):
        """選択ファイルをクリア"""
        ui.notify('ファイル選択をクリアしました')
    
    def _upload_folder(self):
        """フォルダアップロード実行"""
        ui.notify('フォルダアップロードを開始します')
    
    def _reset_folder(self):
        """フォルダ設定リセット"""
        self.folder_path_input.value = "/workspace/ignored/input_files"
        self.subfolder_checkbox.value = False
        ui.notify('フォルダ設定をリセットしました')
    
    def _switch_folder_tab(self, tab_name):
        """フォルダタブ切り替え"""
        if tab_name == 'local':
            self.local_tab.style('background: #2563eb; color: white; font-weight: 600;')
            self.server_tab.style('background: transparent; color: #6b7280; font-weight: 400;')
            ui.run_javascript('''
                document.getElementById('local-folder-content').style.display = 'flex';
                document.getElementById('server-folder-content').style.display = 'none';
            ''')
        else:
            self.local_tab.style('background: transparent; color: #6b7280; font-weight: 400;')
            self.server_tab.style('background: #2563eb; color: white; font-weight: 600;')
            ui.run_javascript('''
                document.getElementById('local-folder-content').style.display = 'none';
                document.getElementById('server-folder-content').style.display = 'flex';
            ''')
    
    def _browse_folder(self):
        """フォルダブラウザを開く"""
        ui.notify('フォルダブラウザ機能（将来実装予定）')