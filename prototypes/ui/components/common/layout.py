"""
レイアウト関連の共通コンポーネント
Splitter、Card、SectionTitle、Tabs
"""
from nicegui import ui
from typing import Optional, Callable, Any


class CommonSplitter:
    """
    共通スプリッターコンポーネント（NiceGUI公式準拠）
    
    機能:
    - 横・縦スプリッター対応
    - ホバー・ドラッグ時の色変更
    - 最小サイズ制限
    - カスタマイズ可能な外観
    
    Usage:
        CommonSplitter.create_horizontal(splitter_id="h-splitter-1")
        CommonSplitter.create_vertical(splitter_id="v-splitter-1")
    """
    
    @staticmethod
    def create_horizontal(splitter_id: str, height: str = "6px"):
        """横スプリッター作成"""
        with ui.element('div').style(
            f'width: 100%; height: {height}; '
            f'background: #e5e7eb; '
            f'cursor: row-resize; margin: 0; padding: 0; '
            f'display: flex; align-items: center; justify-content: center; '
            f'transition: background 0.2s ease;'
        ).props(f'id="{splitter_id}" class="splitter"'):
            ui.label('⋮⋮⋮').style(
                'color: #9ca3af; font-size: 8px; transform: rotate(90deg); '
                'transition: color 0.2s ease;'
            ).classes('splitter-dots')
    
    @staticmethod
    def create_vertical(splitter_id: str, width: str = "6px"):
        """縦スプリッター作成"""
        with ui.element('div').style(
            f'width: {width}; height: 100%; '
            f'background: #e5e7eb; '
            f'cursor: col-resize; margin: 0; padding: 0; '
            f'display: flex; align-items: center; justify-content: center; '
            f'transition: background 0.2s ease;'
        ).props(f'id="{splitter_id}" class="splitter"'):
            ui.label('⋮⋮⋮').style(
                'color: #9ca3af; font-size: 8px; '
                'transition: color 0.2s ease;'
            ).classes('splitter-dots')
    
    @staticmethod
    def add_splitter_styles():
        """スプリッター用CSSスタイル追加"""
        ui.add_head_html('''
        <style>
        .splitter:hover {
            background: linear-gradient(135deg, #3b82f6, #1d4ed8) !important;
        }
        .splitter:hover .splitter-dots {
            color: white !important;
        }
        .splitter.dragging {
            background: linear-gradient(135deg, #1d4ed8, #1e40af) !important;
        }
        .splitter.dragging .splitter-dots {
            color: white !important;
        }
        </style>
        ''')
    
    @staticmethod
    def add_splitter_javascript():
        """統一スプリッターJavaScript（全IDに対応）"""
        ui.add_head_html('''
        <script>
        // グローバルスプリッター管理システム
        window.splitterManager = window.splitterManager || {
            initialized: false,
            isDragging: false,
            currentSplitter: null,
            
            init: function() {
                if (this.initialized) return;
                
                setTimeout(() => {
                    // 全スプリッター要素を自動検出
                    const allSplitters = document.querySelectorAll('.splitter');
                    
                    allSplitters.forEach(splitter => {
                        if (!splitter.dataset.splitterInitialized) {
                            this.initSplitter(splitter);
                            splitter.dataset.splitterInitialized = 'true';
                        }
                    });
                    
                    // グローバルイベント設定
                    this.setupGlobalEvents();
                    this.initialized = true;
                    console.log(`CommonSplitter: ${allSplitters.length}個のスプリッター初期化完了`);
                }, 300);
            },
            
            initSplitter: function(splitter) {
                const isVertical = splitter.style.cursor === 'col-resize';
                
                splitter.addEventListener('mousedown', (e) => {
                    this.isDragging = true;
                    this.currentSplitter = splitter;
                    splitter.classList.add('dragging');
                    document.body.style.userSelect = 'none';
                    document.body.style.cursor = isVertical ? 'col-resize' : 'row-resize';
                    e.preventDefault();
                });
            },
            
            setupGlobalEvents: function() {
                if (this.globalEventsSetup) return;
                
                // mousemoveイベントでサイズ変更
                document.addEventListener('mousemove', (e) => {
                    if (!this.isDragging || !this.currentSplitter) return;
                    
                    const splitter = this.currentSplitter;
                    const isVertical = splitter.style.cursor === 'col-resize';
                    const prevElement = splitter.previousElementSibling;
                    const nextElement = splitter.nextElementSibling;
                    
                    if (!prevElement || !nextElement) return;
                    
                    const parent = splitter.parentElement;
                    const parentRect = parent.getBoundingClientRect();
                    
                    if (isVertical) {
                        // 縦スプリッター（左右分割）
                        const x = e.clientX - parentRect.left;
                        const percentage = Math.max(20, Math.min(80, (x / parentRect.width) * 100));
                        
                        prevElement.style.width = percentage + '%';
                        nextElement.style.width = (100 - percentage) + '%';
                    } else {
                        // 横スプリッター（上下分割）
                        const y = e.clientY - parentRect.top;
                        const percentage = Math.max(20, Math.min(80, (y / parentRect.height) * 100));
                        
                        prevElement.style.height = percentage + '%';
                        nextElement.style.height = (100 - percentage) + '%';
                    }
                });
                
                document.addEventListener('mouseup', () => {
                    if (this.isDragging) {
                        document.querySelectorAll('.splitter').forEach(s => {
                            s.classList.remove('dragging');
                        });
                        this.isDragging = false;
                        this.currentSplitter = null;
                        document.body.style.userSelect = '';
                        document.body.style.cursor = '';
                    }
                });
                
                this.globalEventsSetup = true;
            }
        };
        
        // 初期化実行
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => window.splitterManager.init());
        } else {
            window.splitterManager.init();
        }
        
        // ページ遷移後の再初期化
        setTimeout(() => window.splitterManager.init(), 100);
        </script>
        ''')


