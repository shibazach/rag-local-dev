"""配置テスト - タブC: 共通コンポーネント実証テスト"""

from nicegui import ui
from prototypes.ui.components.elements import CommonPanel, CommonSplitter, CommonCard, CommonSectionTitle

class ArrangementTestTabC:
    """タブC: 共通コンポーネント実証テスト場"""
    
    def render(self):
        """タブCの共通コンポーネントテストを描画"""
        # スプリッター用CSS追加
        CommonSplitter.add_splitter_styles()
        
        with ui.element('div').style(
            'width: 100%; height: 100%; '
            'display: flex; margin: 0; padding: 8px; '
            'box-sizing: border-box; gap: 0;'
        ):
            # 左側: パネルテスト
            with ui.element('div').style(
                'width: 50%; height: 100%; '
                'display: flex; flex-direction: column; '
                'margin: 0; padding: 0; gap: 0;'
            ):
                # 上パネル: データ分析風
                with CommonPanel(
                    title="📊 共通パネルテスト",
                    gradient="linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
                    buttons=[
                        ('📈', lambda: ui.notify('チャートボタン')),
                        ('⚙️', lambda: ui.notify('設定ボタン'))
                    ],
                    footer_content="📊 更新: 2024-01-15 15:30",
                    height="50%",
                    panel_id="test-panel-1"
                ):
                    CommonSectionTitle.create("🎯 パネル内容テスト")
                    ui.label("CommonPanelコンポーネントの動作確認")
                    ui.label("・ヘッダーボタン動作 ✅")
                    ui.label("・コンテンツエリア表示 ✅") 
                    ui.label("・フッター表示 ✅")
                
                # スプリッター
                CommonSplitter.create_horizontal("test-h-splitter")
                
                # 下パネル: タスク管理風
                with CommonPanel(
                    title="📝 タスク管理",
                    gradient="linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)",
                    buttons=[
                        ('✅', lambda: ui.notify('完了')),
                        ('🔄', lambda: ui.notify('更新'))
                    ],
                    footer_content="📝 タスク: 3件",
                    height="50%",
                    panel_id="test-panel-2"
                ):
                    CommonSectionTitle.create("📋 タスクリスト")
                    
                    # タスクアイテム
                    tasks = [
                        ('共通コンポーネント作成', '完了', '#10b981'),
                        ('テスト実装', '進行中', '#f59e0b'),
                        ('ドキュメント作成', '待機', '#6b7280')
                    ]
                    
                    for task, status, color in tasks:
                        with ui.element('div').style(
                            'display: flex; justify-content: space-between; '
                            'align-items: center; padding: 4px 0; '
                            'border-bottom: 1px solid #f3f4f6;'
                        ):
                            ui.label(task).style('font-size: 12px;')
                            with ui.element('span').style(
                                f'background: {color}; color: white; '
                                f'padding: 2px 6px; border-radius: 3px; '
                                f'font-size: 9px;'
                            ):
                                ui.label(status)
            
            # 縦スプリッター
            CommonSplitter.create_vertical("test-v-splitter")
            
            # 右側: カード・セクションテスト
            with ui.element('div').style(
                'width: 50%; height: 100%; '
                'overflow-y: auto; padding: 8px; '
                'background: #f8fafc;'
            ):
                CommonSectionTitle.create("🎨 共通コンポーネント展示", size="18px")
                
                # カードテスト1
                with CommonCard():
                    CommonSectionTitle.create("🔧 CommonPanel", size="14px")
                    ui.label("・ヘッダー・コンテンツ・フッター構造")
                    ui.label("・カスタマイズ可能なグラデーション")
                    ui.label("・ボタン配置対応")
                    ui.label("・NiceGUI公式準拠")
                
                # カードテスト2
                with CommonCard():
                    CommonSectionTitle.create("🎛️ CommonSplitter", size="14px")
                    ui.label("・横・縦スプリッター対応")
                    ui.label("・ホバー・ドラッグ時色変更")
                    ui.label("・CSS自動追加")
                    ui.label("・ID管理対応")
                
                # カードテスト3
                with CommonCard():
                    CommonSectionTitle.create("📦 CommonCard", size="14px")
                    ui.label("・ui.card()ベース")
                    ui.label("・パディング・マージン調整")
                    ui.label("・シャドウ・角丸対応")
                    ui.label("・Context Manager")
                
                # カードテスト4
                with CommonCard():
                    CommonSectionTitle.create("📰 CommonSectionTitle", size="14px")
                    ui.label("・統一タイトルスタイル")
                    ui.label("・アイコン・色・サイズ調整")
                    ui.label("・マージン制御")
                    ui.label("・Static Method")
                
                # 成功メッセージ
                with ui.element('div').style(
                    'background: #dcfce7; border: 1px solid #16a34a; '
                    'border-radius: 8px; padding: 12px; margin-top: 16px;'
                ):
                    ui.label('✅ 共通コンポーネント実装成功！').style(
                        'color: #15803d; font-weight: bold;'
                    )
                    ui.label('各コンポーネントが正常に動作しています').style('color: #166534;')
        
        # スプリッター動作JavaScript追加
        self._add_splitter_js()
    
    def _add_splitter_js(self):
        """スプリッター動作JavaScript"""
        ui.add_head_html('''
        <script>
        function initTestSplitters() {
            setTimeout(() => {
                const vSplitter = document.getElementById('test-v-splitter');
                const hSplitter = document.getElementById('test-h-splitter');
                
                let isDragging = false;
                let currentSplitter = null;
                
                // 縦スプリッター
                if (vSplitter) {
                    vSplitter.addEventListener('mousedown', (e) => {
                        isDragging = true;
                        currentSplitter = 'vertical';
                        vSplitter.classList.add('dragging');
                        document.body.style.userSelect = 'none';
                        document.body.style.cursor = 'col-resize';
                        e.preventDefault();
                    });
                }
                
                // 横スプリッター
                if (hSplitter) {
                    hSplitter.addEventListener('mousedown', (e) => {
                        isDragging = true;
                        currentSplitter = 'horizontal';
                        hSplitter.classList.add('dragging');
                        document.body.style.userSelect = 'none';
                        document.body.style.cursor = 'row-resize';
                        e.preventDefault();
                    });
                }
                
                // ドラッグ終了
                document.addEventListener('mouseup', () => {
                    if (isDragging) {
                        document.querySelectorAll('.splitter').forEach(splitter => {
                            splitter.classList.remove('dragging');
                        });
                        isDragging = false;
                        currentSplitter = null;
                        document.body.style.userSelect = '';
                        document.body.style.cursor = '';
                    }
                });
                
                console.log('Test splitters initialized');
            }, 500);
        }
        
        setTimeout(initTestSplitters, 100);
        </script>
        ''')