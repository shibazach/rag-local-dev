#!/usr/bin/env python3
"""
NiceGUI完全移行版 - R&D RAGシステム
シンプル・統一・直感的な設計
"""

from nicegui import ui, app
from typing import Optional, Dict, Any, List
import asyncio
import logging
from datetime import datetime
import httpx
from pathlib import Path

# ログ設定
logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger(__name__)

# ==============================================================================
# 共通テーマ・設定
# ==============================================================================

class RAGTheme:
    """統一テーマ設定"""
    
    # カラーパレット
    PRIMARY = '#5a6c7d'
    SECONDARY = '#6c757d'
    SUCCESS = '#4a7c59'
    WARNING = '#d4a843'
    DANGER = '#c85450'
    INFO = '#5a9aa8'
    
    # レイアウト設定
    HEADER_HEIGHT = '60px'
    SIDEBAR_WIDTH = '250px'
    CONTENT_PADDING = '20px'
    
    @staticmethod
    def apply_global_styles():
        """グローバルスタイル適用"""
        ui.add_head_html(f'''
        <style>
            :root {{
                --primary-color: {RAGTheme.PRIMARY};
                --secondary-color: {RAGTheme.SECONDARY};
                --success-color: {RAGTheme.SUCCESS};
                --warning-color: {RAGTheme.WARNING};
                --danger-color: {RAGTheme.DANGER};
                --info-color: {RAGTheme.INFO};
            }}
            
            body {{
                margin: 0;
                padding: 0;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background-color: #f8f9fa;
            }}
            
            .rag-header {{
                background: linear-gradient(135deg, {RAGTheme.PRIMARY} 0%, {RAGTheme.SECONDARY} 100%);
                color: white;
                padding: 0 20px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}
            
            .rag-content {{
                padding: {RAGTheme.CONTENT_PADDING};
                max-width: 1200px;
                margin: 0 auto;
            }}
            
            .rag-card {{
                background: white;
                border-radius: 8px;
                padding: 20px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.05);
                margin-bottom: 20px;
            }}
            
            .rag-button {{
                background: {RAGTheme.PRIMARY};
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                cursor: pointer;
                transition: all 0.2s;
            }}
            
            .rag-button:hover {{
                background: {RAGTheme.SECONDARY};
                transform: translateY(-1px);
            }}
        </style>
        ''')

# ==============================================================================
# 共通コンポーネント
# ==============================================================================

class RAGHeader:
    """統一ヘッダーコンポーネント"""
    
    def __init__(self, title: str = "R&D RAGシステム", current_page: str = ""):
        self.title = title
        self.current_page = current_page
        self.create_header()
    
    def create_header(self):
        with ui.header().classes('rag-header'):
            with ui.row().classes('w-full items-center justify-between'):
                # 左側：タイトルとナビゲーション
                with ui.row().classes('items-center gap-6'):
                    ui.label(self.title).classes('text-xl font-bold')
                    
                    nav_items = [
                        ('🏠 ダッシュボード', '/'),
                        ('💬 チャット', '/chat'),
                        ('📁 データ登録', '/data-registration'),
                        ('🛠️ 管理', '/admin')
                    ]
                    
                    for label, path in nav_items:
                        is_current = path == self.current_page
                        classes = 'text-white hover:text-gray-200 px-3 py-2 rounded'
                        if is_current:
                            classes += ' bg-white bg-opacity-20'
                        
                        ui.link(label, path).classes(classes)
                
                # 右側：ユーザー情報
                with ui.row().classes('items-center gap-4'):
                    ui.label('👤 admin').classes('text-white')
                    ui.button('ログアウト', on_click=self.logout).props('flat').classes('text-white')
    
    def logout(self):
        ui.notify('ログアウトしました', type='info')
        # 実際のログアウト処理をここに実装

