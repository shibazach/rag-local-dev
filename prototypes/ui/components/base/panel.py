"""
継承可能な基本パネルコンポーネント
"""
from nicegui import ui
from typing import Optional, Dict, Any
from .styles import StyleBuilder, CommonStyles


class BasePanel:
    """
    継承可能な基本パネルクラス
    
    Usage:
        # 基本使用
        with BasePanel() as panel:
            ui.label("コンテンツ")
            
        # スタイルカスタマイズ
        with BasePanel(additional_styles={'height': '400px'}) as panel:
            ui.label("カスタムコンテンツ")
    """
    
    # デフォルトスタイル（継承して上書き可能）
    BASE_STYLES = CommonStyles.PANEL_BASE.copy()
    
    def __init__(
        self,
        additional_styles: Optional[Dict[str, str]] = None,
        width: str = "100%",
        height: str = "100%",
        **kwargs
    ):
        # サイズ指定をスタイルに統合
        size_styles = {'width': width, 'height': height}
        
        # スタイルマージ
        self.styles = StyleBuilder.merge_styles(self.BASE_STYLES, size_styles)
        if additional_styles:
            self.styles.update(additional_styles)
            
        self.element = None
        self.kwargs = kwargs
    
    def __enter__(self):
        style_string = StyleBuilder.to_string(self.styles)
        self.element = ui.element('div').style(style_string)
        if self.kwargs.get('classes'):
            self.element.classes(self.kwargs['classes'])
        return self.element.__enter__()
    
    def __exit__(self, *args):
        return self.element.__exit__(*args)


class InheritablePanel(BasePanel):
    """
    ヘッダー・コンテンツ・フッター構造を持つ継承可能パネル
    
    Usage:
        panel_config = {
            'title': '⚙️ 設定',
            'gradient': 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            'footer_text': '設定パネル'
        }
        
        with InheritablePanel(**panel_config) as panel:
            ui.label("コンテンツ")
    """
    
    def __init__(
        self,
        title: str = "",
        gradient: Optional[str] = None,
        header_color: str = "white",
        footer_text: str = "",
        content_padding: str = "8px",
        additional_styles: Optional[Dict[str, str]] = None,
        **kwargs
    ):
        super().__init__(additional_styles=additional_styles, **kwargs)
        
        self.title = title
        self.gradient = gradient or "linear-gradient(135deg, #667eea 0%, #764ba2 100%)"
        self.header_color = header_color
        self.footer_text = footer_text
        self.content_padding = content_padding
        
        # 内部要素への参照
        self.header_element = None
        self.content_element = None
        self.footer_element = None
    
    def __enter__(self):
        # 親クラスでメインコンテナ作成
        super().__enter__()
        
        # ヘッダー作成
        if self.title:
            header_styles = CommonStyles.HEADER_BASE.copy()
            header_styles['background'] = self.gradient
            header_styles['color'] = self.header_color
            
            with ui.element('div').style(StyleBuilder.to_string(header_styles)) as header:
                ui.element('div').style('font-weight: bold; font-size: 14px;').props(
                    f'innerHTML="{self.title}"'
                )
                self.header_element = header
        
        # コンテンツエリア作成
        content_styles = CommonStyles.CONTENT_BASE.copy()
        content_styles['padding'] = self.content_padding
        
        self.content_element = ui.element('div').style(StyleBuilder.to_string(content_styles))
        content_context = self.content_element.__enter__()
        
        # フッター準備（__exit__で作成）
        self._content_context = content_context
        return content_context
    
    def __exit__(self, *args):
        # コンテンツエリアを閉じる
        self._content_context.__exit__(*args)
        
        # フッター作成
        if self.footer_text:
            footer_styles = CommonStyles.FOOTER_BASE.copy()
            with ui.element('div').style(StyleBuilder.to_string(footer_styles)) as footer:
                ui.label(self.footer_text)
                self.footer_element = footer
        
        # メインコンテナを閉じる
        return super().__exit__(*args)


class FormPanel(InheritablePanel):
    """
    フォーム用に特化したパネル
    行間やフォーム要素の配置に最適化
    """
    
    def __init__(
        self,
        form_gap: str = "4px",
        content_padding: str = "8px",
        **kwargs
    ):
        super().__init__(content_padding=content_padding, **kwargs)
        self.form_gap = form_gap
    
    def add_form_row(
        self,
        label_text: str,
        control_builder: Any,
        label_width: str = "80px",
        additional_row_styles: Optional[Dict[str, str]] = None
    ):
        """
        フォーム行を追加
        
        Args:
            label_text: ラベルテキスト
            control_builder: コントロールを作成する関数またはui要素
            label_width: ラベルの幅
            additional_row_styles: 行に追加するスタイル
        """
        row_styles = CommonStyles.FORM_ROW.copy()
        row_styles['margin-bottom'] = self.form_gap
        
        if additional_row_styles:
            row_styles.update(additional_row_styles)
            
        with ui.row().style(StyleBuilder.to_string(row_styles)):
            # ラベル
            label_styles = CommonStyles.FORM_LABEL.copy()
            label_styles['min-width'] = label_width
            ui.label(label_text).style(StyleBuilder.to_string(label_styles))
            
            # コントロール
            if callable(control_builder):
                control_builder()
            else:
                # ui要素の場合はそのまま配置
                control_builder