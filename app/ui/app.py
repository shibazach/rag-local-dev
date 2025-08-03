"""
NiceGUI統合アプリケーション
Main NiceGUI application with all pages
"""

from nicegui import ui
from typing import Dict, Any, Optional, List
import httpx
from app.config import config, logger
from app.ui.themes.base import RAGTheme
from app.ui.components import (
    RAGPageLayout,
    RAGTable,
    RAGButton,
    RAGInput,
    RAGSelect,
    RAGFileUpload,
    RAGForm
)

def create_nicegui_pages():
    """全NiceGUIページ作成"""
    
    @ui.page('/dashboard')
    async def dashboard():
        """ダッシュボードページ"""
        RAGTheme.apply_global_styles()
        
        layout = RAGPageLayout(
            title="R&D RAGシステム - ダッシュボード",
            current_page="dashboard",
            breadcrumbs=[
                {"label": "ホーム", "path": "/"}
            ]
        )
        
        with layout.get_content_area():
            # 統計カード
            with ui.row().classes('rag-grid rag-grid-4 w-full mb-8'):
                create_stat_card("📄", "総ファイル数", "1,234", "前月比 +12%")
                create_stat_card("✅", "処理済み", "987", "80%")
                create_stat_card("👥", "アクティブユーザー", "45", "オンライン")
                create_stat_card("💾", "ストレージ使用量", "234 GB", "78%")
            
            # 最近の活動
            with ui.card().classes('rag-card'):
                ui.label('📊 最近の活動').classes('text-lg font-bold mb-4')
                
                activities = [
                    {"time": "2分前", "action": "ファイルアップロード", "user": "田中太郎", "file": "報告書.pdf"},
                    {"time": "5分前", "action": "検索実行", "user": "佐藤花子", "query": "AI技術動向"},
                    {"time": "12分前", "action": "チャット開始", "user": "山田次郎", "topic": "市場分析"},
                ]
                
                for activity in activities:
                    with ui.row().classes('w-full items-center p-2 hover:bg-gray-50 rounded'):
                        ui.label(activity["time"]).classes('text-sm text-gray-500 w-16')
                        ui.label(activity["action"]).classes('font-medium w-32')
                        ui.label(activity["user"]).classes('text-sm w-24')
                        ui.label(activity.get("file", activity.get("query", activity.get("topic", "")))).classes('text-sm text-gray-600')
    
    @ui.page('/files')
    async def files_page():
        """ファイル管理ページ（new/系レイアウト準拠）"""
        RAGTheme.apply_global_styles()
        
        # new/系ファイル管理レイアウト準拠
        with ui.element('div').style('''
            display: flex;
            height: calc(100vh - 95px);
            gap: 6px;
            padding: 8px;
            overflow: hidden;
            background: transparent;
        '''):
            # 左側：ファイル一覧パネル
            with ui.element('div').classes('rag-panel').style('flex: 1; min-width: 400px; max-width: 60%'):
                with ui.element('div').classes('rag-panel-header').style('justify-content: flex-start; gap: 12px; flex-wrap: nowrap; align-items: center; padding-right: 8px'):
                    ui.label('📄 ファイル一覧').style('flex-shrink: 0; margin: 0; white-space: nowrap; min-width: 120px; font-size: 16px; font-weight: 600')
                    ui.select(
                        options=[
                            {'label': 'すべてのステータス', 'value': ''},
                            {'label': '未処理', 'value': 'pending_processing'},
                            {'label': '処理中', 'value': 'processing'},
                            {'label': '処理完了', 'value': 'processed'},
                            {'label': 'エラー', 'value': 'error'}
                        ],
                        value=''
                    ).classes('rag-select').style('flex-shrink: 0; min-width: 180px; max-width: 220px; height: 32px; font-size: 12px')
                    ui.input(placeholder='ファイル名で検索...').classes('rag-input-compact').style('flex: 1 1 auto; min-width: 120px; max-width: none; height: 32px; font-size: 12px')
                
                with ui.element('div').classes('rag-panel-content').style('padding: 0; overflow: hidden; display: flex; flex-direction: column'):
                    # ファイル一覧テーブル（new/系準拠）
                    await create_files_management_table()
            
            # 右側：プレビューパネル
            with ui.element('div').classes('rag-panel').style('flex: 1; min-width: 300px'):
                with ui.element('div').classes('rag-panel-header'):
                    ui.label('📄 プレビュー').style('font-size: 16px; font-weight: 600; margin: 0')
                
                with ui.element('div').classes('rag-panel-content'):
                    ui.label('ファイルを選択してください').style('color: #888; text-align: center; margin-top: 2em')
    
    @ui.page('/chat')
    async def chat_page():
        """チャットページ（new/系レイアウト準拠）"""
        RAGTheme.apply_global_styles()
        
        # new/系レイアウト：app-container準拠
        with ui.column().classes('rag-container layout-no-preview'):
            # 上部設定エリア（new/系準拠）
            with ui.column().classes('settings-container').style('flex: 0 0 180px'):
                with ui.element('div').classes('rag-panel'):
                    # 設定パネルヘッダー
                    with ui.element('div').classes('rag-panel-header'):
                        ui.label('⚙️ 検索設定').style('font-size: 16px; font-weight: 600; margin: 0')
                        
                    # 設定パネルコンテンツ
                    with ui.element('div').classes('rag-panel-content'):
                        # クエリ入力
                        ui.textarea(
                            placeholder='質問を入力してください…',
                            value=''
                        ).classes('rag-input').props('rows=4').style('margin-bottom: 12px')
                        
                        # 設定フォーム（new/系準拠の水平レイアウト）
                        with ui.row().classes('w-full gap-4 items-center').style('margin-bottom: 12px'):
                            ui.label('検索モード：').style('min-width: 120px; font-size: 13px')
                            ui.select(
                                options=[
                                    {'label': 'チャンク統合', 'value': 'chunk_merge'},
                                    {'label': 'ファイル別（要約+一致度）', 'value': 'file_separate'}
                                ],
                                value='file_separate'
                            ).classes('rag-select').style('min-width: 180px')
                            
                            ui.label('埋め込みモデル：').style('margin-left: 1em; font-size: 13px')
                            ui.select(
                                options=[
                                    {'label': 'intfloat/e5-large-v2 (SentenceTransformer)', 'value': '1'},
                                    {'label': 'intfloat/e5-small-v2 (SentenceTransformer)', 'value': '2'},
                                    {'label': 'nomic-embed-text (OllamaEmbeddings)', 'value': '3'}
                                ],
                                value='1'
                            ).classes('rag-select').style('min-width: 200px')
                        
                        with ui.row().classes('w-full gap-4 items-center').style('margin-bottom: 12px'):
                            ui.label('検索件数：').style('min-width: 120px; font-size: 13px')
                            ui.number(value=10, min=1, max=50).classes('rag-input-compact').style('width: 4em')
                            ui.label('件').style('color: #666; font-size: 12px')
                            
                            ui.label('最小一致度：').style('margin-left: 1em; font-size: 13px')
                            ui.number(value=0.0, min=0, max=1, step=0.1).classes('rag-input-compact').style('width: 4em')
                            ui.label('以上').style('color: #666; font-size: 12px')
                        
                        with ui.row().classes('w-full gap-4 items-center').style('margin-bottom: 12px'):
                            ui.label('⏱️ 検索タイムアウト：').style('font-size: 13px')
                            ui.number(value=10, min=0, max=3600, step=5).classes('rag-input-compact').style('width: 5em; text-align: center')
                            ui.label('秒（0でタイムアウトなし）').style('font-size: 13px')
                        
                        # アクションボタン
                        with ui.row().classes('w-full gap-2'):
                            ui.button('🔍 検索実行', on_click=lambda: ui.notify('検索実行')).classes('rag-button')
                            ui.button('📜 履歴', on_click=lambda: ui.notify('履歴表示')).props('outline')
                            
                            with ui.row().classes('gap-2 items-center').style('margin-left: 1em'):
                                ui.label('PDF表示：').style('font-size: 13px')
                                ui.radio(['同一タブ内', '別タブ'], value='同一タブ内').style('font-size: 12px')
            
            # 下部コンテナ（new/系準拠）
            with ui.row().classes('w-full').style('flex: 1; gap: 6px'):
                # 左側：検索結果パネル
                with ui.element('div').classes('rag-panel').style('flex: 1'):
                    # 検索結果ヘッダー
                    with ui.element('div').classes('rag-panel-header'):
                        ui.label('📋 検索結果').style('font-size: 16px; font-weight: 600; margin: 0')
                        
                    # 検索結果コンテンツ
                    with ui.element('div').classes('rag-panel-content'):
                        ui.label('質問を入力して検索を実行してください').style('color: #888; text-align: center; margin-top: 2em')
                
                # 右側：PDFプレビューパネル（new/系準拠で非表示状態）
                with ui.element('div').classes('rag-panel').style('flex: 1; display: none'):
                    with ui.element('div').classes('rag-panel-header'):
                        ui.label('📄 PDFプレビュー').style('font-size: 16px; font-weight: 600; margin: 0')
                        
                    with ui.element('div').classes('rag-panel-content'):
                        ui.label('PDFが選択されていません').style('color: #888; text-align: center; margin-top: 2em')
    
    @ui.page('/data-registration')
    async def data_registration_page():
        """データ登録ページ（new/系レイアウト準拠）"""
        RAGTheme.apply_global_styles()
        
        # new/系データ登録グリッドレイアウト準拠
        with ui.element('div').style('''
            display: grid;
            grid-template-columns: 3fr 3fr 4fr;
            grid-template-rows: 1fr 1fr;
            gap: 6px;
            height: calc(100vh - 95px);
            padding: 8px;
            overflow: hidden;
        '''):
            # 左上：設定パネル
            with ui.element('div').classes('rag-panel').style('grid-row: 1 / 2; grid-column: 1 / 2; min-height: 405px'):
                with ui.element('div').classes('rag-panel-header').style('justify-content: space-between'):
                    ui.label('📋 処理設定').style('font-size: 16px; font-weight: 600; margin: 0')
                    with ui.row().classes('gap-2'):
                        ui.button('🚀 処理開始', on_click=lambda: start_processing_new()).classes('rag-button').props('size=sm')
                        ui.button('⏹️ 停止', on_click=lambda: stop_processing_new()).props('outline size=sm').style('display: none')
                
                with ui.element('div').classes('rag-panel-content'):
                    # 整形プロセス選択（new/系準拠の水平グループ）
                    with ui.row().classes('w-full gap-4 items-center').style('margin-bottom: 16px'):
                        with ui.column().style('flex: 1'):
                            ui.label('整形プロセス').style('font-size: 13px; margin-bottom: 6px')
                            ui.select(
                                options=[
                                    {'label': 'デフォルト (OCR + LLM整形)', 'value': 'default'},
                                    {'label': 'マルチモーダル', 'value': 'multimodal'}
                                ],
                                value='default'
                            ).classes('rag-select')
                        
                        with ui.column().style('flex: 1'):
                            ui.label('使用モデル：自動判定中...').style('font-size: 12px; color: #666')
                    
                    # 埋め込みモデル選択（new/系準拠のチェックボックス）
                    ui.label('埋め込みモデル').style('font-size: 13px; margin-bottom: 6px')
                    with ui.column().style('margin-bottom: 16px'):
                        ui.checkbox('SentenceTransformer: intfloat/e5-large-v2', value=True).style('font-size: 12px')
                        ui.checkbox('SentenceTransformer: intfloat/e5-small-v2', value=False).style('font-size: 12px')
                        ui.checkbox('OllamaEmbeddings: nomic-embed-text', value=False).style('font-size: 12px')
                    
                    # 水平設定グループ（new/系準拠）
                    with ui.row().classes('w-full gap-4 items-center').style('margin-bottom: 16px'):
                        with ui.column().style('flex: 1'):
                            ui.checkbox('既存データを上書き', value=True).style('font-size: 12px')
                        
                        with ui.column().style('flex: 1'):
                            ui.label('品質しきい値').style('font-size: 13px; margin-bottom: 4px')
                            ui.number(value=0.0, min=0, max=1, step=0.1).classes('rag-input-compact')
                    
                    # LLMタイムアウト
                    ui.label('LLMタイムアウト (秒)').style('font-size: 13px; margin-bottom: 4px')
                    ui.number(value=300, min=30, max=3600).classes('rag-input-compact')
            
            # 中央：処理ログパネル（new/系準拠）
            with ui.element('div').classes('rag-panel').style('grid-row: 1 / 3; grid-column: 2 / 3; min-height: 305px'):
                with ui.element('div').classes('rag-panel-header'):
                    ui.label('📊 処理ログ').style('font-size: 16px; font-weight: 600; margin: 0')
                
                with ui.element('div').classes('rag-panel-content').style('display: flex; flex-direction: column'):
                    # 現在の進捗表示エリア（new/系準拠の固定表示）
                    with ui.element('div').style('''
                        padding: 8px 12px;
                        background: #f8f9fa;
                        border: 1px solid #ddd;
                        border-radius: 4px;
                        margin-bottom: 8px;
                        font-size: 12px;
                        min-height: 24px;
                    '''):
                        ui.label('待機中...').style('color: #666')
                    
                    # ログコンテンツエリア
                    with ui.element('div').style('''
                        flex: 1;
                        overflow-y: auto;
                        background: #f5f5f5;
                        border: 1px solid #ddd;
                        border-radius: 4px;
                        padding: 8px;
                        font-size: 12px;
                        min-height: 0;
                    '''):
                        ui.label('処理を開始してください').style('color: #888; text-align: center')
            
            # 右側：ファイル選択パネル（new/系準拠）
            with ui.element('div').classes('rag-panel').style('grid-row: 1 / 3; grid-column: 3 / 4; max-height: calc(100vh - 130px)'):
                with ui.element('div').classes('rag-panel-header').style('justify-content: flex-start; gap: 12px; flex-wrap: nowrap'):
                    ui.label('📁 ファイル選択').style('flex-shrink: 0; margin: 0; white-space: nowrap; min-width: 120px; font-size: 16px; font-weight: 600')
                    ui.select(
                        options=[
                            {'label': 'すべてのステータス', 'value': ''},
                            {'label': '未処理', 'value': 'pending_processing'},
                            {'label': '処理中', 'value': 'processing'},
                            {'label': '未整形', 'value': 'text_extracted'},
                            {'label': '未ベクトル化', 'value': 'text_refined'},
                            {'label': '処理完了', 'value': 'processed'},
                            {'label': 'エラー', 'value': 'error'}
                        ],
                        value=''
                    ).classes('rag-select').style('flex-shrink: 0; min-width: 180px; max-width: 220px; height: 32px; font-size: 12px')
                    ui.input(placeholder='ファイル名で検索...').classes('rag-input-compact').style('flex: 1 1 auto; min-width: 120px; height: 32px; font-size: 12px')
                    ui.label('選択: 0件').style('font-size: 12px; white-space: nowrap')
                
                with ui.element('div').classes('rag-panel-content').style('padding: 0; overflow: hidden; display: flex; flex-direction: column'):
                    # ファイル一覧テーブル（new/系準拠）
                    await create_file_selection_table()
    
    @ui.page('/admin')
    async def admin_page():
        """管理ページ"""
        RAGTheme.apply_global_styles()
        
        layout = RAGPageLayout(
            title="R&D RAGシステム - 管理",
            current_page="admin",
            breadcrumbs=[
                {"label": "ホーム", "path": "/"},
                {"label": "管理", "path": "/admin"}
            ]
        )
        
        with layout.get_content_area():
            # システム情報
            with ui.card().classes('rag-card mb-6'):
                ui.label('🖥️ システム情報').classes('text-lg font-bold mb-4')
                
                system_info = get_system_info()
                for key, value in system_info.items():
                    with ui.row().classes('w-full justify-between py-1'):
                        ui.label(key).classes('font-medium')
                        ui.label(str(value)).classes('text-gray-600')
            
            # 設定管理
            with ui.card().classes('rag-card'):
                ui.label('⚙️ システム設定').classes('text-lg font-bold mb-4')
                
                create_admin_settings()