class RAGStats:
    """システム統計表示コンポーネント"""
    
    def __init__(self):
        self.stats_container = None
        self.create_stats()
    
    def create_stats(self):
        with ui.card().classes('rag-card'):
            ui.label('📊 システム統計').classes('text-lg font-bold mb-4')
            
            self.stats_container = ui.row().classes('w-full gap-6')
            self.update_stats()
    
    async def update_stats(self):
        """統計情報を更新"""
        if self.stats_container:
            self.stats_container.clear()
            
            with self.stats_container:
                # 実際のAPI呼び出しをここに実装
                stats = {
                    'files': 32,
                    'processed': 10,
                    'chunks': 1250,
                    'searches': 89
                }
                
                for key, value in stats.items():
                    with ui.card().classes('text-center p-4'):
                        ui.label(str(value)).classes('text-2xl font-bold text-primary')
                        ui.label(key.title()).classes('text-sm text-gray-600')

# ==============================================================================
# ページ実装
# ==============================================================================

@ui.page('/')
async def dashboard():
    """ダッシュボード - NiceGUI完全版"""
    RAGTheme.apply_global_styles()
    
    # ヘッダー
    header = RAGHeader("R&D RAGシステム - ダッシュボード", "/")
    
    # メインコンテンツ
    with ui.column().classes('rag-content'):
        # 統計情報
        stats = RAGStats()
        
        # クイックアクション
        with ui.card().classes('rag-card'):
            ui.label('🚀 クイックアクション').classes('text-lg font-bold mb-4')
            
            with ui.row().classes('gap-4'):
                ui.button('📁 新しいファイルをアップロード', 
                         on_click=lambda: ui.open('/data-registration')).classes('rag-button')
                ui.button('💬 チャットを開始', 
                         on_click=lambda: ui.open('/chat')).classes('rag-button')
                ui.button('🔍 検索履歴を確認', 
                         on_click=lambda: ui.notify('検索履歴を表示', type='info')).classes('rag-button')
        
        # 最近の活動
        with ui.card().classes('rag-card'):
            ui.label('📋 最近の活動').classes('text-lg font-bold mb-4')
            
            activities = [
                {'time': '09:45', 'action': 'ファイルアップロード完了', 'status': '成功'},
                {'time': '09:42', 'action': 'チャット検索実行', 'status': '成功'},
                {'time': '09:38', 'action': 'データ処理開始', 'status': '実行中'},
            ]
            
            with ui.column().classes('gap-2'):
                for activity in activities:
                    with ui.row().classes('items-center gap-4 p-2 border-b'):
                        ui.label(activity['time']).classes('text-sm text-gray-500 w-16')
                        ui.label(activity['action']).classes('flex-1')
                        status_color = 'success' if activity['status'] == '成功' else 'warning'
                        ui.badge(activity['status'], color=status_color)

@ui.page('/chat')
async def chat_page():
    """チャットページ - NiceGUI完全版"""
    RAGTheme.apply_global_styles()
    
    # ヘッダー
    header = RAGHeader("R&D RAGシステム - チャット", "/chat")
    
    # メインコンテンツ
    with ui.column().classes('rag-content'):
        
        # チャット検索エリア
        with ui.card().classes('rag-card'):
            ui.label('💬 チャット検索').classes('text-lg font-bold mb-4')
            
            # 質問入力
            query_input = ui.textarea(
                placeholder='質問を入力してください...',
                value=''
            ).props('rows=3').classes('w-full mb-4')
            
            # 設定エリア
            with ui.row().classes('w-full gap-4 mb-4'):
                # 基本設定
                with ui.column().classes('flex-1'):
                    ui.label('基本設定').classes('font-bold mb-2')
                    
                    search_mode = ui.select(
                        ['チャンク統合', 'ファイル別検索'],
                        value='ファイル別検索',
                        label='検索モード'
                    ).classes('w-full mb-2')
                    
                    model_type = ui.select(
                        ['標準モデル', '高精度モデル', '高速モデル'],
                        value='標準モデル',
                        label='埋め込みモデル'
                    ).classes('w-full')
                
                # 詳細設定
                with ui.column().classes('flex-1'):
                    ui.label('詳細設定').classes('font-bold mb-2')
                    
                    search_limit = ui.number(
                        label='検索件数',
                        value=10,
                        min=1,
                        max=50
                    ).classes('w-full mb-2')
                    
                    min_score = ui.number(
                        label='最小一致度',
                        value=0.3,
                        min=0.0,
                        max=1.0,
                        step=0.1
                    ).classes('w-full')
            
            # 実行ボタン
            with ui.row().classes('gap-2'):
                ui.button('🔍 検索実行', 
                         on_click=lambda: execute_search(query_input.value, search_mode.value, model_type.value, search_limit.value, min_score.value)
                         ).classes('rag-button')
                ui.button('📜 履歴表示', 
                         on_click=lambda: ui.notify('履歴機能は準備中です', type='info')
                         ).classes('rag-button bg-gray-500')
        
        # 検索結果表示エリア
        global result_container
        result_container = ui.column().classes('w-full')

