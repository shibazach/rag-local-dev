"""
チャットページ - UI設計ポリシー準拠実装
"""
from nicegui import ui
from ui.components.layout import RAGHeader, RAGFooter

class ChatPage:
    """チャットページクラス - UI設計ポリシー準拠"""
    
    def render(self):
        """ページレンダリング"""
        from main import SimpleAuth, ChatState
        
        if not SimpleAuth.is_authenticated():
            ui.navigate.to('/login')
            return
        
        layout_pattern = getattr(ChatState, 'current_pattern', 'no-preview')
        
        # UI設計ポリシー準拠実装
        self._render_policy_compliant_chat(layout_pattern)
    
    def _render_policy_compliant_chat(self, layout_pattern: str):
        """UI設計ポリシー準拠のチャット実装"""
        # 共通ヘッダー（チャットページ用 - サイト名付き）
        RAGHeader(show_site_name=True, current_page="chat")
        
        # チャット用JavaScript（必要最小限）
        self._add_minimal_scripts(layout_pattern)
        
        # メインレイアウト（NiceGUIコンポーネント使用）
        with ui.element('div').style('margin-top:48px;height:calc(100vh - 95px);padding:8px;'):
            # 上下分割レイアウト
            with ui.splitter(value=25, horizontal=True).style('height:100%;') as main_splitter:
                with main_splitter.before:
                    self._create_settings_panel(layout_pattern)
                
                with main_splitter.after:
                    # 左右分割（パターンに応じて表示制御）
                    if layout_pattern in ['pattern1', 'pattern2']:
                        with ui.splitter(value=60).style('height:100%;') as sub_splitter:
                            with sub_splitter.before:
                                self._create_results_panel()
                            with sub_splitter.after:
                                self._create_pdf_panel()
                    else:
                        self._create_results_panel()
        
        # 共通フッター
        RAGFooter()
    
    def _add_minimal_scripts(self, layout_pattern: str):
        """最小限のJavaScript追加"""
        ui.add_body_html(f'''
        <script>
        function switchPattern(pattern) {{
            fetch('/chat/switch-pattern', {{
                method: 'POST',
                headers: {{'Content-Type': 'application/json'}},
                body: JSON.stringify({{pattern: pattern}})
            }}).then(() => {{
                location.reload();
            }});
        }}
        
        function performSearch() {{
            alert('検索機能は実装中です');
        }}
        </script>
        ''')
    
    def _create_settings_panel(self, layout_pattern: str):
        """設定パネル作成"""
        with ui.card().style('height:100%;margin:0;'):
            with ui.card_section():
                ui.label('⚙️ 検索設定').style('font-size:16px;font-weight:600;')
                
                # レイアウト切り替えボタン（右上）
                if layout_pattern == 'no-preview':
                    with ui.row().classes('justify-end'):
                        ui.button('▽', on_click=lambda: ui.run_javascript('switchPattern("pattern1")')).props('size=sm')
                        ui.button('△', on_click=lambda: ui.run_javascript('switchPattern("pattern2")')).props('size=sm')
                elif layout_pattern == 'pattern1':
                    with ui.row().classes('justify-end'):
                        ui.button('△', on_click=lambda: ui.run_javascript('switchPattern("pattern2")')).props('size=sm')
                elif layout_pattern == 'pattern2':
                    with ui.row().classes('justify-end'):
                        ui.button('▽', on_click=lambda: ui.run_javascript('switchPattern("pattern1")')).props('size=sm')
            
            with ui.card_section():
                # 質問入力
                ui.textarea(label='質問', placeholder='質問を入力してください…').props('outlined dense').style('width:100%;')
                
                # 設定項目
                with ui.row().classes('items-center gap-2'):
                    ui.label('検索モード：').style('min-width:120px;')
                    ui.select(['チャンク統合', 'ファイル別（要約+一致度）'], value='ファイル別（要約+一致度）').props('outlined dense')
                
                with ui.row().classes('items-center gap-2'):
                    ui.label('検索件数：').style('min-width:120px;')
                    ui.number(value=10, min=1, max=50).props('outlined dense').style('width:80px;')
                    ui.label('件')
                
                with ui.row().classes('items-center gap-2 mt-4'):
                    ui.button('🔍 検索実行', on_click=lambda: ui.run_javascript('performSearch()')).props('color=primary')
                    ui.button('📜 履歴').props('color=secondary')
    
    def _create_results_panel(self):
        """検索結果パネル作成"""
        with ui.card().style('height:100%;margin:0;'):
            with ui.card_section():
                ui.label('📋 検索結果').style('font-size:16px;font-weight:600;')
            
            with ui.card_section().style('flex:1;overflow-y:auto;'):
                ui.label('質問を入力して「検索実行」ボタンを押してください').style('color:#888;text-align:center;margin-top:2em;')
    
    def _create_pdf_panel(self):
        """PDFパネル作成"""
        with ui.card().style('height:100%;margin:0;'):
            with ui.card_section():
                ui.label('📄 PDFプレビュー').style('font-size:16px;font-weight:600;')
            
            with ui.card_section().style('flex:1;overflow:hidden;'):
                ui.html('<iframe src="" style="width:100%;height:100%;border:none;"></iframe>')