# ヘルパー関数

async def create_file_selection_table():
    """ファイル選択テーブル作成（new/系準拠）"""
    # new/系準拠のファイルテーブル
    with ui.element('div').style('flex: 1; overflow: hidden; display: flex; flex-direction: column'):
        # テーブルヘッダー
        with ui.element('div').style('''
            display: grid;
            grid-template-columns: 40px 1fr 80px 120px 100px;
            gap: 8px;
            padding: 8px 12px;
            background: #f8f9fa;
            border-bottom: 1px solid #ddd;
            font-size: 12px;
            font-weight: 600;
        '''):
            ui.checkbox(value=False).style('justify-self: center')
            ui.label('ファイル名')
            ui.label('頁数').style('text-align: center')
            ui.label('ステータス').style('text-align: center')
            ui.label('サイズ').style('text-align: center')
        
        # テーブルボディ（スクロール可能）
        with ui.element('div').style('flex: 1; overflow-y: auto'):
            # サンプルファイル行
            for i in range(5):
                with ui.element('div').style(f'''
                    display: grid;
                    grid-template-columns: 40px 1fr 80px 120px 100px;
                    gap: 8px;
                    padding: 6px 12px;
                    border-bottom: 1px solid #eee;
                    font-size: 12px;
                    {"background: #f9f9f9;" if i % 2 == 0 else ""}
                '''):
                    ui.checkbox(value=False).style('justify-self: center')
                    ui.label(f'サンプルファイル{i+1}.pdf').style('overflow: hidden; text-overflow: ellipsis')
                    ui.label(f'{i+3}').style('text-align: center')
                    
                    # ステータスバッジ
                    statuses = ['未処理', '処理中', '処理完了', 'エラー', '未整形']
                    colors = ['#ffeaa7', '#74b9ff', '#00b894', '#d63031', '#fd79a8']
                    status = statuses[i % len(statuses)]
                    color = colors[i % len(colors)]
                    ui.label(status).style(f'background: {color}; color: white; padding: 2px 8px; border-radius: 12px; font-size: 11px; text-align: center; font-weight: 600')
                    
                    ui.label(f'{(i+1)*0.8:.1f} MB').style('text-align: center')
        
        # ページネーション（new/系準拠）
        with ui.element('div').style('''
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 8px 12px;
            background: #f8f9fa;
            border-top: 1px solid #ddd;
            font-size: 12px;
        '''):
            ui.label('5件のファイル')
            with ui.row().classes('gap-2 items-center'):
                ui.select(
                    options=[
                        {'label': '50件/ページ', 'value': 50},
                        {'label': '100件/ページ', 'value': 100},
                        {'label': '200件/ページ', 'value': 200}
                    ],
                    value=100
                ).style('font-size: 11px; height: 24px; min-width: 120px')
                ui.button('◀', on_click=lambda: ui.notify('前のページ')).props('size=xs outline').style('width: 24px; height: 24px')
                ui.label('1 / 1').style('min-width: 40px; text-align: center')
                ui.button('▶', on_click=lambda: ui.notify('次のページ')).props('size=xs outline').style('width: 24px; height: 24px')

