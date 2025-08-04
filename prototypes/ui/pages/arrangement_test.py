"""
UI共通パネル練習ページ - 開発・実験・配置テスト用
本番ページを書き換えずに、共通コンポーネント化の練習やテストに使用
"""

from nicegui import ui
from ui.components import RAGHeader, RAGFooter, MainContentArea, CommonPanel, PanelButton, DataTable

class ArrangementTestPage:
    """UI配置テストページクラス - リサイズ対応・スクロール制御"""
    
    def __init__(self):
        """テストページ初期化"""
        pass
    
    def render(self):
        """配置テストページ描画"""
        
        # 共通ヘッダー
        RAGHeader(show_site_name=True, current_page="test")
        
        # 【TEST】C13方式直接実装（simple_testスタイル）
        with ui.element('div').style(
            'margin-top: 48px;'          # ヘッダー分
            'margin-bottom: 24px;'       # フッター分  
            'margin-left: 0;'
            'margin-right: 0;'
            'padding: 8px;'              # コンテンツ余白
            'width: 100%;'
            'height: calc(100vh - 48px - 24px);'  # 正確な高さ計算
            'overflow: hidden;'
            'position: relative;'
            'box-sizing: border-box;'
        ):
            # タブコンテナ：外枠付き・高さ圧迫最小・境界明確化
            with ui.element('div').style('border:2px solid #d1d5db;border-radius:8px;overflow:hidden;height:100%;background:white;display:flex;flex-direction:column;') as tab_container:
                
                # タブヘッダー：最小高さ・アイコンなし・小文字
                with ui.tabs().classes('w-full').style('margin:0;padding:0;min-height:24px;background:#f8f9fa;border-bottom:1px solid #d1d5db;') as tabs:
                    tab1 = ui.tab('A').style('padding:2px 8px;margin:0;font-size:10px;min-height:24px;')
                    tab2 = ui.tab('B').style('padding:2px 8px;margin:0;font-size:10px;min-height:24px;')
                    tab3 = ui.tab('C').style('padding:2px 8px;margin:0;font-size:10px;min-height:24px;')
                    tab4 = ui.tab('D').style('padding:2px 8px;margin:0;font-size:10px;min-height:24px;')
                
                # タブコンテンツ：flex:1で残り空間を全て使用・パディングゼロ
                with ui.tab_panels(tabs, value=tab1).classes('w-full').style('flex:1;margin:0;padding:0;background:white;overflow:hidden;'):
                    
                    # タブ1：C13方式4ペイン分割（simple_testスタイル）
                    with ui.tab_panel(tab1).style('margin:0;padding:0;height:100%;'):
                        self._create_c13_split_layout()
                    
                    # タブ2：新レイアウト実験エリア1
                    with ui.tab_panel(tab2).style('margin:0;padding:0;height:100%;'):
                        self._create_experimental_layout_1()
                    
                    # タブ3：新レイアウト実験エリア2
                    with ui.tab_panel(tab3).style('margin:0;padding:0;height:100%;'):
                        self._create_experimental_layout_2()
                    
                    # タブ4：コンポーネント単体練習
                    with ui.tab_panel(tab4).style('margin:0;padding:0;height:100%;'):
                        self._create_component_practice_area()
        
        # 共通フッター
        RAGFooter()
    
    def _create_c13_split_layout(self):
        """C13方式4ペイン分割レイアウト（simple_testスタイル）"""
        
        # スプリッターとリサイズのJavaScript（simple_testからの移植）
        ui.add_head_html('''
        <script>
        function initArrangementSplitters() {
            // 縦スプリッター（左右分割）
            const vSplitter = document.getElementById('arr-vertical-splitter');
            const leftPane = document.getElementById('arr-left-pane');
            const rightPane = document.getElementById('arr-right-pane');
            
            // 横スプリッター（上下分割）- 左側
            const hSplitterLeft = document.getElementById('arr-horizontal-splitter-left');
            const leftTopPane = document.getElementById('arr-left-top-pane');
            const leftBottomPane = document.getElementById('arr-left-bottom-pane');
            
            // 横スプリッター（上下分割）- 右側
            const hSplitterRight = document.getElementById('arr-horizontal-splitter-right');
            const rightTopPane = document.getElementById('arr-right-top-pane');
            const rightBottomPane = document.getElementById('arr-right-bottom-pane');
            
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
                
                const container = document.getElementById('arr-split-container');
                if (!container) return;
                const containerRect = container.getBoundingClientRect();
                
                if (currentSplitter === 'vertical') {
                    const leftWidth = Math.max(200, Math.min(containerRect.width - 200, e.clientX - containerRect.left));
                    const leftPercent = (leftWidth / containerRect.width) * 100;
                    
                    if (leftPane) leftPane.style.width = leftPercent + '%';
                    if (rightPane) rightPane.style.width = (100 - leftPercent) + '%';
                    
                } else if (currentSplitter === 'horizontal-left') {
                    const topHeight = Math.max(100, Math.min(containerRect.height - 100, e.clientY - containerRect.top));
                    const topPercent = (topHeight / containerRect.height) * 100;
                    
                    if (leftTopPane) leftTopPane.style.height = topPercent + '%';
                    if (leftBottomPane) leftBottomPane.style.height = (100 - topPercent) + '%';
                    
                } else if (currentSplitter === 'horizontal-right') {
                    const topHeight = Math.max(100, Math.min(containerRect.height - 100, e.clientY - containerRect.top));
                    const topPercent = (topHeight / containerRect.height) * 100;
                    
                    if (rightTopPane) rightTopPane.style.height = topPercent + '%';
                    if (rightBottomPane) rightBottomPane.style.height = (100 - topPercent) + '%';
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
        setTimeout(initArrangementSplitters, 100);
        </script>
        ''')
        
        # 4ペイン分割コンテナ
        with ui.element('div').style(
            'width: 100%;'
            'height: 100%;'
            'display: flex;'
            'margin: 0;'
            'padding: 4px;'
            'box-sizing: border-box;'
            'gap: 0;'
        ).props('id="arr-split-container"'):
            
            # 左側エリア（50%）
            with ui.element('div').style(
                'width: 50%;'
                'height: 100%;'
                'display: flex;'
                'flex-direction: column;'
                'margin: 0;'
                'padding: 0;'
                'gap: 0;'
            ).props('id="arr-left-pane"'):
                
                # 左上ペイン（50%）
                with ui.element('div').style(
                    'width: 100%;'
                    'height: 50%;'
                    'margin: 0;'
                    'padding: 2px;'
                    'box-sizing: border-box;'
                    'overflow: hidden;'
                ).props('id="arr-left-top-pane"'):
                    self._create_data_analysis_panel()
                
                # 横スプリッター（左側）
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
                ).props('id="arr-horizontal-splitter-left"'):
                    ui.label('⋮⋮⋮').style('color: white; font-size: 8px; transform: rotate(90deg);')
                
                # 左下ペイン（50%）
                with ui.element('div').style(
                    'width: 100%;'
                    'height: 50%;'
                    'margin: 0;'
                    'padding: 2px;'
                    'box-sizing: border-box;'
                    'overflow: hidden;'
                ).props('id="arr-left-bottom-pane"'):
                    self._create_user_management_panel()
            
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
            ).props('id="arr-vertical-splitter"'):
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
            ).props('id="arr-right-pane"'):
                
                # 右上ペイン（50%）
                with ui.element('div').style(
                    'width: 100%;'
                    'height: 50%;'
                    'margin: 0;'
                    'padding: 2px;'
                    'box-sizing: border-box;'
                    'overflow: hidden;'
                ).props('id="arr-right-top-pane"'):
                    self._create_task_management_panel()
                
                # 横スプリッター（右側）
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
                ).props('id="arr-horizontal-splitter-right"'):
                    ui.label('⋮⋮⋮').style('color: white; font-size: 8px; transform: rotate(90deg);')
                
                # 右下ペイン（50%）
                with ui.element('div').style(
                    'width: 100%;'
                    'height: 50%;'
                    'margin: 0;'
                    'padding: 2px;'
                    'box-sizing: border-box;'
                    'overflow: hidden;'
                ).props('id="arr-right-bottom-pane"'):
                    self._create_system_log_panel()

    def _create_data_analysis_panel(self):
        """左上：データ分析パネル"""
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
                'padding: 8px 12px;'
                'display: flex;'
                'align-items: center;'
                'justify-content: space-between;'
                'height: 36px;'
                'box-sizing: border-box;'
                'flex-shrink: 0;'
            ):
                ui.label('📊 データ分析').style('font-weight: bold; font-size: 12px;')
                with ui.element('div').style('display: flex; gap: 4px;'):
                    ui.button('📈', color='white').style('padding: 1px 4px; font-size: 9px; min-width: 16px;')
                    ui.button('⚙️', color='white').style('padding: 1px 4px; font-size: 9px; min-width: 16px;')
            
            # コンテンツ
            with ui.element('div').style(
                'flex: 1;'
                'padding: 8px;'
                'overflow-y: auto;'
                'overflow-x: hidden;'
            ):
                ui.label('📈 パフォーマンス指標').style('font-weight: bold; color: #374151; margin-bottom: 6px; font-size: 11px;')
                with ui.element('div').style('display: grid; grid-template-columns: repeat(2, 1fr); gap: 4px;'):
                    for i, (label, value, color) in enumerate([
                        ('アクティブユーザー', '1,247', '#10b981'),
                        ('処理済み', '3,892', '#3b82f6'),
                        ('待機中', '127', '#f59e0b'),
                        ('エラー', '12', '#ef4444')
                    ]):
                        with ui.element('div').style(f'background: {color}; color: white; padding: 4px; border-radius: 4px; text-align: center;'):
                            ui.label(label).style('font-size: 8px; opacity: 0.9;')
                            ui.label(value).style('font-weight: bold; font-size: 10px;')

    def _create_user_management_panel(self):
        """左下：ユーザー管理パネル"""
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
                'padding: 8px 12px;'
                'display: flex;'
                'align-items: center;'
                'justify-content: space-between;'
                'height: 36px;'
                'box-sizing: border-box;'
                'flex-shrink: 0;'
            ):
                ui.label('👥 ユーザー管理').style('font-weight: bold; font-size: 12px;')
                with ui.element('div').style('display: flex; gap: 4px;'):
                    ui.button('➕', color='white').style('padding: 1px 4px; font-size: 9px; min-width: 16px;')
                    ui.button('📝', color='white').style('padding: 1px 4px; font-size: 9px; min-width: 16px;')
            
            # テーブル
            with ui.element('div').style(
                'flex: 1;'
                'overflow-y: auto;'
                'overflow-x: hidden;'
            ):
                with ui.element('table').style('width: 100%; border-collapse: collapse; margin: 0;'):
                    # ヘッダー
                    with ui.element('thead'):
                        with ui.element('tr').style('background: #f8f9fa; border-bottom: 1px solid #e5e7eb;'):
                            ui.element('th').style('padding: 4px 6px; text-align: left; font-size: 9px; font-weight: bold;').text = 'ID'
                            ui.element('th').style('padding: 4px 6px; text-align: left; font-size: 9px; font-weight: bold;').text = 'ユーザー'
                            ui.element('th').style('padding: 4px 6px; text-align: left; font-size: 9px; font-weight: bold;').text = 'ステータス'
                    
                    # データ
                    with ui.element('tbody'):
                        for i, (name, status) in enumerate([
                            ('admin', 'アクティブ'),
                            ('user1', 'アクティブ'),
                            ('user2', '休止中'),
                            ('guest', '制限'),
                            ('test', 'アクティブ')
                        ]):
                            status_color = '#10b981' if status == 'アクティブ' else '#f59e0b' if status == '休止中' else '#ef4444'
                            with ui.element('tr').style('border-bottom: 1px solid #f3f4f6;'):
                                ui.element('td').style('padding: 3px 6px; font-size: 9px;').text = f'{i+1:02d}'
                                ui.element('td').style('padding: 3px 6px; font-size: 9px;').text = name
                                ui.element('td').style(f'padding: 3px 6px; font-size: 9px; color: {status_color}; font-weight: bold;').text = status

    def _create_task_management_panel(self):
        """右上：タスク管理パネル"""
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
                'padding: 8px 12px;'
                'display: flex;'
                'align-items: center;'
                'justify-content: space-between;'
                'height: 36px;'
                'box-sizing: border-box;'
                'flex-shrink: 0;'
            ):
                ui.label('📝 タスク管理').style('font-weight: bold; font-size: 12px;')
                with ui.element('div').style('display: flex; gap: 4px;'):
                    ui.button('✅', color='white').style('padding: 1px 4px; font-size: 9px; min-width: 16px;')
                    ui.button('📋', color='white').style('padding: 1px 4px; font-size: 9px; min-width: 16px;')
            
            # タスクリスト
            with ui.element('div').style(
                'flex: 1;'
                'padding: 6px;'
                'overflow-y: auto;'
                'overflow-x: hidden;'
            ):
                for i, (task, priority, status) in enumerate([
                    ('UI改善', '高', '進行中'),
                    ('パフォーマンス最適化', '中', '完了'),
                    ('ドキュメント更新', '低', '待機'),
                    ('バグ修正', '高', '進行中'),
                    ('テスト追加', '中', '待機')
                ]):
                    priority_color = '#ef4444' if priority == '高' else '#f59e0b' if priority == '中' else '#10b981'
                    status_color = '#3b82f6' if status == '進行中' else '#10b981' if status == '完了' else '#6b7280'
                    
                    with ui.element('div').style('background: #f8f9fa; border: 1px solid #e5e7eb; border-radius: 4px; padding: 4px; margin-bottom: 2px;'):
                        ui.label(task).style('font-size: 10px; font-weight: bold; color: #374151; margin-bottom: 2px;')
                        with ui.element('div').style('display: flex; justify-content: space-between; align-items: center;'):
                            with ui.element('span').style(f'background: {priority_color}; color: white; padding: 1px 4px; border-radius: 2px; font-size: 8px;'):
                                ui.label(priority)
                            with ui.element('span').style(f'color: {status_color}; font-size: 8px; font-weight: bold;'):
                                ui.label(status)

    def _create_system_log_panel(self):
        """右下：システムログパネル"""
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
                'padding: 8px 12px;'
                'display: flex;'
                'align-items: center;'
                'justify-content: space-between;'
                'height: 36px;'
                'box-sizing: border-box;'
                'flex-shrink: 0;'
            ):
                ui.label('💬 システムログ').style('font-weight: bold; font-size: 12px;')
                with ui.element('div').style('display: flex; gap: 4px;'):
                    ui.button('🔄', color='white').style('padding: 1px 4px; font-size: 9px; min-width: 16px;')
                    ui.button('🗑️', color='white').style('padding: 1px 4px; font-size: 9px; min-width: 16px;')
            
            # ログコンテンツ
            with ui.element('div').style(
                'flex: 1;'
                'padding: 4px;'
                'overflow-y: auto;'
                'overflow-x: hidden;'
                'font-family: monospace;'
                'background: #1f2937;'
                'color: #e5e7eb;'
            ):
                for i in range(15):
                    timestamp = f'15:{30+i%30:02d}:{10+i%50:02d}'
                    log_type = ['INFO', 'WARN', 'ERROR'][i % 3]
                    log_color = {'INFO': '#10b981', 'WARN': '#f59e0b', 'ERROR': '#ef4444'}[log_type]
                    message = [
                        'User login successful',
                        'Database connected',
                        'Processing request',
                        'Cache updated',
                        'Session expired'
                    ][i % 5]
                    
                    with ui.element('div').style('margin-bottom: 1px; font-size: 8px; line-height: 1.2;'):
                        ui.label(f'[{timestamp}] ').style('color: #9ca3af;')
                        ui.label(f'{log_type}: ').style(f'color: {log_color}; font-weight: bold;')
                        ui.label(message).style('color: #e5e7eb;')

    def _create_resizable_layout(self):
        """リサイズ対応の4分割レイアウト作成（VB Splitter風）"""
        
        # VB風2段階層Splitter（細線・爽やかブルー）
        ui.add_head_html('''
        <style>
        /* 外側コンテナ（上下分割） */
        .splitter-main-container {
            display: flex;
            flex-direction: column;
            height: 100%;
            width: 100%;
            overflow: hidden;
            padding: 4px;
            box-sizing: border-box;
        }
        
        /* 上段・下段エリア */
        .splitter-row {
            display: flex;
            flex-direction: row;
            flex: 1;
            min-height: 80px;
        }
        
        /* パネル */
        .resizable-panel {
            flex: 1;
            overflow: hidden;
            min-height: 80px;
            min-width: 120px;
            padding: 0;
            box-sizing: border-box;
            display: flex;
            flex-direction: column;
        }
        
        /* パネル内コンテンツエリア（スクロール対応） */
        .resizable-panel .panel-content {
            flex: 1;
            overflow: auto;
            padding: 4px;
            box-sizing: border-box;
        }
        
        /* 垂直スプリッター（左右分割・細線・爽やかブルー） */
        .splitter-vertical {
            width: 6px;
            background: #e0f2fe;
            cursor: col-resize;
            user-select: none;
            position: relative;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.2s ease;
            border-left: 1px solid #b3e5fc;
            border-right: 1px solid #b3e5fc;
        }
        
        /* 水平スプリッター（上下分割・細線・爽やかブルー） */
        .splitter-horizontal {
            height: 6px;
            background: #e0f2fe;
            cursor: row-resize;
            user-select: none;
            position: relative;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.2s ease;
            border-top: 1px solid #b3e5fc;
            border-bottom: 1px solid #b3e5fc;
        }
        
        /* ホバー状態（爽やかブルー強調） */
        .splitter-vertical:hover {
            background: #29b6f6;
            border-color: #0288d1;
            box-shadow: 0 0 4px rgba(41, 182, 246, 0.3);
        }
        .splitter-horizontal:hover {
            background: #29b6f6;
            border-color: #0288d1;
            box-shadow: 0 0 4px rgba(41, 182, 246, 0.3);
        }
        
        /* ドラッグ中状態（濃いブルー） */
        .splitter-dragging {
            background: #0277bd !important;
            border-color: #01579b !important;
            box-shadow: 0 0 8px rgba(2, 119, 189, 0.5) !important;
            z-index: 1000;
        }
        
        /* スプリッター内ドットアイコン（小さく・薄く） */
        .splitter-vertical::before {
            content: '⋮';
            color: #81d4fa;
            font-size: 8px;
            font-weight: normal;
            transition: color 0.2s ease;
        }
        .splitter-horizontal::before {
            content: '⋯';
            color: #81d4fa;
            font-size: 8px;
            font-weight: normal;
            transition: color 0.2s ease;
        }
        
        /* ホバー時アイコン色変更 */
        .splitter-vertical:hover::before, 
        .splitter-horizontal:hover::before {
            color: white;
        }
        
        /* ドラッグ中アイコン */
        .splitter-dragging::before {
            color: #ffffff !important;
        }
        </style>
        ''')
        
        # VB風2段階層Splitterコンテナ
        with ui.element('div').classes('splitter-main-container') as main_container:
            
            # 上段（左上・右上パネル）
            with ui.element('div').classes('splitter-row') as top_row:
                # 左上パネル
                with ui.element('div').classes('resizable-panel'):
                    with ui.element('div').classes('panel-content'):
                        self._create_basic_panel()
                
                # 上段の垂直スプリッター（左右分割）
                with ui.element('div').classes('splitter-vertical') as top_vertical:
                    pass
                
                # 右上パネル
                with ui.element('div').classes('resizable-panel'):
                    with ui.element('div').classes('panel-content'):
                        self._create_compact_panel()
            
            # 水平スプリッター（上下分割）
            with ui.element('div').classes('splitter-horizontal') as horizontal_splitter:
                pass
            
            # 下段（左下・右下パネル）
            with ui.element('div').classes('splitter-row') as bottom_row:
                # 左下パネル
                with ui.element('div').classes('resizable-panel'):
                    with ui.element('div').classes('panel-content'):
                        self._create_full_panel()
                
                # 下段の垂直スプリッター（左右分割）
                with ui.element('div').classes('splitter-vertical') as bottom_vertical:
                    pass
                
                # 右下パネル
                with ui.element('div').classes('resizable-panel'):
                    with ui.element('div').classes('panel-content'):
                        self._create_custom_test_area()
        
        # VB風2段階層Splitter制御JavaScript
        ui.add_body_html('''
        <script>
        document.addEventListener('DOMContentLoaded', function() {
            const mainContainer = document.querySelector('.splitter-main-container');
            if (!mainContainer) return;
            
            let isResizing = false;
            let currentSplitter = null;
            let splitterType = '';
            let startX = 0;
            let startY = 0;
            
            // 全スプリッターにイベント追加
            const allSplitters = mainContainer.querySelectorAll('.splitter-vertical, .splitter-horizontal');
            
            allSplitters.forEach(splitter => {
                splitter.addEventListener('mousedown', (e) => {
                    isResizing = true;
                    currentSplitter = splitter;
                    startX = e.clientX;
                    startY = e.clientY;
                    
                    if (splitter.classList.contains('splitter-vertical')) {
                        splitterType = 'vertical';
                        document.body.style.cursor = 'col-resize';
                    } else if (splitter.classList.contains('splitter-horizontal')) {
                        splitterType = 'horizontal';
                        document.body.style.cursor = 'row-resize';
                    }
                    
                    // ドラッグ開始視覚フィードバック
                    splitter.classList.add('splitter-dragging');
                    e.preventDefault();
                });
            });
            
            document.addEventListener('mousemove', (e) => {
                if (!isResizing || !currentSplitter) return;
                
                const deltaX = e.clientX - startX;
                const deltaY = e.clientY - startY;
                
                if (splitterType === 'vertical') {
                    // 垂直スプリッター：左右リサイズ（コンテンツベース最小幅）
                    const row = currentSplitter.parentElement;
                    const leftPanel = row.children[0];
                    const rightPanel = row.children[2];
                    
                    // 動的最小幅計算（ボタンが見える最小サイズ）
                    const getMinContentWidth = (panel) => {
                        const buttons = panel.querySelectorAll('button');
                        if (buttons.length === 0) return 120; // デフォルト最小幅
                        
                        let maxButtonWidth = 0;
                        buttons.forEach(btn => {
                            const btnRect = btn.getBoundingClientRect();
                            maxButtonWidth = Math.max(maxButtonWidth, btnRect.width);
                        });
                        
                        // ボタン幅 + パディング + 余裕 = 最小パネル幅
                        const calculatedWidth = Math.max(120, maxButtonWidth + 40);
                        console.log('Panel buttons:', buttons.length, 'Max button width:', maxButtonWidth, 'Calculated min width:', calculatedWidth);
                        return calculatedWidth;
                    };
                    
                    const leftMinWidth = getMinContentWidth(leftPanel);
                    const rightMinWidth = getMinContentWidth(rightPanel);
                    
                    const rowRect = row.getBoundingClientRect();
                    const newLeftWidth = Math.max(leftMinWidth, Math.min(rowRect.width - rightMinWidth - 6, 
                        leftPanel.offsetWidth + deltaX));
                    const newRightWidth = rowRect.width - newLeftWidth - 6;
                    
                    leftPanel.style.flex = `0 0 ${newLeftWidth}px`;
                    rightPanel.style.flex = `0 0 ${newRightWidth}px`;
                    
                } else if (splitterType === 'horizontal') {
                    // 水平スプリッター：上下リサイズ（両方の段が追従）
                    const topRow = mainContainer.children[0];
                    const bottomRow = mainContainer.children[2];
                    
                    const containerRect = mainContainer.getBoundingClientRect();
                    const newTopHeight = Math.max(80, Math.min(containerRect.height - 80 - 6,
                        topRow.offsetHeight + deltaY));
                    const newBottomHeight = containerRect.height - newTopHeight - 6;
                    
                    topRow.style.flex = `0 0 ${newTopHeight}px`;
                    bottomRow.style.flex = `0 0 ${newBottomHeight}px`;
                }
                
                // 開始位置更新（連続ドラッグ対応）
                startX = e.clientX;
                startY = e.clientY;
            });
            
            document.addEventListener('mouseup', () => {
                if (currentSplitter) {
                    currentSplitter.classList.remove('splitter-dragging');
                }
                
                isResizing = false;
                currentSplitter = null;
                splitterType = '';
                document.body.style.cursor = '';
            });
        });
        </script>
        ''')
    
    def _create_basic_panel(self):
        """基本パネル（左上）"""
        with CommonPanel(
            title="基本パネル",
            icon="📋",
            actions=[
                {
                    'text': '🚀 実行', 
                    'on_click': lambda: ui.notify('実行ボタンクリック！', type='positive'), 
                    'props': 'size=sm color=primary'
                },
                {
                    'text': '⏹️ 停止', 
                    'on_click': lambda: ui.notify('停止ボタンクリック！', type='warning'), 
                    'props': 'size=sm color=secondary'
                }
            ],
            style="full",
            height="100%"
        ):
            ui.label('リサイズ対応の基本パネル').style('margin-bottom:12px;font-weight:600;color:#1f2937;')
            
            # 入力要素（スクロール対応）
            ui.input(label='テキスト入力', placeholder='何か入力してください').props('outlined dense').style('width:100%;margin-bottom:8px;')
            ui.select(['オプション1', 'オプション2', 'オプション3'], label='選択ボックス', value='オプション1').props('outlined dense').style('width:100%;margin-bottom:8px;')
            ui.number(label='数値入力', value=100, min=0, max=1000).props('outlined dense').style('width:100%;margin-bottom:8px;')
            ui.textarea(label='詳細説明', placeholder='複数行のテキストを入力').props('outlined').style('width:100%;margin-bottom:8px;min-height:60px;')
            
            # PanelButton使用例（コンテンツ用）
            with ui.row().classes('gap-1').style('width:100%;margin-top:8px;'):
                PanelButton.content_button('実行', on_click=lambda: ui.notify('テスト実行！'), color='positive', icon='🚀', size='sm').style('flex:1;')
                PanelButton.content_button('リセット', on_click=lambda: ui.notify('リセット！'), color='grey', icon='🔄', size='sm').style('flex:1;')
    
    def _create_compact_panel(self):
        """コンパクトパネル（右上）"""
        with CommonPanel(
            title="コンパクト",
            icon="⚡",
            style="full",
            height="100%"
        ):
            ui.label('コンパクトスタイル').style('margin-bottom:8px;color:#374151;font-weight:600;')
            ui.label('余白・影を最小限に抑制').style('font-size:12px;color:#6b7280;margin-bottom:12px;')
            
            # 小さなコントロール群
            ui.toggle(['モード1', 'モード2', 'モード3'], value='モード1').style('margin-bottom:8px;')
            ui.slider(min=0, max=100, value=50, step=10).props('label-always').style('margin-bottom:8px;')
            
            # カラーピッカー風
            colors = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444']
            with ui.row().classes('gap-1').style('width:100%;margin-bottom:8px;'):
                for color in colors:
                    ui.button('●', on_click=lambda c=color: ui.notify(f'色選択: {c}')).props('size=sm').style(f'background:{color};color:white;min-width:30px;')
            
            with ui.row().classes('gap-1').style('width:100%;'):
                ui.button('小', on_click=lambda: ui.notify('小ボタン')).props('size=sm color=primary')
                ui.button('中', on_click=lambda: ui.notify('中ボタン')).props('size=sm color=secondary')
                ui.button('大', on_click=lambda: ui.notify('大ボタン')).props('size=sm color=positive')
    
    def _create_full_panel(self):
        """フルパネル（左下）"""
        with CommonPanel(
            title="フルスタイル",
            icon="🎯",
            actions=[
                {
                    'text': '📤 エクスポート', 
                    'on_click': lambda: ui.notify('エクスポート処理開始', type='info'), 
                    'props': 'size=sm color=primary'
                },
                {
                    'text': '📥 インポート', 
                    'on_click': lambda: ui.notify('インポート処理開始', type='info'), 
                    'props': 'size=sm color=secondary'
                }
            ],
            style="full",
            height="100%"
        ):
            ui.label('フルスタイル（影強・余白なし）').style('margin-bottom:8px;font-weight:bold;color:#1f2937;')
            
            # ページネーション付きDataTable（角丸完璧）
            test_data = [
                ['データ項目 1', '完了', '2024-01-15'],
                ['データ項目 2', '処理中', '2024-01-16'],
                ['データ項目 3', 'エラー', '2024-01-17'],
                ['データ項目 4', '待機', '2024-01-18'],
                ['データ項目 5', '準備中', '2024-01-19'],
                ['データ項目 6', '完了', '2024-01-20'],
                ['データ項目 7', '処理中', '2024-01-21'],
                ['データ項目 8', 'エラー', '2024-01-22'],
                ['データ項目 9', '待機', '2024-01-23'],
                ['データ項目 10', '準備中', '2024-01-24'],
            ]
            
            DataTable(
                headers=['項目名', 'ステータス', '日付'],
                rows=test_data,
                page_size=3,
                show_pagination=True,
                striped=True,
                bordered=True
            )
            
            # プログレス表示
            ui.label('処理進捗').style('font-size:12px;font-weight:600;color:#374151;margin:8px 0 4px 0;')
            progress_value = 65
            with ui.element('div').style('background:#e5e7eb;border-radius:4px;height:6px;overflow:hidden;margin-bottom:8px;'):
                ui.element('div').style(f'background:#3b82f6;height:100%;width:{progress_value}%;transition:width 0.3s ease;')
            ui.label(f'{progress_value}% 完了').style('font-size:11px;color:#6b7280;')
    
    def _create_custom_test_area(self):
        """カスタムテスト領域（右下）- 自由編集用"""
        with CommonPanel(
            title="配置テスト",
            icon="🔬",
            actions=[
                {
                    'text': '🧹 クリア', 
                    'on_click': lambda: ui.notify('テストエリアクリア', type='info'), 
                    'props': 'size=sm color=warning'
                },
                {
                    'text': '🔄 リロード', 
                    'on_click': lambda: ui.notify('リロード実行', type='info'), 
                    'props': 'size=sm color=info'
                }
            ],
            style="full",
            height="100%"
        ):
            ui.label('🎨 配置・レイアウトテストエリア').style('margin-bottom:12px;font-weight:bold;color:#7c3aed;')
            ui.label('ここで新しいコンポーネントの配置をテスト').style('margin-bottom:12px;color:#6b7280;font-size:13px;')
            
            # === 自由編集エリア開始 ===
            
            # タブ風インターフェース例
            with ui.element('div').style('border:1px solid #d1d5db;border-radius:6px;overflow:hidden;margin-bottom:12px;'):
                # タブヘッダー
                with ui.element('div').style('background:#f8f9fa;display:flex;border-bottom:1px solid #d1d5db;'):
                    for i, tab_name in enumerate(['設定', 'データ', 'ログ']):
                        bg = '#3b82f6' if i == 0 else 'transparent'
                        color = 'white' if i == 0 else '#6b7280'
                        with ui.element('div').style(f'padding:6px 12px;background:{bg};color:{color};font-size:12px;font-weight:500;cursor:pointer;border-right:1px solid #d1d5db;'):
                            ui.label(tab_name)
                
                # タブコンテンツ
                with ui.element('div').style('padding:8px;min-height:80px;'):
                    ui.label('選択されたタブの内容がここに表示されます').style('color:#6b7280;font-size:12px;')
            
            # カード風レイアウト例
            with ui.row().classes('gap-1').style('width:100%;margin-bottom:8px;'):
                for i, (icon, label) in enumerate([('📊', 'データ'), ('⚙️', '設定'), ('📈', '分析')]):
                    with ui.element('div').style('flex:1;border:1px solid #e5e7eb;border-radius:4px;padding:6px;text-align:center;cursor:pointer;background:white;').on('click', lambda l=label: ui.notify(f'{l}クリック')):
                        ui.label(icon).style('font-size:16px;margin-bottom:2px;')
                        ui.label(label).style('font-size:11px;color:#6b7280;')
            
            # === 自由編集エリア終了 ===
            
            ui.label('💡 新機能配置テスト時はここを使用').style('margin-top:8px;font-size:11px;color:#9ca3af;text-align:center;')

    def _create_experimental_layout_1(self):
        """新レイアウト実験エリア1 - 自由に書き換え可能"""
        with ui.element('div').style('padding:6px;height:100%;overflow:hidden;max-height:100%;'):
            ui.label('🧪 新レイアウト実験エリア①').style('font-size:18px;font-weight:bold;text-align:center;margin:8px 0;color:#7c3aed;')
            ui.label('ここで新しいレイアウトパターンを実験してください').style('text-align:center;color:#6b7280;margin-bottom:16px;font-size:13px;')
            
            # === 実験エリア開始 ===
            
            # 例：横一列カードレイアウト
            with ui.row().classes('w-full gap-2'):
                for i in range(3):
                    with CommonPanel(
                        title=f"カード{i+1}",
                        icon="📄",
                        style="compact",
                        height="180px"
                    ):
                        ui.label(f'カード{i+1}の内容').style('text-align:center;margin:16px;')
            
            # === 実験エリア終了 ===
    
    def _create_experimental_layout_2(self):
        """新レイアウト実験エリア2 - 自由に書き換え可能"""
        with ui.element('div').style('padding:6px;height:100%;overflow:hidden;max-height:100%;'):
            ui.label('⚡ 新レイアウト実験エリア②').style('font-size:18px;font-weight:bold;text-align:center;margin:8px 0;color:#f59e0b;')
            ui.label('別のレイアウトパターンをここで実験してください').style('text-align:center;color:#6b7280;margin-bottom:16px;font-size:13px;')
            
            # === 実験エリア開始 ===
            
            # 例：縦積みリストレイアウト
            with ui.column().classes('w-full max-w-lg mx-auto gap-2'):
                for i in range(4):
                    with CommonPanel(
                        title=f"リスト項目{i+1}",
                        icon="📋",
                        actions=[
                            {'text': '編集', 'on_click': lambda j=i: ui.notify(f'項目{j+1}編集'), 'props': 'size=sm color=primary'}
                        ],
                        style="default",
                        height="auto"
                    ):
                        ui.label(f'リスト項目{i+1}の詳細説明がここに入ります').style('margin:8px;')
            
            # === 実験エリア終了 ===
    
    def _create_component_practice_area(self):
        """コンポーネント単体練習エリア - 自由に書き換え可能"""
        with ui.element('div').style('padding:6px;height:100%;overflow:hidden;max-height:100%;'):
            ui.label('🔬 コンポーネント単体練習').style('font-size:18px;font-weight:bold;text-align:center;margin:8px 0;color:#10b981;')
            ui.label('新しいコンポーネントの練習・作り込みはここで').style('text-align:center;color:#6b7280;margin-bottom:16px;font-size:13px;')
            
            # === 練習エリア開始 ===
            
            # 例：コンポーネントバリエーション
            with ui.row().classes('w-full gap-4'):
                # default スタイル
                with CommonPanel(
                    title="default",
                    icon="📄",
                    style="default",
                    height="140px"
                ):
                    ui.label('デフォルトスタイル').style('text-align:center;margin:16px;font-size:13px;')
                
                # compact スタイル
                with CommonPanel(
                    title="compact",
                    icon="⚡",
                    style="compact",
                    height="140px"
                ):
                    ui.label('コンパクトスタイル').style('text-align:center;margin:16px;font-size:13px;')
                
                # full スタイル
                with CommonPanel(
                    title="full",
                    icon="🎯",
                    style="full",
                    height="140px"
                ):
                    ui.label('フルスタイル').style('text-align:center;margin:16px;font-size:13px;')
            
            # === 練習エリア終了 ===

# テスト用関数（必要に応じて追加）
def test_notification():
    """通知テスト"""
    ui.notify('🧪 配置テスト通知！', type='positive')

def test_dialog():
    """ダイアログテスト"""
    with ui.dialog() as dialog, ui.card():
        ui.label('配置テストダイアログ')
        ui.button('閉じる', on_click=dialog.close)
    dialog.open()