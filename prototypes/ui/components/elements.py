"""
個別UI要素の共通コンポーネント
ボタン、パネル、テーブル等の再利用可能な基本要素
"""
from nicegui import ui
from typing import List, Dict, Any, Optional, Callable

class StyledButton:
    """スタイル統一されたボタン"""
    
    STYLES = {
        'primary': 'background:#3b82f6;color:white;border:none;padding:8px 16px;border-radius:6px;font-size:14px;cursor:pointer;font-weight:500;',
        'secondary': 'background:#6b7280;color:white;border:none;padding:8px 16px;border-radius:6px;font-size:14px;cursor:pointer;font-weight:500;',
        'danger': 'background:#ef4444;color:white;border:none;padding:8px 16px;border-radius:6px;font-size:14px;cursor:pointer;font-weight:500;',
        'success': 'background:#10b981;color:white;border:none;padding:8px 16px;border-radius:6px;font-size:14px;cursor:pointer;font-weight:500;',
        'outline': 'background:transparent;color:#3b82f6;border:1px solid #3b82f6;padding:8px 16px;border-radius:6px;font-size:14px;cursor:pointer;font-weight:500;'
    }
    
    def __init__(self, text: str, style: str = 'primary', on_click: Optional[Callable] = None, **kwargs):
        self.text = text
        self.style = style
        self.on_click = on_click
        self.kwargs = kwargs
        self.render()
    
    def render(self):
        """ボタン描画"""
        button_style = self.STYLES.get(self.style, self.STYLES['primary'])
        button = ui.button(self.text, on_click=self.on_click, **self.kwargs)
        button.style(button_style)
        return button

class InfoCard:
    """情報表示カード"""
    
    def __init__(self, title: str, content: str, icon: Optional[str] = None, 
                 color: str = "#3b82f6", size: str = "medium"):
        self.title = title
        self.content = content
        self.icon = icon
        self.color = color
        self.size = size
        self.render()
    
    def render(self):
        """カード描画"""
        sizes = {
            'small': {'padding': '12px', 'title_size': '14px', 'content_size': '12px'},
            'medium': {'padding': '16px', 'title_size': '16px', 'content_size': '14px'},
            'large': {'padding': '20px', 'title_size': '18px', 'content_size': '16px'}
        }
        
        size_config = sizes.get(self.size, sizes['medium'])
        
        with ui.element('div').style(f'background:white;border:1px solid #e5e7eb;border-radius:8px;padding:{size_config["padding"]};box-shadow:0 1px 3px rgba(0,0,0,0.1);'):
            if self.icon:
                with ui.element('div').style('display:flex;align-items:center;margin-bottom:8px;'):
                    ui.label(self.icon).style(f'font-size:{size_config["title_size"]};margin-right:8px;')
                    ui.label(self.title).style(f'font-size:{size_config["title_size"]};font-weight:bold;color:{self.color};margin:0;')
            else:
                ui.label(self.title).style(f'font-size:{size_config["title_size"]};font-weight:bold;color:{self.color};margin:0 0 8px 0;')
            
            ui.label(self.content).style(f'font-size:{size_config["content_size"]};color:#6b7280;margin:0;line-height:1.5;')

