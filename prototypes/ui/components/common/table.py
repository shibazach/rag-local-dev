"""
共通テーブルコンポーネント
NiceGUIベースのテーブルパネル実装
"""
from nicegui import ui
from typing import List, Dict, Optional, Callable, Any
from ..base import StyleBuilder, CommonStyles, BasePanel, InheritablePanel


class BaseTablePanel(InheritablePanel):
    """
    継承可能なテーブルパネル基本クラス
    
    ヘッダー、テーブル、ページネーション、フッターの基本構造を提供
    """
    
    def __init__(
        self,
        title: str = "テーブル",
        width: str = "100%",
        height: str = "100%",
        rows_per_page: int = 15,
        additional_styles: Optional[Dict[str, str]] = None
    ):
        super().__init__(
            title=title,
            width=width,
            height=height,
            additional_styles=additional_styles
        )
        self.rows_per_page = rows_per_page
        self.current_page = 1
        self.data: List[Dict[str, Any]] = []
        
    def _build_header(self):
        """ヘッダー構築（統一グレー）"""
        with ui.element('div').style(
            StyleBuilder.to_string(CommonStyles.HEADER_BASE)
        ):
            # タイトル
            ui.label(self.title).style(f'font-weight: bold; font-size: {CommonStyles.FONT_SIZE_MD};')
            
            # ヘッダーボタンエリア
            with ui.element('div').style(f'display: flex; gap: {CommonStyles.SPACING_XS};'):
                self._build_header_buttons()
    
    def _build_header_buttons(self):
        """ヘッダーボタン構築（継承先でオーバーライド）"""
        pass
    
    def _build_content(self):
        """コンテンツエリア構築"""
        with ui.element('div').style('flex: 1; display: flex; flex-direction: column; overflow: hidden;'):
            # テーブル本体
            with ui.element('div').style('flex: 1; overflow: auto;'):
                self._build_table()
            
            # ページネーション
            self._build_pagination()
    
    def _build_table(self):
        """テーブル構築（継承先でオーバーライド）"""
        pass
    
    def _build_pagination(self):
        """ページネーション構築"""
        with ui.element('div').style(
            f'height: {CommonStyles.FOOTER_HEIGHT}; '
            f'background: {CommonStyles.COLOR_GRAY_50}; '
            f'border-top: 1px solid {CommonStyles.COLOR_GRAY_200}; '
            f'display: flex; align-items: center; '
            f'justify-content: space-between; '
            f'padding: 0 {CommonStyles.SPACING_MD}; '
            f'font-size: {CommonStyles.FONT_SIZE_XS}; '
            f'color: {CommonStyles.COLOR_GRAY_700}; '
            f'flex-shrink: 0;'
        ):
            # ページ情報
            total_pages = max(1, (len(self.data) + self.rows_per_page - 1) // self.rows_per_page)
            start_idx = (self.current_page - 1) * self.rows_per_page + 1
            end_idx = min(self.current_page * self.rows_per_page, len(self.data))
            
            ui.label(f'{start_idx}-{end_idx} of {len(self.data)} items')
            
            # ページングボタン
            with ui.element('div').style('display: flex; gap: 4px; align-items: center;'):
                ui.button('◀', color='grey').style(
                    'padding: 1px 6px; font-size: 10px; '
                    'width: 20px; height: 20px;'
                ).props(f'onclick="changePage(-1)"')
                
                ui.label(f'{self.current_page} / {total_pages}').style(
                    'font-size: 10px; margin: 0 8px;'
                )
                
                ui.button('▶', color='grey').style(
                    'padding: 1px 6px; font-size: 10px; '
                    'width: 20px; height: 20px;'
                ).props(f'onclick="changePage(1)"')
    
    def _build_footer(self):
        """フッター構築"""
        with ui.element('div').style(
            StyleBuilder.to_string(CommonStyles.FOOTER_BASE)
        ):
            self._build_footer_content()
    
    def _build_footer_content(self):
        """フッターコンテンツ（継承先でオーバーライド）"""
        ui.label(f'Total: {len(self.data)} items')
        ui.label('Last updated: -')