"""
ファイル管理ページ - new/系準拠実装
"""
from nicegui import ui
from ui.components.layout import RAGHeader, RAGFooter, MainContentArea

class FilesPage:
    """ファイル管理ページクラス - new/系準拠"""
    
    def render(self):
        """ページレンダリング"""
        from main import SimpleAuth
        
        if not SimpleAuth.is_authenticated():
            ui.navigate.to('/login')
            return
        
        # 共通ヘッダー
        RAGHeader(show_site_name=True, current_page="files")
        
        # 全ページ共通メインコンテンツエリア（オーバーフロー禁止・パネル内スクロール）
        with MainContentArea(allow_overflow=False):
            # ページ内容（余白調整不要）
            with ui.element('div').style('padding:8px;display:flex;flex-direction:column;height:100%;'):
                # 検索・フィルター
                with ui.card().style('margin-bottom:8px;'):
                    with ui.card_section():
                        with ui.row().classes('gap-4 w-full items-center'):
                            ui.input(placeholder='ファイル名で検索...').props('outlined dense').style('flex:1;')
                            ui.select(['すべて', 'PDF', 'Word', 'Excel', 'テキスト'], value='すべて', label='種類').props('outlined dense').style('width:150px;')
                            ui.select(['すべて', '処理完了', '処理中', 'エラー'], value='すべて', label='ステータス').props('outlined dense').style('width:150px;')
                            ui.button('🔍 検索', on_click=lambda: ui.notify('検索実行')).props('color=primary')
                
                # ファイル一覧
                with ui.card().style('flex:1;'):
                    with ui.card_section().style('padding:0;height:100%;'):
                        # テーブルヘッダー
                        with ui.element('div').style('background:#f8f9fa;border-bottom:1px solid #ddd;padding:8px;'):
                            with ui.row().classes('items-center w-full'):
                                ui.checkbox().style('width:40px;')
                                ui.label('ファイル名').style('flex:1;font-weight:600;')
                                ui.label('サイズ').style('width:100px;font-weight:600;text-align:center;')
                                ui.label('更新日').style('width:120px;font-weight:600;text-align:center;')
                                ui.label('ステータス').style('width:100px;font-weight:600;text-align:center;')
                                ui.label('操作').style('width:120px;font-weight:600;text-align:center;')
                        
                        # ファイル一覧（実際のデータは削除）
                        with ui.element('div').style('flex:1;padding:20px;text-align:center;color:#666;'):
                            ui.label('ファイル一覧がここに表示されます')
        
        # 共通フッター
        RAGFooter()