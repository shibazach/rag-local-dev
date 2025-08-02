# new/routes/nicegui_admin.py
# NiceGUI管理画面統合

from nicegui import ui, app
from fastapi import Depends
from typing import List, Dict, Any
import asyncio
from datetime import datetime

from new.auth import get_current_user
from new.config import LOGGER

# サンプルデータ
sample_queue_data = [
    {
        'id': 1,
        'file_name': 'document1.pdf',
        'status': '処理中',
        'priority': '高',
        'created_at': '2024-01-15 10:30:00',
        'progress': 75
    },
    {
        'id': 2,
        'file_name': 'report2.docx',
        'status': '待機中',
        'priority': '中',
        'created_at': '2024-01-15 11:15:00',
        'progress': 0
    },
    {
        'id': 3,
        'file_name': 'data3.csv',
        'status': '完了',
        'priority': '低',
        'created_at': '2024-01-15 09:45:00',
        'progress': 100
    },
    {
        'id': 4,
        'file_name': 'image4.png',
        'status': 'エラー',
        'priority': '高',
        'created_at': '2024-01-15 12:00:00',
        'progress': 30
    },
    {
        'id': 5,
        'file_name': 'presentation5.pptx',
        'status': '処理中',
        'priority': '中',
        'created_at': '2024-01-15 13:20:00',
        'progress': 45
    }
]

def create_queue_table():
    """処理キューテーブルを作成"""
    
    # テーブルのカラム定義
    columns = [
        {'name': 'id', 'label': 'ID', 'field': 'id', 'sortable': True, 'align': 'center'},
        {'name': 'file_name', 'label': 'ファイル名', 'field': 'file_name', 'sortable': True, 'align': 'left'},
        {'name': 'status', 'label': 'ステータス', 'field': 'status', 'sortable': True, 'align': 'center'},
        {'name': 'priority', 'label': '優先度', 'field': 'priority', 'sortable': True, 'align': 'center'},
        {'name': 'progress', 'label': '進捗', 'field': 'progress', 'sortable': True, 'align': 'center'},
        {'name': 'created_at', 'label': '作成日時', 'field': 'created_at', 'sortable': True, 'align': 'center'},
    ]
    
    # テーブル作成
    with ui.card().classes('w-full'):
        ui.label('📊 処理キューテーブル（NiceGUI サンプル）').classes('text-lg font-bold mb-4')
        
        # 更新ボタン
        with ui.row().classes('mb-4'):
            refresh_btn = ui.button('🔄 更新', on_click=lambda: refresh_table())
            refresh_btn.classes('bg-blue-500 hover:bg-blue-600 text-white')
            
            process_btn = ui.button('▶️ 処理実行', on_click=lambda: process_selected())
            process_btn.classes('bg-green-500 hover:bg-green-600 text-white ml-2')
            
            clear_btn = ui.button('🗑️ クリア', on_click=lambda: clear_completed())
            clear_btn.classes('bg-red-500 hover:bg-red-600 text-white ml-2')
        
        # テーブル
        table = ui.table(
            columns=columns,
            rows=sample_queue_data,
            selection='multiple',
            pagination=10
        ).classes('w-full')
        
        # テーブルのスタイリング
        table.classes('shadow-lg')
        
        # ステータス別の色分け
        def format_status(status):
            colors = {
                '処理中': 'bg-blue-100 text-blue-800',
                '待機中': 'bg-yellow-100 text-yellow-800',
                '完了': 'bg-green-100 text-green-800',
                'エラー': 'bg-red-100 text-red-800'
            }
            return colors.get(status, 'bg-gray-100 text-gray-800')
        
        # 進捗バーの追加
        def format_progress(progress):
            color = 'bg-green-500' if progress == 100 else 'bg-blue-500' if progress > 0 else 'bg-gray-300'
            return f'<div class="w-full bg-gray-200 rounded-full h-2"><div class="{color} h-2 rounded-full" style="width: {progress}%"></div></div>'
        
        # テーブルのカスタムレンダリング
        table.add_slot('body-cell-status', '''
            <q-td :props="props">
                <q-badge :class="props.value === '処理中' ? 'bg-blue text-white' : 
                                props.value === '待機中' ? 'bg-yellow text-black' :
                                props.value === '完了' ? 'bg-green text-white' : 'bg-red text-white'">
                    {{ props.value }}
                </q-badge>
            </q-td>
        ''')
        
        table.add_slot('body-cell-progress', '''
            <q-td :props="props">
                <q-linear-progress 
                    :value="props.value / 100" 
                    :color="props.value === 100 ? 'green' : props.value > 0 ? 'blue' : 'grey'"
                    size="md"
                    class="q-mt-sm"
                />
                <div class="text-center text-xs">{{ props.value }}%</div>
            </q-td>
        ''')
        
        # 統計情報
        with ui.row().classes('mt-4 w-full'):
            with ui.card().classes('flex-1 p-4'):
                ui.label('📈 統計情報').classes('text-md font-bold mb-2')
                total_tasks = len(sample_queue_data)
                completed = len([t for t in sample_queue_data if t['status'] == '完了'])
                processing = len([t for t in sample_queue_data if t['status'] == '処理中'])
                waiting = len([t for t in sample_queue_data if t['status'] == '待機中'])
                errors = len([t for t in sample_queue_data if t['status'] == 'エラー'])
                
                ui.label(f'総タスク数: {total_tasks}').classes('text-sm')
                ui.label(f'完了: {completed} | 処理中: {processing} | 待機中: {waiting} | エラー: {errors}').classes('text-sm text-gray-600')
                
                completion_rate = (completed / total_tasks * 100) if total_tasks > 0 else 0
                ui.label(f'完了率: {completion_rate:.1f}%').classes('text-sm font-bold text-green-600')
    
    return table