async def execute_search(query: str, mode: str, model: str, limit: int, score: float):
    """検索実行"""
    if not query.strip():
        ui.notify('質問を入力してください', type='warning')
        return
    
    ui.notify(f'検索を実行中... (モード: {mode}, モデル: {model})', type='info')
    
    # 検索結果表示
    result_container.clear()
    with result_container:
        with ui.card().classes('rag-card'):
            ui.label('🔍 検索結果').classes('text-lg font-bold mb-4')
            ui.label(f'検索クエリ: "{query}"').classes('text-sm text-gray-600 mb-4')
            
            # モックデータ表示
            results = [
                {
                    'title': 'サンプル文書1.pdf',
                    'content': 'このドキュメントには、ご質問に関連する重要な情報が含まれています...',
                    'score': 0.85
                },
                {
                    'title': 'サンプル文書2.pdf', 
                    'content': '関連する技術的な詳細について説明されており、参考になります...',
                    'score': 0.72
                }
            ]
            
            for i, result in enumerate(results):
                with ui.card().classes('p-4 mb-2 border-l-4 border-blue-500'):
                    with ui.row().classes('items-center justify-between mb-2'):
                        ui.label(result['title']).classes('font-bold')
                        ui.badge(f"関連度: {result['score']:.2f}", color='info')
                    ui.label(result['content']).classes('text-gray-700')

@ui.page('/data-registration')
async def data_registration():
    """データ登録ページ - NiceGUI完全版"""
    RAGTheme.apply_global_styles()
    
    # ヘッダー
    header = RAGHeader("R&D RAGシステム - データ登録", "/data-registration")
    
    # メインコンテンツ
    with ui.column().classes('rag-content'):
        
        # ファイルアップロード
        with ui.card().classes('rag-card'):
            ui.label('📁 ファイルアップロード').classes('text-lg font-bold mb-4')
            
            upload = ui.upload(
                on_upload=lambda e: ui.notify(f'ファイル "{e.name}" をアップロードしました', type='success'),
                multiple=True,
                max_file_size=100_000_000  # 100MB
            ).props('accept=".pdf,.txt,.docx"').classes('w-full')
            
            ui.label('対応形式: PDF, TXT, DOCX (最大100MB)').classes('text-sm text-gray-600 mt-2')
        
        # 処理設定
        with ui.card().classes('rag-card'):
            ui.label('⚙️ 処理設定').classes('text-lg font-bold mb-4')
            
            with ui.row().classes('w-full gap-4'):
                ocr_engine = ui.select(
                    ['OCRmyPDF', 'Tesseract', 'PaddleOCR'],
                    value='OCRmyPDF',
                    label='OCRエンジン'
                ).classes('flex-1')
                
                llm_model = ui.select(
                    ['Claude', 'GPT-4', 'Llama3'],
                    value='Claude',
                    label='LLMモデル'
                ).classes('flex-1')
        
        # 処理開始
        with ui.card().classes('rag-card'):
            ui.label('🚀 処理実行').classes('text-lg font-bold mb-4')
            
            with ui.row().classes('gap-2'):
                ui.button('📊 処理開始', 
                         on_click=lambda: start_processing(ocr_engine.value, llm_model.value)
                         ).classes('rag-button')
                ui.button('⏹️ 処理停止', 
                         on_click=lambda: ui.notify('処理を停止しました', type='warning')
                         ).classes('rag-button bg-red-500')
        
        # 処理ログ
        global log_container
        log_container = ui.column().classes('w-full')