class CommonCard:
    """
    簡易カードコンポーネント（NiceGUI ui.card()準拠）
    
    機能:
    - NiceGUI公式ui.card()ベース
    - カスタマイズ可能なパディング・マージン
    - シャドウ・角丸対応
    
    Usage:
        with CommonCard(padding="16px", margin_bottom="16px"):
            ui.label('カード内容')
    """
    
    def __init__(
        self,
        padding: str = "16px",
        margin_bottom: str = "16px",
        border_radius: str = "8px",
        shadow: str = "0 2px 8px rgba(0,0,0,0.1)"
    ):
        self.padding = padding
        self.margin_bottom = margin_bottom
        self.border_radius = border_radius
        self.shadow = shadow
        self.card = None
    
    def __enter__(self):
        """カード開始"""
        self.card = ui.card().style(
            f'padding: {self.padding}; margin-bottom: {self.margin_bottom}; '
            f'border-radius: {self.border_radius}; '
            f'box-shadow: {self.shadow};'
        )
        return self.card.__enter__()
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """カード終了"""
        return self.card.__exit__(exc_type, exc_val, exc_tb)


class CommonSectionTitle:
    """
    セクションタイトルコンポーネント（NiceGUI公式準拠）
    
    機能:
    - 統一されたタイトルスタイル
    - アイコン・色・サイズカスタマイズ
    - マージン調整
    
    Usage:
        CommonSectionTitle.create("📝 基本要素", size="16px", margin_bottom="12px")
    """
    
    @staticmethod
    def create(
        title: str,
        size: str = "16px",
        color: str = "#1f2937",
        margin_bottom: str = "12px",
        font_weight: str = "bold"
    ):
        """セクションタイトル作成"""
        ui.label(title).style(
            f'font-size: {size}; font-weight: {font_weight}; '
            f'margin-bottom: {margin_bottom}; color: {color};'
        )


