"""チャット画面 - RAGシステム用チャットインターフェース"""

from nicegui import ui
from typing import Optional
from ui.components.elements import CommonPanel, ChatSearchResultCard, ChatLayoutButton, ChatSettingsPanel

class ChatPage:
    """
    チャット画面
    
    機能:
    - 3パターンレイアウト対応（PDFなし/第1パターン/第2パターン）
    - 検索設定パネル
    - 検索結果表示
    - PDFプレビュー
    - レスポンシブ設計
    """
    
    def __init__(self):
        self.current_layout = 'no-preview'  # 'no-preview', 'pattern1', 'pattern2'
        self.search_results = self._create_dummy_search_results()
    
    def render(self):
        """チャット画面を描画"""
        with ui.element('div').style('width: 100%; height: 100%; margin: 0; padding: 0;'):
            self._create_layout_tabs()
    
    def _create_layout_tabs(self):
        """レイアウト切り替えタブシステム"""
        with ui.tabs() as tabs:
            tab1 = ui.tab('no-preview', label='PDFプレビューなし')
            tab2 = ui.tab('pattern1', label='第1パターン（<<）')
            tab3 = ui.tab('pattern2', label='第2パターン（>>）')
        
        with ui.tab_panels(tabs).style('width: 100%; height: calc(100% - 48px);'):
            with ui.tab_panel('no-preview'):
                self._create_no_preview_layout()
            
            with ui.tab_panel('pattern1'):
                self._create_pattern1_layout()
            
            with ui.tab_panel('pattern2'):
                self._create_pattern2_layout()
    
    def _create_no_preview_layout(self):
        """PDFプレビューなし - 縦2分割"""
        with ui.element('div').style(
            'width: 100%; height: 100%; '
            'display: flex; flex-direction: column; '
            'margin: 0; padding: 8px; gap: 6px; '
            'box-sizing: border-box;'
        ):
            # 上部：検索設定パネル
            with ui.element('div').style('flex: 0 0 180px;'):
                self._create_search_settings_panel()
            
            # 下部：検索結果パネル
            with ui.element('div').style('flex: 1;'):
                self._create_search_results_panel()
    
    def _create_pattern1_layout(self):
        """第1パターン - 上部設定、下部左右分割"""
        with ui.element('div').style(
            'width: 100%; height: 100%; '
            'display: flex; flex-direction: column; '
            'margin: 0; padding: 8px; gap: 6px; '
            'box-sizing: border-box;'
        ):
            # 上部：検索設定パネル
            with ui.element('div').style('flex: 0 0 180px; position: relative;'):
                # レイアウト切り替えボタン（右上）
                ChatLayoutButton.create(
                    text=">>",
                    on_click=lambda: self._switch_to_pattern2(),
                    title="第2パターンに切り替え"
                )
                
                self._create_search_settings_panel()
            
            # 下部：左右分割（検索結果 + PDF）
            with ui.element('div').style('flex: 1; display: flex; gap: 6px;'):
                # 左：検索結果パネル
                with ui.element('div').style('flex: 1;'):
                    self._create_search_results_panel()
                
                # 右：PDFパネル
                with ui.element('div').style('flex: 1;'):
                    self._create_pdf_panel()
    
    def _create_pattern2_layout(self):
        """第2パターン - 左縦分割、右PDF"""
        with ui.element('div').style(
            'width: 100%; height: 100%; '
            'display: flex; gap: 6px; '
            'margin: 0; padding: 8px; '
            'box-sizing: border-box;'
        ):
            # 左側：縦分割（設定 + 検索結果）
            with ui.element('div').style('flex: 1; display: flex; flex-direction: column; gap: 6px;'):
                # 左上：検索設定パネル
                with ui.element('div').style('flex: 0 0 180px; position: relative;'):
                    # レイアウト切り替えボタン（右上）
                    ChatLayoutButton.create(
                        text="<<",
                        on_click=lambda: self._switch_to_pattern1(),
                        title="第1パターンに切り替え"
                    )
                    
                    self._create_search_settings_panel()
                
                # 左下：検索結果パネル
                with ui.element('div').style('flex: 1;'):
                    self._create_search_results_panel()
            
            # 右側：PDFパネル
            with ui.element('div').style('flex: 1;'):
                self._create_pdf_panel()
    
    def _create_search_settings_panel(self):
        """検索設定パネル - 共通コンポーネント使用"""
        ChatSettingsPanel.create(
            search_handler=self._handle_search,
            history_handler=self._handle_history,
            width="100%",
            height="100%"
        )
    
    def _create_search_results_panel(self):
        """検索結果パネル - CommonPanel使用"""
        with CommonPanel(
            title="📋 検索結果",
            gradient="linear-gradient(135deg, #f093fb 0%, #f5576c 100%)",
            width="100%",
            height="100%"
        ) as panel:
            # 検索結果表示
            if not self.search_results:
                ui.label('質問を入力して「検索実行」ボタンを押してください').style(
                    'color: #888; text-align: center; margin-top: 2em;'
                )
            else:
                for i, result in enumerate(self.search_results):
                    self._create_search_result_card(result, i)
    
    def _create_search_result_card(self, result: dict, index: int):
        """検索結果カード - 共通コンポーネント使用"""
        ChatSearchResultCard.create(
            result=result,
            on_click=lambda: self._handle_detail(result)
        )
    
    def _create_pdf_panel(self):
        """PDFプレビューパネル - CommonPanel使用（全面表示）"""
        with CommonPanel(
            title="📄 PDF",
            gradient="linear-gradient(135deg, #4ade80 0%, #3b82f6 100%)",
            width="100%",
            height="100%"
        ) as panel:
            # パネルのコンテンツエリアのpaddingを0に上書き
            panel.content_element.style('padding: 0;')
            
            # PDF表示エリア（全面表示）
            with ui.element('div').style(
                'width: 100%; height: 100%; background: #f5f5f5; '
                'display: flex; align-items: center; justify-content: center; '
                'margin: 0; padding: 0;'
            ):
                # プレースホルダー（PDFが読み込まれるまで）
                with ui.element('div').style('text-align: center; color: #888;'):
                    ui.icon('picture_as_pdf', size='64px').style('color: #ccc; margin-bottom: 12px;')
                    ui.label('PDFプレビューエリア').style('font-size: 16px; margin-bottom: 8px;')
                    ui.label('PDF表示準備中...').style('font-size: 12px; color: #aaa;')
                
                # 実際のPDFプレビューエリア（後で実装）
                # ui.html('<iframe src="" style="width: 100%; height: 100%; border: none; margin: 0; padding: 0;"></iframe>')
    
    def _create_dummy_search_results(self):
        """ダミーの検索結果データ"""
        return [
            {
                'filename': 'テストファイル1.pdf',
                'description': 'これはテスト用の検索結果です。実際のサーバーとの通信でエラーが発生したため、ダミーデータを表示しています。',
                'content': 'ファイルをクリックするとダミー時刻がプレビューされます。',
                'score': 0.85
            },
            {
                'filename': 'サンプルドキュメント.pdf',
                'description': 'サンプルの技術文書です。様々な機能やAPIの使用方法について説明しています。',
                'content': 'この文書では、システムアーキテクチャと実装の詳細について解説します。主要なコンポーネントには...',
                'score': 0.73
            },
            {
                'filename': 'プロジェクト仕様書.pdf',
                'description': 'プロジェクトの要件定義と仕様について記載された文書です。',
                'content': '本プロジェクトは、RAGシステムの構築を目的としており、以下の機能を実装します...',
                'score': 0.68
            }
        ]
    
    # ハンドラーメソッド
    def _handle_search(self):
        """検索実行ハンドラー"""
        print("検索実行がクリックされました")
        # 実際の検索処理を実装
    
    def _handle_history(self):
        """履歴表示ハンドラー"""
        print("履歴がクリックされました")
        # 履歴表示処理を実装
    
    def _handle_detail(self, result: dict):
        """詳細表示ハンドラー"""
        print(f"詳細表示: {result['filename']}")
        # 詳細表示処理を実装
    
    def _handle_edit(self, result: dict):
        """編集ハンドラー"""
        print(f"編集: {result['filename']}")
        # 編集処理を実装
    
    def _switch_to_pattern1(self):
        """第1パターンに切り替え"""
        print("第1パターンに切り替え")
        # タブ切り替え処理を実装
    
    def _switch_to_pattern2(self):
        """第2パターンに切り替え"""
        print("第2パターンに切り替え")
        # タブ切り替え処理を実装


# チャット画面のレンダリング関数
def render_chat_page():
    """チャット画面をレンダリング"""
    chat = ChatPage()
    chat.render()