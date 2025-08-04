"""
アップロードページ - new/系準拠実装
"""
from nicegui import ui
from ui.components.layout import RAGHeader, RAGFooter, MainContentArea

class UploadPage:
    """アップロードページクラス - new/系準拠"""
    
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
            with ui.element('div').style('padding:8px;display:flex;justify-content:center;align-items:center;height:100%;'):
                with ui.card().style('width:600px;max-width:90%;'):
                    with ui.card_section():
                        ui.label('📤 ファイルアップロード').style('font-size:24px;font-weight:600;text-align:center;margin-bottom:20px;')
                    
                    with ui.card_section():
                        # ドラッグ&ドロップエリア
                        with ui.element('div').style('''
                        border: 2px dashed #ddd;
                        border-radius: 8px;
                        padding: 40px 20px;
                        text-align: center;
                        background: #fafafa;
                        margin-bottom: 20px;
                    '''):
                            ui.icon('cloud_upload', size='3em', color='grey-5').style('margin-bottom:16px;')
                            ui.label('ファイルをドラッグ&ドロップ').style('font-size:18px;margin-bottom:8px;')
                            ui.label('または').style('color:#666;margin-bottom:16px;')
                            ui.button('📁 ファイルを選択', on_click=lambda: ui.notify('ファイル選択')).props('color=primary')
                    
                        # 対応ファイル形式
                        ui.label('対応形式').style('font-weight:600;margin-bottom:8px;')
                        ui.label('PDF, Word, Excel, PowerPoint, テキスト, CSV, JSON, EML').style('color:#666;font-size:14px;margin-bottom:20px;')
                        
                        # アップロード設定
                        with ui.expansion('⚙️ アップロード設定', icon='settings'):
                            ui.checkbox('アップロード後に自動処理を開始', value=True).style('margin-bottom:8px;')
                            ui.checkbox('重複ファイルをスキップ', value=True).style('margin-bottom:8px;')
                            ui.select(['低', '標準', '高'], value='標準', label='処理優先度').props('outlined dense').style('width:200px;')
        
        # 共通フッター
        RAGFooter()