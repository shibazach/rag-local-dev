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
        # 共通ヘッダー（ホームページ用 - サイト名なし）
        RAGHeader(show_site_name=False, current_page="index")

        # 全ページ共通メインコンテンツエリア（完璧な余白ゼロ）
        with MainContentArea():
            
            # ヒーローセクション（共通コンポーネント）
            HeroSection(
                title='R&D RAGシステム',
                subtitle='AIブーストされた新世代ドキュメント検索プラットフォーム✨',
                background_color='#334155'
            )

            # 機能セクション（共通コンポーネント）
            FeatureSection(
                title='主な機能',
                features=[
                    {'icon': '📄', 'title': '多形式文書対応：', 'description': 'PDF、Word、テキスト、CSV、JSON、EMLファイルの処理に対応'},
                    {'icon': '🔍', 'title': '高精度OCR：', 'description': '複数のOCRエンジンによる高精度なテキスト抽出'},
                    {'icon': '🤖', 'title': 'LLM整形：', 'description': 'Ollamaを使用した日本語テキストの品質向上'},
                    {'icon': '🔎', 'title': 'ベクトル検索：', 'description': '複数の埋め込みモデルによる高精度検索'},
                    {'icon': '⚡', 'title': 'リアルタイム処理：', 'description': 'SSEによる進捗表示とリアルタイム処理'},
                    {'icon': '🔒', 'title': 'セキュリティ設計：', 'description': 'HTTPS対応、認証、API分離によるセキュアな設計'}
                ]
            )

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