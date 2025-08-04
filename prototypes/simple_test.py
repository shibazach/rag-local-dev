#!/usr/bin/env python3
"""
完全シンプルテスト: NiceGUIのみ
DOM構造確認用の実験ファイル（最小構成）
"""

from nicegui import ui

# ===== 完全まっさらなページ =====
@ui.page('/')
def home():
    """完全まっさらなNiceGUIページ"""
    ui.label('🔬 最小構成DOM構造テスト')
    ui.label('これは完全まっさらなNiceGUIページです')

# ===== 基本パネルのみのページ =====
@ui.page('/panel')
def panel_test():
    """基本パネル1つだけのページ"""
    with ui.element('div').style('border:1px solid #ccc;padding:16px;margin:16px;'):
        ui.label('📋 基本パネルテスト')
        ui.button('ボタン')
        ui.input('入力フィールド')

# ===== Quasarタブのみのページ =====
@ui.page('/tabs')
def tabs_test():
    """Quasarタブのみのページ（最小構成）"""
    with ui.tabs() as tabs:
        tab1 = ui.tab('タブA')
        tab2 = ui.tab('タブB')
    
    with ui.tab_panels(tabs, value=tab1):
        with ui.tab_panel(tab1):
            ui.label('タブAの内容')
        with ui.tab_panel(tab2):
            ui.label('タブBの内容')

# ===== position:fixedヘッダーのみのページ =====
@ui.page('/header')
def header_test():
    """position:fixedヘッダーのみのページ"""
    # position:fixedヘッダー
    with ui.element('div').style('position:fixed;top:0;left:0;width:100%;height:48px;background:#334155;color:white;z-index:1000;display:flex;align-items:center;padding:0 16px;'):
        ui.label('🏠 固定ヘッダー')
    
    # メインコンテンツ（margin-top:48px）
    with ui.element('div').style('margin-top:48px;padding:16px;'):
        ui.label('メインコンテンツエリア')
        ui.label('ヘッダーの下に配置されています')

# ===== ヘッダー+フッター+メインのページ =====
@ui.page('/layout')
def layout_test():
    """ヘッダー+フッター+メインコンテンツのページ"""
    # ヘッダー
    with ui.element('div').style('position:fixed;top:0;left:0;width:100%;height:48px;background:#334155;color:white;z-index:1000;display:flex;align-items:center;padding:0 16px;'):
        ui.label('🏠 ヘッダー')
    
    # メインコンテンツ
    with ui.element('div').style('margin-top:48px;margin-bottom:24px;padding:16px;min-height:calc(100vh - 72px);'):
        ui.label('📄 メインコンテンツ')
        ui.label('ヘッダーとフッターの間に配置')
        for i in range(50):
            ui.label(f'コンテンツ行 {i+1}')
    
    # フッター
    with ui.element('div').style('position:fixed;bottom:0;left:0;width:100%;height:24px;background:#374151;color:white;z-index:999;display:flex;align-items:center;padding:0 16px;'):
        ui.label('📊 フッター')

