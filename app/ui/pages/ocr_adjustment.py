"""
OCR調整ページ - new/系準拠実装（4ペイン構成）
"""
from nicegui import ui
from app.ui.components.layout import RAGHeader, RAGFooter, MainContentArea
from app.ui.components.elements import CommonPanel
from app.ui.components.common.layout import CommonSplitter
from app.ui.components.base.button import BaseButton

class OCRAdjustmentPage:
    """OCR調整ページクラス - new/系準拠4ペイン構成"""
    
    def __init__(self):
        """初期化"""
        self.selected_file = None
        self.selected_engine = None  # 空文字列ではなくNone
        self.selected_page = 1
        self.use_correction = True
        self.ocr_results = []
        self.engine_parameters = {}
        self.available_engines = [
            'OCRMyPDF', 'Tesseract', 'PaddleOCR', 'EasyOCR'
        ]
    
    def render(self):
        """ページレンダリング"""
        from app.utils.auth import SimpleAuth
        
        if not SimpleAuth.is_authenticated():
            ui.navigate.to('/login')
            return
        
        # 共通ヘッダー
        RAGHeader(show_site_name=True, current_page="ocr-adjustment")
        
        # 全ページ共通メインコンテンツエリア
        with MainContentArea():
            # 共通スプリッタースタイル・JS追加
            CommonSplitter.add_splitter_styles()
            CommonSplitter.add_splitter_javascript()
            
            self._create_main_layout()
        
        # 共通フッター
        RAGFooter()
    
    def _create_main_layout(self):
        """メインレイアウト作成（4ペイン構成）"""
        with ui.element('div').style(
            'width: 100%; height: 100%; '
            'display: flex; margin: 0; padding: 4px; gap: 4px;'
        ).props('id="ocr-main-container"'):
            
            # 左ペイン：OCR設定・結果（50%幅）
            with ui.element('div').style(
                'width: 50%; height: 100%; '
                'display: flex; flex-direction: column; '
                'margin: 0; padding: 0; gap: 4px;'
            ).props('id="ocr-left-pane"'):
                self._create_ocr_settings_pane()
                CommonSplitter.create_horizontal(splitter_id="ocr-hsplitter", height="4px")
                self._create_ocr_results_pane()
            
            # 縦スプリッター
            CommonSplitter.create_vertical(splitter_id="ocr-vsplitter", width="4px")
            
            # 右ペイン：詳細設定・PDF（50%幅）
            with ui.element('div').style(
                'width: 50%; height: 100%; '
                'display: flex; flex-direction: column; '
                'margin: 0; padding: 0; gap: 4px;'
            ).props('id="ocr-right-pane"'):
                self._create_engine_details_pane()
                CommonSplitter.create_horizontal(splitter_id="ocr-hsplitter-right", height="4px")
                self._create_pdf_preview_pane()
    
    def _create_ocr_settings_pane(self):
        """左上: OCR設定ペイン"""
        with CommonPanel(
            title="⚙️ OCR設定",
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
                    file_btn = BaseButton.create_type_a(
                        "📁 ファイル選択",
                        on_click=self._open_file_dialog
                    )
                    
                    # OCR実行ボタン
                    ocr_btn = BaseButton.create_type_a(
                        "🚀 OCR実行",
                        on_click=self._start_ocr
                    )
            
            # パネル内容
            panel.content_element.style('padding: 0; height: 100%;')
            
            with panel.content_element:
                with ui.element('div').style('padding: 4px; height: 100%; box-sizing: border-box;'):
                    with ui.element('div').style('display: flex; flex-direction: column; gap: 12px; height: 100%;'):
                        
                        # 選択ファイル情報
                        with ui.element('div').style('background: #f3f4f6; padding: 8px; border-radius: 4px;'):
                            with ui.element('div').style('display: flex; align-items: center; gap: 8px;'):
                                ui.label('ファイル:').style('font-weight: 600; min-width: 60px; font-size: 12px;')
                                self.file_info_label = ui.label('未選択').style('color: #6b7280; font-size: 12px;')
                        
                        # OCRエンジン選択
                        with ui.element('div').style('display: flex; align-items: center; gap: 8px;'):
                            ui.label('🔧 OCRエンジン').style('min-width: 100px; font-weight: 500; font-size: 13px;')
                            self.engine_select = ui.select(
                                options=self.available_engines,
                                with_input=True,
                                on_change=self._on_engine_change
                            ).style('flex: 1;').props('outlined dense')
                        
                        # ページ設定と誤字修正（横並び）
                        with ui.element('div').style('display: flex; align-items: center; gap: 16px;'):
                            # ページ設定
                            with ui.element('div').style('display: flex; align-items: center; gap: 6px;'):
                                ui.label('📄 処理ページ').style('font-weight: 500; font-size: 13px;')
                                self.page_input = ui.number(
                                    value=self.selected_page,
                                    min=0,
                                    step=1,
                                    on_change=self._on_page_change
                                ).style('width: 80px;').props('outlined dense')
                                ui.label('0=全て').style('font-size: 11px; color: #6b7280;')
                            
                            # 誤字修正チェックボックス
                            with ui.element('div').style('display: flex; align-items: center; gap: 6px;'):
                                self.correction_checkbox = ui.checkbox(
                                    '🔤 誤字修正',
                                    value=self.use_correction,
                                    on_change=self._on_correction_change
                                ).style('font-size: 13px;')
    
    def _create_engine_details_pane(self):
        """右上: エンジン詳細設定ペイン"""
        with CommonPanel(
            title="🔧 詳細設定",
            gradient="#334155",
            header_color="white",
            width="100%",
            height="50%"
        ) as panel:
            
            # ヘッダーにボタンを追加
            with panel.header_element:
                with ui.element('div').style('display: flex; gap: 6px; margin-right: 8px;'):
                    load_button = BaseButton.create_type_b('📂 読込', on_click=self._load_settings)
                    save_button = BaseButton.create_type_b('💾 保存', on_click=self._save_settings)
            
            # パネル内容
            panel.content_element.style('padding: 0; height: 100%;')
            
            with panel.content_element:
                self.engine_details_container = ui.element('div').style('padding: 4px; height: 100%; box-sizing: border-box;')
                
                with self.engine_details_container:
                    # 初期状態：空の説明
                    with ui.element('div').style(
                        'height: 100%; display: flex; align-items: center; justify-content: center; '
                        'color: #9ca3af; text-align: center;'
                    ):
                        with ui.element('div'):
                            ui.icon('settings', size='3em').style('margin-bottom: 16px; opacity: 0.5;')
                            ui.label('OCRエンジンを選択すると').style('font-size: 16px; margin-bottom: 4px;')
                            ui.label('詳細設定が表示されます').style('font-size: 16px;')
    
    def _create_ocr_results_pane(self):
        """左下: OCR結果ペイン"""
        with CommonPanel(
            title="📋 OCR結果",
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
                    # エクスポートボタン
                    export_btn = BaseButton.create_type_b(
                        "📄 エクスポート",
                        on_click=self._export_results
                    )
                    
                    # クリアボタン
                    clear_btn = BaseButton.create_type_b(
                        "🗑️ クリア",
                        on_click=self._clear_results
                    )
            
            # パネル内容
            panel.content_element.style('padding: 0; height: 100%;')
            
            with panel.content_element:
                with ui.element('div').style('padding: 4px; height: 100%; box-sizing: border-box;'):
                    # OCR結果表示エリア
                    self.results_container = ui.element('div').style('height: 100%; overflow-y: auto;')
                    
                    with self.results_container:
                        # 初期状態：空の説明
                        with ui.element('div').style(
                            'height: 100%; display: flex; align-items: center; justify-content: center; '
                            'color: #9ca3af; text-align: center;'
                        ):
                            with ui.element('div'):
                                ui.icon('text_snippet', size='3em').style('margin-bottom: 16px; opacity: 0.5;')
                                ui.label('OCR実行すると').style('font-size: 16px; margin-bottom: 4px;')
                                ui.label('結果がここに表示されます').style('font-size: 16px;')
    
    def _create_pdf_preview_pane(self):
        """右下: PDFプレビューペイン（filesページと完全同構造）"""
        # ヘッダーなしの直接コンテンツ表示
        with ui.element('div').style(
            'width: 100%; height: 50%; '
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
    
    # イベントハンドラー
    def _open_file_dialog(self):
        """ファイル選択ダイアログを開く"""
        ui.notify('ファイル選択ダイアログ（将来実装予定）')
        # 仮の選択
        self.selected_file = "sample_document.pdf"
        self.file_info_label.text = self.selected_file
    
    def _start_ocr(self):
        """OCR実行"""
        if not self.selected_file:
            ui.notify('ファイルを選択してください', type='warning')
            return
        if not self.selected_engine:
            ui.notify('OCRエンジンを選択してください', type='warning')
            return
        
        ui.notify(f'OCR実行開始: {self.selected_engine}')
        
        # OCR処理の実装
        # TODO: 実際のOCR処理APIを呼び出す
        # 現時点では仮実装として、サンプル結果を表示
        self.ocr_results = [
            {
                'page': 1,
                'text': 'これはOCRで抽出されたサンプルテキストです。\n実際の実装では、選択されたエンジンを使用してPDFからテキストを抽出します。',
                'confidence': 0.95
            }
        ]
        
        # 結果を表示
        self._display_ocr_results()
    
    def _on_engine_change(self, e):
        """エンジン選択変更時"""
        self.selected_engine = e.value
        self._update_engine_details()
    
    def _on_page_change(self, e):
        """ページ設定変更時"""
        self.selected_page = e.value
    
    def _on_correction_change(self, e):
        """誤字修正設定変更時"""
        self.use_correction = e.value
    
    def _update_engine_details(self):
        """エンジン詳細設定を更新"""
        # エンジンごとの詳細設定を動的に生成（将来実装）
        ui.notify(f'{self.selected_engine}の詳細設定を表示')
    
    def _export_results(self):
        """OCR結果をエクスポート"""
        ui.notify('OCR結果をエクスポートします')
    
    def _clear_results(self):
        """OCR結果をクリア"""
        ui.notify('OCR結果をクリアしました')
    
    def _save_settings(self):
        """OCR設定を保存"""
        import json
        from pathlib import Path
        
        # 設定保存ディレクトリ
        settings_dir = Path('/workspace/config/ocr_settings')
        settings_dir.mkdir(parents=True, exist_ok=True)
        
        # 現在の設定を取得
        settings = {
            'selected_engine': self.selected_engine,
            'selected_page': self.selected_page,
            'use_correction': self.use_correction,
            'engine_parameters': self.engine_parameters
        }
        
        # JSON形式で保存
        settings_file = settings_dir / 'ocr_settings.json'
        with open(settings_file, 'w', encoding='utf-8') as f:
            json.dump(settings, f, ensure_ascii=False, indent=2)
        
        ui.notify('設定を保存しました', type='positive')
    
    def _load_settings(self):
        """OCR設定を読み込み"""
        import json
        from pathlib import Path
        
        settings_file = Path('/workspace/config/ocr_settings/ocr_settings.json')
        
        if not settings_file.exists():
            ui.notify('保存された設定がありません', type='warning')
            return
        
        try:
            with open(settings_file, 'r', encoding='utf-8') as f:
                settings = json.load(f)
            
            # 設定を適用
            if 'selected_engine' in settings:
                self.selected_engine = settings['selected_engine']
            if 'selected_page' in settings:
                self.selected_page = settings['selected_page']
            if 'use_correction' in settings:
                self.use_correction = settings['use_correction']
            if 'engine_parameters' in settings:
                self.engine_parameters = settings['engine_parameters']
            
            ui.notify('設定を読み込みました', type='positive')
            
            # UIを更新（エンジン詳細設定の再描画など）
            self._update_engine_details()
            
        except Exception as e:
            ui.notify(f'設定の読み込みに失敗しました: {str(e)}', type='negative')
    
    def _open_file_dialog(self):
        """ファイル選択ダイアログを開く"""
        # DBからPDFファイル一覧を取得
        result = get_file_list(limit=1000, offset=0)
        
        if not result or 'files' not in result:
            ui.notify('ファイルが見つかりません', type='warning')
            return
        
        # PDFファイルのみフィルタリング
        pdf_files = [
            f for f in result['files'] 
            if f.get('content_type') == 'application/pdf'
        ]
        
        if not pdf_files:
            ui.notify('PDFファイルが見つかりません', type='warning')
            return
        
        # ファイル選択ダイアログを表示
        with ui.dialog() as dialog, ui.card():
            ui.label('PDFファイルを選択').style('font-size: 18px; font-weight: bold; margin-bottom: 16px;')
            
            # ファイルリスト
            file_select = ui.select(
                options=[{'label': f['filename'], 'value': f['file_id']} for f in pdf_files],
                label='ファイル',
                value=pdf_files[0]['file_id'] if pdf_files else None
            ).style('width: 400px;')
            
            # ボタン
            with ui.row():
                ui.button('選択', on_click=lambda: self._select_file(file_select.value, dialog))
                ui.button('キャンセル', on_click=dialog.close)
        
        dialog.open()
    
    def _select_file(self, file_id, dialog):
        """ファイルを選択"""
        if not file_id:
            ui.notify('ファイルを選択してください', type='warning')
            return
        
        self.selected_file = file_id
        ui.notify('ファイルを選択しました', type='positive')
        dialog.close()
        
        # ファイル情報を表示（必要に応じて）
        # self._display_file_info()
    
    def _display_ocr_results(self):
        """OCR結果を表示"""
        if not self.ocr_results:
            return
        
        # 結果コンテナをクリア
        if hasattr(self, 'results_container'):
            self.results_container.clear()
            
            with self.results_container:
                # 結果サマリー
                ui.label(f'OCR結果: {len(self.ocr_results)}ページ').style(
                    'font-size: 16px; font-weight: bold; margin-bottom: 12px;'
                )
                
                # 各ページの結果を表示
                for result in self.ocr_results:
                    with ui.card().style('margin-bottom: 8px; padding: 12px;'):
                        ui.label(f'ページ {result["page"]} (信頼度: {result.get("confidence", 0):.0%})').style(
                            'font-size: 14px; font-weight: 600; margin-bottom: 8px;'
                        )
                        ui.label(result['text']).style('font-size: 12px; white-space: pre-wrap;')