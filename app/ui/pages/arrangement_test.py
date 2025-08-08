"""配置テスト練習フィールド - タブ形式（分離版）"""

from nicegui import ui
from app.ui.components.layout import RAGHeader, RAGFooter, MainContentArea

class ArrangementTestPage:
    def __init__(self, current_page: str = "arrangement-test"):
        """配置テスト練習フィールドの初期化"""
        self.current_page = current_page
        self.render()

    def render(self):
        """ページレンダリング"""
        RAGHeader(current_page="arrangement-test")
        
        with MainContentArea():
            self._create_tab_interface()
        
        RAGFooter()

    def _create_tab_interface(self):
        """タブインターフェース作成 - シンプル版"""
        with ui.element('div').style(
            'width: 100%; height: 100%; '
            'display: flex; flex-direction: column; '
            'margin: 0; padding: 0; '
        ):
            # NiceGUI標準のタブ機能を使用
            with ui.tabs().classes('w-full') as tabs:
                tab1 = ui.tab('レイアウト')
                tab2 = ui.tab('コンポーネント')
                tab3 = ui.tab('練習エリア')
                tab4 = ui.tab('統合展示')
                tab5 = ui.tab('ui.table')
            
            # タブパネル
            with ui.tab_panels(tabs, value=tab1).classes('w-full flex-grow'):
                with ui.tab_panel(tab1):
                    self._create_tab1_content()
                
                with ui.tab_panel(tab2):
                    ui.label('タブ2のコンテンツ')
                
                with ui.tab_panel(tab3):
                    ui.label('タブ3のコンテンツ')
                
                with ui.tab_panel(tab4):
                    ui.label('タブ4のコンテンツ')
                
                with ui.tab_panel(tab5):
                    self._create_tab5_content()
    
    def _create_tab1_content(self):
        """タブ1: 4分割レイアウト"""
        with ui.element('div').style(
            'display: grid; '
            'grid-template-columns: 1fr 1fr; '
            'grid-template-rows: 1fr 1fr; '
            'gap: 8px; '
            'height: 100%; '
            'padding: 8px;'
        ):
            # 左上
            with ui.card().classes('col-span-1 row-span-1'):
                ui.label('左上パネル').style('font-weight: bold;')
                ui.button('ボタン1', on_click=lambda: ui.notify('左上クリック'))
            
            # 右上
            with ui.card().classes('col-span-1 row-span-1'):
                ui.label('右上パネル').style('font-weight: bold;')
                ui.input('テキスト入力').style('width: 100%;')
            
            # 左下
            with ui.card().classes('col-span-1 row-span-1'):
                ui.label('左下パネル').style('font-weight: bold;')
                ui.select(['オプション1', 'オプション2', 'オプション3'], value='オプション1').style('width: 100%;')
            
            # 右下
            with ui.card().classes('col-span-1 row-span-1'):
                ui.label('右下パネル').style('font-weight: bold;')
                ui.slider(min=0, max=100, value=50).style('width: 100%;')
    
    def _create_tab5_content(self):
        """タブ5: ui.table実装例"""
        with ui.element('div').style('padding: 16px; height: 100%;'):
            ui.label('📊 ファイル一覧（ui.table版）').style('font-size: 20px; font-weight: bold; margin-bottom: 16px;')
            
            # ダミーデータ
            rows = [
                {'id': 1, 'filename': 'report_2025.pdf', 'size': '2.5MB', 'status': '処理完了', 'created_at': '2025-01-07'},
                {'id': 2, 'filename': 'data_analysis.xlsx', 'size': '1.2MB', 'status': '処理中', 'created_at': '2025-01-06'},
                {'id': 3, 'filename': 'presentation.pptx', 'size': '5.8MB', 'status': '未処理', 'created_at': '2025-01-05'},
            ]
            
            columns = [
                {'name': 'filename', 'label': 'ファイル名', 'field': 'filename', 'sortable': True, 'align': 'left'},
                {'name': 'size', 'label': 'サイズ', 'field': 'size', 'sortable': True, 'align': 'center'},
                {'name': 'status', 'label': 'ステータス', 'field': 'status', 'sortable': True, 'align': 'center'},
                {'name': 'created_at', 'label': '作成日時', 'field': 'created_at', 'sortable': True, 'align': 'center'},
            ]
            
            # ui.table作成
            table = ui.table(
                columns=columns,
                rows=rows,
                row_key='id',
                pagination={'rowsPerPage': 10}
            ).classes('w-full')
            
            # テーブルスタイルをカスタマイズ
            table.style('border: 1px solid #e5e7eb;')