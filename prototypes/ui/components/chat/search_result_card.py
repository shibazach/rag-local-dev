"""
チャット検索結果カード
InteractiveCardを継承した実装
"""
from nicegui import ui
from typing import Dict, Any, Optional, Callable
from ..base.card import InteractiveCard


class ChatSearchResultCard(InteractiveCard):
    """
    チャット検索結果カード（継承ベース実装）
    
    InteractiveCardを継承し、検索結果固有の表示とインタラクションを追加
    """
    
    def __init__(
        self,
        result: Dict[str, Any],
        on_click: Optional[Callable] = None,
        on_filename_click: Optional[Callable] = None
    ):
        # メタデータ準備
        metadata = {}
        if 'score' in result:
            metadata['スコア'] = f"{result['score']:.3f}"
        if 'page' in result:
            metadata['ページ'] = str(result['page'])
            
        # 親クラス初期化（タイトルとコンテンツは後で独自処理）
        # on_clickは個別要素に設定するため、ここではNone
        super().__init__(
            title="",  # ファイル名は独自処理
            content="",  # 要約も独自処理
            metadata=metadata,
            on_click=None
        )
        
        self.card_on_click = on_click
        
        self.result = result
        self.on_filename_click = on_filename_click
    
    def __enter__(self):
        # 親クラスでカード作成（ただしtitle/contentは空）
        card_context = super().__enter__()
        
        # カスタムコンテンツを作成
        self._create_custom_content()
        
        return card_context
    
    def _create_custom_content(self):
        """検索結果カード固有のコンテンツ作成"""
        # カード全体をクリッカブルにする（on_clickが設定されている場合）
        if self.card_on_click:
            # カード内に見えないボタンを配置してクリック領域を作成
            ui.button('', on_click=lambda: self.card_on_click()).style(
                'position: absolute; top: 0; left: 0; right: 0; bottom: 0; '
                'z-index: 0; opacity: 0; cursor: pointer;'
            )
                
        # コンテンツコンテナ（z-indexを上に設定）
        with ui.element('div').style('position: relative; z-index: 1;'):
            # ファイル名（クリッカブルまたは通常）
            if self.on_filename_click:
                ui.button(
                    self.result['filename'],
                    on_click=lambda e: self.on_filename_click(self.result)
                ).style(
                    'background: none; border: none; padding: 0; '
                    'color: #2563eb; text-decoration: underline; '
                    'cursor: pointer; text-align: left; '
                    'font-size: 13px; font-weight: bold; margin-bottom: 4px; '
                    'z-index: 2; position: relative;'
                )
            else:
                ui.label(self.result['filename']).style(
                    'font-weight: bold; color: #1f2937; '
                    'margin-bottom: 4px; font-size: 13px;'
                )
            
            # 要約（summaryまたはdescriptionキーを使用）
            summary_text = self.result.get('summary', self.result.get('description', ''))
            if summary_text:
                ui.label(summary_text).style(
                    'color: #4b5563; font-size: 12px; '
                    'line-height: 1.4; margin-bottom: 6px;'
                )
            
            # メタデータは親クラスが処理済み
    
    @classmethod
    def create(
        cls,
        result: Dict[str, Any],
        on_click: Optional[Callable] = None,
        on_filename_click: Optional[Callable] = None
    ):
        """ファクトリメソッド（既存コードとの互換性維持）"""
        card = cls(
            result=result,
            on_click=on_click,
            on_filename_click=on_filename_click
        )
        # with文で使用
        with card:
            pass
        return card