"""配置テスト - タブE: チャットレイアウト実験（Splitter対応）"""

from nicegui import ui
from typing import Optional
from ui.components.elements import CommonPanel, ChatSearchResultCard, ChatLayoutButton, ChatSettingsPanel

class ArrangementTestTabE:
    """
    タブE: チャットレイアウト実験（Splitter対応）
    
    目的:
    - リサイズ可能なsplitterレイアウト
    - PDFファイル名クリックでレイアウト切り替え
    - 動的なパネル表示制御
    """
    
    def __init__(self):
        self.current_layout = 'pattern1'  # 'pattern1', 'pattern2'
        self.search_results = self._create_dummy_search_results()
        self.selected_pdf = None
    
    def render(self):
        """チャットレイアウトを描画（正確な高さ計算）"""
        with ui.element('div').style(
            'width: 100%; height: 100%; '  # tab-contentから100%継承（MainContentAreaが既にcalc処理済み）
            'margin: 0; padding: 0; overflow: hidden; box-sizing: border-box;'
        ):
            self._create_main_layout()
    
    def _create_main_layout(self):
        """メインレイアウト作成（Splitter対応）"""
        if self.current_layout == 'pattern1':
            self._create_pattern1_layout()
        elif self.current_layout == 'pattern2':
            self._create_pattern2_layout()
    
    def _create_pattern1_layout(self):
        """第1パターン - 上部設定、下部左右Splitter分割（自然な高さ制御）"""
        with ui.element('div').style(
            'width: 100%; height: 100%; display: flex; flex-direction: column; '
            'margin: 0; padding: 4px; box-sizing: border-box; overflow: hidden;'
        ):
            # 上部：検索設定パネル（コンテンツに応じた自然な高さ）
            with ui.element('div').style('position: relative; flex-shrink: 0;'):
                # レイアウト切り替えボタン（右上）
                ChatLayoutButton.create(
                    text=">>",
                    on_click=lambda: self._switch_to_pattern2(),
                    title="第2パターンに切り替え"
                )
                self._create_search_settings_panel()
            
            # 下部：左右Splitter分割（全体から上部を除いた残り空間）
            with ui.element('div').style('flex: 1; margin-top: 4px; overflow: hidden;'):
                with ui.splitter(value=50).style('width: 100%; height: 100%;') as splitter:
                    with splitter.before:
                        self._create_search_results_panel()
                    with splitter.after:
                        self._create_pdf_panel()
    
    def _create_pattern2_layout(self):
        """第2パターン - 左Splitter縦分割、右PDF（Flexbox制御）"""
        with ui.element('div').style(
            'width: 100%; height: 100%; display: flex; '
            'margin: 0; padding: 4px; box-sizing: border-box; overflow: hidden;'
        ):
            # 左右Splitter分割（Flexboxで自動調整）
            with ui.element('div').style('flex: 1; overflow: hidden;'):
                with ui.splitter(value=50).style('width: 100%; height: 100%;') as main_splitter:
                    with main_splitter.before:
                        # 左側：縦Splitter分割（設定 + 検索結果）
                        with ui.splitter(value=25, vertical=True).style('width: 100%; height: 100%;') as left_splitter:
                            with left_splitter.before:
                                # 左上：検索設定パネル（自然な高さ）
                                with ui.element('div').style('width: 100%; position: relative;'):
                                    # レイアウト切り替えボタン（右上）
                                    ChatLayoutButton.create(
                                        text="<<",
                                        on_click=lambda: self._switch_to_pattern1(),
                                        title="第1パターンに切り替え"
                                    )
                                    self._create_search_settings_panel()
                            
                            with left_splitter.after:
                                # 左下：検索結果パネル
                                self._create_search_results_panel()
                    
                    with main_splitter.after:
                        # 右側：PDFパネル
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
        """検索結果カード - 共通コンポーネント使用（ファイル名クリッカブル対応）"""
        ChatSearchResultCard.create(
            result=result,
            on_click=lambda: self._handle_detail(result),
            on_filename_click=lambda: self._handle_filename_click(result)
        )
    
    def _create_pdf_panel(self):
        """PDFプレビューパネル - CommonPanel使用（全面表示）"""
        with CommonPanel(
            title=f"📄 PDF {f'- {self.selected_pdf}' if self.selected_pdf else ''}",
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
                if self.selected_pdf:
                    # PDFが選択されている場合の表示
                    self._create_sample_pdf_content()
                else:
                    # プレースホルダー（PDFが選択されていない）
                    with ui.element('div').style('text-align: center; color: #888;'):
                        ui.icon('picture_as_pdf', size='64px').style('color: #ccc; margin-bottom: 12px;')
                        ui.label('PDFプレビューエリア').style('font-size: 16px; margin-bottom: 8px;')
                        ui.label('ファイル名をクリックしてPDFを表示').style('font-size: 12px; color: #aaa;')
    
    def _create_sample_pdf_content(self):
        """サンプルPDFコンテンツ表示"""
        with ui.element('div').style(
            'width: 100%; height: 100%; background: white; '
            'border: 1px solid #ddd; margin: 0; padding: 16px; '
            'box-sizing: border-box; overflow: auto;'
        ):
            # PDFヘッダー
            ui.label(f"📄 {self.selected_pdf}").style(
                'font-size: 18px; font-weight: bold; color: #333; margin-bottom: 16px; '
                'border-bottom: 2px solid #3b82f6; padding-bottom: 8px;'
            )
            
            # サンプルコンテンツ
            sample_content = [
                "1. はじめに",
                "このドキュメントは、RAGシステムにおけるPDFプレビュー機能のテスト用サンプルファイルです。",
                "",
                "2. 主要な機能",
                "• 検索結果の表示",
                "• PDFファイルのプレビュー",
                "• レイアウトの動的切り替え",
                "",
                "3. 技術仕様",
                "フレームワーク: NiceGUI",
                "言語: Python",
                "UI Components: Splitter, Panel, Button",
                "",
                "4. 実装詳細",
                "このシステムでは、左右および上下にリサイズ可能なSplitterを使用しており、",
                "ユーザーがレイアウトを自由に調整できます。",
                "",
                "PDFファイル名をクリックすることで、第1パターンレイアウトに自動切り替えされ、",
                "選択されたPDFファイルがこのプレビューエリアに表示されます。",
                "",
                "5. 操作方法",
                "• ファイル名クリック: PDFプレビュー表示",
                "• >>ボタン: 第2パターンに切り替え",
                "• <<ボタン: 第1パターンに切り替え",
                "",
                "※ これはサンプル表示です。実際のPDFファイルではありません。"
            ]
            
            for line in sample_content:
                if line.startswith(("1.", "2.", "3.", "4.", "5.")):
                    ui.label(line).style(
                        'font-size: 16px; font-weight: bold; color: #2563eb; margin: 12px 0 6px 0;'
                    )
                elif line.startswith("•"):
                    ui.label(line).style(
                        'font-size: 14px; color: #555; margin: 4px 0 4px 16px;'
                    )
                elif line.strip() == "":
                    ui.label(" ").style('margin: 8px 0;')
                else:
                    ui.label(line).style(
                        'font-size: 14px; color: #333; margin: 4px 0; line-height: 1.5;'
                    )
    
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
        self.current_layout = 'pattern1'
        self._refresh_layout()
    
    def _switch_to_pattern2(self):
        """第2パターンに切り替え"""
        self.current_layout = 'pattern2'
        self._refresh_layout()
    
    def _handle_filename_click(self, result: dict):
        """ファイル名クリック処理 - 第1パターンに切り替えてPDF表示"""
        self.selected_pdf = result['filename']
        self.current_layout = 'pattern1'
        self._refresh_layout()
        print(f"PDFファイル選択: {result['filename']}")
    
    def _refresh_layout(self):
        """レイアウト再構築"""
        # NiceGUIの制約により、ページ全体をリフレッシュ
        ui.notify(f"レイアウト切り替え: {self.current_layout}", type='info')