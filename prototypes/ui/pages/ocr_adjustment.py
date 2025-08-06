"""
OCR調整ページ - new/系準拠実装（4ペイン構成）
"""
from nicegui import ui
from ui.components.layout import RAGHeader, RAGFooter, MainContentArea
from ui.components.elements import CommonPanel
from ui.components.common.layout import CommonSplitter
from ui.components.base.button import BaseButton

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
        from main import SimpleAuth
        
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
            gradient="#f8f9fa",
            header_color="#374151",
            width="100%",
            height="50%"
        ) as panel:
            
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
        # OCR処理の実装（将来）
    
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