def refresh_table():
    """テーブルデータを更新"""
    ui.notify('テーブルを更新しました', type='positive')
    # 実際の実装では、ここでAPIからデータを取得して更新

def process_selected():
    """選択されたタスクを処理"""
    ui.notify('選択されたタスクの処理を開始しました', type='info')
    # 実際の実装では、選択されたタスクの処理を実行

def clear_completed():
    """完了したタスクをクリア"""
    ui.notify('完了したタスクをクリアしました', type='warning')
    # 実際の実装では、完了したタスクをデータベースから削除

@ui.page('/admin/nicegui-admin')
async def nicegui_admin_full():
    """管理画面全体をNiceGUIで置き換え"""
    
    ui.page_title('RAGシステム管理 - NiceGUI版')
    
    # ヘッダー
    with ui.header().classes('bg-slate-800 text-white'):
        with ui.row().classes('w-full items-center justify-between px-4'):
            ui.label('🔧 R&D RAGシステム | 管理').classes('text-xl font-bold')
            with ui.row().classes('gap-2'):
                ui.button('利用', on_click=lambda: ui.open('/')).classes('bg-blue-600 hover:bg-blue-700')
                ui.button('管理', on_click=lambda: ui.open('/admin')).classes('bg-gray-600 hover:bg-gray-700')
    
    # メインコンテンツ
    with ui.column().classes('w-full max-w-7xl mx-auto p-4'):
        
        # システム統計
        with ui.card().classes('w-full mb-6'):
            ui.label('システム統計').classes('text-2xl font-bold mb-4')
            
            with ui.row().classes('w-full gap-4'):
                # 統計カード
                with ui.card().classes('flex-1 text-center p-4'):
                    ui.label('32').classes('text-3xl font-bold text-blue-600')
                    ui.label('総ファイル数').classes('text-sm text-gray-600')
                
                with ui.card().classes('flex-1 text-center p-4'):
                    ui.label('5').classes('text-3xl font-bold text-green-600')
                    ui.label('処理済みファイル').classes('text-sm text-gray-600')
                
                with ui.card().classes('flex-1 text-center p-4'):
                    ui.label('0').classes('text-3xl font-bold text-orange-600')
                    ui.label('テキストチャンク').classes('text-sm text-gray-600')
                
                with ui.card().classes('flex-1 text-center p-4'):
                    ui.label('15.6%').classes('text-3xl font-bold text-purple-600')
                    ui.label('処理率').classes('text-sm text-gray-600')
        
        # タブ
        with ui.tabs().classes('w-full') as tabs:
            queue_tab = ui.tab('処理キュー管理')
            logs_tab = ui.tab('システムログ監視')
            search_tab = ui.tab('検索機能')
        
        with ui.tab_panels(tabs, value=queue_tab).classes('w-full'):
            # 処理キュー管理タブ
            with ui.tab_panel(queue_tab):
                # コントロールボタン
                with ui.row().classes('w-full gap-4 mb-4'):
                    ui.button('🔄 更新', on_click=lambda: refresh_queue_nicegui()).classes('bg-blue-500 hover:bg-blue-600 text-white')
                    ui.button('▶️ 全タスク処理', on_click=lambda: process_all_queue_nicegui()).classes('bg-green-500 hover:bg-green-600 text-white')
                    ui.button('⏳ 待機タスク処理', on_click=lambda: process_pending_queue_nicegui()).classes('bg-yellow-500 hover:bg-yellow-600 text-white')
                
                # 処理キューテーブル（固定サイズ、7件/頁）
                create_queue_table_fixed()
            
            # システムログ監視タブ
            with ui.tab_panel(logs_tab):
                with ui.row().classes('w-full gap-4 mb-4'):
                    log_level = ui.select(
                        options=['全レベル', 'エラーのみ', '警告のみ'],
                        value='全レベル'
                    ).classes('w-32')
                    ui.button('🔄 更新', on_click=lambda: refresh_logs_nicegui()).classes('bg-blue-500 hover:bg-blue-600 text-white')
                    ui.button('🗑️ ログクリア', on_click=lambda: clear_logs_nicegui()).classes('bg-red-500 hover:bg-red-600 text-white')
                
                # ログ表示エリア
                with ui.card().classes('w-full h-96'):
                    ui.label('ログを読み込み中...').classes('text-gray-600')
            
            # 検索機能タブ
            with ui.tab_panel(search_tab):
                with ui.row().classes('w-full gap-4 mb-4'):
                    search_input = ui.input('検索クエリを入力...').classes('flex-1')
                    ui.button('🔍 検索', on_click=lambda: perform_search_nicegui()).classes('bg-blue-500 hover:bg-blue-600 text-white')
                
                # 検索結果表示エリア
                with ui.card().classes('w-full h-96'):
                    ui.label('検索結果がここに表示されます').classes('text-gray-600')

