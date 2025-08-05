"""配置テスト練習フィールド - タブ形式（分離版）"""

from nicegui import ui
from ui.components.layout import RAGHeader, RAGFooter, MainContentArea
from ui.pages.arrangement_test_tab_a import ArrangementTestTabA
from ui.pages.arrangement_test_tab_b import ArrangementTestTabB
from ui.pages.arrangement_test_tab_c import ArrangementTestTabC
from ui.pages.arrangement_test_tab_d import ArrangementTestTabD
from ui.pages.arrangement_test_tab_e import ArrangementTestTabE

class ArrangementTestPage:
    def __init__(self, current_page: str = "arrangement-test"):
        """配置テスト練習フィールドの初期化"""
        self.current_page = current_page
        self._create_page()

    def _create_page(self):
        """ページ作成"""
        RAGHeader(current_page="arrangement-test")
        
        with MainContentArea():
            self._create_tab_interface()
        
        RAGFooter()

    def _create_tab_interface(self):
        """タブインターフェース作成 - 完全paddingゼロ"""
        with ui.element('div').style(
            'width: 100%; height: 100%; '
            'display: flex; flex-direction: column; '
            'margin: 0; padding: 0; '
            'overflow: hidden;'
        ):
            # タブヘッダー（32px固定）
            with ui.element('div').style(
                'width: 100%; height: 32px; '
                'background: #ffffff; '
                'border-bottom: 1px solid #e5e7eb; '
                'display: flex; margin: 0; padding: 0; '
                'flex-shrink: 0;'
            ):
                self._tab_button('tab1', 'A', True)   # デフォルト選択
                self._tab_button('tab2', 'B', False)
                self._tab_button('tab3', 'C', False)
                self._tab_button('tab4', 'D', False)
                self._tab_button('tab5', 'E', False)
            
            # タブコンテンツエリア
            with ui.element('div').style(
                'flex: 1; margin: 0; padding: 0; '
                'overflow: hidden; background: #f8fafc;'
            ):
                # タブ1: 4ペイン分割
                with ui.element('div').style(
                    'display: block; height: 100%; '
                    'margin: 0; padding: 0;'
                ).props('id="tab1-content"'):
                    ArrangementTestTabA().render()
                
                # タブ2: NiceGUIコンポーネント全サンプル
                with ui.element('div').style(
                    'display: none; height: 100%; '
                    'margin: 0; padding: 0;'
                ).props('id="tab2-content"'):
                    ArrangementTestTabB().render()
                
                # タブ3: 空の練習エリア
                with ui.element('div').style(
                    'display: none; height: 100%; '
                    'margin: 0; padding: 0;'
                ).props('id="tab3-content"'):
                    ArrangementTestTabC().render()
                
                # タブ4: 全共通コンポーネント統合展示
                with ui.element('div').style(
                    'display: none; height: 100%; '
                    'margin: 0; padding: 0;'
                ).props('id="tab4-content"'):
                    ArrangementTestTabD().render()
                
                # タブ5: 新機能実験エリア
                with ui.element('div').style(
                    'display: none; height: 100%; '
                    'margin: 0; padding: 0;'
                ).props('id="tab5-content"'):
                    ArrangementTestTabE().render()
        
        # タブ切り替えJavaScript
        self._add_tab_switching_js()

    def _tab_button(self, tab_id, label, is_active):
        """タブボタン作成"""
        if is_active:
            style = (
                'padding: 6px 16px; cursor: pointer; '
                'border-right: 1px solid #e5e7eb; '
                'font-weight: 500; font-size: 14px; '
                'transition: 0.2s; '
                'background: #3b82f6; color: white;'
            )
        else:
            style = (
                'padding: 6px 16px; cursor: pointer; '
                'border-right: 1px solid #e5e7eb; '
                'font-weight: 500; font-size: 14px; '
                'transition: 0.2s; '
                'background: #f3f4f6; color: #6b7280;'
            )
        
        with ui.element('div').style(style).props(
            f'id="tab-{tab_id}" onclick="switchTab(\'{tab_id}\')"'
        ):
            ui.label(label)

    def _add_tab_switching_js(self):
        """タブ切り替えJavaScript"""
        ui.add_head_html('''
        <script>
        function switchTab(tabId) {
            const allTabs = ['tab1-content', 'tab2-content', 'tab3-content', 'tab4-content', 'tab5-content'];
            allTabs.forEach(function(id) {
                const element = document.getElementById(id);
                if (element) {
                    element.style.display = 'none';
                }
            });
            
            const targetTab = document.getElementById(tabId + '-content');
            if (targetTab) {
                targetTab.style.display = 'block';
            }
            
            const allTabButtons = ['tab-tab1', 'tab-tab2', 'tab-tab3', 'tab-tab4', 'tab-tab5'];
            allTabButtons.forEach(function(id) {
                const button = document.getElementById(id);
                if (button) {
                    button.style.background = '#f3f4f6';
                    button.style.color = '#6b7280';
                }
            });
            
            const activeButton = document.getElementById('tab-' + tabId);
            if (activeButton) {
                activeButton.style.background = '#3b82f6';
                activeButton.style.color = 'white';
            }
            
            console.log('Switched to tab: ' + tabId);
        }
        </script>
        ''')