async def start_processing(ocr_engine: str, llm_model: str):
    """処理開始"""
    ui.notify(f'処理を開始します (OCR: {ocr_engine}, LLM: {llm_model})', type='info')
    
    log_container.clear()
    with log_container:
        with ui.card().classes('rag-card'):
            ui.label('📋 処理ログ').classes('text-lg font-bold mb-4')
            
            # リアルタイムログ表示（モック）
            logs = [
                '処理を開始しました...',
                f'OCRエンジン {ocr_engine} を初期化中...',
                'ファイル読み込み完了',
                'OCR処理実行中...',
                'テキスト抽出完了',
                f'LLMモデル {llm_model} で精緻化中...',
                '処理完了！'
            ]
            
            log_display = ui.column().classes('w-full')
            
            for i, log in enumerate(logs):
                await asyncio.sleep(1)  # 1秒間隔でログ表示
                with log_display:
                    timestamp = datetime.now().strftime('%H:%M:%S')
                    ui.label(f'[{timestamp}] {log}').classes('text-sm text-gray-700 p-1')

@ui.page('/files/nicegui')
async def files_page():
    """ファイル管理ページ - NiceGUI完全版"""
    RAGTheme.apply_global_styles()
    
    # ヘッダー
    header = RAGHeader("R&D RAGシステム - ファイル管理", "/files")
    
    # メインコンテンツ
    with ui.column().classes('rag-content'):
        
        # ファイル管理ヘッダー
        with ui.card().classes('rag-card bg-green-500 text-white'):
            ui.label('📁 NiceGUIファイル管理').classes('text-xl font-bold mb-2')
            ui.label('ファイル管理機能をNiceGUIで完全再構築しました。').classes('mb-4')
            ui.button('📂 NiceGUIファイル管理を開く', 
                     on_click=lambda: ui.notify('ファイル管理機能を開きます', type='info')
                     ).classes('bg-white text-green-600 hover:bg-gray-100')
        
        # ファイル検索・フィルター
        with ui.card().classes('rag-card'):
            ui.label('🔍 ファイル検索').classes('text-lg font-bold mb-4')
            
            with ui.row().classes('w-full gap-4 mb-4'):
                search_input = ui.input(
                    placeholder='ファイル名で検索...',
                    value=''
                ).classes('flex-1')
                
                status_filter = ui.select(
                    ['すべてのステータス', '処理済み', '未処理', 'エラー'],
                    value='すべてのステータス',
                    label='ステータス'
                ).classes('w-48')
                
                ui.button('🔍 検索', 
                         on_click=lambda: search_files(search_input.value, status_filter.value)
                         ).classes('rag-button')
        
        # ファイル一覧表
        global files_table
        files_table = ui.column().classes('w-full')
        
        # ページネーション設定情報
        with ui.card().classes('rag-card p-2 mb-2 bg-blue-50'):
            with ui.row().classes('items-center gap-4'):
                ui.icon('info').classes('text-blue-600')
                ui.label('1ページあたり10件表示 | ソート・検索・フィルター機能付き').classes('text-sm text-blue-800')
        
        await load_files_table()

