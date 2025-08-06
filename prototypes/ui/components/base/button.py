"""
継承可能な基本ボタンコンポーネント
"""
from nicegui import ui
from typing import Optional, Dict, Callable
from .styles import StyleBuilder, CommonStyles


class BaseButton:
    """
    継承可能な基本ボタンクラス
    
    Usage:
        BaseButton.create("クリック", on_click=handler)
        BaseButton.create_type_a("保存", on_click=handler)  # 塗りつぶし
        BaseButton.create_type_b("キャンセル", on_click=handler)  # 縁取り
    """
    
    # デフォルトスタイル
    BASE_STYLES = {
        'padding': '4px 12px',
        'font-size': '13px',
        'border-radius': '4px',
        'cursor': 'pointer',
        'transition': 'all 0.2s ease',
        'min-height': '28px',
        'font-weight': '500'
    }
    
    # タイプA: 塗りつぶしボタン（NiceGUI標準のブルー）
    TYPE_A_STYLES = {
        'background': '#2563eb',
        'color': 'white',
        'border': 'none'
    }
    
    # タイプB: 縁取りボタン
    TYPE_B_STYLES = {
        'background': 'transparent',
        'color': '#2563eb',
        'border': '1px solid #2563eb'
    }
    
    @classmethod
    def create(
        cls,
        text: str,
        on_click: Optional[Callable] = None,
        color: str = 'primary',
        additional_styles: Optional[Dict[str, str]] = None,
        **kwargs
    ):
        """基本ボタン作成"""
        # スタイルマージ
        styles = cls.BASE_STYLES.copy()
        if additional_styles:
            styles.update(additional_styles)
            
        # NiceGUIボタン作成
        button = ui.button(text, color=color, on_click=on_click)
        button.style(StyleBuilder.to_string(styles))
        
        # 追加props
        if kwargs.get('props'):
            button.props(kwargs['props'])
            
        return button
    
    @classmethod
    def create_type_a(
        cls,
        text: str,
        on_click: Optional[Callable] = None,
        additional_styles: Optional[Dict[str, str]] = None,
        **kwargs
    ):
        """タイプA: 塗りつぶしボタン作成"""
        merged_styles = StyleBuilder.merge_styles(cls.TYPE_A_STYLES, additional_styles)
        return cls.create(
            text=text,
            on_click=on_click,
            color='primary',
            additional_styles=merged_styles,
            **kwargs
        )
    
    @classmethod
    def create_type_b(
        cls,
        text: str,
        on_click: Optional[Callable] = None,
        additional_styles: Optional[Dict[str, str]] = None,
        **kwargs
    ):
        """タイプB: 縁取りボタン作成"""
        merged_styles = StyleBuilder.merge_styles(cls.TYPE_B_STYLES, additional_styles)
        return cls.create(
            text=text,
            on_click=on_click,
            color=None,  # 色なし
            additional_styles=merged_styles,
            **kwargs
        )


class PositionedButton(BaseButton):
    """
    位置指定可能なボタン（position使用）
    """
    
    POSITIONED_STYLES = {
        'position': 'absolute',
        'z-index': '10'
    }
    
    @classmethod
    def create(
        cls,
        text: str,
        position: Dict[str, str],  # {'top': '10px', 'right': '10px'}
        on_click: Optional[Callable] = None,
        title: str = "",
        additional_styles: Optional[Dict[str, str]] = None,
        **kwargs
    ):
        """位置指定ボタン作成"""
        # 位置スタイルをマージ
        styles = cls.POSITIONED_STYLES.copy()
        styles.update(position)
        
        if additional_styles:
            styles.update(additional_styles)
            
        # コンテナ作成
        with ui.element('div').style(StyleBuilder.to_string(styles)):
            button = super().create(
                text=text,
                on_click=on_click,
                additional_styles=additional_styles,
                **kwargs
            )
            
            if title:
                button.props(f'title="{title}"')
                
            return button


class FloatingActionButton(PositionedButton):
    """
    フローティングアクションボタン
    """
    
    FAB_STYLES = {
        'background': 'rgba(255, 255, 255, 0.9)',
        'border': '1px solid #ddd',
        'border-radius': '4px',
        'padding': '5px 10px',
        'font-size': '12px',
        'box-shadow': '0 2px 4px rgba(0,0,0,0.1)'
    }
    
    @classmethod
    def create(
        cls,
        text: str,
        position: Optional[Dict[str, str]] = None,
        on_click: Optional[Callable] = None,
        title: str = "",
        additional_styles: Optional[Dict[str, str]] = None,
        **kwargs
    ):
        """FAB作成"""
        # デフォルト位置
        if position is None:
            position = {'bottom': '20px', 'right': '20px'}
            
        # FABスタイル適用
        merged_styles = cls.FAB_STYLES.copy()
        if additional_styles:
            merged_styles.update(additional_styles)
            
        return super().create(
            text=text,
            position=position,
            on_click=on_click,
            title=title,
            additional_styles=merged_styles,
            **kwargs
        )