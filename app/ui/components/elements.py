"""
UI共通コンポーネント（リファクタリング版）

既存機能を保持しながら、段階的に新しい構造へ移行中
Phase 1: 基本的なコンポーネントをbase/commonへ移動 ✅
Phase 2: 既存のCommonPanel保持（互換性のため）✅
Phase 3: 具体的コンポーネントを継承ベースへ移行 ✅
"""

from nicegui import ui
from typing import Optional, Callable, List, Dict, Any

# 新しい構造からインポート
from .base import (
    StyleBuilder, CommonStyles,
    BasePanel, InheritablePanel, FormPanel,
    BaseFormRow, FormBuilder, CompactFormRow,
    BaseCard, InteractiveCard,
    BaseButton, PositionedButton, FloatingActionButton
)
from .common import (
    CommonSplitter, CommonCard, CommonSectionTitle, CommonTabs,
    # BaseDataGridView,  # ui.tableに移行済み
    CommonFormElements
)
from .chat import (
    ChatSettingsPanel, ChatSearchResultCard, ChatLayoutButton
)

# 既存のCommonPanelを保持（互換性のため）
class CommonPanel:
    """
    共通パネルコンポーネント（NiceGUI公式準拠）
    ヘッダー・フッター付きパネル
    
    機能:
    - グラデーションヘッダー
    - コンテンツエリア（スクロール対応）
    - フッター（ステータス表示）
    - 内部要素への参照保持
    
    Usage:
        with CommonPanel(
            title="📊 データ分析",
            gradient="linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
            width="500px",
            height="400px"
        ) as panel:
            # コンテンツ追加
            ui.label("パネル内容")
            
        # 内部要素へのアクセス
        panel.header_element.style('background: red;')
        panel.content_element.style('padding: 20px;')
    """
    
    def __init__(
        self,
        title: str = "",
        gradient: str = "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
        header_color: str = "white",
        footer_content: str = "",
        width: str = "100%",
        height: str = "100%",
        content_padding: str = "8px"
    ):
        self.title = title
        self.gradient = gradient
        self.header_color = header_color
        self.footer_content = footer_content
        self.width = width
        self.height = height
        self.content_padding = content_padding
        
        # 内部要素への参照
        self.container = None
        self.header_element = None
        self.content_element = None
        self.footer_element = None
    
    def __enter__(self):
        """パネル開始（コンテキストマネージャー）"""
        # メインコンテナ
        self.container = ui.element('div').style(
            f'width: {self.width}; height: {self.height}; '
            f'background: white; border-radius: 12px; '
            f'box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15); '
            f'border: 1px solid #e5e7eb; '
            f'display: flex; flex-direction: column; '
            f'overflow: hidden;'
        )
        
        with self.container:
            # ヘッダー（オプション）
            if self.title:
                self._create_header()
        
            # コンテンツエリア
            self.content_element = ui.element('div').style(
                f'flex: 1; padding: {self.content_padding}; overflow: auto;'
            )
            
            # コンテンツエリアのコンテキストを開始
            content_context = self.content_element.__enter__()
            
            # フッター用のコンテキストを保持
            self._content_context = content_context
        
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """パネル終了"""
        # コンテンツエリアを閉じる
        self._content_context.__exit__(exc_type, exc_val, exc_tb)
        
        # フッター（オプション）
        if self.footer_content:
            self._create_footer()
    
    def _create_header(self):
        """ヘッダー作成"""
        self.header_element = ui.element('div').style(
            f'background: {self.gradient}; '
            f'color: {self.header_color}; '
            f'padding: 12px 16px; '
            f'height: 48px; '
            f'display: flex; '
            f'align-items: center; '
            f'justify-content: space-between; '
            f'box-sizing: border-box; '
            f'flex-shrink: 0; '
            f'border-bottom: 1px solid #e5e7eb;'
        )
        
        with self.header_element:
            ui.element('div').style(
                'font-weight: bold; font-size: 16px; flex-shrink: 0; margin-right: 12px;'
            ).props(f'innerHTML="{self.title}"')
    
    def _create_footer(self):
        """フッター作成"""
        with ui.element('div').style(
            'height: 24px; background: #f8f9fa; '
            'border-top: 1px solid #e5e7eb; '
            'display: flex; align-items: center; '
            'justify-content: space-between; '
            'padding: 0 12px; font-size: 11px; '
            'color: #6b7280; flex-shrink: 0;'
        ):
            ui.label(self.footer_content)


# Phase 3完了：具体的コンポーネントは chatディレクトリに移動済み
# 既存コードとの互換性のため、このファイルからもエクスポート