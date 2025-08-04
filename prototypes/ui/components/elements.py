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
    """データテーブル"""
    
    def __init__(self, headers: List[str], rows: List[List[str]], 
                 striped: bool = True, bordered: bool = True):
        self.headers = headers
        self.rows = rows
        self.striped = striped
        self.bordered = bordered
        self.render()
    
    def render(self):
        """テーブル描画"""
        border_style = 'border:1px solid #e5e7eb;' if self.bordered else ''
        
        with ui.element('div').style(f'overflow-x:auto;{border_style}border-radius:8px;'):
            with ui.element('table').style('width:100%;border-collapse:collapse;'):
                # ヘッダー
                with ui.element('thead').style('background:#f9fafb;'):
                    with ui.element('tr'):
                        for header in self.headers:
                            ui.element('th').style('padding:12px;text-align:left;font-weight:600;color:#374151;border-bottom:1px solid #e5e7eb;').text = header
                
                # データ行
                with ui.element('tbody'):
                    for i, row in enumerate(self.rows):
                        bg_color = '#f9fafb' if self.striped and i % 2 == 1 else 'white'
                        with ui.element('tr').style(f'background:{bg_color};'):
                            for cell in row:
                                ui.element('td').style('padding:12px;color:#374151;border-bottom:1px solid #e5e7eb;').text = str(cell)

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