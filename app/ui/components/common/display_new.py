"""
表示関連の共通コンポーネント
FormElements
"""
from nicegui import ui
from typing import List, Dict, Any, Optional, Callable


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