def create_queue_table_fixed():
    """固定サイズの処理キューテーブル（7件/頁、スクロール対応）"""
    
    # テーブルデータ（10件のサンプルデータ）
    table_data = [
        {'id': 1, 'file_name': 'document1.pdf', 'status': '処理中', 'priority': '高', 'progress': 75, 'created_at': '2024-01-15 10:30'},
        {'id': 2, 'file_name': 'report2.docx', 'status': '待機中', 'priority': '中', 'progress': 0, 'created_at': '2024-01-15 11:15'},
        {'id': 3, 'file_name': 'data3.csv', 'status': '完了', 'priority': '低', 'progress': 100, 'created_at': '2024-01-15 09:45'},
        {'id': 4, 'file_name': 'image4.png', 'status': 'エラー', 'priority': '高', 'progress': 30, 'created_at': '2024-01-15 12:00'},
        {'id': 5, 'file_name': 'presentation5.pptx', 'status': '処理中', 'priority': '中', 'progress': 45, 'created_at': '2024-01-15 13:20'},
        {'id': 6, 'file_name': 'spreadsheet6.xlsx', 'status': '完了', 'priority': '低', 'progress': 100, 'created_at': '2024-01-15 14:10'},
        {'id': 7, 'file_name': 'archive7.zip', 'status': '待機中', 'priority': '中', 'progress': 0, 'created_at': '2024-01-15 15:00'},
        {'id': 8, 'file_name': 'video8.mp4', 'status': 'エラー', 'priority': '高', 'progress': 20, 'created_at': '2024-01-15 16:30'},
        {'id': 9, 'file_name': 'audio9.wav', 'status': '処理中', 'priority': '中', 'progress': 60, 'created_at': '2024-01-15 17:45'},
        {'id': 10, 'file_name': 'text10.txt', 'status': '完了', 'priority': '低', 'progress': 100, 'created_at': '2024-01-15 18:20'}
    ]
    
    # テーブルカラム定義
    columns = [
        {'name': 'id', 'label': 'ID', 'field': 'id', 'sortable': True, 'align': 'center'},
        {'name': 'file_name', 'label': 'ファイル名', 'field': 'file_name', 'sortable': True, 'align': 'left'},
        {'name': 'status', 'label': 'ステータス', 'field': 'status', 'sortable': True, 'align': 'center'},
        {'name': 'priority', 'label': '優先度', 'field': 'priority', 'sortable': True, 'align': 'center'},
        {'name': 'progress', 'label': '進捗', 'field': 'progress', 'sortable': True, 'align': 'center'},
        {'name': 'created_at', 'label': '作成日時', 'field': 'created_at', 'sortable': True, 'align': 'center'},
    ]
    
    # 固定サイズテーブル（高さ400px、7件/頁）
    with ui.card().classes('w-full'):
        ui.label('📊 処理キューテーブル（固定サイズ・7件/頁）').classes('text-lg font-bold mb-4')
        
        # テーブル作成（固定高さ、ページネーション7件）
        table = ui.table(
            columns=columns,
            rows=table_data,
            pagination={'rowsPerPage': 7, 'page': 1},
            selection='multiple'
        ).classes('w-full').style('height: 400px; overflow-y: auto;')
        
        # ステータスバッジのカスタムレンダリング
        table.add_slot('body-cell-status', '''
            <q-td :props="props">
                <q-badge :class="props.value === '処理中' ? 'bg-blue text-white' : 
                                props.value === '待機中' ? 'bg-yellow text-black' :
                                props.value === '完了' ? 'bg-green text-white' : 'bg-red text-white'">
                    {{ props.value }}
                </q-badge>
            </q-td>
        ''')
        
        # 進捗バーのカスタムレンダリング
        table.add_slot('body-cell-progress', '''
            <q-td :props="props">
                <q-linear-progress 
                    :value="props.value / 100" 
                    :color="props.value === 100 ? 'green' : props.value > 0 ? 'blue' : 'grey'"
                    size="md"
                    class="q-mt-sm"
                />
                <div class="text-center text-xs">{{ props.value }}%</div>
            </q-td>
        ''')
        
        # 統計情報
        with ui.row().classes('w-full mt-4 gap-4'):
            with ui.card().classes('flex-1 text-center p-4'):
                ui.label('10').classes('text-2xl font-bold text-blue-600')
                ui.label('総タスク数').classes('text-sm text-gray-600')
            
            with ui.card().classes('flex-1 text-center p-4'):
                ui.label('3').classes('text-2xl font-bold text-green-600')
                ui.label('完了').classes('text-sm text-gray-600')
            
            with ui.card().classes('flex-1 text-center p-4'):
                ui.label('3').classes('text-2xl font-bold text-orange-600')
                ui.label('処理中').classes('text-sm text-gray-600')
            
            with ui.card().classes('flex-1 text-center p-4'):
                ui.label('2').classes('text-2xl font-bold text-red-600')
                ui.label('エラー').classes('text-sm text-gray-600')

