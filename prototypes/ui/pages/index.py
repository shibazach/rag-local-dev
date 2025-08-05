"""
インデックスページ - UI設計ポリシー準拠実装（共通コンポーネント使用）
"""
from nicegui import ui
from ui.components.layout import RAGHeader, RAGFooter, MainContentArea
from ui.components.sections import HeroSection, FeatureSection, StatusSection

class IndexPage:
    """インデックスページクラス - UI設計ポリシー準拠・共通コンポーネント使用"""
    
    def render(self):
        """メインページ描画"""
        self._render_policy_compliant_index()
    
    def _render_policy_compliant_index(self):
        """UI設計ポリシー準拠のインデックス実装（完全共通化）"""
        # 共通ヘッダー（ホームページ用）
        RAGHeader(show_site_name=False, current_page="index")

        # 全ページ共通メインコンテンツエリア（完璧な余白ゼロ）
        with MainContentArea():
            
            # ヒーローセクション（共通コンポーネント）
            HeroSection(
                title='R&D RAGシステム',
                subtitle='AIブーストされた新世代ドキュメント検索プラットフォーム✨',
                background_color='#334155'
            )

            # 機能セクション（6行3カラム透明表形式）
            with ui.element('div').style('padding:32px 0;width:100%;margin:0;display:flex;flex-direction:column;align-items:center;justify-content:center;'):
                ui.label('主な機能').style('font-size:24px;font-weight:bold;color:#1f2937;margin:0 0 20px 0;text-align:center;')
                
                # 機能リスト表（透明・センタリング・最適幅）
                with ui.element('div').style('display:flex;justify-content:center;align-items:center;width:100%;'):
                    with ui.element('table').style('border-collapse:collapse;background:transparent;border:none;'):
                        # 表ヘッダーなし、6行のデータ行のみ
                        with ui.element('tbody'):
                            # 1行目: 多形式文書対応
                            with ui.element('tr'):
                                with ui.element('td').style('text-align:center;padding:2px 12px 2px 0;font-size:20px;width:40px;vertical-align:middle;'):
                                    ui.label('📄')
                                with ui.element('td').style('text-align:left;padding:2px 8px 2px 0;font-size:14px;font-weight:bold;color:#1f2937;white-space:nowrap;vertical-align:middle;'):
                                    ui.label('多形式文書対応：')
                                with ui.element('td').style('text-align:left;padding:2px 0;font-size:14px;color:#6b7280;line-height:1.2;vertical-align:middle;'):
                                    ui.label('PDF、Word、テキスト、CSV、JSON、EMLファイルの処理に対応')
                            
                            # 2行目: 高精度OCR
                            with ui.element('tr'):
                                with ui.element('td').style('text-align:center;padding:2px 12px 2px 0;font-size:20px;width:40px;vertical-align:middle;'):
                                    ui.label('🔍')
                                with ui.element('td').style('text-align:left;padding:2px 8px 2px 0;font-size:14px;font-weight:bold;color:#1f2937;white-space:nowrap;vertical-align:middle;'):
                                    ui.label('高精度OCR：')
                                with ui.element('td').style('text-align:left;padding:2px 0;font-size:14px;color:#6b7280;line-height:1.2;vertical-align:middle;'):
                                    ui.label('複数のOCRエンジンによる高精度なテキスト抽出')
                            
                            # 3行目: LLM整形
                            with ui.element('tr'):
                                with ui.element('td').style('text-align:center;padding:2px 12px 2px 0;font-size:20px;width:40px;vertical-align:middle;'):
                                    ui.label('🤖')
                                with ui.element('td').style('text-align:left;padding:2px 8px 2px 0;font-size:14px;font-weight:bold;color:#1f2937;white-space:nowrap;vertical-align:middle;'):
                                    ui.label('LLM整形：')
                                with ui.element('td').style('text-align:left;padding:2px 0;font-size:14px;color:#6b7280;line-height:1.2;vertical-align:middle;'):
                                    ui.label('Ollamaを使用した日本語テキストの品質向上')
                            
                            # 4行目: ベクトル検索
                            with ui.element('tr'):
                                with ui.element('td').style('text-align:center;padding:2px 12px 2px 0;font-size:20px;width:40px;vertical-align:middle;'):
                                    ui.label('🔎')
                                with ui.element('td').style('text-align:left;padding:2px 8px 2px 0;font-size:14px;font-weight:bold;color:#1f2937;white-space:nowrap;vertical-align:middle;'):
                                    ui.label('ベクトル検索：')
                                with ui.element('td').style('text-align:left;padding:2px 0;font-size:14px;color:#6b7280;line-height:1.2;vertical-align:middle;'):
                                    ui.label('複数の埋め込みモデルによる高精度検索')
                            
                            # 5行目: リアルタイム処理
                            with ui.element('tr'):
                                with ui.element('td').style('text-align:center;padding:2px 12px 2px 0;font-size:20px;width:40px;vertical-align:middle;'):
                                    ui.label('⚡')
                                with ui.element('td').style('text-align:left;padding:2px 8px 2px 0;font-size:14px;font-weight:bold;color:#1f2937;white-space:nowrap;vertical-align:middle;'):
                                    ui.label('リアルタイム処理：')
                                with ui.element('td').style('text-align:left;padding:2px 0;font-size:14px;color:#6b7280;line-height:1.2;vertical-align:middle;'):
                                    ui.label('SSEによる進捗表示とリアルタイム処理')
                            
                            # 6行目: セキュリティ設計
                            with ui.element('tr'):
                                with ui.element('td').style('text-align:center;padding:2px 12px 2px 0;font-size:20px;width:40px;vertical-align:middle;'):
                                    ui.label('🔒')
                                with ui.element('td').style('text-align:left;padding:2px 8px 2px 0;font-size:14px;font-weight:bold;color:#1f2937;white-space:nowrap;vertical-align:middle;'):
                                    ui.label('セキュリティ設計：')
                                with ui.element('td').style('text-align:left;padding:2px 0;font-size:14px;color:#6b7280;line-height:1.2;vertical-align:middle;'):
                                    ui.label('HTTPS対応、認証、API分離によるセキュアな設計')

            # スペーサー（主な機能とシステム状況の間隔）
            ui.element('div').style('height: 24px;')
            
            # ステータスセクション（共通コンポーネント）
            StatusSection(
                title='システム状況',
                stats=[
                    {'value': '42', 'label': '登録ファイル数', 'color': '#3b82f6'},
                    {'value': '3', 'label': 'チャットセッション数', 'color': '#10b981'},
                    {'value': '1547', 'label': '埋め込みベクトル数', 'color': '#f59e0b'}
                ]
            )

        # 共通フッター
        RAGFooter()