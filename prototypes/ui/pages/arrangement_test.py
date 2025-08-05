"""
配置テストページ - simple_test.pyのc13split完全移植
"""

from nicegui import ui
from ..components.layout import RAGHeader, RAGFooter

class ArrangementTestPage:
    """UI配置テストページクラス - simple_testのc13split完全移植"""
    
    def __init__(self):
        self.create_page()
    
    def create_page(self):
        """ページ作成（simple_testと完全同一）"""
        # 共通ヘッダー
        RAGHeader(current_page="arrangement_test")
        
        # C13方式4ペイン分割（simple_testから完全移植）
        self._create_c13_split()
        
        # 共通フッター
        RAGFooter()
    
    def _create_c13_split(self):
        """C13方式4ペイン分割（simple_testから完全移植）"""
        
        # グローバルリセット強化（simple_testと完全同一）
        ui.query('html').style('margin: 0; padding: 0; height: 100vh; overflow: hidden;')
        ui.query('body').style('margin: 0; padding: 0; height: 100vh; overflow: hidden;')
        ui.query('.q-layout').style('margin: 0; padding: 0; height: 100vh; overflow: hidden;')
        ui.query('.q-page-container').style('margin: 0; padding: 0; height: 100vh; overflow: hidden;')
        ui.query('.q-page').style('margin: 0; padding: 0; height: 100vh; overflow: hidden;')
        ui.query('.nicegui-content').style('margin: 0; padding: 0; height: 100vh; overflow: hidden;')
        
        # スプリッターとリサイズのJavaScript（simple_testから完全移植）
        ui.add_head_html('''
        <script>
        function initSplitters() {
            // 縦スプリッター（左右分割）
            const vSplitter = document.getElementById('vertical-splitter');
            const leftPane = document.getElementById('left-pane');
            const rightPane = document.getElementById('right-pane');
            
            // 横スプリッター（上下分割）- 左側
            const hSplitterLeft = document.getElementById('horizontal-splitter-left');
            const leftTopPane = document.getElementById('left-top-pane');
            const leftBottomPane = document.getElementById('left-bottom-pane');
            
            // 横スプリッター（上下分割）- 右側
            const hSplitterRight = document.getElementById('horizontal-splitter-right');
            const rightTopPane = document.getElementById('right-top-pane');
            const rightBottomPane = document.getElementById('right-bottom-pane');
            
            let isDragging = false;
            let currentSplitter = null;
            
            // 縦スプリッターのドラッグ
            if (vSplitter) {
                vSplitter.addEventListener('mousedown', (e) => {
                    isDragging = true;
                    currentSplitter = 'vertical';
                    document.body.style.userSelect = 'none';
                    document.body.style.cursor = 'col-resize';
                });
            }
            
            // 横スプリッター（左）のドラッグ
            if (hSplitterLeft) {
                hSplitterLeft.addEventListener('mousedown', (e) => {
                    isDragging = true;
                    currentSplitter = 'horizontal-left';
                    document.body.style.userSelect = 'none';
                    document.body.style.cursor = 'row-resize';
                });
            }
            
            // 横スプリッター（右）のドラッグ
            if (hSplitterRight) {
                hSplitterRight.addEventListener('mousedown', (e) => {
                    isDragging = true;
                    currentSplitter = 'horizontal-right';
                    document.body.style.userSelect = 'none';
                    document.body.style.cursor = 'row-resize';
                });
            }
            
            // マウス移動時のリサイズ処理
            document.addEventListener('mousemove', (e) => {
                if (!isDragging || !currentSplitter) return;
                
                const container = document.getElementById('split-container');
                const containerRect = container.getBoundingClientRect();
                
                if (currentSplitter === 'vertical') {
                    const leftWidth = Math.max(200, Math.min(containerRect.width - 200, e.clientX - containerRect.left));
                    const leftPercent = (leftWidth / containerRect.width) * 100;
                    
                    leftPane.style.width = leftPercent + '%';
                    rightPane.style.width = (100 - leftPercent) + '%';
                    
                } else if (currentSplitter === 'horizontal-left') {
                    const topHeight = Math.max(100, Math.min(containerRect.height - 100, e.clientY - containerRect.top));
                    const topPercent = (topHeight / containerRect.height) * 100;
                    
                    leftTopPane.style.height = topPercent + '%';
                    leftBottomPane.style.height = (100 - topPercent) + '%';
                    
                } else if (currentSplitter === 'horizontal-right') {
                    const topHeight = Math.max(100, Math.min(containerRect.height - 100, e.clientY - containerRect.top));
                    const topPercent = (topHeight / containerRect.height) * 100;
                    
                    rightTopPane.style.height = topPercent + '%';
                    rightBottomPane.style.height = (100 - topPercent) + '%';
                }
            });
            
            // ドラッグ終了
            document.addEventListener('mouseup', () => {
                isDragging = false;
                currentSplitter = null;
                document.body.style.userSelect = '';
                document.body.style.cursor = '';
            });
        }
        
        // ページ読み込み後に初期化
        setTimeout(initSplitters, 100);
        </script>
        ''')
        
        # C13方式メインコンテナ（simple_testから完全移植）
        with ui.element('div').style(
            'margin-top: 48px;'
            'margin-bottom: 24px;'
            'margin-left: 0;'
            'margin-right: 0;'
            'padding: 0;'
            'width: 100%;'
            'height: calc(100vh - 48px - 24px);'
            'overflow: hidden;'
            'position: relative;'
            'box-sizing: border-box;'
        ):
            # 4ペイン分割コンテナ（simple_testから完全移植）
            with ui.element('div').style(
                'width: 100%;'
                'height: 100%;'
                'display: flex;'
                'margin: 0;'
                'padding: 8px;'
                'box-sizing: border-box;'
                'gap: 0;'
            ).props('id="split-container"'):
                
                # 左側エリア（50%）
                with ui.element('div').style(
                    'width: 50%;'
                    'height: 100%;'
                    'display: flex;'
                    'flex-direction: column;'
                    'margin: 0;'
                    'padding: 0;'
                    'gap: 0;'
                ).props('id="left-pane"'):
                    
                    # 左上ペイン（50%）
                    with ui.element('div').style(
                        'width: 100%;'
                        'height: 50%;'
                        'margin: 0;'
                        'padding: 4px;'
                        'box-sizing: border-box;'
                        'overflow: hidden;'
                    ).props('id="left-top-pane"'):
                        
                        # 左上パネル
                        with ui.element('div').style(
                            'width: 100%;'
                            'height: 100%;'
                            'background-color: white;'
                            'border-radius: 8px;'
                            'box-shadow: 0 2px 8px rgba(0,0,0,0.15);'
                            'display: flex;'
                            'flex-direction: column;'
                            'overflow: hidden;'
                            'border: 1px solid #e5e7eb;'
                        ):
                            # ヘッダー
                            with ui.element('div').style(
                                'background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);'
                                'color: white;'
                                'padding: 12px 16px;'
                                'display: flex;'
                                'align-items: center;'
                                'justify-content: space-between;'
                                'height: 48px;'
                                'box-sizing: border-box;'
                                'flex-shrink: 0;'
                            ):
                                ui.label('📊 データ分析').style('font-weight: bold; font-size: 14px;')
                                with ui.element('div').style('display: flex; gap: 4px;'):
                                    ui.button('📈', color='white').style('padding: 2px 6px; font-size: 10px; min-width: 20px;')
                                    ui.button('⚙️', color='white').style('padding: 2px 6px; font-size: 10px; min-width: 20px;')
                            
                            # コンテンツ
                            with ui.element('div').style(
                                'flex: 1;'
                                'padding: 12px;'
                                'overflow-y: auto;'
                                'overflow-x: hidden;'
                            ):
                                ui.label('📈 売上推移').style('font-weight: bold; color: #374151; margin-bottom: 8px;')
                                with ui.element('div').style('display: grid; grid-template-columns: repeat(2, 1fr); gap: 8px;'):
                                    with ui.element('div').style('background: #10b981; color: white; padding: 8px; border-radius: 6px; text-align: center;'):
                                        ui.label('今月').style('font-size: 10px; opacity: 0.9;')
                                        ui.label('¥1,250,000').style('font-weight: bold; font-size: 12px;')
                                    with ui.element('div').style('background: #3b82f6; color: white; padding: 8px; border-radius: 6px; text-align: center;'):
                                        ui.label('前月').style('font-size: 10px; opacity: 0.9;')
                                        ui.label('¥1,180,000').style('font-weight: bold; font-size: 12px;')
                                    with ui.element('div').style('background: #8b5cf6; color: white; padding: 8px; border-radius: 6px; text-align: center;'):
                                        ui.label('前年同月').style('font-size: 10px; opacity: 0.9;')
                                        ui.label('¥980,000').style('font-weight: bold; font-size: 12px;')
                                    with ui.element('div').style('background: #f59e0b; color: white; padding: 8px; border-radius: 6px; text-align: center;'):
                                        ui.label('目標').style('font-size: 10px; opacity: 0.9;')
                                        ui.label('¥1,500,000').style('font-weight: bold; font-size: 12px;')
                    
                    # 水平スプリッター（左）
                    with ui.element('div').style(
                        'width: 100%;'
                        'height: 6px;'
                        'background: linear-gradient(90deg, #3b82f6, #1d4ed8);'
                        'cursor: row-resize;'
                        'display: flex;'
                        'align-items: center;'
                        'justify-content: center;'
                        'transition: background 0.2s;'
                        'margin: 0;'
                        'padding: 0;'
                    ).props('id="horizontal-splitter-left"'):
                        ui.label('⋮⋮⋮').style('color: white; font-size: 8px; transform: rotate(90deg);')
                    
                    # 左下ペイン（50%）
                    with ui.element('div').style(
                        'width: 100%;'
                        'height: 50%;'
                        'margin: 0;'
                        'padding: 4px;'
                        'box-sizing: border-box;'
                        'overflow: hidden;'
                    ).props('id="left-bottom-pane"'):
                        
                        # 左下パネル
                        with ui.element('div').style(
                            'width: 100%;'
                            'height: 100%;'
                            'background-color: white;'
                            'border-radius: 8px;'
                            'box-shadow: 0 2px 8px rgba(0,0,0,0.15);'
                            'display: flex;'
                            'flex-direction: column;'
                            'overflow: hidden;'
                            'border: 1px solid #e5e7eb;'
                        ):
                            # ヘッダー
                            with ui.element('div').style(
                                'background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);'
                                'color: white;'
                                'padding: 12px 16px;'
                                'display: flex;'
                                'align-items: center;'
                                'justify-content: space-between;'
                                'height: 48px;'
                                'box-sizing: border-box;'
                                'flex-shrink: 0;'
                            ):
                                ui.label('👥 ユーザー管理').style('font-weight: bold; font-size: 14px;')
                                with ui.element('div').style('display: flex; gap: 4px;'):
                                    ui.button('➕', color='white').style('padding: 2px 6px; font-size: 10px; min-width: 20px;')
                                    ui.button('📝', color='white').style('padding: 2px 6px; font-size: 10px; min-width: 20px;')
                            
                            # テーブル
                            with ui.element('div').style(
                                'flex: 1;'
                                'overflow-y: auto;'
                                'overflow-x: hidden;'
                            ):
                                with ui.element('table').style('width: 100%; border-collapse: collapse; margin: 0;'):
                                    # ヘッダー
                                    with ui.element('thead'):
                                        with ui.element('tr').style('background: #f8f9fa; border-bottom: 2px solid #e5e7eb;'):
                                            ui.element('th').style('padding: 8px; text-align: left; font-size: 11px; font-weight: bold;').text = 'ID'
                                            ui.element('th').style('padding: 8px; text-align: left; font-size: 11px; font-weight: bold;').text = 'ユーザー名'
                                            ui.element('th').style('padding: 8px; text-align: left; font-size: 11px; font-weight: bold;').text = 'ステータス'
                                            ui.element('th').style('padding: 8px; text-align: left; font-size: 11px; font-weight: bold;').text = '最終ログイン'
                                    
                                    # データ
                                    with ui.element('tbody'):
                                        for i, (name, status, login) in enumerate([
                                            ('admin', 'アクティブ', '2024-01-15'),
                                            ('user1', 'アクティブ', '2024-01-14'),
                                            ('user2', '休止中', '2024-01-10'),
                                            ('user3', 'アクティブ', '2024-01-15'),
                                            ('guest', '制限', '2024-01-12')
                                        ]):
                                            status_color = '#10b981' if status == 'アクティブ' else '#f59e0b' if status == '休止中' else '#ef4444'
                                            with ui.element('tr').style('border-bottom: 1px solid #f3f4f6; transition: background 0.2s;'):
                                                ui.element('td').style('padding: 6px 8px; font-size: 11px;').text = f'{i+1:03d}'
                                                ui.element('td').style('padding: 6px 8px; font-size: 11px;').text = name
                                                ui.element('td').style(f'padding: 6px 8px; font-size: 11px; color: {status_color}; font-weight: bold;').text = status
                                                ui.element('td').style('padding: 6px 8px; font-size: 11px; color: #6b7280;').text = login
                
                # 縦スプリッター
                with ui.element('div').style(
                    'width: 6px;'
                    'height: 100%;'
                    'background: linear-gradient(180deg, #3b82f6, #1d4ed8);'
                    'cursor: col-resize;'
                    'display: flex;'
                    'align-items: center;'
                    'justify-content: center;'
                    'transition: background 0.2s;'
                    'margin: 0;'
                    'padding: 0;'
                ).props('id="vertical-splitter"'):
                    ui.label('⋮⋮⋮').style('color: white; font-size: 8px;')
                
                # 右側エリア（50%）
                with ui.element('div').style(
                    'width: 50%;'
                    'height: 100%;'
                    'display: flex;'
                    'flex-direction: column;'
                    'margin: 0;'
                    'padding: 0;'
                    'gap: 0;'
                ).props('id="right-pane"'):
                    
                    # 右上ペイン（50%）
                    with ui.element('div').style(
                        'width: 100%;'
                        'height: 50%;'
                        'margin: 0;'
                        'padding: 4px;'
                        'box-sizing: border-box;'
                        'overflow: hidden;'
                    ).props('id="right-top-pane"'):
                        
                        # 右上パネル
                        with ui.element('div').style(
                            'width: 100%;'
                            'height: 100%;'
                            'background-color: white;'
                            'border-radius: 8px;'
                            'box-shadow: 0 2px 8px rgba(0,0,0,0.15);'
                            'display: flex;'
                            'flex-direction: column;'
                            'overflow: hidden;'
                            'border: 1px solid #e5e7eb;'
                        ):
                            # ヘッダー
                            with ui.element('div').style(
                                'background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);'
                                'color: white;'
                                'padding: 12px 16px;'
                                'display: flex;'
                                'align-items: center;'
                                'justify-content: space-between;'
                                'height: 48px;'
                                'box-sizing: border-box;'
                                'flex-shrink: 0;'
                            ):
                                ui.label('📝 タスク管理').style('font-weight: bold; font-size: 14px;')
                                with ui.element('div').style('display: flex; gap: 4px;'):
                                    ui.button('✅', color='white').style('padding: 2px 6px; font-size: 10px; min-width: 20px;')
                                    ui.button('📋', color='white').style('padding: 2px 6px; font-size: 10px; min-width: 20px;')
                            
                            # タスクリスト
                            with ui.element('div').style(
                                'flex: 1;'
                                'padding: 8px;'
                                'overflow-y: auto;'
                                'overflow-x: hidden;'
                            ):
                                tasks = [
                                    ('UI レイアウト改善', '高', '進行中', '#ef4444', '#3b82f6'),
                                    ('パフォーマンス最適化', '中', '完了', '#f59e0b', '#10b981'),
                                    ('ドキュメント更新', '低', '待機', '#10b981', '#6b7280'),
                                    ('バグ修正 #123', '高', '進行中', '#ef4444', '#3b82f6'),
                                    ('テストケース追加', '中', '待機', '#f59e0b', '#6b7280'),
                                    ('コードレビュー', '中', '完了', '#f59e0b', '#10b981'),
                                ]
                                
                                for task, priority, status, priority_color, status_color in tasks:
                                    with ui.element('div').style('background: #f8f9fa; border: 1px solid #e5e7eb; border-radius: 6px; padding: 8px; margin-bottom: 4px;'):
                                        ui.label(task).style('font-size: 12px; font-weight: bold; color: #374151; margin-bottom: 4px;')
                                        with ui.element('div').style('display: flex; justify-content: space-between; align-items: center;'):
                                            with ui.element('span').style(f'background: {priority_color}; color: white; padding: 2px 6px; border-radius: 3px; font-size: 9px;'):
                                                ui.label(priority)
                                            with ui.element('span').style(f'color: {status_color}; font-size: 10px; font-weight: bold;'):
                                                ui.label(status)
                    
                    # 水平スプリッター（右）
                    with ui.element('div').style(
                        'width: 100%;'
                        'height: 6px;'
                        'background: linear-gradient(90deg, #3b82f6, #1d4ed8);'
                        'cursor: row-resize;'
                        'display: flex;'
                        'align-items: center;'
                        'justify-content: center;'
                        'transition: background 0.2s;'
                        'margin: 0;'
                        'padding: 0;'
                    ).props('id="horizontal-splitter-right"'):
                        ui.label('⋮⋮⋮').style('color: white; font-size: 8px; transform: rotate(90deg);')
                    
                    # 右下ペイン（50%）
                    with ui.element('div').style(
                        'width: 100%;'
                        'height: 50%;'
                        'margin: 0;'
                        'padding: 4px;'
                        'box-sizing: border-box;'
                        'overflow: hidden;'
                    ).props('id="right-bottom-pane"'):
                        
                        # 右下パネル
                        with ui.element('div').style(
                            'width: 100%;'
                            'height: 100%;'
                            'background-color: white;'
                            'border-radius: 8px;'
                            'box-shadow: 0 2px 8px rgba(0,0,0,0.15);'
                            'display: flex;'
                            'flex-direction: column;'
                            'overflow: hidden;'
                            'border: 1px solid #e5e7eb;'
                        ):
                            # ヘッダー
                            with ui.element('div').style(
                                'background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);'
                                'color: white;'
                                'padding: 12px 16px;'
                                'display: flex;'
                                'align-items: center;'
                                'justify-content: space-between;'
                                'height: 48px;'
                                'box-sizing: border-box;'
                                'flex-shrink: 0;'
                            ):
                                ui.label('💬 システムログ').style('font-weight: bold; font-size: 14px;')
                                with ui.element('div').style('display: flex; gap: 4px;'):
                                    ui.button('🔄', color='white').style('padding: 2px 6px; font-size: 10px; min-width: 20px;')
                                    ui.button('🗑️', color='white').style('padding: 2px 6px; font-size: 10px; min-width: 20px;')
                            
                            # ログコンテンツ
                            with ui.element('div').style(
                                'flex: 1;'
                                'padding: 8px;'
                                'overflow-y: auto;'
                                'overflow-x: hidden;'
                                'font-family: monospace;'
                                'background: #1f2937;'
                                'color: #e5e7eb;'
                            ):
                                logs = [
                                    ('[2024-01-15 15:30:10] ', 'INFO: ', 'User login successful', '#9ca3af', '#10b981'),
                                    ('[2024-01-15 15:31:11] ', 'WARN: ', 'Database connection established', '#9ca3af', '#f59e0b'),
                                    ('[2024-01-15 15:32:12] ', 'ERROR: ', 'Cache miss for key: user_123', '#9ca3af', '#ef4444'),
                                    ('[2024-01-15 15:33:13] ', 'DEBUG: ', 'API request processed in 245ms', '#9ca3af', '#6b7280'),
                                    ('[2024-01-15 15:34:14] ', 'INFO: ', 'Memory usage: 75%', '#9ca3af', '#10b981'),
                                    ('[2024-01-15 15:35:15] ', 'WARN: ', 'Backup completed successfully', '#9ca3af', '#f59e0b'),
                                    ('[2024-01-15 15:36:16] ', 'ERROR: ', 'User login successful', '#9ca3af', '#ef4444'),
                                    ('[2024-01-15 15:37:17] ', 'DEBUG: ', 'Database connection established', '#9ca3af', '#6b7280'),
                                    ('[2024-01-15 15:38:18] ', 'INFO: ', 'Cache miss for key: user_123', '#9ca3af', '#10b981'),
                                    ('[2024-01-15 15:39:19] ', 'WARN: ', 'API request processed in 245ms', '#9ca3af', '#f59e0b'),
                                    ('[2024-01-15 15:40:20] ', 'ERROR: ', 'Memory usage: 75%', '#9ca3af', '#ef4444'),
                                    ('[2024-01-15 15:41:21] ', 'DEBUG: ', 'Backup completed successfully', '#9ca3af', '#6b7280'),
                                    ('[2024-01-15 15:42:22] ', 'INFO: ', 'User login successful', '#9ca3af', '#10b981'),
                                    ('[2024-01-15 15:43:23] ', 'WARN: ', 'Database connection established', '#9ca3af', '#f59e0b'),
                                    ('[2024-01-15 15:44:24] ', 'ERROR: ', 'Cache miss for key: user_123', '#9ca3af', '#ef4444'),
                                    ('[2024-01-15 15:45:25] ', 'DEBUG: ', 'API request processed in 245ms', '#9ca3af', '#6b7280'),
                                    ('[2024-01-15 15:46:26] ', 'INFO: ', 'Memory usage: 75%', '#9ca3af', '#10b981'),
                                    ('[2024-01-15 15:47:27] ', 'WARN: ', 'Backup completed successfully', '#9ca3af', '#f59e0b'),
                                    ('[2024-01-15 15:48:28] ', 'ERROR: ', 'User login successful', '#9ca3af', '#ef4444'),
                                    ('[2024-01-15 15:49:29] ', 'DEBUG: ', 'Database connection established', '#9ca3af', '#6b7280'),
                                ]
                                
                                for timestamp, level, message, time_color, level_color in logs:
                                    with ui.element('div').style('margin-bottom: 2px; font-size: 10px; line-height: 1.4;'):
                                        ui.label(timestamp).style(f'color: {time_color};')
                                        ui.label(level).style(f'color: {level_color}; font-weight: bold;')
                                        ui.label(message).style('color: #e5e7eb;')

# ページインスタンス作成用の関数
def create_arrangement_test_page():
    """配置テストページ作成"""
    return ArrangementTestPage()