def refresh_queue_nicegui():
    """キューを更新（NiceGUI版）"""
    ui.notify('キューを更新しました', type='positive')

def process_all_queue_nicegui():
    """全タスクを処理（NiceGUI版）"""
    ui.notify('全タスクの処理を開始しました', type='info')

def process_pending_queue_nicegui():
    """待機タスクを処理（NiceGUI版）"""
    ui.notify('待機タスクの処理を開始しました', type='warning')

def refresh_logs_nicegui():
    """ログを更新（NiceGUI版）"""
    ui.notify('ログを更新しました', type='positive')

def clear_logs_nicegui():
    """ログをクリア（NiceGUI版）"""
    ui.notify('ログをクリアしました', type='warning')

def perform_search_nicegui():
    """検索を実行（NiceGUI版）"""
    ui.notify('検索を実行しました', type='info')

def refresh_queue():
    """キューを更新"""
    ui.notify('キューを更新しました', type='positive')
    # 親ウィンドウの関数を呼び出し
    ui.run_javascript('parent.refreshTasks()')

def process_all_queue():
    """全タスクを処理"""
    ui.notify('全タスクの処理を開始しました', type='info')
    # 親ウィンドウの関数を呼び出し
    ui.run_javascript('parent.processAllTasks()')

def process_pending_queue():
    """待機タスクを処理"""
    ui.notify('待機タスクの処理を開始しました', type='warning')
    # 親ウィンドウの関数を呼び出し
    ui.run_javascript('parent.processPendingTasks()')

@ui.page('/admin/nicegui-log-controls')
async def nicegui_log_controls():
    """システムログ監視タブのNiceGUIコントロール"""
    
    ui.page_title('ログコントロール')
    
    with ui.row().classes('w-full items-center gap-4 p-2'):
        # ログレベルフィルター
        with ui.column().classes('flex-shrink-0'):
            ui.label('ログレベル:').classes('text-xs text-gray-600 mb-1')
            log_level_select = ui.select(
                options=[
                    {'label': '全レベル', 'value': ''},
                    {'label': 'エラーのみ', 'value': 'ERROR'},
                    {'label': '警告のみ', 'value': 'WARNING'}
                ],
                value='',
                on_change=lambda e: on_log_level_change(e.value)
            ).classes('w-32')
        
        # 更新ボタン
        refresh_logs_btn = ui.button('🔄 更新', on_click=lambda: refresh_logs_nicegui())
        refresh_logs_btn.classes('bg-blue-500 hover:bg-blue-600 text-white px-4 py-2')
        
        # ログクリアボタン
        clear_logs_btn = ui.button('🗑️ ログクリア', on_click=lambda: clear_logs_nicegui())
        clear_logs_btn.classes('bg-red-500 hover:bg-red-600 text-white px-4 py-2')
        
        # ログ出力ボタン
        export_logs_btn = ui.button('📄 ログ出力', on_click=lambda: export_logs_nicegui())
        export_logs_btn.classes('bg-gray-500 hover:bg-gray-600 text-white px-4 py-2')
        
        # ステータス表示
        with ui.column().classes('ml-auto'):
            status_label = ui.label('ログ監視中...').classes('text-sm text-gray-600')

def on_log_level_change(level):
    """ログレベル変更時の処理"""
    ui.notify(f'ログレベルを変更: {level or "全レベル"}', type='info')
    # 親ウィンドウのログレベルフィルターを更新
    ui.run_javascript(f'parent.document.getElementById("log-level-filter").value = "{level}"; parent.refreshLogs()')

def refresh_logs_nicegui():
    """ログを更新"""
    ui.notify('ログを更新しました', type='positive')
    # 親ウィンドウの関数を呼び出し
    ui.run_javascript('parent.refreshLogs()')

def clear_logs_nicegui():
    """ログをクリア"""
    ui.notify('ログをクリアしました', type='warning')
    # 親ウィンドウの関数を呼び出し
    ui.run_javascript('parent.clearLogs()')

