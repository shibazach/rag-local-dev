"""
継承可能なフォーム要素コンポーネント
"""
from nicegui import ui
from typing import Optional, Dict, List, Callable, Any
from .styles import StyleBuilder, CommonStyles


class BaseFormRow:
    """
    フォーム行の基本クラス
    ラベルとコントロールの配置を標準化
    """
    
    ROW_STYLES = CommonStyles.FORM_ROW.copy()
    LABEL_STYLES = CommonStyles.FORM_LABEL.copy()
    
    @classmethod
    def create(
        cls,
        label: str,
        control_type: str,
        label_width: str = "80px",
        control_props: Optional[Dict[str, Any]] = None,
        additional_row_styles: Optional[Dict[str, str]] = None,
        additional_label_styles: Optional[Dict[str, str]] = None,
        **kwargs
    ):
        """
        フォーム行を作成
        
        Args:
            label: ラベルテキスト
            control_type: 'input', 'select', 'number', 'textarea', 'radio', 'checkbox'
            label_width: ラベルの幅
            control_props: コントロールに渡すプロパティ
            additional_row_styles: 行の追加スタイル
            additional_label_styles: ラベルの追加スタイル
            **kwargs: コントロールに渡す追加引数
        """
        # 行スタイル
        row_styles = cls.ROW_STYLES.copy()
        if additional_row_styles:
            row_styles.update(additional_row_styles)
            
        with ui.row().style(StyleBuilder.to_string(row_styles)):
            # ラベル
            label_styles = cls.LABEL_STYLES.copy()
            label_styles['min-width'] = label_width
            if additional_label_styles:
                label_styles.update(additional_label_styles)
            
            ui.label(label).style(StyleBuilder.to_string(label_styles))
            
            # コントロール作成
            control = cls._create_control(control_type, control_props, **kwargs)
            return control
    
    @staticmethod
    def _create_control(
        control_type: str,
        control_props: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        """コントロールタイプに応じたUI要素を作成"""
        control_props = control_props or {}
        
        if control_type == 'input':
            return ui.input(**kwargs).props(**control_props) if control_props else ui.input(**kwargs)
        elif control_type == 'select':
            options = kwargs.pop('options', [])
            value = kwargs.pop('value', None)
            return ui.select(options, value=value, **kwargs)
        elif control_type == 'number':
            return ui.number(**kwargs)
        elif control_type == 'textarea':
            return ui.textarea(**kwargs)
        elif control_type == 'radio':
            options = kwargs.pop('options', [])
            value = kwargs.pop('value', None)
            return ui.radio(options, value=value, **kwargs)
        elif control_type == 'checkbox':
            return ui.checkbox(**kwargs)
        else:
            raise ValueError(f"Unknown control type: {control_type}")


class FormBuilder:
    """
    フォーム全体を構築するビルダークラス
    """
    
    def __init__(self, gap: str = "4px"):
        self.gap = gap
        self.rows = []
    
    def add_row(
        self,
        label: str,
        control_type: str,
        **kwargs
    ) -> 'FormBuilder':
        """フォーム行を追加（チェーン可能）"""
        self.rows.append({
            'label': label,
            'control_type': control_type,
            'kwargs': kwargs
        })
        return self
    
    def add_custom_row(self, builder_func: Callable) -> 'FormBuilder':
        """カスタム行を追加"""
        self.rows.append({
            'custom': True,
            'builder': builder_func
        })
        return self
    
    def build(self, container_styles: Optional[Dict[str, str]] = None):
        """フォームを構築"""
        form_styles = CommonStyles.FLEX_COLUMN.copy()
        form_styles['gap'] = self.gap
        form_styles['width'] = '100%'
        
        if container_styles:
            form_styles.update(container_styles)
            
        with ui.element('div').style(StyleBuilder.to_string(form_styles)) as form:
            for row_config in self.rows:
                if row_config.get('custom'):
                    row_config['builder']()
                else:
                    BaseFormRow.create(
                        label=row_config['label'],
                        control_type=row_config['control_type'],
                        additional_row_styles={'margin-bottom': '0'},
                        **row_config['kwargs']
                    )
        
        return form


class CompactFormRow:
    """
    コンパクトなフォーム行（複数コントロールを横並び）
    """
    
    @staticmethod
    def create_dual_controls(
        left_config: Dict[str, Any],
        right_config: Dict[str, Any],
        gap: str = "8px",
        additional_styles: Optional[Dict[str, str]] = None
    ):
        """
        2つのコントロールを横並びで配置
        
        Args:
            left_config: {'label': str, 'control_type': str, ...}
            right_config: {'label': str, 'control_type': str, ...}
        """
        row_styles = {
            'width': '100%',
            'display': 'flex',
            'align-items': 'center',
            'gap': gap,
            'justify-content': 'flex-start'
        }
        
        if additional_styles:
            row_styles.update(additional_styles)
            
        with ui.row().style(StyleBuilder.to_string(row_styles)):
            # 左側
            with ui.column().style('min-width: 0; flex-shrink: 1;'):
                BaseFormRow.create(**left_config)
            
            # 右側  
            with ui.column().style(f'min-width: 0; flex-shrink: 1; margin-left: {gap};'):
                BaseFormRow.create(**right_config)