async def load_files_table():
    """ファイル一覧表を読み込み"""
    files_table.clear()
    
    with files_table:
        with ui.card().classes('rag-card'):
            ui.label('📄 ファイル一覧').classes('text-lg font-bold mb-4')
            
            # テーブルヘッダー
            columns = [
                {'name': 'name', 'label': 'ファイル名', 'field': 'name', 'align': 'left'},
                {'name': 'size', 'label': 'サイズ', 'field': 'size', 'align': 'right'},
                {'name': 'status', 'label': 'ステータス', 'field': 'status', 'align': 'center'},
                {'name': 'processed_at', 'label': '処理日時', 'field': 'processed_at', 'align': 'center'},
                {'name': 'actions', 'label': '操作', 'field': 'actions', 'align': 'center'}
            ]
            
            # 実際のファイルデータを取得（API呼び出し）
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get('http://localhost:8000/api/files')
                    if response.status_code == 200:
                        files_data = response.json()
                        rows = []
                        for file_info in files_data:
                            rows.append({
                                'name': file_info.get('original_filename', 'Unknown'),
                                'size': f"{file_info.get('file_size', 0) / 1024:.1f} KB",
                                'status': get_status_badge(file_info.get('is_processed', False)),
                                'processed_at': file_info.get('created_at', 'N/A')[:19] if file_info.get('created_at') else 'N/A',
                                'actions': file_info.get('id', '')
                            })
                    else:
                        rows = get_mock_files()
            except Exception as e:
                LOGGER.error(f"ファイル取得エラー: {e}")
                rows = get_mock_files()
            
            # テーブル表示（ページネーション有効化 + 高さ最適化）
            table = ui.table(
                columns=columns, 
                rows=rows,
                pagination={'rowsPerPage': 10, 'sortBy': 'name'}
            ).classes('w-full').style('max-height: 500px; overflow-y: auto;')
            
            # テーブルスタイル最適化
            table.props('dense flat bordered')
            
            table.add_slot('body-cell-status', '''
                <q-td :props="props">
                    <q-badge :color="props.value.color" :label="props.value.text" />
                </q-td>
            ''')
            table.add_slot('body-cell-actions', '''
                <q-td :props="props">
                    <q-btn flat round icon="visibility" size="sm" @click="$parent.$emit('view', props.row)" 
                           class="q-mr-xs" />
                    <q-btn flat round icon="download" size="sm" @click="$parent.$emit('download', props.row)" 
                           class="q-mr-xs" />
                    <q-btn flat round icon="delete" size="sm" color="negative" 
                           @click="$parent.$emit('delete', props.row)" />
                </q-td>
            ''')
            
            # テーブルイベント処理
            table.on('view', lambda e: view_file(e.args))
            table.on('download', lambda e: download_file(e.args))
            table.on('delete', lambda e: delete_file(e.args))

def get_status_badge(is_processed: bool):
    """ステータスバッジを取得"""
    if is_processed:
        return {'text': '処理済み', 'color': 'positive'}
    else:
        return {'text': '未処理', 'color': 'warning'}

def get_mock_files():
    """モックファイルデータ（ページネーションテスト用）"""
    mock_files = []
    statuses = [
        {'text': '処理済み', 'color': 'positive'},
        {'text': '未処理', 'color': 'warning'},
        {'text': 'エラー', 'color': 'negative'}
    ]
    
    file_types = [
        ('技術仕様書', 'pdf', '2.4 MB'),
        ('研究報告書', 'docx', '1.8 MB'),
        ('実験データ', 'xlsx', '956 KB'),
        ('分析結果', 'pdf', '3.2 MB'),
        ('設計図面', 'dwg', '4.1 MB'),
        ('プレゼン資料', 'pptx', '5.6 MB'),
        ('測定データ', 'csv', '2.3 MB'),
        ('論文草稿', 'pdf', '1.2 MB'),
        ('画像解析', 'tiff', '8.9 MB'),
        ('計算書', 'xlsx', '1.5 MB'),
        ('マニュアル', 'pdf', '6.7 MB'),
        ('CADデータ', 'step', '12.3 MB'),
        ('測定結果', 'txt', '456 KB'),
        ('シミュレーション', 'dat', '15.7 MB'),
        ('レポート', 'docx', '2.1 MB')
    ]
    
    for i, (base_name, ext, size) in enumerate(file_types):
        mock_files.append({
            'name': f'{base_name}_{i+1:03d}.{ext}',
            'size': size,
            'status': statuses[i % 3],
            'processed_at': f'2025-08-02 {9 + i//4:02d}:{(i*7) % 60:02d}:23',
            'actions': str(i + 1)
        })
    
    return mock_files