def export_logs_nicegui():
    """ログを出力"""
    ui.notify('ログを出力しました', type='info')
    # 実際の実装では、ログファイルのダウンロード処理

@ui.page('/admin/nicegui-table')
async def nicegui_table_embedded():
    """管理画面に埋め込み用のシンプルなNiceGUIテーブル"""
    
    ui.page_title('処理キューテーブル')
    
    # シンプルなテーブル作成
    with ui.column().classes('w-full p-4'):
        
        # ヘッダー
        with ui.row().classes('w-full items-center mb-4'):
            ui.label('📊 処理キューテーブル').classes('text-lg font-bold')
            
            # 更新ボタン
            refresh_btn = ui.button('🔄 更新', on_click=lambda: refresh_embedded_table())
            refresh_btn.classes('bg-blue-500 hover:bg-blue-600 text-white ml-auto')
        
        # テーブル
        columns = [
            {'name': 'id', 'label': 'ID', 'field': 'id', 'sortable': True, 'align': 'center'},
            {'name': 'file_name', 'label': 'ファイル名', 'field': 'file_name', 'sortable': True, 'align': 'left'},
            {'name': 'status', 'label': 'ステータス', 'field': 'status', 'sortable': True, 'align': 'center'},
            {'name': 'priority', 'label': '優先度', 'field': 'priority', 'sortable': True, 'align': 'center'},
            {'name': 'progress', 'label': '進捗', 'field': 'progress', 'sortable': True, 'align': 'center'},
            {'name': 'created_at', 'label': '作成日時', 'field': 'created_at', 'sortable': True, 'align': 'center'},
        ]
        
        global embedded_table
        embedded_table = ui.table(
            columns=columns,
            rows=sample_queue_data,
            selection='multiple',
            pagination=5
        ).classes('w-full shadow-lg')
        
        # ステータスバッジのカスタムレンダリング
        embedded_table.add_slot('body-cell-status', '''
            <q-td :props="props">
                <q-badge :class="props.value === '処理中' ? 'bg-blue text-white' : 
                                props.value === '待機中' ? 'bg-yellow text-black' :
                                props.value === '完了' ? 'bg-green text-white' : 'bg-red text-white'">
                    {{ props.value }}
                </q-badge>
            </q-td>
        ''')
        
        # 進捗バーのカスタムレンダリング
        embedded_table.add_slot('body-cell-progress', '''
            <q-td :props="props">
                <q-linear-progress 
                    :value="props.value / 100" 
                    :color="props.value === 100 ? 'green' : props.value > 0 ? 'blue' : 'grey'"
                    size="md"
                    class="q-mt-sm"
                />
                <div class="text-center text-xs">{{ props.value }}%</div>
            </q-td>
        ''')
        
        # 統計情報（コンパクト版）
        with ui.row().classes('w-full mt-4'):
            total_tasks = len(sample_queue_data)
            completed = len([t for t in sample_queue_data if t['status'] == '完了'])
            processing = len([t for t in sample_queue_data if t['status'] == '処理中'])
            
            ui.label(f'総数: {total_tasks}').classes('text-sm bg-gray-100 px-2 py-1 rounded')
            ui.label(f'完了: {completed}').classes('text-sm bg-green-100 text-green-800 px-2 py-1 rounded ml-2')
            ui.label(f'処理中: {processing}').classes('text-sm bg-blue-100 text-blue-800 px-2 py-1 rounded ml-2')

def refresh_embedded_table():
    """埋め込みテーブルを更新"""
    ui.notify('テーブルを更新しました', type='positive')
    # 実際の実装では、ここでAPIからデータを取得して更新
    if 'embedded_table' in globals():
        embedded_table.update()

@ui.page('/admin/nicegui-demo')
async def nicegui_admin_demo():
    """NiceGUI管理画面デモページ"""
    
    ui.page_title('RAGシステム管理 - NiceGUI Demo')
    
    with ui.header().classes('bg-blue-600 text-white'):
        ui.label('🔧 RAGシステム管理画面 (NiceGUI Demo)').classes('text-xl font-bold')
        
        with ui.row().classes('ml-auto'):
            ui.button('🏠 メイン画面', on_click=lambda: ui.open('/admin')).classes('bg-blue-500 hover:bg-blue-400')
    
    with ui.column().classes('w-full max-w-7xl mx-auto p-4'):
        
        # ヘッダー情報
        with ui.card().classes('w-full mb-4'):
            ui.label('NiceGUIテーブルサンプル').classes('text-2xl font-bold mb-2')
            ui.label('このページは、NiceGUIライブラリを使用したテーブル表示のデモンストレーションです。').classes('text-gray-600')
            ui.separator()
            
            # 機能説明
            with ui.expansion('📋 機能説明', icon='info').classes('mt-2'):
                ui.markdown('''
                **NiceGUIテーブルの特徴:**
                - ✅ ソート機能（カラムヘッダークリック）
                - ✅ 複数選択機能（チェックボックス）
                - ✅ ページネーション（10件ずつ表示）
                - ✅ カスタムレンダリング（ステータスバッジ、進捗バー）
                - ✅ リアルタイム更新対応
                - ✅ レスポンシブデザイン
                
                **操作方法:**
                - 行をクリックして選択
                - 複数行選択可能
                - 更新ボタンでデータ再読み込み
                - 処理実行ボタンで選択タスク処理
                ''')
        
        # メインテーブル
        create_queue_table()
        
        # フッター
        with ui.card().classes('w-full mt-4'):
            ui.label('💡 このテーブルは既存の管理画面に統合可能です').classes('text-sm text-gray-600')
            ui.label('実装時は、FastAPIのエンドポイントと連携してリアルタイムデータを表示します').classes('text-sm text-gray-600')