def start_processing_new():
    """新しい処理開始"""
    ui.notify('処理を開始しました', type='positive')

def stop_processing_new():
    """新しい処理停止"""
    ui.notify('処理を停止しました', type='warning')

def create_stat_card(icon: str, title: str, value: str, subtitle: str):
    """統計カード作成"""
    with ui.card().classes('rag-card text-center'):
        ui.label(icon).classes('text-3xl mb-2')
        ui.label(title).classes('text-sm text-gray-600 mb-1')
        ui.label(value).classes('text-2xl font-bold mb-1')
        ui.label(subtitle).classes('text-xs text-gray-500')

async def create_files_management_table():
    """ファイル管理テーブル作成（new/系準拠）"""
    # new/系準拠のファイル管理テーブル
    with ui.element('div').style('flex: 1; overflow: hidden; display: flex; flex-direction: column'):
        # テーブルヘッダー
        with ui.element('div').style('''
            display: grid;
            grid-template-columns: 1fr 100px 120px 120px 80px;
            gap: 8px;
            padding: 8px 12px;
            background: #f8f9fa;
            border-bottom: 1px solid #ddd;
            font-size: 12px;
            font-weight: 600;
        '''):
            ui.label('ファイル名')
            ui.label('サイズ').style('text-align: center')
            ui.label('ステータス').style('text-align: center')
            ui.label('処理日時').style('text-align: center')
            ui.label('操作').style('text-align: center')
        
        # テーブルボディ（スクロール可能）
        with ui.element('div').style('flex: 1; overflow-y: auto'):
            # サンプルファイル行
            sample_files = [
                {'name': '技術報告書.pdf', 'size': '2.1 MB', 'status': '処理完了', 'color': '#00b894', 'date': '2024-01-15'},
                {'name': '研究資料.docx', 'size': '1.8 MB', 'status': '処理中', 'color': '#74b9ff', 'date': '2024-01-15'},
                {'name': 'データ分析.xlsx', 'size': '1.2 MB', 'status': '未処理', 'color': '#ffeaa7', 'date': '2024-01-14'},
                {'name': '会議議事録.pdf', 'size': '0.9 MB', 'status': 'エラー', 'color': '#d63031', 'date': '2024-01-14'},
                {'name': '仕様書.docx', 'size': '1.5 MB', 'status': '未整形', 'color': '#fd79a8', 'date': '2024-01-13'},
            ]
            
            for i, file_data in enumerate(sample_files):
                with ui.element('div').style(f'''
                    display: grid;
                    grid-template-columns: 1fr 100px 120px 120px 80px;
                    gap: 8px;
                    padding: 6px 12px;
                    border-bottom: 1px solid #eee;
                    font-size: 12px;
                    cursor: pointer;
                    {"background: #f9f9f9;" if i % 2 == 0 else ""}
                    transition: background-color 0.2s;
                ''').on('click', lambda: ui.notify(f'選択: {file_data["name"]}')):
                    ui.label(file_data['name']).style('overflow: hidden; text-overflow: ellipsis; color: #0066cc; text-decoration: underline')
                    ui.label(file_data['size']).style('text-align: center')
                    
                    # ステータスバッジ
                    ui.label(file_data['status']).style(f'''
                        background: {file_data['color']};
                        color: white;
                        padding: 2px 8px;
                        border-radius: 12px;
                        font-size: 11px;
                        text-align: center;
                        font-weight: 600;
                    ''')
                    
                    ui.label(file_data['date']).style('text-align: center; color: #666')
                    
                    # 操作ボタン
                    with ui.row().classes('gap-1 justify-center'):
                        ui.button('👁', on_click=lambda f=file_data: view_file_new(f)).props('size=xs outline').style('width: 20px; height: 20px; font-size: 10px')
                        ui.button('⬇', on_click=lambda f=file_data: download_file_new(f)).props('size=xs outline').style('width: 20px; height: 20px; font-size: 10px')
                        ui.button('🗑', on_click=lambda f=file_data: delete_file_new(f)).props('size=xs outline').style('width: 20px; height: 20px; font-size: 10px; color: #d63031')
        
        # ページネーション（new/系準拠）
        with ui.element('div').style('''
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 8px 12px;
            background: #f8f9fa;
            border-top: 1px solid #ddd;
            font-size: 12px;
        '''):
            ui.label('5件のファイル（全体の1-5件を表示）')
            with ui.row().classes('gap-2 items-center'):
                ui.select(
                    options=[
                        {'label': '20件/ページ', 'value': 20},
                        {'label': '50件/ページ', 'value': 50},
                        {'label': '100件/ページ', 'value': 100}
                    ],
                    value=20
                ).style('font-size: 11px; height: 24px; min-width: 120px')
                ui.button('◀', on_click=lambda: ui.notify('前のページ')).props('size=xs outline').style('width: 24px; height: 24px')
                ui.label('1 / 1').style('min-width: 40px; text-align: center')
                ui.button('▶', on_click=lambda: ui.notify('次のページ')).props('size=xs outline').style('width: 24px; height: 24px')

