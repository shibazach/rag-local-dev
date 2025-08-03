"""
レイアウトコンポーネント
Reusable layout components for consistent UI structure
"""

from nicegui import ui
from typing import Optional, List, Dict, Any
from app.config import config
from app.ui.themes.base import RAGTheme

class RAGHeader:
    """統一ヘッダーコンポーネント"""
    
    def __init__(
        self,
        title: str,
        current_page: str = "",
        user: Optional[Dict[str, Any]] = None,
        show_nav: bool = True
    ):
        self.title = title
        self.current_page = current_page
        self.user = user
        self.show_nav = show_nav
        self._create_header()
    
    def _create_header(self):
        """ヘッダー作成"""
        with ui.header().classes('rag-header'):
            with ui.row().classes('w-full items-center justify-between'):
                # 左側：タイトルとナビゲーション
                with ui.row().classes('items-center gap-6'):
                    ui.label(self.title).classes('text-xl font-bold')
                    
                    if self.show_nav:
                        self._create_navigation()
                
                # 右側：ユーザー情報
                self._create_user_area()
    
    def _create_navigation(self):
        """ナビゲーション作成"""
        nav_items = [
            {"label": "🏠 ダッシュボード", "path": "/", "key": "dashboard"},
            {"label": "💬 チャット", "path": "/chat", "key": "chat"},
            {"label": "📁 データ登録", "path": "/data-registration", "key": "data_registration"},
            {"label": "📄 ファイル管理", "path": "/files", "key": "files"},
            {"label": "🛠️ 管理", "path": "/admin", "key": "admin"}
        ]
        
        for item in nav_items:
            is_current = self.current_page == item["key"]
            classes = "text-white hover:text-gray-200 px-3 py-2 rounded"
            if is_current:
                classes += " bg-white bg-opacity-20"
            
            ui.link(item["label"], item["path"]).classes(classes)
    
    def _create_user_area(self):
        """ユーザーエリア作成"""
        with ui.row().classes('items-center gap-4'):
            if self.user:
                ui.label(f"👤 {self.user.get('display_name', self.user.get('username', 'User'))}").classes('text-white')
                ui.button('ログアウト', on_click=self._logout).classes('text-white').props('flat')
            else:
                ui.button('ログイン', on_click=lambda: ui.navigate.to('/login')).classes('text-white').props('flat')
    
    def _logout(self):
        """ログアウト処理"""
        # TODO: 実際のログアウト処理実装
        ui.notify('ログアウトしました', type='info')
        ui.navigate.to('/login')

class RAGSidebar:
    """サイドバーコンポーネント"""
    
    def __init__(
        self,
        items: List[Dict[str, Any]],
        current_item: str = "",
        collapsible: bool = True
    ):
        self.items = items
        self.current_item = current_item
        self.collapsible = collapsible
        self._create_sidebar()
    
    def _create_sidebar(self):
        """サイドバー作成"""
        with ui.column().classes('rag-card h-full w-64 p-4'):
            for item in self.items:
                self._create_sidebar_item(item)
    
    def _create_sidebar_item(self, item: Dict[str, Any]):
        """サイドバーアイテム作成"""
        is_current = self.current_item == item.get("key", "")
        classes = "w-full mb-2 p-3 rounded-lg transition-all"
        
        if is_current:
            classes += " bg-primary text-white"
        else:
            classes += " hover:bg-gray-100"
        
        with ui.row().classes('w-full items-center'):
            if item.get("icon"):
                ui.icon(item["icon"]).classes('mr-3')
            
            if item.get("action"):
                ui.button(
                    item["label"],
                    on_click=item["action"]
                ).classes(classes).props('flat no-caps')
            elif item.get("path"):
                ui.link(item["label"], item["path"]).classes(classes)
            else:
                ui.label(item["label"]).classes('font-medium')