class DataTable:
    """データテーブル（ページネーション付き）"""
    
    def __init__(self, headers: List[str], rows: List[List[str]], 
                 striped: bool = True, bordered: bool = True, 
                 page_size: int = 5, show_pagination: bool = True):
        self.headers = headers
        self.rows = rows
        self.striped = striped
        self.bordered = bordered
        self.page_size = page_size
        self.show_pagination = show_pagination
        self.current_page = 1
        self.total_pages = max(1, (len(rows) + page_size - 1) // page_size) if rows else 1
        self.pagination_container = None
        self.table_container = None
        self.render()
    
    def render(self):
        """テーブル描画"""
        border_style = 'border:1px solid #e5e7eb;' if self.bordered else ''
        
        with ui.element('div').style(f'{border_style}border-radius:8px;overflow:hidden;') as main_container:
            # テーブル本体（角丸考慮）
            with ui.element('div').style('overflow:hidden;border-radius:8px 8px 0 0;') as table_container:
                self.table_container = table_container
                self._render_table()
            
            # ページネーション
            if self.show_pagination and self.total_pages > 1:
                with ui.element('div').style('background:#f8f9fa;border-top:1px solid #e5e7eb;padding:8px 12px;display:flex;justify-content:space-between;align-items:center;border-radius:0 0 8px 8px;') as pagination:
                    self.pagination_container = pagination
                    self._render_pagination()
    
    def _render_table(self):
        """テーブル本体描画"""
        start_idx = (self.current_page - 1) * self.page_size
        end_idx = start_idx + self.page_size
        current_rows = self.rows[start_idx:end_idx] if self.rows else []
        
        with ui.element('table').style('width:100%;border-collapse:collapse;'):
            # ヘッダー
            with ui.element('thead').style('background:#f9fafb;'):
                with ui.element('tr'):
                    for header in self.headers:
                        ui.element('th').style('padding:10px 12px;text-align:left;font-weight:600;color:#374151;border-bottom:1px solid #e5e7eb;font-size:13px;').text = header
            
            # データ行
            with ui.element('tbody'):
                for i, row in enumerate(current_rows):
                    bg_color = '#f9fafb' if self.striped and i % 2 == 1 else 'white'
                    with ui.element('tr').style(f'background:{bg_color};'):
                        for j, cell in enumerate(row):
                            # 最後の行かつページネーションありの場合、下border調整
                            bottom_border = 'none' if (i == len(current_rows) - 1 and self.show_pagination and self.total_pages > 1) else '1px solid #e5e7eb'
                            ui.element('td').style(f'padding:8px 12px;border-bottom:{bottom_border};color:#6b7280;font-size:12px;').text = str(cell)
    
    def _render_pagination(self):
        """ページネーション描画"""
        # 左側：件数表示
        start_num = (self.current_page - 1) * self.page_size + 1
        end_num = min(self.current_page * self.page_size, len(self.rows))
        ui.label(f'{start_num}-{end_num} / {len(self.rows)}件').style('font-size:11px;color:#6b7280;')
        
        # 右側：ページボタン
        with ui.row().classes('gap-1'):
            # 前へボタン
            prev_btn = ui.button('◀', on_click=self._prev_page)
            prev_btn.props('size=sm color=grey')
            prev_btn.style('font-size:10px;padding:2px 6px;height:24px;')
            if self.current_page <= 1:
                prev_btn.props('disable')
            
            # ページ番号
            ui.label(f'{self.current_page} / {self.total_pages}').style('font-size:11px;color:#374151;margin:0 4px;line-height:24px;')
            
            # 次へボタン
            next_btn = ui.button('▶', on_click=self._next_page)
            next_btn.props('size=sm color=grey')
            next_btn.style('font-size:10px;padding:2px 6px;height:24px;')
            if self.current_page >= self.total_pages:
                next_btn.props('disable')
    
    def _prev_page(self):
        """前のページ"""
        if self.current_page > 1:
            self.current_page -= 1
            self._refresh_table()
    
    def _next_page(self):
        """次のページ"""
        if self.current_page < self.total_pages:
            self.current_page += 1
            self._refresh_table()
    
    def _refresh_table(self):
        """テーブル再描画"""
        if self.table_container:
            self.table_container.clear()
            with self.table_container:
                self._render_table()
        
        if self.pagination_container:
            self.pagination_container.clear()
            with self.pagination_container:
                self._render_pagination()

class StatusBadge:
    """ステータスバッジ"""
    
    STATUSES = {
        'active': {'bg': '#dcfce7', 'text': '#166534', 'label': 'アクティブ'},
        'inactive': {'bg': '#fee2e2', 'text': '#dc2626', 'label': '非アクティブ'},
        'pending': {'bg': '#fef3c7', 'text': '#d97706', 'label': '保留中'},
        'completed': {'bg': '#dbeafe', 'text': '#1d4ed8', 'label': '完了'},
        'error': {'bg': '#fee2e2', 'text': '#dc2626', 'label': 'エラー'}
    }
    
    def __init__(self, status: str, custom_label: Optional[str] = None):
        self.status = status
        self.custom_label = custom_label
        self.render()
    
    def render(self):
        """バッジ描画"""
        config = self.STATUSES.get(self.status, self.STATUSES['pending'])
        label = self.custom_label or config['label']
        
        ui.label(label).style(f'background:{config["bg"]};color:{config["text"]};padding:4px 8px;border-radius:4px;font-size:12px;font-weight:500;display:inline-block;')

class FormGroup:
    """フォームグループ（ラベル + 入力要素）"""
    
    def __init__(self, label: str, required: bool = False, help_text: Optional[str] = None):
        self.label = label
        self.required = required
        self.help_text = help_text
        self.container = None
        self.render()
    
    def render(self):
        """フォームグループ描画"""
        with ui.element('div').style('margin-bottom:16px;') as container:
            self.container = container
            
            # ラベル
            label_text = f"{self.label} {'*' if self.required else ''}"
            ui.label(label_text).style('display:block;font-size:14px;font-weight:500;color:#374151;margin-bottom:4px;')
            
            # 入力要素エリア（子要素で追加）
            self.input_container = ui.element('div').style('margin-bottom:4px;')
            
            # ヘルプテキスト
            if self.help_text:
                ui.label(self.help_text).style('font-size:12px;color:#6b7280;margin:0;')
    
    def __enter__(self):
        """コンテキストマネージャー - 入力要素追加用"""
        return self.input_container.__enter__()
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """コンテキストマネージャー終了"""
        return self.input_container.__exit__(exc_type, exc_val, exc_tb)

class ProgressBar:
    """プログレスバー"""
    
    def __init__(self, value: float, max_value: float = 100.0, 
                 color: str = "#3b82f6", height: str = "8px", show_text: bool = True):
        self.value = value
        self.max_value = max_value
        self.color = color
        self.height = height
        self.show_text = show_text
        self.render()
    
    def render(self):
        """プログレスバー描画"""
        percentage = (self.value / self.max_value) * 100
        
        with ui.element('div').style('width:100%;'):
            if self.show_text:
                ui.label(f'{percentage:.1f}%').style('font-size:12px;color:#6b7280;margin-bottom:4px;')
            
            with ui.element('div').style(f'background:#e5e7eb;border-radius:4px;height:{self.height};overflow:hidden;'):
                ui.element('div').style(f'background:{self.color};height:100%;width:{percentage}%;transition:width 0.3s ease;')

class PanelButton:
    """パネル用ボタン（2種類）"""
    
    @staticmethod
    def header_button(text: str, on_click=None, color: str = "primary", icon: str = ""):
        """ヘッダー用コンパクトボタン"""
        btn_text = f"{icon} {text}" if icon else text
        btn = ui.button(btn_text, on_click=on_click)
        btn.props(f'size=sm color={color}')
        btn.style('font-size:10px;padding:4px 8px;height:28px;line-height:1;margin:0;')
        return btn
    
    @staticmethod
    def content_button(text: str, on_click=None, color: str = "primary", icon: str = "", size: str = "md"):
        """コンテンツ用標準ボタン"""
        btn_text = f"{icon} {text}" if icon else text
        btn = ui.button(btn_text, on_click=on_click)
        btn.props(f'size={size} color={color}')
        if size == "sm":
            btn.style('font-size:12px;padding:6px 12px;height:32px;')
        elif size == "lg":
            btn.style('font-size:16px;padding:12px 24px;height:44px;')
        else:  # md
            btn.style('font-size:14px;padding:8px 16px;height:36px;')
        return btn

class CommonPanel:
    """共通パネル - data-registration処理設定 + ocr-adjustment影付きベース"""
    
    def __init__(self, title: str, icon: Optional[str] = None, 
                 actions: Optional[List[Dict[str, Any]]] = None,
                 style: str = "default", height: Optional[str] = None):
        """
        共通パネル初期化
        
        Args:
            title: パネルタイトル
            icon: タイトル用アイコン
            actions: ヘッダーボタン配列 [{'text': 'ボタン名', 'on_click': func, 'props': 'color=primary', 'style': 'css'}]
            style: パネルスタイル ('default', 'compact', 'full')
            height: 高さ指定 ('100%', '400px', None=auto)
        """
        self.title = title
        self.icon = icon
        self.actions = actions or []
        self.style_type = style
        self.height = height
        self.content_container = None
        self.render()
    
    def render(self):
        """パネル描画"""
        # スタイル設定
        base_styles = {
            'default': {
                'margin': '8px',          # 外側余白（並べたときの間隔）
                'padding': '0',           # パネル自体のpadding
                'shadow': '0 2px 8px rgba(0,0,0,0.1)',  # ocr-adjustment風影
                'border_radius': '8px'    # data-registration風角丸
            },
            'compact': {
                'margin': '6px',
                'padding': '0',
                'shadow': '0 1px 4px rgba(0,0,0,0.08)',
                'border_radius': '6px'
            },
            'full': {
                'margin': '0',
                'padding': '0',
                'shadow': '0 4px 12px rgba(0,0,0,0.15)',
                'border_radius': '8px'
            }
        }
        
        config = base_styles.get(self.style_type, base_styles['default'])
        height_style = f'height:{self.height};' if self.height else ''
        
        # パネル外側コンテナ（margin管理）
        with ui.element('div').style(f'margin:{config["margin"]};{height_style}') as outer:
            # パネル本体（data-registration + ocr-adjustment風）
            with ui.element('div').style(f'''
                background: white;
                border: 1px solid #ddd;
                border-radius: {config["border_radius"]};
                box-shadow: {config["shadow"]};
                display: flex;
                flex-direction: column;
                overflow: hidden;
                height: 100%;
            ''') as panel:
                
                # パネルヘッダー（固定高さ48px・ツラ合わせ）
                with ui.element('div').style('background:#f8f9fa;padding:8px 12px;border-bottom:1px solid #ddd;display:flex;justify-content:space-between;align-items:center;flex-shrink:0;height:48px;box-sizing:border-box;'):
                    # タイトル部分
                    title_text = f"{self.icon} {self.title}" if self.icon else self.title
                    ui.label(title_text).style('font-size:15px;font-weight:600;margin:0;color:#1f2937;line-height:1;')
                    
                    # アクションボタン（ヘッダー用最適化）
                    if self.actions:
                        with ui.row().classes('gap-1').style('height:32px;align-items:center;'):
                            for action in self.actions:
                                btn = ui.button(
                                    action.get('text', 'ボタン'),
                                    on_click=action.get('on_click')
                                )
                                if 'props' in action:
                                    btn.props(action['props'])
                                if 'style' in action:
                                    btn.style(action['style'])
                                else:
                                    btn.style('font-size:10px;padding:4px 8px;height:28px;line-height:1;')  # ヘッダー用コンパクト
                    else:
                        # ボタンなしでも高さ確保
                        ui.element('div').style('height:32px;width:1px;')
                
                # パネルコンテンツエリア
                with ui.element('div').style('flex:1;overflow:hidden;padding:12px;') as content:
                    self.content_container = content
    
    def __enter__(self):
        """コンテキストマネージャー - コンテンツ追加用"""
        return self.content_container.__enter__()
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """コンテキストマネージャー終了"""
        return self.content_container.__exit__(exc_type, exc_val, exc_tb)