# ===== グレー背景でmargin確認ページ =====
@ui.page('/gray')
def gray_test():
    """グレー背景でmargin16px確認ページ"""
    # より強力にリセット
    ui.query('html').style('margin: 0; padding: 0; background-color: #808080;')
    ui.query('body').style('margin: 0; padding: 0; background-color: #808080;')
    ui.query('.q-layout').style('margin: 0; padding: 0;')
    ui.query('.q-page-container').style('margin: 0; padding: 0;')
    ui.query('.q-page').style('margin: 0; padding: 0;')
    ui.query('.nicegui-content').style('margin: 0; padding: 0;')
    
    # 緑枠の外枠
    with ui.element('div').style(
        'position: fixed;'
        'top: 0;'
        'left: 0;'
        'width: 100vw;'
        'height: 100vh;'
        'background-color: #00ff00;'  # 緑色背景
        'z-index: 9999;'              # 最前面
        'margin: 0;'
        'padding: 0;'
        'box-sizing: border-box;'
    ):
        # 赤枠（16px内側）
        with ui.element('div').style(
            'position: absolute;'
            'top: 16px;'
            'left: 16px;'
            'width: calc(100% - 32px);'
            'height: calc(100% - 32px);'
            'background-color: #ff0000;'  # 赤色背景
            'margin: 0;'
            'padding: 0;'
            'box-sizing: border-box;'
            'display: flex;'
            'flex-direction: column;'
        ):
            # 上部ヘッダエリア（32px、赤）
            with ui.element('div').style(
                'height: 32px;'
                'background-color: #ff0000;'
                'margin: 0;'
                'padding: 0;'
                'flex-shrink: 0;'
            ):
                pass
            
            # 中央白エリア（メインコンテンツ）
            with ui.element('div').style(
                'flex: 1;'
                'background-color: #ffffff;'  # 白色背景
                'margin: 0;'
                'padding: 0;'
                'display: flex;'
                'flex-direction: column;'
                'justify-content: center;'
                'align-items: center;'
            ):
                ui.label('🔍 強制表示テスト').style('color: #ff0000; font-size: 32px; margin: 10px 0; font-weight: bold;')
                ui.label('緑の境界線が画面端に届いているか確認').style('color: #ff0000; font-size: 20px; margin: 10px 0;')
                ui.label('隙間があればその幅がNiceGUIのmarginです').style('color: #ff0000; font-size: 20px; margin: 10px 0;')
            
            # 下部フッタエリア（8px、赤）
            with ui.element('div').style(
                'height: 8px;'
                'background-color: #ff0000;'
                'margin: 0;'
                'padding: 0;'
                'flex-shrink: 0;'
            ):
                pass
    
    # 上部48px青帯（ヘッダー位置）
    with ui.element('div').style(
        'position: fixed;'
        'top: 0;'
        'left: 0;'
        'width: 100%;'
        'height: 48px;'
        'background-color: #0000ff;'  # 青色
        'z-index: 10001;'              # 赤より前面
        'margin: 0;'
        'padding: 0;'
        'display: flex;'
        'align-items: center;'
        'justify-content: center;'
    ):
        ui.label('📍 ヘッダー位置 48px').style('color: white; font-weight: bold;')
    
    # 下部24px茶帯（フッター位置）
    with ui.element('div').style(
        'position: fixed;'
        'bottom: 0;'
        'left: 0;'
        'width: 100%;'
        'height: 24px;'
        'background-color: #8B4513;'  # 茶色
        'z-index: 10001;'              # 赤より前面
        'margin: 0;'
        'padding: 0;'
        'display: flex;'
        'align-items: center;'
        'justify-content: center;'
    ):
        ui.label('📍 フッター位置 24px').style('color: white; font-weight: bold; font-size: 12px;')

