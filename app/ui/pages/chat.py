"""チャット画面 - RAGシステム用チャットインターフェース（4ペイン方式）"""

from nicegui import ui
from typing import Optional, List, Dict, Any
from app.ui.components.layout import RAGHeader, RAGFooter, MainContentArea
from app.ui.components.elements import CommonPanel
from app.ui.components.common import CommonSplitter
from app.ui.components.base.styles import CommonStyles
from app.ui.components.base.button import BaseButton

class ChatPage:
    """
    チャット画面（4ペイン方式）
    
    構造:
    - RAGHeader（共通ヘッダー）
    - MainContentArea内に4分割splitter
      - 左上: 質問エリア
      - 右上: 検索設定
      - 左下: 検索結果
      - 右下: PDFプレビュー
    - RAGFooter（共通フッター）
    """
    
    def __init__(self):
        self.search_results = self._create_dummy_search_results()
        self.current_question = ""
        self.embedding_model = "all-MiniLM-L6-v2"
        self.min_similarity = 0.7
        self.max_results = 10
    
    def render(self):
        """チャット画面を描画"""
        # 認証チェック
        from app.auth.session import SessionManager
        
        current_user = SessionManager.get_current_user()
        if not current_user:
            ui.navigate.to('/login?redirect=/chat')
            return
        
        # 共通ヘッダー
        RAGHeader(show_site_name=True, current_page="chat")
        
        # メインコンテンツエリア（C31相当）に4分割splitter配置
        with MainContentArea():
            self._create_four_pane_layout()
        
        # 共通フッター
        RAGFooter()
    
    def _create_four_pane_layout(self):
        """4分割splitterレイアウト"""
        with ui.element('div').style(
            'width: 100%; height: 100%; '
            'display: flex; margin: 0; padding: 4px; gap: 4px;'
        ).props('id="chat-main-container"'):
            
            # 左側エリア（33.33%）- 左：右 = 1:2
            with ui.element('div').style(
                'width: 33.33%; height: 100%; '
                'display: flex; flex-direction: column; '
                'margin: 0; padding: 0; gap: 4px;'
            ).props('id="chat-left-pane"'):
                
                # 左上ペイン: 質問エリア
                self._create_question_pane()
                
                # 横スプリッター（左）
                CommonSplitter.create_horizontal(splitter_id="chat-hsplitter-left", height="4px")
                
                # 左下ペイン: 検索設定（移動）
                self._create_search_settings_pane()
            
            # 縦スプリッター
            CommonSplitter.create_vertical(splitter_id="chat-vsplitter", width="4px")
            
            # 右側エリア（66.67%）- 左：右 = 1:2
            with ui.element('div').style(
                'width: 66.67%; height: 100%; '
                'display: flex; flex-direction: column; '
                'margin: 0; padding: 0; gap: 4px;'
            ).props('id="chat-right-pane"'):
                
                # 右上ペイン: 検索結果（移動）
                self._create_search_results_pane()
                
                # 横スプリッター（右）
                CommonSplitter.create_horizontal(splitter_id="chat-hsplitter-right", height="4px")
                
                # 右下ペイン: PDFプレビュー
                self._create_pdf_preview_pane()
        
        # CommonSplitter初期化
        CommonSplitter.add_splitter_styles()
        CommonSplitter.add_splitter_javascript()
    
    def _create_question_pane(self):
        """左上: 質問エリア"""
        with CommonPanel(
            title="質問",
            gradient="#334155",
            header_color="white",
            width="100%",
            height="50%"
        ) as panel:
            
            # ヘッダーにボタンを追加
            with panel.header_element:
                with ui.element('div').style('display: flex; gap: 6px; margin-right: 8px;'):
                    clear_button = BaseButton.create_type_b('クリア')
                    search_button = ui.button('検索実行', color='primary').style(
                        'padding: 4px 12px; font-size: 12px;'
                    )
            
            panel.content_element.style('padding: 4px; height: 100%; box-sizing: border-box;')
            
            # 質問入力エリア（パネル全体に追従）
            question_input = ui.textarea(
                placeholder="RAGシステムに質問したい内容を入力してください...",
                value=self.current_question
            ).style(
                'width: calc(100% - 8px); height: calc(100% - 8px); '
                'margin: 4px; resize: none; box-sizing: border-box;'
            ).props('outlined')
            
            # ボタンのイベントハンドラーを設定
            clear_button.on('click', lambda: question_input.set_value(''))
            search_button.on('click', lambda: self._execute_search(question_input.value))
    
    def _create_search_settings_pane(self):
        """右上: 検索設定"""
        with CommonPanel(
            title="検索設定",
            gradient="#334155",
            header_color="white",
            width="100%",
            height="50%"
        ) as panel:
            # 右ペインもpadding付きのコンテナで左ペインと同じ構造にする
            with ui.element('div').style('padding: 4px; height: 100%; box-sizing: border-box;'):
                with ui.element('div').style('display: flex; flex-direction: column; gap: 6px; height: 100%;'):
                    
                    # 検索モード設定
                    with ui.element('div').style('display: flex; align-items: center; gap: 8px;'):
                        ui.label('検索モード').style(
                            'min-width: 100px; font-weight: 500; text-align: left;'
                        )
                        ui.select(
                            options=['チャンク統合', 'ファイル別（要約+一致度）'],
                            value='ファイル別（要約+一致度）'
                        ).style('width: 360px;').props('outlined dense')
                    
                    # 埋め込みモデル設定
                    with ui.element('div').style('display: flex; align-items: center; gap: 8px;'):
                        ui.label('埋め込みモデル').style(
                            'min-width: 100px; font-weight: 500; text-align: left;'
                        )
                        ui.select(
                            options=['all-MiniLM-L6-v2', 'sentence-transformers/all-mpnet-base-v2', 'text-embedding-ada-002'],
                            value=self.embedding_model
                        ).style('width: 360px;').props('outlined dense')
                    
                    # 最小一致度設定
                    with ui.element('div').style('display: flex; align-items: center; gap: 8px;'):
                        ui.label('最小一致度').style(
                            'min-width: 100px; font-weight: 500; text-align: left;'
                        )
                        with ui.element('div').style('display: flex; align-items: center; gap: 6px;'):
                            # テキストボックスを左に配置（幅60px）
                            similarity_input = ui.number(
                                value=self.min_similarity,
                                format='%.1f',
                                min=0.0,
                                max=1.0,
                                step=0.1
                            ).style('width: 60px;').props('outlined dense')
                            
                            # スライドバーを右に配置（埋め込みモデルの右端に合わせて244px幅）
                            similarity_slider = ui.slider(min=0.0, max=1.0, step=0.1, value=self.min_similarity).style(
                                'width: 244px;'
                            ).props('label')  # label-alwaysを削除して吹き出しを非表示
                            
                            # リアルタイム連動設定
                            similarity_slider.on('update:model-value', lambda e: similarity_input.set_value(e.args))
                            similarity_input.on('update:model-value', lambda e: similarity_slider.set_value(e.args))
                    
                    # 最大結果数設定
                    with ui.element('div').style('display: flex; align-items: center; gap: 8px;'):
                        ui.label('最大結果数').style(
                            'min-width: 100px; font-weight: 500; text-align: left;'
                        )
                        ui.number(
                            value=self.max_results,
                            min=1,
                            max=100,
                            step=1
                        ).style('width: 70px;').props('outlined dense')
                    
                    # 検索オプション
                    with ui.element('div').style('display: flex; align-items: center; gap: 8px;'):
                        ui.label('検索オプション').style(
                            'min-width: 100px; font-weight: 500; text-align: left;'
                        )
                        ui.checkbox('セマンティック検索を使用', value=True)
    
    def _create_search_results_pane(self):
        """左下: 検索結果"""
        with CommonPanel(
            title="検索結果",
            gradient="#334155",
            header_color="white",
            width="100%",
            height="50%"
        ) as panel:
            
            # ヘッダーに履歴ボタンを追加
            with panel.header_element:
                with ui.element('div').style('display: flex; gap: 6px; margin-right: 8px;'):
                    BaseButton.create_type_b('履歴')
                    BaseButton.create_type_a('💾 保存', on_click=self._save_settings)
            
            panel.content_element.style('padding: 0;')
            
            # 検索結果リスト
            with ui.element('div').style(
                'height: 100%; overflow-y: auto; padding: 4px;'
            ):
                for i, result in enumerate(self.search_results):
                    self._create_search_result_item(result, i)
    
    def _save_settings(self):
        """設定を保存"""
        ui.notify('設定を保存しました', type='positive')
    
    def _create_search_result_item(self, result: Dict[str, Any], index: int):
        """検索結果アイテム"""
        with ui.element('div').style(
            f'margin-bottom: 4px; padding: 8px; '
            f'border: 1px solid {CommonStyles.COLOR_GRAY_200}; '
            f'border-radius: 4px; background: white; '
            'cursor: pointer; transition: all 0.2s;'
        ).classes('hover:shadow-md hover:border-blue-300').on('click', lambda: self._select_result(result)):
            
            # ヘッダー（ファイル名とスコア）
            with ui.element('div').style('display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;'):
                ui.label(result['filename']).style(
                    'font-weight: bold; color: #2563eb; font-size: 14px;'
                )
                ui.label(f"{result['score']:.3f}").style(
                    f'background: {CommonStyles.COLOR_PRIMARY}; color: white; '
                    'padding: 2px 8px; border-radius: 12px; font-size: 11px;'
                )
            
            # コンテンツプレビュー
            ui.label(result['content']).style(
                'font-size: 13px; line-height: 1.4; color: #374151; '
                'display: -webkit-box; -webkit-line-clamp: 3; '
                '-webkit-box-orient: vertical; overflow: hidden;'
            )
            
            # メタデータ
            with ui.element('div').style('margin-top: 4px; display: flex; gap: 8px; font-size: 11px; color: #6b7280;'):
                ui.label(f"ページ: {result['page']}")
                ui.label(f"チャンク: {result['chunk']}")
    
    def _create_pdf_preview_pane(self):
        """右下: PDFプレビュー（ヘッダーなし）"""
        # ヘッダーなしの直接コンテンツ表示
        with ui.element('div').style(
            'width: 100%; height: 50%; '
            'background: white; border-radius: 12px; '
            'box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15); '
            'border: 1px solid #e5e7eb; '
            'display: flex; flex-direction: column; '
            'overflow: hidden;'
        ):
            # PDFビューアエリア（破線縁取りなし）
            with ui.element('div').style(
                'height: 100%; background: #f3f4f6; '
                'display: flex; align-items: center; justify-content: center;'
            ):
                with ui.element('div').style('text-align: center; color: #6b7280;'):
                    ui.icon('picture_as_pdf', size='48px').style('margin-bottom: 12px;')
                    ui.label('PDFプレビュー').style('font-size: 16px; font-weight: 500; margin-bottom: 4px;')
                    ui.label('検索結果をクリックするとPDFが表示されます').style('font-size: 12px;')
    

    
    def _execute_search(self, question: str):
        """検索実行"""
        self.current_question = question
        print(f"検索実行: {question}")
        # TODO: 実際の検索処理を実装
    
    def _select_result(self, result: Dict[str, Any]):
        """検索結果選択"""
        print(f"結果選択: {result['filename']}")
        # TODO: PDFプレビュー表示処理を実装
    
    def _create_dummy_search_results(self) -> List[Dict[str, Any]]:
        """ダミー検索結果データ"""
        return [
            {
                'filename': 'テストファイル1.pdf',
                'content': 'これはテストファイル1の内容です。RAGシステムについて詳しく説明しています。機械学習と自然言語処理の技術を組み合わせて、効率的な情報検索を実現します。',
                'score': 0.892,
                'page': 1,
                'chunk': 1
            },
            {
                'filename': 'テストファイル2.pdf',
                'content': '文書検索における最新技術について解説。ベクトル類似度検索やセマンティック検索の手法を詳しく紹介しています。',
                'score': 0.847,
                'page': 3,
                'chunk': 2
            },
            {
                'filename': 'テストファイル3.pdf',
                'content': 'AI技術の応用事例について。特に自然言語処理分野での進歩と実用化について詳細に記載されています。',
                'score': 0.823,
                'page': 2,
                'chunk': 1
            },
            {
                'filename': 'テストファイル4.pdf',
                'content': 'ドキュメント管理システムの構築方法。効率的なインデックス作成と検索最適化について説明しています。',
                'score': 0.789,
                'page': 5,
                'chunk': 3
            }
        ]