# FastAPIアプリケーションにNiceGUIを統合
def init_nicegui_routes(app):
    """NiceGUIルートを初期化"""
    ui.run_with(app, mount_path='/nicegui')
    LOGGER.info("NiceGUIルート初期化完了: /admin/nicegui-table, /admin/nicegui-demo")
@u
i.page('/files/nicegui')
async def nicegui_files():
    """Files頁のNiceGUI版"""
    
    ui.page_title('R&D RAGシステム - ファイル管理')
    
    # ヘッダー
    with ui.header().classes('bg-green-600 text-white'):
        with ui.row().classes('w-full items-center justify-between px-4'):
            ui.label('📁 R&D RAGシステム | ファイル管理').classes('text-xl font-bold')
            with ui.row().classes('gap-2'):
                ui.button('利用', on_click=lambda: ui.open('/')).classes('bg-blue-500 hover:bg-blue-400')
                ui.button('管理', on_click=lambda: ui.open('/admin')).classes('bg-gray-600 hover:bg-gray-700')
    
    # メインレイアウト
    with ui.splitter(value=25).classes('w-full h-screen') as splitter:
        # 左サイドパネル（フィルタ・操作）
        with splitter.before:
            with ui.column().classes('w-full h-full p-4 bg-gray-50'):
                ui.label('🔍 フィルタ・操作').classes('text-lg font-bold mb-4')
                
                # ファイルアップロード
                with ui.expansion('📤 ファイルアップロード', icon='upload').classes('w-full mb-4'):
                    with ui.column().classes('gap-3 p-2'):
                        # ファイルアップロード
                        upload_area = ui.upload(
                            on_upload=lambda e: handle_file_upload_files(e),
                            multiple=True,
                            max_file_size=50_000_000  # 50MB
                        ).props('accept=".pdf,.txt,.docx,.xlsx,.pptx,.jpg,.png"').classes('w-full')
                        
                        # アップロード統計
                        with ui.card().classes('w-full'):
                            ui.label('アップロード統計').classes('font-bold mb-2')
                            upload_stats = ui.column().classes('gap-1')
                            ui.label('今日: 0件').classes('text-sm')
                            ui.label('今月: 0件').classes('text-sm')
                            ui.label('総計: 0件').classes('text-sm')
                
                # フィルタ設定
                with ui.expansion('🔍 フィルタ設定', icon='filter_list').classes('w-full mb-4'):
                    with ui.column().classes('gap-3 p-2'):
                        # ファイル種別フィルタ
                        file_type_filter = ui.select(
                            options=[
                                {'label': '全ての種別', 'value': 'all'},
                                {'label': 'PDF', 'value': 'pdf'},
                                {'label': 'Word文書', 'value': 'docx'},
                                {'label': 'Excel', 'value': 'xlsx'},
                                {'label': 'PowerPoint', 'value': 'pptx'},
                                {'label': 'テキスト', 'value': 'txt'},
                                {'label': '画像', 'value': 'image'}
                            ],
                            value='all',
                            label='ファイル種別'
                        ).classes('w-full')
                        
                        # ステータスフィルタ
                        status_filter = ui.select(
                            options=[
                                {'label': '全てのステータス', 'value': 'all'},
                                {'label': '未処理', 'value': 'pending'},
                                {'label': '処理中', 'value': 'processing'},
                                {'label': '完了', 'value': 'completed'},
                                {'label': 'エラー', 'value': 'error'}
                            ],
                            value='all',
                            label='処理ステータス'
                        ).classes('w-full')
                        
                        # 日付範囲フィルタ
                        date_range = ui.select(
                            options=[
                                {'label': '全期間', 'value': 'all'},
                                {'label': '今日', 'value': 'today'},
                                {'label': '今週', 'value': 'week'},
                                {'label': '今月', 'value': 'month'},
                                {'label': '3ヶ月', 'value': '3months'}
                            ],
                            value='all',
                            label='作成日時'
                        ).classes('w-full')
                        
                        # フィルタ適用ボタン
                        ui.button('🔍 フィルタ適用', on_click=lambda: apply_filters()).classes('w-full bg-blue-500 hover:bg-blue-600 text-white')
                        ui.button('🔄 リセット', on_click=lambda: reset_filters()).classes('w-full bg-gray-500 hover:bg-gray-600 text-white')
                
                # ファイル操作
                with ui.expansion('⚙️ ファイル操作', icon='settings').classes('w-full mb-4'):
                    with ui.column().classes('gap-2 p-2'):
                        ui.button('📥 選択ファイルダウンロード', on_click=lambda: download_selected()).classes('w-full bg-green-500 hover:bg-green-600 text-white')
                        ui.button('🗑️ 選択ファイル削除', on_click=lambda: delete_selected()).classes('w-full bg-red-500 hover:bg-red-600 text-white')
                        ui.button('🔄 選択ファイル再処理', on_click=lambda: reprocess_selected()).classes('w-full bg-orange-500 hover:bg-orange-600 text-white')
                        
                        ui.separator()
                        
                        # 一括操作
                        ui.label('一括操作').classes('font-bold text-sm')
                        ui.button('✅ 全て選択', on_click=lambda: select_all_files()).classes('w-full bg-blue-400 hover:bg-blue-500 text-white text-sm')
                        ui.button('❌ 選択解除', on_click=lambda: deselect_all_files()).classes('w-full bg-gray-400 hover:bg-gray-500 text-white text-sm')
                
                # ファイル統計
                with ui.expansion('📊 ファイル統計', icon='analytics').classes('w-full'):
                    with ui.column().classes('gap-3 p-2'):
                        # 統計カード
                        with ui.row().classes('w-full gap-2'):
                            with ui.card().classes('flex-1 text-center p-2'):
                                ui.label('25').classes('text-lg font-bold text-blue-600')
                                ui.label('総ファイル数').classes('text-xs')
                            
                            with ui.card().classes('flex-1 text-center p-2'):
                                ui.label('15').classes('text-lg font-bold text-green-600')
                                ui.label('処理済み').classes('text-xs')
                        
                        with ui.row().classes('w-full gap-2'):
                            with ui.card().classes('flex-1 text-center p-2'):
                                ui.label('8').classes('text-lg font-bold text-orange-600')
                                ui.label('処理中').classes('text-xs')
                            
                            with ui.card().classes('flex-1 text-center p-2'):
                                ui.label('2').classes('text-lg font-bold text-red-600')
                                ui.label('エラー').classes('text-xs')
        
        # メインファイル一覧エリア
        with splitter.after:
            with ui.column().classes('w-full h-full p-4'):
                # 検索バー
                with ui.card().classes('w-full mb-4'):
                    with ui.row().classes('w-full items-center gap-4 p-4'):
                        search_input = ui.input(
                            placeholder='ファイル名で検索...'
                        ).classes('flex-1')
                        ui.button('🔍 検索', on_click=lambda: search_files()).classes('bg-blue-500 hover:bg-blue-600 text-white')
                        ui.button('🔄 更新', on_click=lambda: refresh_files()).classes('bg-green-500 hover:bg-green-600 text-white')
                
                # ファイル一覧テーブル（固定サイズ、ページネーション）
                create_files_table()