class CommonTabs:
    """
    共通タブコンポーネント（NiceGUI公式準拠）
    
    機能:
    - タブヘッダー・コンテンツエリア管理
    - アクティブ・非アクティブ状態制御
    - JavaScript切り替え自動生成
    - 高さ・幅・背景色カスタマイズ
    
    Usage:
        tabs = CommonTabs(tab_height="32px")
        tabs.add_tab("tab1", "A", ArrangementTestTabA(), is_active=True)
        tabs.add_tab("tab2", "B", ArrangementTestTabB())
        tabs.render()
    """
    
    def __init__(
        self,
        tab_height: str = "32px",
        background_color: str = "#ffffff",
        border_color: str = "#e5e7eb",
        content_background: str = "#f8fafc"
    ):
        self.tab_height = tab_height
        self.background_color = background_color
        self.border_color = border_color
        self.content_background = content_background
        self.tabs = []
        self.tab_container = None
        self.content_container = None
    
    def add_tab(self, tab_id: str, label: str, content_renderer, is_active: bool = False):
        """タブ追加"""
        self.tabs.append({
            'id': tab_id,
            'label': label,
            'content_renderer': content_renderer,
            'is_active': is_active
        })
    
    def render(self):
        """タブインターフェース描画"""
        with ui.element('div').style(
            'width: 100%; height: 100%; '
            'display: flex; flex-direction: column; '
            'margin: 0; padding: 0; '
            'overflow: hidden;'
        ):
            # タブヘッダー
            self._create_tab_header()
            
            # タブコンテンツエリア
            self._create_tab_content()
            
            # タブ切り替えJavaScript
            self._add_tab_switching_js()
    
    def _create_tab_header(self):
        """タブヘッダー作成"""
        with ui.element('div').style(
            f'width: 100%; height: {self.tab_height}; '
            f'background: {self.background_color}; '
            f'border-bottom: 1px solid {self.border_color}; '
            f'display: flex; margin: 0; padding: 0; '
            f'flex-shrink: 0;'
        ):
            for tab in self.tabs:
                self._create_tab_button(tab['id'], tab['label'], tab['is_active'])
    
    def _create_tab_button(self, tab_id: str, label: str, is_active: bool):
        """タブボタン作成"""
        active_style = (
            'background: #3b82f6; color: white; '
            'border-bottom: 2px solid #1d4ed8;'
        ) if is_active else (
            'background: #f3f4f6; color: #6b7280; '
            'border-bottom: 2px solid transparent;'
        )
        
        ui.button(label).style(
            f'padding: 8px 16px; border: none; '
            f'border-radius: 0; font-size: 12px; '
            f'font-weight: 500; cursor: pointer; '
            f'transition: all 0.2s ease; '
            f'min-width: 60px; {active_style}'
        ).props(f'id="btn-{tab_id}" onclick="switchTab(\'{tab_id}\')"')
    
    def _create_tab_content(self):
        """タブコンテンツエリア作成"""
        with ui.element('div').style(
            'flex: 1; margin: 0; padding: 0; '
            'overflow: hidden;'
        ):
            for tab in self.tabs:
                display_style = 'display: block;' if tab['is_active'] else 'display: none;'
                
                with ui.element('div').style(
                    f'{display_style} height: 100%; '
                    f'margin: 0; padding: 0; '
                    f'background: {self.content_background};'
                ).props(f'id="{tab["id"]}-content"'):
                    # コンテンツレンダリング
                    if hasattr(tab['content_renderer'], 'render'):
                        tab['content_renderer'].render()
                    elif callable(tab['content_renderer']):
                        tab['content_renderer']()
    
    def _add_tab_switching_js(self):
        """タブ切り替えJavaScript"""
        tab_ids = [tab['id'] for tab in self.tabs]
        tabs_js_array = str(tab_ids).replace("'", '"')
        
        ui.add_head_html(f'''
        <script>
        const tabIds = {tabs_js_array};
        
        function switchTab(activeTabId) {{
            // 全タブボタンを非アクティブ化
            tabIds.forEach(tabId => {{
                const btn = document.getElementById('btn-' + tabId);
                const content = document.getElementById(tabId + '-content');
                
                if (btn) {{
                    btn.style.background = '#f3f4f6';
                    btn.style.color = '#6b7280';
                    btn.style.borderBottom = '2px solid transparent';
                }}
                
                if (content) {{
                    content.style.display = 'none';
                }}
            }});
            
            // アクティブタブを設定
            const activeBtn = document.getElementById('btn-' + activeTabId);
            const activeContent = document.getElementById(activeTabId + '-content');
            
            if (activeBtn) {{
                activeBtn.style.background = '#3b82f6';
                activeBtn.style.color = 'white';
                activeBtn.style.borderBottom = '2px solid #1d4ed8';
            }}
            
            if (activeContent) {{
                activeContent.style.display = 'block';
            }}
            
            console.log('Switched to tab:', activeTabId);
        }}
        
        // ホバー効果
        document.addEventListener('DOMContentLoaded', () => {{
            tabIds.forEach(tabId => {{
                const btn = document.getElementById('btn-' + tabId);
                if (btn) {{
                    btn.addEventListener('mouseenter', () => {{
                        if (!btn.style.background.includes('#3b82f6')) {{
                            btn.style.background = '#e5e7eb';
                        }}
                    }});
                    
                    btn.addEventListener('mouseleave', () => {{
                        if (!btn.style.background.includes('#3b82f6')) {{
                            btn.style.background = '#f3f4f6';
                        }}
                    }});
                }}
            }});
        }});
        </script>
        ''')