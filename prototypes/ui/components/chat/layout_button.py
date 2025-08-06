"""
チャットレイアウト切り替えボタン
FloatingActionButtonを継承した実装
"""
from typing import Optional, Callable, Dict
from ..base.button import FloatingActionButton


class ChatLayoutButton(FloatingActionButton):
    """
    チャットレイアウト切り替えボタン（継承ベース実装）
    
    FloatingActionButtonを継承し、レイアウト切り替え固有の機能を追加
    """
    
    # レイアウトボタン固有のスタイル
    LAYOUT_BUTTON_STYLES = {
        'min-width': '40px',
        'text-align': 'center',
        'font-weight': 'bold'
    }
    
    @classmethod
    def create(
        cls,
        text: str = ">>",
        on_click: Optional[Callable] = None,
        title: str = "レイアウト切り替え",
        position: Optional[Dict[str, str]] = None,
        **kwargs
    ):
        """レイアウト切り替えボタン作成"""
        # デフォルト位置（右上）
        if position is None:
            position = {'top': '4px', 'right': '4px'}
            
        # レイアウトボタンスタイルを追加
        additional_styles = cls.LAYOUT_BUTTON_STYLES.copy()
        if 'additional_styles' in kwargs:
            additional_styles.update(kwargs.pop('additional_styles'))
            
        return super().create(
            text=text,
            position=position,
            on_click=on_click,
            title=title,
            additional_styles=additional_styles,
            **kwargs
        )