def create_files_table():
    """ファイル一覧テーブルを作成（固定サイズ、ページネーション対応）"""
    
    # サンプルファイルデータ（25件）
    files_data = []
    file_types = ['pdf', 'docx', 'xlsx', 'pptx', 'txt', 'jpg', 'png']
    statuses = ['未処理', '処理中', '完了', 'エラー']
    
    for i in range(1, 26):
        files_data.append({
            'id': i,
            'file_name': f'document_{i:02d}.{file_types[(i-1) % len(file_types)]}',
            'size': f'{(i * 123 + 500) // 1024} KB',
            'created_at': f'2024-01-{(i % 30) + 1:02d} {10 + (i % 12)}:{(i * 7) % 60:02d}',
            'status': statuses[(i-1) % len(statuses)],
            'progress': (i * 17) % 101,
            'file_type': file_types[(i-1) % len(file_types)]
        })
    
    # テーブルカラム定義
    columns = [
        {'name': 'select', 'label': '', 'field': 'select', 'align': 'center'},
        {'name': 'file_name', 'label': 'ファイル名', 'field': 'file_name', 'sortable': True, 'align': 'left'},
        {'name': 'file_type', 'label': '種別', 'field': 'file_type', 'sortable': True, 'align': 'center'},
        {'name': 'size', 'label': 'サイズ', 'field': 'size', 'sortable': True, 'align': 'center'},
        {'name': 'status', 'label': 'ステータス', 'field': 'status', 'sortable': True, 'align': 'center'},
        {'name': 'progress', 'label': '進捗', 'field': 'progress', 'sortable': True, 'align': 'center'},
        {'name': 'created_at', 'label': '作成日時', 'field': 'created_at', 'sortable': True, 'align': 'center'},
        {'name': 'actions', 'label': '操作', 'field': 'actions', 'align': 'center'},
    ]
    
    # 固定サイズテーブル（高さ500px、10件/頁）
    with ui.card().classes('w-full'):
        ui.label('📁 ファイル一覧（25件中、10件/頁表示）').classes('text-lg font-bold mb-4')
        
        # テーブル作成（固定高さ、ページネーション10件）
        table = ui.table(
            columns=columns,
            rows=files_data,
            pagination={'rowsPerPage': 10, 'page': 1},
            selection='multiple'
        ).classes('w-full').style('height: 500px; overflow-y: auto;')
        
        # チェックボックス列のカスタムレンダリング
        table.add_slot('body-cell-select', '''
            <q-td :props="props">
                <q-checkbox v-model="props.selected" />
            </q-td>
        ''')
        
        # ファイル種別のカスタムレンダリング
        table.add_slot('body-cell-file_type', '''
            <q-td :props="props">
                <q-chip :class="props.value === 'pdf' ? 'bg-red text-white' : 
                               props.value === 'docx' ? 'bg-blue text-white' :
                               props.value === 'xlsx' ? 'bg-green text-white' :
                               props.value === 'pptx' ? 'bg-orange text-white' :
                               props.value === 'txt' ? 'bg-gray text-white' : 'bg-purple text-white'"
                        size="sm">
                    {{ props.value.toUpperCase() }}
                </q-chip>
            </q-td>
        ''')
        
        # ステータスバッジのカスタムレンダリング
        table.add_slot('body-cell-status', '''
            <q-td :props="props">
                <q-badge :class="props.value === '処理中' ? 'bg-blue text-white' : 
                                props.value === '未処理' ? 'bg-yellow text-black' :
                                props.value === '完了' ? 'bg-green text-white' : 'bg-red text-white'">
                    {{ props.value }}
                </q-badge>
            </q-td>
        ''')
        
        # 進捗バーのカスタムレンダリング
        table.add_slot('body-cell-progress', '''
            <q-td :props="props">
                <q-linear-progress 
                    :value="props.value / 100" 
                    :color="props.value === 100 ? 'green' : props.value > 50 ? 'blue' : 'orange'"
                    size="md"
                    class="q-mt-sm"
                />
                <div class="text-center text-xs">{{ props.value }}%</div>
            </q-td>
        ''')
        
        # 操作ボタンのカスタムレンダリング
        table.add_slot('body-cell-actions', '''
            <q-td :props="props">
                <q-btn-group>
                    <q-btn size="sm" color="blue" icon="visibility" @click="previewFile(props.row)" />
                    <q-btn size="sm" color="green" icon="download" @click="downloadFile(props.row)" />
                    <q-btn size="sm" color="red" icon="delete" @click="deleteFile(props.row)" />
                </q-btn-group>
            </q-td>
        ''')
        
        # 選択されたファイル数の表示
        with ui.row().classes('w-full mt-4 justify-between items-center'):
            selected_count = ui.label('選択: 0件').classes('text-sm text-gray-600')
            
            with ui.row().classes('gap-2'):
                ui.button('📥 選択ファイルダウンロード', on_click=lambda: download_selected_files()).classes('bg-green-500 hover:bg-green-600 text-white')
                ui.button('🗑️ 選択ファイル削除', on_click=lambda: delete_selected_files()).classes('bg-red-500 hover:bg-red-600 text-white')

