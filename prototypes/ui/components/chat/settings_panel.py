"""
チャット検索設定パネル
FormPanelを継承した実装
"""
from nicegui import ui
from typing import Optional, Callable
from ..base import FormPanel, CompactFormRow, StyleBuilder


class ChatSettingsPanel(FormPanel):
    """
    チャット検索設定パネル（継承ベース実装）
    
    FormPanelを継承し、チャット検索固有の設定フォームを構築
    """
    
    def __init__(
        self,
        search_handler: Optional[Callable] = None,
        history_handler: Optional[Callable] = None,
        width: str = "100%",
        height: str = "100%"
    ):
        # 親クラス初期化
        super().__init__(
            title="⚙️ 検索設定",
            gradient="linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
            form_gap="2px",
            content_padding="8px",
            width=width,
            height=height
        )
        
        self.search_handler = search_handler
        self.history_handler = history_handler
        
        # PDFモード選択用
        self.pdf_display_mode = 'same_tab'
    
    def __enter__(self):
        # 親クラスのコンテキストマネージャー開始
        context = super().__enter__()
        
        # フォーム構築
        self._build_form()
        
        return context
    
    def _build_form(self):
        """チャット検索フォームを構築"""
        # 質問入力エリア
        self._create_question_input()
        
        # 検索設定（2列レイアウト）
        self._create_search_settings()
        
        # 数値設定（2列レイアウト）
        self._create_numeric_settings()
        
        # タイムアウト設定
        self._create_timeout_setting()
        
        # アクションボタンとPDF表示設定
        self._create_actions_and_pdf_settings()
    
    def _create_question_input(self):
        """質問入力エリア作成"""
        ui.textarea(
            label='質問を入力してください',
            placeholder='質問を入力してください…'
        ).style(
            'width: 100%; min-height: 40px; margin-bottom: 2px;'
        )
    
    def _create_search_settings(self):
        """検索モード・埋め込みモデル設定（2列）"""
        with ui.row().style(
            'width: 100%; align-items: center; margin-bottom: 0px; '
            'gap: 4px; justify-content: flex-start;'
        ):
            # 検索モード
            with ui.column().style('min-width: 0; flex-shrink: 1;'):
                with ui.row().style('align-items: center;'):
                    ui.label('検索モード：').style(
                        'min-width: 70px; font-size: 12px; line-height: 1.4;'
                    )
                    ui.select(
                        ['ファイル別（要約+一致度）', 'チャンク統合'],
                        value='ファイル別（要約+一致度）'
                    ).style('width: 160px; font-size: 12px;')
            
            # 埋め込みモデル
            with ui.column().style('min-width: 0; flex-shrink: 1; margin-left: 8px;'):
                with ui.row().style('align-items: center;'):
                    ui.label('埋め込みモデル：').style(
                        'min-width: 80px; font-size: 12px; line-height: 1.4;'
                    )
                    ui.select(
                        ['intfloat/e5-large-v2'],
                        value='intfloat/e5-large-v2'
                    ).style('width: 140px; font-size: 12px;')
    
    def _create_numeric_settings(self):
        """検索件数・最小一致度設定（2列）"""
        with ui.row().style(
            'width: 100%; align-items: center; margin-bottom: 0px; '
            'gap: 4px; justify-content: flex-start;'
        ):
            # 検索件数
            with ui.column().style('min-width: 0; flex-shrink: 1;'):
                with ui.row().style('align-items: center;'):
                    ui.label('検索件数：').style(
                        'min-width: 60px; font-size: 12px; line-height: 1.4;'
                    )
                    ui.number(
                        label='', value=10, min=1, max=50
                    ).style(
                        'width: 3.5em; font-size: 12px; height: 32px; line-height: 1.4;'
                    )
                    ui.label('件').style(
                        'margin-left: 4px; color: #666; font-size: 12px; line-height: 1.4;'
                    )
            
            # 最小一致度
            with ui.column().style('min-width: 0; flex-shrink: 1; margin-left: 8px;'):
                with ui.row().style('align-items: center;'):
                    ui.label('最小一致度：').style(
                        'min-width: 70px; font-size: 12px; line-height: 1.4;'
                    )
                    ui.number(
                        label='', value=0.0, min=0, max=1, step=0.1
                    ).style(
                        'width: 3.5em; font-size: 12px; height: 32px; line-height: 1.4;'
                    )
                    ui.label('以上').style(
                        'margin-left: 4px; color: #666; font-size: 12px; line-height: 1.4;'
                    )
    
    def _create_timeout_setting(self):
        """検索タイムアウト設定"""
        with ui.row().style('width: 100%; align-items: center; margin-bottom: 2px;'):
            ui.label('⏱️ 検索タイムアウト：').style(
                'min-width: 100px; font-size: 12px; line-height: 1.4;'
            )
            ui.number(
                label='', value=10, min=0, max=3600, step=5
            ).style('width: 4em; font-size: 12px;')
            ui.label('秒（0でタイムアウトなし）').style(
                'margin-left: 4px; color: #666; font-size: 12px; line-height: 1.4;'
            )
    
    def _create_actions_and_pdf_settings(self):
        """アクションボタンとPDF表示設定"""
        with ui.row().style(
            'width: 100%; align-items: center; gap: 4px; margin-top: 2px;'
        ):
            # アクションボタン
            ui.button(
                '🔍 検索実行',
                color='primary',
                on_click=self.search_handler if self.search_handler else lambda: None
            ).style('font-size: 12px; padding: 4px 8px;')
            
            ui.button(
                '📜 履歴',
                on_click=self.history_handler if self.history_handler else lambda: None
            ).style('font-size: 12px; padding: 4px 8px;')
            
            # PDF表示設定
            with ui.element('div').style(
                'margin-left: 12px; display: flex; align-items: center;'
            ):
                ui.label('PDF表示：').style(
                    'font-size: 12px; margin-right: 6px; line-height: 1.4;'
                )
                ui.radio(
                    ['同一タブ内', '別タブ'],
                    value='同一タブ内',
                    on_change=lambda e: setattr(self, 'pdf_display_mode', e.value)
                ).style('font-size: 11px;').props('inline dense')
    
    @classmethod
    def create(
        cls,
        search_handler: Optional[Callable] = None,
        history_handler: Optional[Callable] = None,
        width: str = "100%",
        height: str = "100%"
    ):
        """ファクトリメソッド（既存コードとの互換性維持）"""
        panel = cls(
            search_handler=search_handler,
            history_handler=history_handler,
            width=width,
            height=height
        )
        # コンテキストマネージャーとして使用されるため、__enter__を呼ぶ
        with panel:
            pass
        return panel