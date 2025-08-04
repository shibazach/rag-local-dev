"""
OCR調整ページ - new/系準拠実装
"""
from nicegui import ui
from ui.components.layout import RAGHeader, RAGFooter, MainContentArea

class OCRAdjustmentPage:
    """OCR調整ページクラス - new/系準拠"""
    
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
            # メインコンテンツ（3分割：ファイル選択、画像プレビュー、OCR結果）
            with ui.element('div').style('display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px;height:100%;padding:8px;'):
                # 左: ファイル選択
                with ui.card().style('height:100%;'):
                    with ui.card_section():
                        ui.label('📁 ファイル選択').style('font-size:16px;font-weight:600;margin-bottom:16px;')
                        ui.select(['sample_document.pdf'], label='対象ファイル').props('outlined dense').style('width:100%;margin-bottom:16px;')
                        ui.select(['Tesseract', 'PaddleOCR'], value='Tesseract', label='OCRエンジン').props('outlined dense').style('width:100%;margin-bottom:16px;')
                        ui.select(['日本語', '英語', '中国語'], value='日本語', label='言語').props('outlined dense').style('width:100%;margin-bottom:16px;')
                        ui.button('🔄 OCR実行', on_click=lambda: ui.notify('OCR実行')).props('color=primary').style('width:100%;')
            
                # 中央: 画像プレビュー  
                with ui.card().style('height:100%;'):
                    with ui.card_section():
                        ui.label('🖼️ 画像プレビュー').style('font-size:16px;font-weight:600;margin-bottom:16px;')
                        with ui.element('div').style('border:1px solid #ddd;height:400px;background:#f8f9fa;display:flex;align-items:center;justify-content:center;'):
                            ui.label('画像プレビューエリア').style('color:#666;')
                
                # 右: OCR結果編集
                with ui.card().style('height:100%;'):
                    with ui.card_section():
                        ui.label('📝 OCR結果').style('font-size:16px;font-weight:600;margin-bottom:16px;')
                        with ui.row().classes('gap-2 w-full'):
                            ui.label('元テキスト').style('font-weight:600;flex:1;text-align:center;')
                            ui.label('修正後').style('font-weight:600;flex:1;text-align:center;')
                        
                        with ui.row().classes('gap-2 w-full').style('height:300px;'):
                            ui.textarea(placeholder='OCR結果がここに表示されます').props('outlined').style('flex:1;height:100%;')
                            ui.textarea(placeholder='修正内容を入力してください').props('outlined').style('flex:1;height:100%;')
                        
                        with ui.row().classes('justify-end gap-2').style('margin-top:16px;'):
                            ui.button('🔄 再実行', on_click=lambda: ui.notify('再実行')).props('color=secondary')
                            ui.button('💾 保存', on_click=lambda: ui.notify('保存完了')).props('color=positive')
        
        # 共通フッター
        RAGFooter()