class RAGFooter:
    """フッターコンポーネント"""
    
    def __init__(self, show_version: bool = True, show_links: bool = True):
        self.show_version = show_version
        self.show_links = show_links
        self._create_footer()
    
    def _create_footer(self):
        """フッター作成"""
        with ui.footer().classes('bg-gray-100 p-4 mt-8'):
            with ui.row().classes('w-full justify-between items-center'):
                # 左側：バージョン情報
                if self.show_version:
                    ui.label(f'© 2024 {config.APP_NAME} v{config.APP_VERSION}').classes('text-gray-600 text-sm')
                
                # 右側：リンク
                if self.show_links:
                    with ui.row().classes('gap-4'):
                        ui.link('API文書', config.API_DOCS_URL).classes('text-gray-600 text-sm')
                        ui.link('ヘルス', '/health').classes('text-gray-600 text-sm')

class RAGBreadcrumb:
    """パンくずリストコンポーネント"""
    
    def __init__(self, items: List[Dict[str, str]]):
        self.items = items
        self._create_breadcrumb()
    
    def _create_breadcrumb(self):
        """パンくずリスト作成"""
        with ui.row().classes('items-center gap-2 mb-4'):
            for i, item in enumerate(self.items):
                if i > 0:
                    ui.icon('chevron_right').classes('text-gray-400')
                
                if i == len(self.items) - 1:
                    # 最後の項目（現在ページ）
                    ui.label(item["label"]).classes('text-gray-800 font-medium')
                else:
                    # リンク項目
                    if item.get("path"):
                        ui.link(item["label"], item["path"]).classes('text-blue-600 hover:text-blue-800')
                    else:
                        ui.label(item["label"]).classes('text-gray-600')

class RAGContainer:
    """メインコンテナコンポーネント"""
    
    def __init__(
        self,
        max_width: str = "1200px",
        padding: str = "2rem",
        centered: bool = True
    ):
        self.max_width = max_width
        self.padding = padding
        self.centered = centered
        self.container = self._create_container()
    
    def _create_container(self):
        """コンテナ作成"""
        classes = f'rag-content p-{self.padding}'
        if self.centered:
            classes += ' mx-auto'
        
        return ui.column().classes(classes).style(f'max-width: {self.max_width}')
    
    def __enter__(self):
        return self.container.__enter__()
    
    def __exit__(self, *args):
        return self.container.__exit__(*args)

class RAGPageLayout:
    """統一ページレイアウト"""
    
    def __init__(
        self,
        title: str,
        current_page: str = "",
        user: Optional[Dict[str, Any]] = None,
        breadcrumbs: Optional[List[Dict[str, str]]] = None,
        sidebar_items: Optional[List[Dict[str, Any]]] = None,
        show_header: bool = True,
        show_footer: bool = True
    ):
        self.title = title
        self.current_page = current_page
        self.user = user
        self.breadcrumbs = breadcrumbs
        self.sidebar_items = sidebar_items
        self.show_header = show_header
        self.show_footer = show_footer
        
        # テーマ適用
        RAGTheme.apply_global_styles()
        
        self._create_layout()
    
    def _create_layout(self):
        """レイアウト作成"""
        with ui.column().classes('min-h-screen'):
            # ヘッダー
            if self.show_header:
                RAGHeader(self.title, self.current_page, self.user)
            
            # メインコンテンツエリア
            with ui.row().classes('flex-1 w-full'):
                # サイドバー
                if self.sidebar_items:
                    RAGSidebar(self.sidebar_items, self.current_page)
                
                # メインコンテンツ
                with ui.column().classes('flex-1'):
                    with RAGContainer():
                        # パンくずリスト
                        if self.breadcrumbs:
                            RAGBreadcrumb(self.breadcrumbs)
                        
                        # コンテンツエリア（継承先で実装）
                        self.content_area = ui.column().classes('w-full')
            
            # フッター
            if self.show_footer:
                RAGFooter()
    
    def get_content_area(self):
        """コンテンツエリア取得"""
        return self.content_area