"""UI個別要素 - 再利用可能なコンポーネント（NiceGUI公式準拠）"""

from nicegui import ui
from typing import Optional, List, Dict, Any, Callable

class CommonPanel:
    """
    共通パネルコンポーネント（NiceGUI公式準拠）
    
    機能:
    - ヘッダー・コンテンツ・フッター構造
    - カスタマイズ可能なスタイリング
    - ボタン配置・色設定対応
    - NiceGUI公式コンポーネント最大活用
    
    Usage:
        with CommonPanel(
            title="📊 データ分析",
            gradient="linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
            buttons=[('📈', lambda: print('chart')), ('⚙️', lambda: print('setting'))],
            footer_content="📊 データ更新: 2024-01-15 15:30"
        ) as panel:
            # コンテンツを配置
            ui.label('パネル内容')
    """
    
    def __init__(
        self,
        title: str,
        gradient: str = "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
        buttons: Optional[List[tuple]] = None,
        footer_content: Optional[str] = None,
        width: str = "100%",
        height: str = "100%",
        panel_id: Optional[str] = None
    ):
        self.title = title
        self.gradient = gradient
        self.buttons = buttons or []
        self.footer_content = footer_content
        self.width = width
        self.height = height
        self.panel_id = panel_id
        self.content_element = None
    
    def __enter__(self):
        """パネル開始 - context manager"""
        # 外側コンテナ
        self.outer_container = ui.element('div').style(
            f'width: {self.width}; height: {self.height}; '
            f'margin: 0; padding: 4px; '
            f'box-sizing: border-box; overflow: hidden;'
        )
        
        if self.panel_id:
            self.outer_container.props(f'id="{self.panel_id}"')
        
        self.outer_container.__enter__()
        
        # パネル本体
        self.panel_body = ui.element('div').style(
            'width: 100%; height: 100%; '
            'background: white; border-radius: 12px; '
            'box-shadow: 0 2px 8px rgba(0,0,0,0.15); '
            'border: 1px solid #e5e7eb; '
            'display: flex; flex-direction: column; '
            'overflow: hidden;'
        )
        self.panel_body.__enter__()
        
        # ヘッダー作成
        self._create_header()
        
        # コンテンツエリア作成
        self.content_element = ui.element('div').style(
            'flex: 1; padding: 8px; overflow: auto;'
        )
        self.content_element.__enter__()
        
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """パネル終了 - context manager"""
        # コンテンツエリア終了
        self.content_element.__exit__(exc_type, exc_val, exc_tb)
        
        # フッター作成（必要な場合）
        if self.footer_content:
            self._create_footer()
        
        # パネル本体終了
        self.panel_body.__exit__(exc_type, exc_val, exc_tb)
        
        # 外側コンテナ終了
        self.outer_container.__exit__(exc_type, exc_val, exc_tb)
    
    def _create_header(self):
        """ヘッダー作成（NiceGUI公式コンポーネント活用）"""
        with ui.element('div').style(
            f'background: {self.gradient}; '
            f'color: white; padding: 12px 16px; height: 48px; '
            f'display: flex; align-items: center; justify-content: space-between; '
            f'box-sizing: border-box; flex-shrink: 0;'
        ):
            # タイトル
            ui.label(self.title).style('font-weight: bold; font-size: 14px;')
            
            # ボタングループ
            if self.buttons:
                with ui.element('div').style('display: flex; gap: 4px;'):
                    for button_icon, button_action in self.buttons:
                        ui.button(
                            button_icon, 
                            color='white',
                            on_click=button_action
                        ).style('padding: 2px 6px; font-size: 10px; min-width: 20px;')
    
    def _create_footer(self):
        """フッター作成（NiceGUI公式コンポーネント活用）"""
        with ui.element('div').style(
            'height: 24px; background: #f8f9fa; '
            'border-top: 1px solid #e5e7eb; '
            'display: flex; align-items: center; '
            'justify-content: space-between; '
            'padding: 0 12px; font-size: 11px; '
            'color: #6b7280; flex-shrink: 0;'
        ):
            ui.label(self.footer_content)


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
                    
                    // デバッグ情報出力
                    allSplitters.forEach((splitter, index) => {
                        console.log(`Splitter ${index}:`, {
                            id: splitter.id,
                            cursor: splitter.style.cursor,
                            parent: splitter.parentElement?.tagName,
                            siblings: splitter.parentElement?.children.length
                        });
                    });
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
                
                // マウス移動処理（実際のリサイズ）
                document.addEventListener('mousemove', (e) => {
                    if (!this.isDragging || !this.currentSplitter) return;
                    
                    const splitter = this.currentSplitter;
                    const isVertical = splitter.style.cursor === 'col-resize';
                    
                    // スプリッターの親要素を取得
                    const container = splitter.parentElement;
                    if (!container) {
                        console.log('Container not found for splitter:', splitter.id);
                        return;
                    }
                    
                    console.log('Splitter drag:', {
                        splitterId: splitter.id,
                        isVertical: isVertical,
                        containerChildren: container.children.length,
                        containerTagName: container.tagName
                    });
                    
                    // 縦スプリッター（左右分割）
                    if (isVertical) {
                        const rect = container.getBoundingClientRect();
                        const x = e.clientX - rect.left;
                        const percentage = Math.max(20, Math.min(80, (x / rect.width) * 100));
                        
                        // 左右のパネルを取得
                        const children = Array.from(container.children);
                        const leftPanel = children[0];
                        const rightPanel = children[2]; // スプリッターが1番目なので2番目
                        
                        if (leftPanel && rightPanel) {
                            leftPanel.style.width = percentage + '%';
                            rightPanel.style.width = (100 - percentage) + '%';
                        }
                    } 
                    // 横スプリッター（上下分割）
                    else {
                        const rect = container.getBoundingClientRect();
                        const y = e.clientY - rect.top;
                        const percentage = Math.max(20, Math.min(80, (y / rect.height) * 100));
                        
                        // 上下のパネルを取得
                        const children = Array.from(container.children);
                        const topPanel = children[0];
                        const bottomPanel = children[2]; // スプリッターが1番目なので2番目
                        
                        if (topPanel && bottomPanel) {
                            topPanel.style.height = percentage + '%';
                            bottomPanel.style.height = (100 - percentage) + '%';
                        }
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


class CommonTable:
    """
    共通テーブルコンポーネント（NiceGUI公式準拠）
    
    機能:
    - ヘッダー固定・スクロール対応
    - ページネーション内蔵
    - 行ホバー効果
    - カスタマイズ可能なカラム設定
    
    Usage:
        table = CommonTable(
            columns=[
                {'key': 'id', 'label': 'ID', 'width': '60px', 'align': 'center'},
                {'key': 'name', 'label': '名前', 'width': '1fr'}
            ],
            data=users_data,
            rows_per_page=15
        )
        table.render()
    """
    
    def __init__(
        self,
        columns: List[Dict[str, str]],
        data: List[Dict[str, Any]],
        rows_per_page: int = 15,
        header_color: str = "#3b82f6",
        row_hover_color: str = "#f8f9fa"
    ):
        self.columns = columns
        self.data = data
        self.rows_per_page = rows_per_page
        self.header_color = header_color
        self.row_hover_color = row_hover_color
        self.current_page = 1
        self.total_pages = (len(data) - 1) // rows_per_page + 1 if data else 1
        self.table_id = f"common-table-{id(self)}"
    
    def render(self):
        """テーブル描画"""
        with ui.element('div').style(
            'height: 100%; display: flex; flex-direction: column; overflow: hidden;'
        ):
            # テーブル本体
            with ui.element('div').style('flex: 1; overflow: auto;'):
                self._create_table()
            
            # ページネーション
            self._create_pagination()
            
            # JavaScript追加
            self._add_table_js()
    
    def _create_table(self):
        """テーブル本体作成"""
        # グリッドカラム設定
        grid_columns = ' '.join([col.get('width', '1fr') for col in self.columns])
        
        # ヘッダー固定コンテナ
        with ui.element('div').style(
            'width: 100%; height: 100%; '
            'display: flex; flex-direction: column; '
            'overflow: hidden;'
        ).props(f'id="{self.table_id}-container"'):
            
            # ヘッダー（固定・スクロールバー幅考慮）
            with ui.element('div').style(
                f'flex-shrink: 0; background: {self.header_color}; '
                f'color: white; font-weight: bold; '
                f'font-size: 11px; border-bottom: 1px solid #e5e7eb; '
                f'padding-right: 17px; box-sizing: border-box;'
            ):
                with ui.element('div').style(
                    f'display: grid; '
                    f'grid-template-columns: {grid_columns}; '
                    f'gap: 0; padding: 0;'
                ):
                    for col in self.columns:
                        align_style = 'text-align: center;' if col.get('align') == 'center' else ''
                        with ui.element('div').style(
                            f'padding: 6px 8px; '
                            f'border-right: 1px solid rgba(255,255,255,0.2); '
                            f'{align_style} '
                            f'background: {self.header_color};'
                        ):
                            ui.label(col['label'])
            
            # テーブル本体（スクロール可能）
            with ui.element('div').style(
                'flex: 1; overflow-y: auto; overflow-x: auto; '
                'border: 1px solid #e5e7eb;'
            ).props(f'id="{self.table_id}-body"'):
                self._create_table_rows()
    
    def _create_table_rows(self):
        """テーブル行作成"""
        start_idx = (self.current_page - 1) * self.rows_per_page
        end_idx = min(start_idx + self.rows_per_page, len(self.data))
        current_page_data = self.data[start_idx:end_idx]
        
        grid_columns = ' '.join([col.get('width', '1fr') for col in self.columns])
        
        for row in current_page_data:
            with ui.element('div').style(
                f'display: grid; '
                f'grid-template-columns: {grid_columns}; '
                f'gap: 0; padding: 0; '
                f'border-bottom: 1px solid #f3f4f6; '
                f'transition: background 0.2s; '
                f'min-height: 28px;'
            ).props(f'onmouseover="this.style.background=\'{self.row_hover_color}\'" onmouseout="this.style.background=\'white\'"'):
                
                for col in self.columns:
                    align_style = 'text-align: center;' if col.get('align') == 'center' else ''
                    justify_style = 'justify-content: center;' if col.get('align') == 'center' else ''
                    
                    with ui.element('div').style(
                        f'padding: 4px 8px; border-right: 1px solid #f3f4f6; '
                        f'font-size: 11px; display: flex; align-items: center; '
                        f'{align_style} {justify_style}'
                    ):
                        # セル内容
                        cell_value = row.get(col['key'], '')
                        
                        # 特殊レンダリング（役割・ステータス等）
                        if col.get('render_type') == 'badge':
                            self._render_badge_cell(cell_value, col.get('badge_colors', {}))
                        else:
                            ui.label(str(cell_value))
    
    def _render_badge_cell(self, value: str, colors: Dict[str, str]):
        """バッジ形式セル描画"""
        color = colors.get(value, '#6b7280')
        with ui.element('span').style(
            f'background: {color}; color: white; '
            f'padding: 1px 6px; border-radius: 3px; '
            f'font-size: 9px;'
        ):
            ui.label(value)
    
    def _create_pagination(self):
        """ページネーション作成"""
        with ui.element('div').style(
            'height: 36px; background: #f8f9fa; '
            'border-top: 1px solid #e5e7eb; '
            'display: flex; align-items: center; '
            'justify-content: space-between; '
            'padding: 0 12px; font-size: 12px; '
            'color: #374151; flex-shrink: 0;'
        ).props(f'id="{self.table_id}-pagination"'):
            # 情報表示
            with ui.element('div').props(f'id="{self.table_id}-info"'):
                start_idx = (self.current_page - 1) * self.rows_per_page + 1
                end_idx = min(self.current_page * self.rows_per_page, len(self.data))
                ui.label(f'{start_idx}-{end_idx} of {len(self.data)} items')
            
            # ページ操作
            with ui.element('div').style('display: flex; gap: 4px; align-items: center;'):
                # 前ページボタン
                ui.button('◀', color='grey').style(
                    'padding: 2px 8px; font-size: 10px; min-width: 20px;'
                ).props(f'id="{self.table_id}-prev" onclick="changeTablePage(\'{self.table_id}\', -1)"')
                
                # ページ入力
                with ui.element('div').style('display: flex; align-items: center; gap: 4px;'):
                    ui.input(value=str(self.current_page)).style(
                        'width: 40px; height: 24px; font-size: 11px; '
                        'text-align: center; border: 1px solid #d1d5db; '
                        'border-radius: 3px; padding: 2px;'
                    ).props(f'id="{self.table_id}-input" onchange="goToTablePageFromInput(\'{self.table_id}\')" onkeypress="handleTablePageInputEnter(event, \'{self.table_id}\')"')
                    
                    ui.label('/').style('font-size: 11px; color: #6b7280;')
                    
                    ui.label(str(self.total_pages)).style(
                        'font-size: 11px; color: #374151; font-weight: bold;'
                    ).props(f'id="{self.table_id}-max"')
                
                # 次ページボタン
                ui.button('▶', color='grey').style(
                    'padding: 2px 8px; font-size: 10px; min-width: 20px;'
                ).props(f'id="{self.table_id}-next" onclick="changeTablePage(\'{self.table_id}\', 1)"')
    
    def _add_table_js(self):
        """テーブル用JavaScript"""
        data_js = str(self.data).replace("'", '"').replace('True', 'true').replace('False', 'false')
        
        ui.add_head_html(f'''
        <script>
        // テーブルデータ管理
        const tableData_{self.table_id.replace('-', '_')} = {data_js};
        const tableConfig_{self.table_id.replace('-', '_')} = {{
            currentPage: {self.current_page},
            rowsPerPage: {self.rows_per_page},
            totalPages: {self.total_pages},
            columns: {str(self.columns).replace("'", '"')},
            headerColor: "{self.header_color}",
            hoverColor: "{self.row_hover_color}"
        }};
        
        // グローバル関数（テーブル操作）
        function changeTablePage(tableId, direction) {{
            const config = window['tableConfig_' + tableId.replace('-', '_')];
            const data = window['tableData_' + tableId.replace('-', '_')];
            
            const newPage = config.currentPage + direction;
            if (newPage >= 1 && newPage <= config.totalPages) {{
                config.currentPage = newPage;
                updateTableContent(tableId, data, config);
                updateTablePagination(tableId, config);
            }}
        }}
        
        function goToTablePageFromInput(tableId) {{
            const input = document.getElementById(tableId + '-input');
            const config = window['tableConfig_' + tableId.replace('-', '_')];
            const data = window['tableData_' + tableId.replace('-', '_')];
            
            if (input) {{
                const inputPage = parseInt(input.value);
                if (!isNaN(inputPage) && inputPage >= 1 && inputPage <= config.totalPages) {{
                    config.currentPage = inputPage;
                    updateTableContent(tableId, data, config);
                    updateTablePagination(tableId, config);
                }} else {{
                    input.value = config.currentPage;
                }}
            }}
        }}
        
        function handleTablePageInputEnter(event, tableId) {{
            if (event.key === 'Enter') {{
                goToTablePageFromInput(tableId);
            }}
        }}
        
        function updateTableContent(tableId, data, config) {{
            const tableBody = document.getElementById(tableId + '-body');
            if (!tableBody) return;
            
            // 現在ページのデータ
            const startIdx = (config.currentPage - 1) * config.rowsPerPage;
            const endIdx = Math.min(startIdx + config.rowsPerPage, data.length);
            const pageData = data.slice(startIdx, endIdx);
            
            // テーブル本体をクリア
            tableBody.innerHTML = '';
            
            // グリッドカラム設定
            const gridColumns = config.columns.map(col => col.width || '1fr').join(' ');
            
            pageData.forEach(row => {{
                const rowElement = document.createElement('div');
                rowElement.style.cssText = `display: grid; grid-template-columns: ${{gridColumns}}; gap: 0; padding: 0; border-bottom: 1px solid #f3f4f6; transition: background 0.2s; min-height: 28px;`;
                rowElement.onmouseover = () => rowElement.style.background = config.hoverColor;
                rowElement.onmouseout = () => rowElement.style.background = 'white';
                
                config.columns.forEach(col => {{
                    const cellDiv = document.createElement('div');
                    const alignStyle = col.align === 'center' ? 'text-align: center; justify-content: center;' : '';
                    cellDiv.style.cssText = `padding: 4px 8px; border-right: 1px solid #f3f4f6; font-size: 11px; display: flex; align-items: center; ${{alignStyle}}`;
                    
                    const cellValue = row[col.key] || '';
                    
                    if (col.render_type === 'badge' && col.badge_colors) {{
                        const span = document.createElement('span');
                        const color = col.badge_colors[cellValue] || '#6b7280';
                        span.style.cssText = `background: ${{color}}; color: white; padding: 1px 6px; border-radius: 3px; font-size: 9px;`;
                        span.textContent = cellValue;
                        cellDiv.appendChild(span);
                    }} else {{
                        cellDiv.textContent = cellValue;
                    }}
                    
                    rowElement.appendChild(cellDiv);
                }});
                
                tableBody.appendChild(rowElement);
            }});
        }}
        
        function updateTablePagination(tableId, config) {{
            // 情報更新
            const startIdx = (config.currentPage - 1) * config.rowsPerPage + 1;
            const endIdx = Math.min(config.currentPage * config.rowsPerPage, tableData_{self.table_id.replace('-', '_')}.length);
            const infoElement = document.querySelector(`#${{tableId}}-info label`);
            if (infoElement) {{
                infoElement.textContent = `${{startIdx}}-${{endIdx}} of ${{tableData_{self.table_id.replace('-', '_')}.length}} items`;
            }}
            
            // ページ入力更新
            const pageInput = document.getElementById(tableId + '-input');
            if (pageInput) {{
                pageInput.value = config.currentPage;
            }}
            
            // ボタン状態更新
            const prevBtn = document.getElementById(tableId + '-prev');
            const nextBtn = document.getElementById(tableId + '-next');
            
            if (prevBtn) {{
                prevBtn.style.opacity = config.currentPage === 1 ? '0.5' : '1';
            }}
            
            if (nextBtn) {{
                nextBtn.style.opacity = config.currentPage === config.totalPages ? '0.5' : '1';
            }}
        }}
        </script>
        ''')


class CommonFormElements:
    """
    共通フォーム要素コンポーネント（NiceGUI公式準拠）
    
    機能:
    - ボタン・チェックボックス・ラジオボタン・ドロップダウン
    - 統一されたスタイル・色・サイズ
    - バリデーション・状態管理対応
    - アクセシビリティ配慮
    
    Usage:
        CommonFormElements.create_button("保存", color="primary", size="medium")
        CommonFormElements.create_checkbox("同意する", on_change=callback)
        CommonFormElements.create_radio_group("選択肢", ["A", "B", "C"])
        CommonFormElements.create_dropdown("選択", ["オプション1", "オプション2"])
    """
    
    # カラーパレット
    COLORS = {
        'primary': '#3b82f6',
        'secondary': '#6b7280', 
        'success': '#10b981',
        'warning': '#f59e0b',
        'danger': '#ef4444',
        'info': '#06b6d4',
        'light': '#f8f9fa',
        'dark': '#374151'
    }
    
    # サイズ設定
    SIZES = {
        'small': {'padding': '4px 8px', 'font_size': '11px', 'height': '24px'},
        'medium': {'padding': '8px 16px', 'font_size': '14px', 'height': '32px'},
        'large': {'padding': '12px 24px', 'font_size': '16px', 'height': '40px'}
    }
    
    @staticmethod
    def create_button(
        text: str,
        color: str = "primary",
        size: str = "medium",
        variant: str = "solid",  # solid, outline, ghost
        icon: Optional[str] = None,
        disabled: bool = False,
        on_click: Optional[Callable] = None
    ):
        """統一ボタン作成"""
        base_color = CommonFormElements.COLORS.get(color, CommonFormElements.COLORS['primary'])
        size_config = CommonFormElements.SIZES.get(size, CommonFormElements.SIZES['medium'])
        
        # バリアント別スタイル
        if variant == "solid":
            button_style = (
                f'background: {base_color}; color: white; '
                f'border: 1px solid {base_color};'
            )
            hover_style = f'background: {base_color}dd; border-color: {base_color}dd;'
        elif variant == "outline":
            button_style = (
                f'background: transparent; color: {base_color}; '
                f'border: 1px solid {base_color};'
            )
            hover_style = f'background: {base_color}11; color: {base_color};'
        else:  # ghost
            button_style = (
                f'background: transparent; color: {base_color}; '
                f'border: 1px solid transparent;'
            )
            hover_style = f'background: {base_color}11;'
        
        # 無効化スタイル
        disabled_style = 'opacity: 0.5; cursor: not-allowed;' if disabled else ''
        
        # ボタンテキスト
        button_text = f'{icon} {text}' if icon else text
        
        return ui.button(
            button_text,
            on_click=on_click if not disabled else None
        ).style(
            f'{button_style} '
            f'padding: {size_config["padding"]}; '
            f'font-size: {size_config["font_size"]}; '
            f'height: {size_config["height"]}; '
            f'border-radius: 6px; '
            f'font-weight: 500; '
            f'cursor: {"pointer" if not disabled else "not-allowed"}; '
            f'transition: all 0.2s ease; '
            f'display: inline-flex; align-items: center; '
            f'justify-content: center; gap: 4px; '
            f'{disabled_style}'
        ).props(f'onmouseover="this.style.cssText+=\'{hover_style}\'" onmouseout="this.style.cssText=this.style.cssText.replace(\'{hover_style}\',\'\')"' if not disabled else '')
    
    @staticmethod
    def create_checkbox(
        label: str,
        value: bool = False,
        disabled: bool = False,
        on_change: Optional[Callable] = None,
        size: str = "medium"
    ):
        """統一チェックボックス作成"""
        size_config = CommonFormElements.SIZES.get(size, CommonFormElements.SIZES['medium'])
        
        with ui.element('div').style(
            'display: flex; align-items: center; gap: 8px; '
            f'font-size: {size_config["font_size"]}; '
            f'opacity: {"0.5" if disabled else "1"};'
        ):
            checkbox = ui.checkbox(value=value, on_change=on_change).style(
                'margin: 0; accent-color: #3b82f6;'
            )
            
            if disabled:
                checkbox.props('disabled')
            
            ui.label(label).style(
                f'margin: 0; cursor: {"pointer" if not disabled else "not-allowed"}; '
                f'user-select: none;'
            ).props(f'onclick="document.querySelector(\'#{checkbox.id}\').click()"' if not disabled else '')
            
            return checkbox
    
    @staticmethod
    def create_radio_group(
        label: str,
        options: List[str],
        value: Optional[str] = None,
        disabled: bool = False,
        on_change: Optional[Callable] = None,
        layout: str = "horizontal"  # horizontal, vertical
    ):
        """統一ラジオボタングループ作成"""
        with ui.element('div').style('margin-bottom: 8px;'):
            ui.label(label).style(
                'font-weight: 500; margin-bottom: 4px; '
                'display: block; font-size: 14px;'
            )
            
            layout_style = (
                'display: flex; gap: 16px; flex-wrap: wrap;' 
                if layout == "horizontal" 
                else 'display: flex; flex-direction: column; gap: 8px;'
            )
            
            with ui.element('div').style(layout_style):
                radio_group = ui.radio(
                    options=options,
                    value=value,
                    on_change=on_change
                ).style(
                    'margin: 0; accent-color: #3b82f6;'
                )
                
                if disabled:
                    radio_group.props('disabled')
                    radio_group.style('opacity: 0.5;')
                
                return radio_group
    
    @staticmethod
    def create_dropdown(
        label: str,
        options: List[str],
        value: Optional[str] = None,
        placeholder: str = "選択してください",
        disabled: bool = False,
        on_change: Optional[Callable] = None,
        width: str = "200px"
    ):
        """統一ドロップダウン作成"""
        with ui.element('div').style('margin-bottom: 8px;'):
            ui.label(label).style(
                'font-weight: 500; margin-bottom: 4px; '
                'display: block; font-size: 14px;'
            )
            
            dropdown = ui.select(
                options=options,
                value=value,
                on_change=on_change
            ).style(
                f'width: {width}; '
                f'border: 1px solid #d1d5db; '
                f'border-radius: 6px; '
                f'padding: 8px 12px; '
                f'font-size: 14px; '
                f'background: white; '
                f'transition: border-color 0.2s ease; '
                f'opacity: {"0.5" if disabled else "1"};'
            ).props(f'placeholder="{placeholder}"')
            
            if disabled:
                dropdown.props('disabled')
            
            # フォーカススタイル
            dropdown.props(
                'onfocus="this.style.borderColor=\'#3b82f6\'; this.style.boxShadow=\'0 0 0 3px rgba(59, 130, 246, 0.1)\'" '
                'onblur="this.style.borderColor=\'#d1d5db\'; this.style.boxShadow=\'none\'"'
            )
            
            return dropdown
    
    @staticmethod
    def create_input(
        label: str,
        value: str = "",
        placeholder: str = "",
        input_type: str = "text",  # text, email, password, number
        disabled: bool = False,
        required: bool = False,
        on_change: Optional[Callable] = None,
        width: str = "200px",
        validation_pattern: Optional[str] = None
    ):
        """統一入力フィールド作成"""
        with ui.element('div').style('margin-bottom: 8px;'):
            label_text = f'{label}{"*" if required else ""}'
            ui.label(label_text).style(
                'font-weight: 500; margin-bottom: 4px; '
                'display: block; font-size: 14px; '
                f'color: {"#ef4444" if required else "#374151"};'
            )
            
            input_field = ui.input(
                value=value,
                placeholder=placeholder,
                on_change=on_change
            ).style(
                f'width: {width}; '
                f'border: 1px solid #d1d5db; '
                f'border-radius: 6px; '
                f'padding: 8px 12px; '
                f'font-size: 14px; '
                f'background: white; '
                f'transition: border-color 0.2s ease; '
                f'opacity: {"0.5" if disabled else "1"};'
            )
            
            # 入力タイプ設定
            if input_type != "text":
                input_field.props(f'type="{input_type}"')
            
            if disabled:
                input_field.props('disabled')
            
            if required:
                input_field.props('required')
            
            if validation_pattern:
                input_field.props(f'pattern="{validation_pattern}"')
            
            # フォーカススタイル
            input_field.props(
                'onfocus="this.style.borderColor=\'#3b82f6\'; this.style.boxShadow=\'0 0 0 3px rgba(59, 130, 246, 0.1)\'" '
                'onblur="this.style.borderColor=\'#d1d5db\'; this.style.boxShadow=\'none\'"'
            )
            
            return input_field
    
    @staticmethod
    def create_form_row(*elements, gap: str = "16px"):
        """フォーム要素の横並び配置"""
        with ui.element('div').style(
            f'display: flex; gap: {gap}; align-items: end; '
            f'flex-wrap: wrap; margin-bottom: 16px;'
        ):
            for element in elements:
                element