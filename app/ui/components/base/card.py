"""
継承可能な基本カードコンポーネント
"""
from nicegui import ui
from typing import Optional, Dict, Callable
from .styles import StyleBuilder, CommonStyles


class BaseCard:
    """
    継承可能な基本カードクラス
    
    Usage:
        with BaseCard() as card:
            ui.label("カード内容")
            
        # カスタムスタイル
        with BaseCard(
            additional_styles={'border': '2px solid #3b82f6'}
        ) as card:
            ui.label("カスタムカード")
    """
    
    # デフォルトスタイル
    BASE_STYLES = {
        'padding': '12px',
        'margin-bottom': '8px',
        'cursor': 'pointer',
        'transition': 'all 0.2s ease',
        'border': '1px solid #e5e7eb',
        'background': 'white',
        'border-radius': '8px'
    }
    
    # ホバー効果のデフォルト
    HOVER_STYLES = {
        'background': '#f8f9fa',
        'border-color': '#3b82f6'
    }
    
    def __init__(
        self,
        additional_styles: Optional[Dict[str, str]] = None,
        hover_styles: Optional[Dict[str, str]] = None,
        on_click: Optional[Callable] = None,
        **kwargs
    ):
        # スタイルマージ
        self.styles = self.BASE_STYLES.copy()
        if additional_styles:
            self.styles.update(additional_styles)
            
        # ホバースタイル
        self.hover_styles = self.HOVER_STYLES.copy()
        if hover_styles:
            self.hover_styles.update(hover_styles)
            
        self.on_click = on_click
        self.kwargs = kwargs
        self.card = None
    
    def __enter__(self):
        style_string = StyleBuilder.to_string(self.styles)
        
        # NiceGUIのカードを作成
        self.card = ui.card().style(style_string)
        
        # ホバー効果を設定
        if self.hover_styles:
            hover_props = self._create_hover_props()
            self.card.props(hover_props)
        
        # カードにon_clickを設定（スタイルに追加）
        if self.on_click:
            self.card.style('position: relative;')
            
        return self.card.__enter__()
    
    def __exit__(self, *args):
        return self.card.__exit__(*args)
    
    def _create_hover_props(self):
        """ホバー効果のprops文字列を生成"""
        # ホバー時のスタイル変更
        hover_changes = []
        original_values = []
        
        for key, value in self.hover_styles.items():
            js_key = self._css_to_js_property(key)
            hover_changes.append(f"this.style.{js_key}='{value}'")
            original_value = self.styles.get(key, '')
            original_values.append(f"this.style.{js_key}='{original_value}'")
        
        onmouseover = f'onmouseover="{"; ".join(hover_changes)};"'
        onmouseout = f'onmouseout="{"; ".join(original_values)};"'
        
        return f'{onmouseover} {onmouseout}'
    
    def _css_to_js_property(self, css_property: str) -> str:
        """CSS プロパティ名を JavaScript のキャメルケースに変換"""
        parts = css_property.split('-')
        if len(parts) == 1:
            return parts[0]
        return parts[0] + ''.join(word.capitalize() for word in parts[1:])


class InteractiveCard(BaseCard):
    """
    インタラクティブなカード（クリック可能、ホバー効果付き）
    """
    
    def __init__(
        self,
        title: str = "",
        content: str = "",
        metadata: Optional[Dict[str, str]] = None,
        on_click: Optional[Callable] = None,
        **kwargs
    ):
        super().__init__(on_click=on_click, **kwargs)
        
        self.title = title
        self.content = content
        self.metadata = metadata or {}
    
    def __enter__(self):
        # 親クラスでカード作成
        card_context = super().__enter__()
        
        # タイトル
        if self.title:
            ui.label(self.title).style(
                'font-weight: bold; color: #1f2937; '
                'margin-bottom: 4px; font-size: 13px;'
            )
        
        # コンテンツ
        if self.content:
            ui.label(self.content).style(
                'color: #4b5563; font-size: 12px; '
                'line-height: 1.4; margin-bottom: 6px;'
            )
        
        # メタデータ
        if self.metadata:
            with ui.row().style('gap: 12px; align-items: center;'):
                for key, value in self.metadata.items():
                    ui.label(f"{key}: {value}").style(
                        'background: #eff6ff; color: #2563eb; '
                        'padding: 2px 8px; border-radius: 4px; '
                        'font-size: 11px;'
                    )
        
        return card_context