# ===== C13方式パネルテスト =====
@ui.page('/c13test')
def c13_panel_test():
    """C13方式でパネル類をテスト - ベタ打ち実装"""
    
    # グローバルリセット強化
    ui.query('html').style('margin: 0; padding: 0; height: 100vh; overflow: hidden;')
    ui.query('body').style('margin: 0; padding: 0; height: 100vh; overflow: hidden;')
    ui.query('.q-layout').style('margin: 0; padding: 0; height: 100vh; overflow: hidden;')
    ui.query('.q-page-container').style('margin: 0; padding: 0; height: 100vh; overflow: hidden;')
    ui.query('.q-page').style('margin: 0; padding: 0; height: 100vh; overflow: hidden;')
    ui.query('.nicegui-content').style('margin: 0; padding: 0; height: 100vh; overflow: hidden;')
    
    # 固定ヘッダー（青帯）
    with ui.element('div').style(
        'position: fixed;'
        'top: 0;'
        'left: 0;'
        'width: 100%;'
        'height: 48px;'
        'background-color: #334155;'
        'color: white;'
        'z-index: 1000;'
        'display: flex;'
        'align-items: center;'
        'justify-content: center;'
        'margin: 0;'
        'padding: 0;'
    ):
        ui.label('🏠 C13テストヘッダー').style('font-weight: bold;')
    
    # 固定フッター（茶帯）
    with ui.element('div').style(
        'position: fixed;'
        'bottom: 0;'
        'left: 0;'
        'width: 100%;'
        'height: 24px;'
        'background-color: #374151;'
        'color: white;'
        'z-index: 999;'
        'display: flex;'
        'align-items: center;'
        'justify-content: center;'
        'margin: 0;'
        'padding: 0;'
    ):
        ui.label('📊 C13テストフッター').style('font-size: 12px;')
    
    # C13方式メインコンテナ
    with ui.element('div').style(
        # ヘッダー・フッターに合わせた配置
        'margin-top: 48px;'
        'margin-bottom: 24px;'
        'margin-left: 0;'
        'margin-right: 0;'
        'padding: 0;'
        'width: 100%;'
        'height: calc(100vh - 48px - 24px);'  # 正確な高さ計算
        'overflow: hidden;'
        'position: relative;'
        'box-sizing: border-box;'
        'display: flex;'
        'flex-direction: column;'
    ):
        # 内部コンテンツエリア（8pxパディング）
        with ui.element('div').style(
            'flex: 1;'
            'padding: 8px;'
            'margin: 0;'
            'overflow-y: auto;'
            'overflow-x: hidden;'
            'box-sizing: border-box;'
            'background-color: #f8f9fa;'
        ):
            ui.label('🎯 C13方式パネルテスト').style('font-size: 24px; margin-bottom: 16px; color: #1f2937;')
            
            # パネル1: デフォルトスタイル
            with ui.element('div').style(
                'background-color: white;'
                'border-radius: 8px;'
                'box-shadow: 0 2px 4px rgba(0,0,0,0.1);'
                'margin-bottom: 8px;'
                'overflow: hidden;'
            ):
                # パネルヘッダー
                with ui.element('div').style(
                    'background-color: #f8f9fa;'
                    'padding: 12px 16px;'
                    'border-bottom: 1px solid #e5e7eb;'
                    'display: flex;'
                    'align-items: center;'
                    'justify-content: space-between;'
                    'height: 48px;'
                    'box-sizing: border-box;'
                ):
                    ui.label('📄 基本パネル').style('font-weight: bold; color: #374151;')
                    with ui.element('div').style('display: flex; gap: 8px;'):
                        ui.button('編集', color='primary').style('padding: 4px 12px; font-size: 12px;')
                        ui.button('削除', color='negative').style('padding: 4px 12px; font-size: 12px;')
                
                # パネルコンテンツ
                with ui.element('div').style('padding: 16px;'):
                    ui.label('これは基本パネルのコンテンツです。C13方式でレイアウトが正しく動作するかテストしています。')
                    for i in range(5):
                        ui.label(f'テストデータ {i+1}: Lorem ipsum dolor sit amet, consectetur adipiscing elit.')
            
            # パネル2: コンパクトスタイル
            with ui.element('div').style(
                'background-color: white;'
                'border-radius: 8px;'
                'box-shadow: 0 2px 4px rgba(0,0,0,0.1);'
                'margin-bottom: 8px;'
                'overflow: hidden;'
            ):
                # コンパクトヘッダー
                with ui.element('div').style(
                    'background-color: #3b82f6;'
                    'color: white;'
                    'padding: 8px 16px;'
                    'display: flex;'
                    'align-items: center;'
                    'justify-content: space-between;'
                    'height: 36px;'
                    'box-sizing: border-box;'
                ):
                    ui.label('📊 コンパクトパネル').style('font-weight: bold; font-size: 14px;')
                    ui.button('設定', color='white').style('padding: 2px 8px; font-size: 11px;')
                
                # コンパクトコンテンツ
                with ui.element('div').style('padding: 12px;'):
                    with ui.element('table').style('width: 100%; border-collapse: collapse;'):
                        # テーブルヘッダー
                        with ui.element('tr').style('background-color: #f3f4f6;'):
                            ui.element('th').style('padding: 8px; text-align: left; border: 1px solid #d1d5db;').text = 'ID'
                            ui.element('th').style('padding: 8px; text-align: left; border: 1px solid #d1d5db;').text = '名前'
                            ui.element('th').style('padding: 8px; text-align: left; border: 1px solid #d1d5db;').text = 'ステータス'
                        
                        # テーブルデータ
                        for i in range(3):
                            with ui.element('tr'):
                                ui.element('td').style('padding: 6px; border: 1px solid #d1d5db;').text = f'{i+1}'
                                ui.element('td').style('padding: 6px; border: 1px solid #d1d5db;').text = f'項目{i+1}'
                                ui.element('td').style('padding: 6px; border: 1px solid #d1d5db;').text = '完了'
            
            # パネル3: フルスタイル（大量データでスクロールテスト）
            with ui.element('div').style(
                'background-color: white;'
                'border-radius: 8px;'
                'box-shadow: 0 2px 4px rgba(0,0,0,0.1);'
                'margin-bottom: 8px;'
                'height: 300px;'
                'overflow: hidden;'
                'display: flex;'
                'flex-direction: column;'
            ):
                # フルヘッダー
                with ui.element('div').style(
                    'background-color: #10b981;'
                    'color: white;'
                    'padding: 12px 16px;'
                    'display: flex;'
                    'align-items: center;'
                    'justify-content: space-between;'
                    'height: 48px;'
                    'box-sizing: border-box;'
                    'flex-shrink: 0;'
                ):
                    ui.label('📈 フルパネル（スクロールテスト）').style('font-weight: bold;')
                    with ui.element('div').style('display: flex; gap: 4px;'):
                        ui.button('追加', color='white').style('padding: 4px 8px; font-size: 11px;')
                        ui.button('エクスポート', color='white').style('padding: 4px 8px; font-size: 11px;')
                        ui.button('設定', color='white').style('padding: 4px 8px; font-size: 11px;')
                
                # スクロール可能コンテンツ
                with ui.element('div').style(
                    'flex: 1;'
                    'padding: 16px;'
                    'overflow-y: auto;'
                    'overflow-x: hidden;'
                ):
                    ui.label('大量データのスクロールテスト:').style('font-weight: bold; margin-bottom: 8px;')
                    for i in range(50):
                        ui.label(f'データ行 {i+1}: これは長いテストデータです。パネル内部のスクロールが正しく動作するかを確認しています。Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.')