# ファイル操作関数群
def handle_file_upload_files(event):
    """ファイルアップロード処理（Files版）"""
    ui.notify(f'ファイル「{event.name}」をアップロードしました', type='positive')

def apply_filters():
    """フィルタを適用"""
    ui.notify('フィルタを適用しました', type='info')

def reset_filters():
    """フィルタをリセット"""
    ui.notify('フィルタをリセットしました', type='warning')

def download_selected():
    """選択ファイルをダウンロード"""
    ui.notify('選択されたファイルをダウンロードします', type='positive')

def delete_selected():
    """選択ファイルを削除"""
    ui.notify('選択されたファイルを削除します', type='negative')

def reprocess_selected():
    """選択ファイルを再処理"""
    ui.notify('選択されたファイルを再処理します', type='info')

def select_all_files():
    """全ファイルを選択"""
    ui.notify('全てのファイルを選択しました', type='info')

def deselect_all_files():
    """全ファイル選択を解除"""
    ui.notify('選択を解除しました', type='info')

def search_files():
    """ファイルを検索"""
    ui.notify('ファイル検索を実行しました', type='info')

def refresh_files():
    """ファイル一覧を更新"""
    ui.notify('ファイル一覧を更新しました', type='positive')

def download_selected_files():
    """選択されたファイルをダウンロード"""
    ui.notify('選択されたファイルをダウンロードします', type='positive')

def delete_selected_files():
    """選択されたファイルを削除"""
    ui.notify('選択されたファイルを削除します', type='negative')