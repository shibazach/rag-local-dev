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