# ===== C13方式4ペイン分割テスト =====
@ui.page('/c13split')
def c13_split_test():
    """C13方式4ペイン分割ドラッグリサイズテスト"""
    
    # グローバルリセット強化
    ui.query('html').style('margin: 0; padding: 0; height: 100vh; overflow: hidden;')
    ui.query('body').style('margin: 0; padding: 0; height: 100vh; overflow: hidden;')
    ui.query('.q-layout').style('margin: 0; padding: 0; height: 100vh; overflow: hidden;')
    ui.query('.q-page-container').style('margin: 0; padding: 0; height: 100vh; overflow: hidden;')
    ui.query('.q-page').style('margin: 0; padding: 0; height: 100vh; overflow: hidden;')
    ui.query('.nicegui-content').style('margin: 0; padding: 0; height: 100vh; overflow: hidden;')
    
    # 固定ヘッダー
    with ui.element('div').style(
        'position: fixed;'
        'top: 0;'
        'left: 0;'
        'width: 100%;'
        'height: 48px;'
        'background-color: #334155;'
        'color: white;'
        'z-index: 1000;'
        'display: flex;'
        'align-items: center;'
        'justify-content: center;'
        'margin: 0;'
        'padding: 0;'
    ):
        ui.label('🎯 C13 4ペイン分割テスト').style('font-weight: bold;')
    
    # 固定フッター
    with ui.element('div').style(
        'position: fixed;'
        'bottom: 0;'
        'left: 0;'
        'width: 100%;'
        'height: 24px;'
        'background-color: #374151;'
        'color: white;'
        'z-index: 999;'
        'display: flex;'
        'align-items: center;'
        'justify-content: center;'
        'margin: 0;'
        'padding: 0;'
    ):
        ui.label('📊 ドラッグでペインサイズ変更可能').style('font-size: 12px;')
    
    # スプリッターとリサイズのJavaScript
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
    
    # C13方式メインコンテナ
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
        # 4ペイン分割コンテナ
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
                                for i, (label, value, color) in enumerate([
                                    ('今月', '¥1,250,000', '#10b981'),
                                    ('前月', '¥1,180,000', '#3b82f6'),
                                    ('前年同月', '¥980,000', '#8b5cf6'),
                                    ('目標', '¥1,500,000', '#f59e0b')
                                ]):
                                    with ui.element('div').style(f'background: {color}; color: white; padding: 8px; border-radius: 6px; text-align: center;'):
                                        ui.label(label).style('font-size: 10px; opacity: 0.9;')
                                        ui.label(value).style('font-weight: bold; font-size: 12px;')
                
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
                            for i, (task, priority, status) in enumerate([
                                ('UI レイアウト改善', '高', '進行中'),
                                ('パフォーマンス最適化', '中', '完了'),
                                ('ドキュメント更新', '低', '待機'),
                                ('バグ修正 #123', '高', '進行中'),
                                ('テストケース追加', '中', '待機'),
                                ('コードレビュー', '中', '完了')
                            ]):
                                priority_color = '#ef4444' if priority == '高' else '#f59e0b' if priority == '中' else '#10b981'
                                status_color = '#3b82f6' if status == '進行中' else '#10b981' if status == '完了' else '#6b7280'
                                
                                with ui.element('div').style('background: #f8f9fa; border: 1px solid #e5e7eb; border-radius: 6px; padding: 8px; margin-bottom: 4px;'):
                                    ui.label(task).style('font-size: 12px; font-weight: bold; color: #374151; margin-bottom: 4px;')
                                    with ui.element('div').style('display: flex; justify-content: space-between; align-items: center;'):
                                        with ui.element('span').style(f'background: {priority_color}; color: white; padding: 2px 6px; border-radius: 3px; font-size: 9px;'):
                                            ui.label(priority)
                                        with ui.element('span').style(f'color: {status_color}; font-size: 10px; font-weight: bold;'):
                                            ui.label(status)
                
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
                            for i in range(20):
                                timestamp = f'2024-01-15 15:{30+i%30:02d}:{10+i%50:02d}'
                                log_type = ['INFO', 'WARN', 'ERROR', 'DEBUG'][i % 4]
                                log_color = {'INFO': '#10b981', 'WARN': '#f59e0b', 'ERROR': '#ef4444', 'DEBUG': '#6b7280'}[log_type]
                                message = [
                                    'User login successful',
                                    'Database connection established',
                                    'Cache miss for key: user_123',
                                    'API request processed in 245ms',
                                    'Memory usage: 75%',
                                    'Backup completed successfully'
                                ][i % 6]
                                
                                with ui.element('div').style('margin-bottom: 2px; font-size: 10px; line-height: 1.4;'):
                                    ui.label(f'[{timestamp}] ').style('color: #9ca3af;')
                                    ui.label(f'{log_type}: ').style(f'color: {log_color}; font-weight: bold;')
                                    ui.label(message).style('color: #e5e7eb;')