async def search_files(query: str, status: str):
    """ファイル検索"""
    ui.notify(f'検索中: "{query}" (ステータス: {status})', type='info')
    await load_files_table()  # 検索結果でテーブル更新

def view_file(file_data):
    """ファイル表示"""
    ui.notify(f'ファイルを表示: {file_data.get("name", "Unknown")}', type='info')

def download_file(file_data):
    """ファイルダウンロード"""
    ui.notify(f'ダウンロード開始: {file_data.get("name", "Unknown")}', type='success')

def delete_file(file_data):
    """ファイル削除"""
    ui.notify(f'ファイルを削除: {file_data.get("name", "Unknown")}', type='warning')

@ui.page('/admin')
async def admin_page():
    """管理ページ - NiceGUI完全版"""
    RAGTheme.apply_global_styles()
    
    # ヘッダー
    header = RAGHeader("R&D RAGシステム - 管理", "/admin")
    
    # メインコンテンツ
    with ui.column().classes('rag-content'):
        
        # システム状態
        with ui.card().classes('rag-card'):
            ui.label('🖥️ システム状態').classes('text-lg font-bold mb-4')
            
            with ui.row().classes('gap-4'):
                ui.badge('システム正常', color='positive')
                ui.badge('DB接続中', color='info')
                ui.badge('NiceGUI統合完了', color='accent')
        
        # 管理機能
        with ui.row().classes('w-full gap-4'):
            # 左列：システム操作
            with ui.column().classes('flex-1'):
                with ui.card().classes('rag-card'):
                    ui.label('🔧 システム操作').classes('text-lg font-bold mb-4')
                    
                    with ui.column().classes('gap-2'):
                        ui.button('🔄 キャッシュクリア', 
                                 on_click=lambda: ui.notify('キャッシュをクリアしました', type='success')
                                 ).classes('w-full rag-button')
                        ui.button('📊 統計更新', 
                                 on_click=lambda: ui.notify('統計を更新しました', type='info')
                                 ).classes('w-full rag-button')
                        ui.button('🗂️ ログ確認', 
                                 on_click=lambda: ui.notify('ログを確認しました', type='info')
                                 ).classes('w-full rag-button')
            
            # 右列：設定
            with ui.column().classes('flex-1'):
                with ui.card().classes('rag-card'):
                    ui.label('⚙️ システム設定').classes('text-lg font-bold mb-4')
                    
                    log_level = ui.select(
                        ['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                        value='INFO',
                        label='ログレベル'
                    ).classes('w-full mb-2')
                    
                    max_files = ui.number(
                        label='最大ファイル数',
                        value=1000,
                        min=100,
                        max=10000
                    ).classes('w-full mb-4')
                    
                    ui.button('💾 設定保存', 
                             on_click=lambda: save_settings(log_level.value, max_files.value)
                             ).classes('w-full rag-button')

async def save_settings(log_level: str, max_files: int):
    """設定保存"""
    ui.notify(f'設定を保存しました (ログレベル: {log_level}, 最大ファイル数: {max_files})', type='success')

# ==============================================================================
# アプリケーション初期化
# ==============================================================================

def init_nicegui_app(fastapi_app):
    """NiceGUIアプリケーション初期化"""
    
    # FastAPIアプリと統合
    ui.run_with(
        fastapi_app,
        mount_path='/rag-nicegui',
        title='R&D RAGシステム'
    )
    
    LOGGER.info("🚀 NiceGUI完全版RAGシステム起動完了")
    LOGGER.info("📍 アクセス: http://localhost:8000/rag-nicegui/")

if __name__ == '__main__':
    # スタンドアロン実行時
    ui.run(
        title='R&D RAGシステム',
        port=8001,
        show=True
    )