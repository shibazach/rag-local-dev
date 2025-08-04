"""
データ登録ページ - UI設計ポリシー準拠実装
"""
from nicegui import ui
from ui.components.layout import RAGHeader, RAGFooter, MainContentArea

class DataRegistrationPage:
    """データ登録ページクラス - UI設計ポリシー準拠"""
    
    def render(self):
        """ページレンダリング"""
        from main import SimpleAuth
        
        if not SimpleAuth.is_authenticated():
            ui.navigate.to('/login')
            return
        
        # UI設計ポリシー準拠実装
        self._render_policy_compliant_registration()
    
    def _render_policy_compliant_registration(self):
        """new/系完全準拠のデータ登録実装"""
        # 共通ヘッダー
        RAGHeader(show_site_name=True, current_page="data-registration")
        
        # 全ページ共通メインコンテンツエリア
        with MainContentArea():
            # new/系Grid Layout (3:3:4, 上下分割)
            with ui.element('div').style('display:grid;grid-template-columns:3fr 3fr 4fr;grid-template-rows:1fr 1fr;gap:6px;height:100%;padding:8px;overflow:hidden;'):
                self._create_settings_panel()      # 左上
                self._create_log_panel()           # 中央（全体）
                self._create_file_panel()          # 右（全体）
                self._create_status_panel()        # 左下
        
        # 共通フッター
        RAGFooter()
    
    def _create_settings_panel(self):
        """設定パネル（左上）- new/系準拠"""
        with ui.element('div').style('''
            grid-row: 1 / 2;
            grid-column: 1 / 2;
            background: white;
            border: 1px solid #ddd;
            border-radius: 8px;
            display: flex;
            flex-direction: column;
            overflow: hidden;
        '''):
            # パネルヘッダー
            with ui.element('div').style('background:#f8f9fa;padding:8px 12px;border-bottom:1px solid #ddd;display:flex;justify-content:space-between;align-items:center;'):
                ui.label('📋 処理設定').style('font-size:16px;font-weight:600;margin:0;')
                with ui.row().classes('gap-1'):
                    ui.button('🚀 処理開始', on_click=lambda: ui.notify('処理開始')).props('size=sm color=primary').style('font-size:11px;')
                    ui.button('⏹️ 停止', on_click=lambda: ui.notify('停止')).props('size=sm color=secondary').style('font-size:11px;display:none;')
            
            # パネル内容
            with ui.element('div').style('flex:1;padding:8px;overflow-y:auto;'):
                # 整形プロセス
                ui.label('整形プロセス').style('font-weight:600;margin-bottom:6px;font-size:13px;')
                ui.select(['デフォルト (OCR + LLM整形)', 'マルチモーダル'], value='デフォルト (OCR + LLM整形)').props('outlined dense').style('width:100%;margin-bottom:16px;')
                
                # 埋め込みモデル
                ui.label('埋め込みモデル').style('font-weight:600;margin-bottom:6px;font-size:13px;')
                with ui.element('div').style('border:1px solid #eee;border-radius:4px;padding:8px;background:#fafafa;margin-bottom:16px;'):
                    ui.checkbox('intfloat/e5-large-v2: multilingual-e5-large', value=True).style('margin-bottom:3px;font-size:14px;')
                    ui.checkbox('intfloat/e5-small-v2: multilingual-e5-small').style('margin-bottom:3px;font-size:14px;')
                    ui.checkbox('nomic-embed-text: nomic-text-embed').style('margin-bottom:3px;font-size:14px;')
                
                # 横並び設定
                with ui.row().classes('gap-4 w-full'):
                    with ui.column():
                        ui.checkbox('既存データを上書き', value=True).style('margin-bottom:8px;')
                    with ui.column():
                        ui.label('品質しきい値').style('font-weight:600;margin-bottom:6px;font-size:13px;')
                        ui.number(value=0.0, min=0, max=1, step=0.1).props('outlined dense').style('width:80px;height:28px;font-size:11px;')
                
                # LLMタイムアウト
                ui.label('LLMタイムアウト (秒)').style('font-weight:600;margin-bottom:6px;font-size:13px;')
                ui.number(value=300, min=30, max=3600).props('outlined dense').style('width:120px;height:28px;font-size:11px;')

    def _create_log_panel(self):
        """処理ログパネル（中央全体）- new/系準拠"""
        with ui.element('div').style('''
            grid-row: 1 / 3;
            grid-column: 2 / 3;
            background: white;
            border: 1px solid #ddd;
            border-radius: 8px;
            display: flex;
            flex-direction: column;
            overflow: hidden;
        '''):
            # パネルヘッダー
            with ui.element('div').style('background:#f8f9fa;padding:8px 12px;border-bottom:1px solid #ddd;display:flex;justify-content:space-between;align-items:center;'):
                ui.label('📋 処理ログ').style('font-size:16px;font-weight:600;margin:0;')
                with ui.row().classes('items-center gap-2'):
                    ui.switch('自動スクロール', value=True).style('font-size:11px;')
                    ui.button('CSV出力').props('size=sm outline').style('font-size:11px;')
            
            # ログコンテナ
            with ui.element('div').style('flex:1;overflow-y:auto;padding:8px;font-family:"Courier New",monospace;font-size:11px;'):
                ui.label('処理ログはここに表示されます').style('color:#666;text-align:center;margin-top:4em;')

    def _create_file_panel(self):
        """ファイル選択パネル（右全体）- new/系準拠"""
        with ui.element('div').style('''
            grid-row: 1 / 3;
            grid-column: 3 / 4;
            background: white;
            border: 1px solid #ddd;
            border-radius: 8px;
            display: flex;
            flex-direction: column;
            overflow: hidden;
        '''):
            # パネルヘッダー（横並び）
            with ui.element('div').style('background:#f8f9fa;padding:8px 12px;border-bottom:1px solid #ddd;display:flex;justify-content:flex-start;align-items:center;gap:12px;'):
                ui.label('📁 ファイル選択').style('font-size:16px;font-weight:600;margin:0;flex-shrink:0;min-width:120px;')
                ui.select(['すべてのステータス', '未処理', '処理中', '処理完了'], value='すべてのステータス').props('outlined dense').style('min-width:180px;height:32px;font-size:12px;')
                ui.input(placeholder='ファイル名で検索...').props('outlined dense').style('flex:1;height:32px;font-size:12px;')
                ui.label('選択: 0件').style('font-size:12px;color:#666;flex-shrink:0;min-width:80px;text-align:right;')
            
            # ファイル一覧
            with ui.element('div').style('flex:1;overflow:hidden;padding:0;'):
                ui.label('ファイル一覧はここに表示されます').style('color:#666;text-align:center;margin-top:4em;padding:16px;')

    def _create_status_panel(self):
        """処理状況パネル（左下）- new/系準拠"""
        with ui.element('div').style('''
            grid-row: 2 / 3;
            grid-column: 1 / 2;
            background: white;
            border: 1px solid #ddd;
            border-radius: 8px;
            display: flex;
            flex-direction: column;
            overflow: hidden;
            margin-top: 6px;
        '''):
            # パネルヘッダー
            with ui.element('div').style('background:#f8f9fa;padding:8px 12px;border-bottom:1px solid #ddd;'):
                ui.label('📊 処理状況').style('font-size:16px;font-weight:600;margin:0;')
            
            # パネル内容
            with ui.element('div').style('flex:1;padding:8px;'):
                # 全体進捗
                ui.label('全体進捗').style('font-weight:600;font-size:13px;margin-bottom:6px;')
                ui.label('待機中').style('font-size:11px;color:#666;margin-bottom:6px;')
                with ui.element('div').style('height:16px;background:#e9ecef;border-radius:8px;overflow:hidden;margin-bottom:16px;'):
                    ui.element('div').style('height:100%;width:0%;background:linear-gradient(90deg,#007bff,#0056b3);')
                
                # 現在の処理
                ui.label('現在の処理').style('font-weight:600;font-size:13px;margin-bottom:6px;')
                ui.label('待機中...').style('font-size:12px;margin-bottom:16px;')
                
                # 統計（4個横並び）
                with ui.row().classes('gap-2 w-full'):
                    with ui.element('div').style('flex:1;text-align:center;padding:8px;background:#f8f9fa;border-radius:4px;'):
                        ui.label('0').style('font-size:16px;font-weight:700;color:#007bff;')
                        ui.label('総ファイル数').style('font-size:10px;color:#666;margin-top:2px;')
                    
                    with ui.element('div').style('flex:1;text-align:center;padding:8px;background:#f8f9fa;border-radius:4px;'):
                        ui.label('0').style('font-size:16px;font-weight:700;color:#007bff;')
                        ui.label('選択数').style('font-size:10px;color:#666;margin-top:2px;')