# ===== ルートインデックス（ナビゲーション） =====
@ui.page('/nav')
def navigation():
    """全テストページへのナビゲーション"""
    ui.markdown("""
    # 🔬 DOM構造テスト - ナビゲーション
    
    各ページでブラウザ開発者ツールを開いてDOM構造を確認してください。
    """)
    
    ui.link('1. 完全まっさら', '/')
    ui.link('2. 基本パネルのみ', '/panel')
    ui.link('3. Quasarタブのみ', '/tabs')
    ui.link('4. position:fixedヘッダーのみ', '/header')
    ui.link('5. ヘッダー+フッター+メイン', '/layout')
    ui.link('6. 🔍 グレー背景でmargin確認', '/gray')
    ui.link('7. 🎯 C13方式パネルテスト', '/c13test')
    ui.link('8. 🎮 C13方式4ペイン分割テスト', '/c13split')

if __name__ in {"__main__", "__mp_main__"}:
    print("🔬 シンプルDOM構造テスト開始")
    print("📍 ナビゲーション: http://localhost:8082/nav")
    print("📍 完全まっさら: http://localhost:8082/")
    print("📍 基本パネル: http://localhost:8082/panel")
    print("📍 Quasarタブ: http://localhost:8082/tabs")
    print("📍 固定ヘッダー: http://localhost:8082/header")
    print("📍 フルレイアウト: http://localhost:8082/layout")
    print("📍 🔍 Margin確認: http://localhost:8082/gray")
    print("📍 🎯 C13パネルテスト: http://localhost:8082/c13test")
    print("📍 🎮 C13 4ペイン分割: http://localhost:8082/c13split")
    
    # ポート8082で起動（本プロジェクトと完全分離）
    ui.run(
        host='0.0.0.0', 
        port=8082,
        title='シンプルDOM構造テスト',
        show=False
    )