async def create_files_table():
    """ファイル一覧テーブル作成（廃止：create_files_management_table使用）"""
    pass

def create_chat_settings():
    """チャット設定パネル作成"""
    with ui.card().classes('rag-card'):
        ui.label('⚙️ 検索設定').classes('text-lg font-bold mb-4')
        
        RAGSelect(
            label="検索モード",
            options=[
                {'label': 'セマンティック検索', 'value': 'semantic'},
                {'label': 'キーワード検索', 'value': 'keyword'},
                {'label': 'ハイブリッド検索', 'value': 'hybrid'}
            ],
            value='semantic'
        )
        
        RAGSelect(
            label="埋め込みモデル",
            options=[
                {'label': 'e5-large-v2 (推奨)', 'value': '1'},
                {'label': 'e5-small-v2 (軽量)', 'value': '2'},
                {'label': 'nomic-embed-text', 'value': '3'}
            ],
            value='1'
        )
        
        RAGInput(
            label="結果件数",
            value="10",
            input_type="number"
        )
        
        RAGInput(
            label="最小スコア",
            value="0.7",
            input_type="number"
        )

def create_admin_settings():
    """管理設定フォーム作成"""
    form = RAGForm(
        title="",
        submit_label="設定保存",
        on_submit=save_admin_settings
    )
    
    form.add_field(RAGSelect(
        label="LLMモデル",
        options=[
            {'label': 'phi4-mini (CPU)', 'value': 'phi4-mini'},
            {'label': 'gemma:7b (GPU)', 'value': 'gemma:7b'}
        ],
        value=config.OLLAMA_MODEL
    ))
    
    form.add_field(RAGSelect(
        label="OCRエンジン",
        options=[
            {'label': 'ocrmypdf (推奨)', 'value': 'ocrmypdf'},
            {'label': 'tesseract', 'value': 'tesseract'}
        ],
        value=config.DEFAULT_OCR_ENGINE
    ))
    
    form.add_field(RAGInput(
        label="最大ファイルサイズ (MB)",
        value=str(config.MAX_UPLOAD_SIZE // (1024*1024)),
        input_type="number"
    ))

# イベントハンドラー

def handle_file_upload(e):
    """ファイルアップロードハンドラー"""
    ui.notify(f'ファイルをアップロードしました: {e.name}', type='positive')
    # TODO: 実際のアップロード処理

def handle_processing_upload(e):
    """処理用ファイルアップロードハンドラー"""
    ui.notify(f'処理対象ファイルを追加しました: {e.name}', type='info')
    # TODO: 処理ファイル一覧に追加

def start_processing(selected_files_area):
    """処理開始"""
    ui.notify('ファイル処理を開始しました', type='positive')
    # TODO: 実際の処理開始

def stop_processing():
    """処理停止"""
    ui.notify('処理を停止しました', type='warning')
    # TODO: 実際の処理停止

def send_chat_message(message: str, chat_area):
    """チャットメッセージ送信"""
    if message.strip():
        with chat_area:
            with ui.row().classes('w-full mb-2'):
                ui.label(f'👤 You: {message}').classes('bg-blue-100 p-2 rounded')
        ui.notify('メッセージを送信しました', type='info')
        # TODO: 実際のチャット処理

def view_file_new(file_data):
    """ファイル表示（new版）"""
    ui.notify(f'ファイルを表示: {file_data["name"]}', type='info')

def download_file_new(file_data):
    """ファイルダウンロード（new版）"""
    ui.notify(f'ファイルをダウンロード: {file_data["name"]}', type='info')

def delete_file_new(file_data):
    """ファイル削除（new版）"""
    ui.notify(f'ファイルを削除: {file_data["name"]}', type='warning')

def view_file(e):
    """ファイル表示（旧版）"""
    ui.notify(f'ファイルを表示: {e.name}', type='info')

def download_file(e):
    """ファイルダウンロード（旧版）"""
    ui.notify(f'ファイルをダウンロード: {e.name}', type='info')

def delete_file(e):
    """ファイル削除（旧版）"""
    ui.notify(f'ファイルを削除: {e.name}', type='warning')

def refresh_files():
    """ファイル一覧更新"""
    ui.notify('ファイル一覧を更新しました', type='info')

def save_admin_settings(form_data):
    """管理設定保存"""
    ui.notify('設定を保存しました', type='positive')

# ヘルパー関数

def get_system_info() -> Dict[str, Any]:
    """システム情報取得"""
    return {
        "バージョン": config.APP_VERSION,
        "環境": config.ENVIRONMENT,
        "LLMモデル": config.OLLAMA_MODEL,
        "OCRエンジン": config.DEFAULT_OCR_ENGINE,
        "データベース": "PostgreSQL",
        "ストレージ": "ローカル"
    }

def get_mock_files_data() -> List[Dict[str, Any]]:
    """モックファイルデータ"""
    return [
        {
            'id': '1',
            'name': '技術報告書.pdf',
            'size': 2048000,
            'status': RAGTheme.create_status_badge('completed'),
            'created_at': '2024-01-15T10:30:00Z'
        },
        {
            'id': '2', 
            'name': '研究資料.docx',
            'size': 1024000,
            'status': RAGTheme.create_status_badge('processing'),
            'created_at': '2024-01-15T09:15:00Z'
        },
        {
            'id': '3',
            'name': 'データ分析.xlsx',
            'size': 512000,
            'status': RAGTheme.create_status_badge('pending'),
            'created_at': '2024-01-15T08:45:00Z'
        }
    ]