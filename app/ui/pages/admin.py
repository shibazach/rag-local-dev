"""
管理画面ページ - new/系準拠実装
"""
from nicegui import ui
from app.ui.components.layout import RAGHeader, RAGFooter, MainContentArea

class AdminPage:
    """管理画面ページクラス - new/系準拠"""
    
    def render(self):
        """ページレンダリング"""
        from app.auth.session import SessionManager
        
        current_user = SessionManager.get_current_user()
        if not current_user or not current_user.get('is_admin', False):
            ui.navigate.to('/login?redirect=/admin')
            return
        
        # 共通ヘッダー
        RAGHeader(show_site_name=True, current_page="admin")
        
        # 全ページ共通メインコンテンツエリア
        with MainContentArea():
            with ui.element('div').style('padding:8px;height:100%;'):
                with ui.tabs().classes('w-full') as tabs:
                    user_tab = ui.tab('👥 ユーザー管理')
                    system_tab = ui.tab('⚙️ システム設定')
                    monitor_tab = ui.tab('📊 監視')
                    backup_tab = ui.tab('💾 バックアップ')
                
                with ui.tab_panels(tabs, value=user_tab).classes('w-full').style('height:calc(100% - 60px);'):
                    # ユーザー管理タブ
                    with ui.tab_panel(user_tab):
                        with ui.card().style('height:100%;'):
                            with ui.card_section():
                                with ui.row().classes('justify-between items-center w-full'):
                                    ui.label('ユーザー一覧').style('font-size:18px;font-weight:600;')
                                    ui.button('➕ 新規ユーザー', on_click=lambda: ui.notify('新規ユーザー作成')).props('color=primary')
                                
                                # ユーザーテーブル
                                with ui.element('div').style('margin-top:16px;'):
                                    ui.label('ユーザー管理機能がここに表示されます').style('color:#666;text-align:center;margin-top:4em;')
                    
                    # システム設定タブ
                    with ui.tab_panel(system_tab):
                        with ui.card().style('height:100%;'):
                            with ui.card_section():
                                ui.label('システム設定').style('font-size:18px;font-weight:600;margin-bottom:20px;')
                                
                                # 設定項目
                                with ui.column().classes('gap-4'):
                                    ui.checkbox('デバッグモード').style('margin-bottom:8px;')
                                    ui.checkbox('ログ詳細出力').style('margin-bottom:8px;')
                                    ui.number(label='セッションタイムアウト(分)', value=30, min=5, max=1440).props('outlined dense').style('width:200px;')
                                    ui.number(label='最大アップロードサイズ(MB)', value=100, min=1, max=1000).props('outlined dense').style('width:200px;')
                                    
                                    ui.button('💾 設定保存', on_click=lambda: ui.notify('設定保存完了')).props('color=positive')
                    
                    # 監視タブ
                    with ui.tab_panel(monitor_tab):
                        with ui.card().style('height:100%;'):
                            with ui.card_section():
                                ui.label('システム監視').style('font-size:18px;font-weight:600;margin-bottom:20px;')
                                ui.label('監視ダッシュボードがここに表示されます').style('color:#666;text-align:center;margin-top:4em;')
                    
                    # バックアップタブ
                    with ui.tab_panel(backup_tab):
                        with ui.card().style('height:100%;'):
                            with ui.card_section():
                                ui.label('バックアップ管理').style('font-size:18px;font-weight:600;margin-bottom:20px;')
                                
                                with ui.row().classes('gap-4'):
                                    ui.button('📤 バックアップ作成', on_click=lambda: ui.notify('バックアップ開始')).props('color=primary')
                                    ui.button('📥 復元', on_click=lambda: ui.notify('復元機能')).props('color=secondary')
                                
                                ui.label('バックアップ履歴がここに表示されます').style('color:#666;text-align:center;margin-top:4em;')
        
        # 共通フッター
        RAGFooter()