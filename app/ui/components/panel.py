"""共通パネルコンポーネント"""

from typing import Optional, List, Dict, Any, Callable
from nicegui import ui

class PanelComponent:
    """
    共通パネルコンポーネント
    
    基本構成：
    - ヘッダー（グラデーション背景、タイトル、ボタン）
    - 本体（コンテンツエリア）
    - フッター（オプション、統計情報）
    """
    
    def __init__(self,
                 title: str,
                 header_gradient: str,
                 header_icon: str = "",
                 header_buttons: Optional[List[Dict[str, Any]]] = None,
                 show_footer: bool = True,
                 footer_left: str = "",
                 footer_right: str = "",
                 footer_background: str = "#f8f9fa",
                 border_radius: int = 12,
                 footer_height: int = 24):
        """
        パネルコンポーネント初期化
        
        Args:
            title: パネルタイトル
            header_gradient: ヘッダーのグラデーション（CSS形式）
            header_icon: タイトル前のアイコン
            header_buttons: ヘッダーボタンのリスト [{'icon': '📈', 'action': callback_func}]
            show_footer: フッター表示フラグ
            footer_left: フッター左側テキスト
            footer_right: フッター右側テキスト
            footer_background: フッター背景色
            border_radius: パネル角丸サイズ
            footer_height: フッター高さ
        """
        self.title = title
        self.header_gradient = header_gradient
        self.header_icon = header_icon
        self.header_buttons = header_buttons or []
        self.show_footer = show_footer
        self.footer_left = footer_left
        self.footer_right = footer_right
        self.footer_background = footer_background
        self.border_radius = border_radius
        self.footer_height = footer_height
        self.content_container = None
    
    def __enter__(self):
        """コンテキストマネージャー開始"""
        # パネルコンテナ
        self.panel_container = ui.element('div').style(
            f'width: 100%; height: 100%; '
            f'background: white; border-radius: {self.border_radius}px; '
            f'box-shadow: 0 2px 8px rgba(0,0,0,0.15); '
            f'border: 1px solid #e5e7eb; '
            f'display: flex; flex-direction: column; '
            f'overflow: hidden;'
        )
        
        # ヘッダー
        with self.panel_container:
            with ui.element('div').style(
                f'background: {self.header_gradient}; '
                f'color: white; padding: 12px 16px; '
                f'display: flex; align-items: center; justify-content: space-between; '
                f'height: 48px; box-sizing: border-box; flex-shrink: 0;'
            ):
                # タイトル
                title_text = f"{self.header_icon} {self.title}" if self.header_icon else self.title
                ui.label(title_text).style('font-weight: bold; font-size: 14px;')
                
                # ボタングループ
                if self.header_buttons:
                    with ui.element('div').style('display: flex; gap: 4px;'):
                        for btn in self.header_buttons:
                            button = ui.button(
                                btn.get('icon', ''), 
                                color='white'
                            ).style('padding: 2px 6px; font-size: 10px; min-width: 20px;')
                            
                            if 'action' in btn:
                                button.on_click(btn['action'])
            
            # コンテンツエリア
            if self.show_footer:
                self.content_container = ui.element('div').style(
                    'flex: 1; overflow: hidden; display: flex; flex-direction: column;'
                )
            else:
                self.content_container = ui.element('div').style(
                    'flex: 1; overflow: auto; padding: 12px;'
                )
        
        return self.content_container
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """コンテキストマネージャー終了"""
        if self.show_footer:
            # フッター追加
            with self.panel_container:
                with ui.element('div').style(
                    f'height: {self.footer_height}px; background: {self.footer_background}; '
                    f'border-top: 1px solid #e5e7eb; '
                    f'display: flex; align-items: center; '
                    f'justify-content: space-between; '
                    f'padding: 0 12px; font-size: 11px; '
                    f'color: #6b7280; flex-shrink: 0;'
                ):
                    ui.label(self.footer_left)
                    ui.label(self.footer_right)

class DataTablePanel(PanelComponent):
    """
    データテーブル専用パネル
    
    高密度テーブル + ページネーション対応
    """
    
    def __init__(self, 
                 title: str,
                 data: List[Dict[str, Any]],
                 columns: List[Dict[str, Any]],
                 rows_per_page: int = 15,
                 **kwargs):
        """
        データテーブルパネル初期化
        
        Args:
            title: パネルタイトル
            data: テーブルデータ
            columns: テーブルカラム定義
            rows_per_page: 1ページあたりの行数
            **kwargs: PanelComponentの他の引数
        """
        super().__init__(title, **kwargs)
        self.data = data
        self.columns = columns
        self.rows_per_page = rows_per_page
        self.current_page = 1
        self.total_pages = (len(data) - 1) // rows_per_page + 1
    
    def create_table_content(self):
        """テーブルコンテンツ作成"""
        # 現在ページのデータ
        start_idx = (self.current_page - 1) * self.rows_per_page
        end_idx = start_idx + self.rows_per_page
        current_data = self.data[start_idx:end_idx]
        
        # テーブル本体
        with ui.element('div').style('flex: 1; overflow: auto;'):
            with ui.table(
                columns=self.columns,
                rows=current_data,
                row_key='id'
            ).style('width: 100%; margin: 0; font-size: 11px;').props('dense flat bordered'):
                # 高密度テーブルスタイル
                ui.add_head_html('''
                <style>
                .q-table thead th {
                    background: #3b82f6 !important;
                    color: white !important;
                    font-weight: bold !important;
                    font-size: 11px !important;
                    padding: 6px 8px !important;
                }
                .q-table tbody td {
                    padding: 4px 8px !important;
                    font-size: 11px !important;
                    line-height: 1.2 !important;
                }
                .q-table tbody tr {
                    height: 28px !important;
                }
                </style>
                ''')
        
        # ページネーション
        with ui.element('div').style(
            'height: 36px; background: #f8f9fa; '
            'border-top: 1px solid #e5e7eb; '
            'display: flex; align-items: center; '
            'justify-content: space-between; '
            'padding: 0 12px; font-size: 12px; '
            'color: #374151; flex-shrink: 0;'
        ):
            # 表示範囲
            start_num = start_idx + 1
            end_num = min(end_idx, len(self.data))
            ui.label(f'{start_num}-{end_num} of {len(self.data)} items')
            
            # ページングボタン
            with ui.element('div').style('display: flex; gap: 4px;'):
                # 前ページボタン
                prev_btn = ui.button('◀', color='grey' if self.current_page == 1 else 'primary')
                prev_btn.style('padding: 2px 8px; font-size: 10px; min-width: 20px;')
                
                # ページ番号ボタン
                for page in range(1, min(self.total_pages + 1, 4)):  # 最大3ページまで表示
                    page_btn = ui.button(
                        str(page), 
                        color='primary' if page == self.current_page else 'grey'
                    )
                    page_btn.style('padding: 2px 8px; font-size: 10px; min-width: 20px;')
                
                # 次ページボタン
                next_btn = ui.button('▶', color='grey' if self.current_page == self.total_pages else 'primary')
                next_btn.style('padding: 2px 8px; font-size: 10px; min-width: 20px;')

# パネル作成ヘルパー関数
def create_data_panel(title: str, header_gradient: str, **kwargs) -> PanelComponent:
    """データ表示パネル作成"""
    return PanelComponent(
        title=title,
        header_gradient=header_gradient,
        header_buttons=[
            {'icon': '📈', 'action': lambda: print('Chart clicked')},
            {'icon': '⚙️', 'action': lambda: print('Settings clicked')}
        ],
        **kwargs
    )

def create_user_table_panel(users_data: List[Dict[str, Any]], **kwargs) -> DataTablePanel:
    """ユーザーテーブルパネル作成"""
    columns = [
        {'name': 'id', 'label': 'ID', 'field': 'id', 'align': 'center'},
        {'name': 'name', 'label': '名前', 'field': 'name', 'align': 'left'},
        {'name': 'email', 'label': 'メール', 'field': 'email', 'align': 'left'},
        {'name': 'role', 'label': '役割', 'field': 'role', 'align': 'center'},
        {'name': 'status', 'label': 'ステータス', 'field': 'status', 'align': 'center'},
        {'name': 'last_login', 'label': '最終ログイン', 'field': 'last_login', 'align': 'center'}
    ]
    
    return DataTablePanel(
        title="👥 ユーザー管理",
        data=users_data,
        columns=columns,
        header_gradient="linear-gradient(135deg, #f093fb 0%, #f5576c 100%)",
        header_buttons=[
            {'icon': '➕', 'action': lambda: print('Add user')},
            {'icon': '📝', 'action': lambda: print('Edit user')}
        ],
        footer_left=f"👥 {len(users_data)}名のユーザー",
        footer_right="最終同期: 15:30",
        **kwargs
    )

def create_task_panel(**kwargs) -> PanelComponent:
    """タスク管理パネル作成"""
    return PanelComponent(
        title="📝 タスク管理",
        header_gradient="linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)",
        header_buttons=[
            {'icon': '✅', 'action': lambda: print('Complete task')},
            {'icon': '📋', 'action': lambda: print('View all tasks')}
        ],
        footer_left="📝 6件のタスク",
        footer_right="更新: 15:32",
        **kwargs
    )

def create_log_panel(**kwargs) -> PanelComponent:
    """システムログパネル作成"""
    return PanelComponent(
        title="💬 システムログ",
        header_gradient="linear-gradient(135deg, #fa709a 0%, #fee140 100%)",
        header_buttons=[
            {'icon': '🔄', 'action': lambda: print('Refresh logs')},
            {'icon': '🗑️', 'action': lambda: print('Clear logs')}
        ],
        footer_left="💬 ログ: 6件",
        footer_right="最新: 15:35",
        footer_background="#374151",
        **kwargs
    )

class PaginationManager:
    """
    共通ページネーション管理クラス
    
    汎用的なページネーション機能を提供
    テーブル、リスト、カード表示などに対応
    """
    
    def __init__(self, 
                 data: List[Dict[str, Any]],
                 rows_per_page: int = 15,
                 container_id: str = "pagination-container"):
        """
        ページネーション初期化
        
        Args:
            data: 全データ
            rows_per_page: 1ページあたりの表示件数
            container_id: ページネーションコンテナのID
        """
        self.data = data
        self.rows_per_page = rows_per_page
        self.container_id = container_id
        self.current_page = 1
        self.total_pages = (len(data) - 1) // rows_per_page + 1 if data else 1
        
    def get_current_page_data(self) -> List[Dict[str, Any]]:
        """現在ページのデータを取得"""
        start_idx = (self.current_page - 1) * self.rows_per_page
        end_idx = start_idx + self.rows_per_page
        return self.data[start_idx:end_idx]
    
    def create_pagination_ui(self, item_name: str = "items") -> None:
        """ページネーションUI作成"""
        start_idx = (self.current_page - 1) * self.rows_per_page + 1
        end_idx = min(self.current_page * self.rows_per_page, len(self.data))
        
        with ui.element('div').style(
            'height: 36px; background: #f8f9fa; '
            'border-top: 1px solid #e5e7eb; '
            'display: flex; align-items: center; '
            'justify-content: space-between; '
            'padding: 0 12px; font-size: 12px; '
            'color: #374151; flex-shrink: 0;'
        ).props(f'id="{self.container_id}"'):
            
            # 表示範囲情報
            with ui.element('div').props('id="pagination-info"'):
                ui.label(f'{start_idx}-{end_idx} of {len(self.data)} {item_name}')
            
            # ページングボタン
            with ui.element('div').style('display: flex; gap: 4px;').props('id="pagination-buttons"'):
                # 前ページボタン
                prev_color = 'grey' if self.current_page == 1 else 'primary'
                ui.button('◀', color=prev_color).style(
                    'padding: 2px 8px; font-size: 10px; min-width: 20px;'
                ).props(f'id="prev-btn" onclick="changePage(-1)"')
                
                # ページ番号ボタン
                for page in range(1, min(self.total_pages + 1, 4)):  # 最大3ページ表示
                    page_color = 'primary' if page == self.current_page else 'grey'
                    ui.button(str(page), color=page_color).style(
                        'padding: 2px 8px; font-size: 10px; min-width: 20px;'
                    ).props(f'id="page-{page}" onclick="goToPage({page})"')
                
                # 次ページボタン
                next_color = 'grey' if self.current_page == self.total_pages else 'primary'
                ui.button('▶', color=next_color).style(
                    'padding: 2px 8px; font-size: 10px; min-width: 20px;'
                ).props(f'id="next-btn" onclick="changePage(1)"')
    
    def generate_pagination_js(self, 
                              table_update_function: str = "updateTable",
                              table_body_id: str = "table-body") -> str:
        """ページネーション用JavaScript生成"""
        
        data_js = str(self.data).replace("'", '"')  # Python dict → JSON変換
        
        return f'''
        <script>
        // ページネーション用グローバル変数
        let currentPage = {self.current_page};
        let totalPages = {self.total_pages};
        let rowsPerPage = {self.rows_per_page};
        
        // 全データ
        const allData = {data_js};
        
        function updatePaginationInfo() {{
            const startIdx = (currentPage - 1) * rowsPerPage + 1;
            const endIdx = Math.min(currentPage * rowsPerPage, allData.length);
            const infoElement = document.querySelector('#{self.container_id} #pagination-info label');
            if (infoElement) {{
                infoElement.textContent = `${{startIdx}}-${{endIdx}} of ${{allData.length}} items`;
            }}
        }}
        
        function updatePaginationButtons() {{
            // 前ページボタン
            const prevBtn = document.getElementById('prev-btn');
            if (prevBtn) {{
                if (currentPage === 1) {{
                    prevBtn.style.opacity = '0.5';
                    prevBtn.style.pointerEvents = 'none';
                }} else {{
                    prevBtn.style.opacity = '1';
                    prevBtn.style.pointerEvents = 'auto';
                }}
            }}
            
            // 次ページボタン
            const nextBtn = document.getElementById('next-btn');
            if (nextBtn) {{
                if (currentPage === totalPages) {{
                    nextBtn.style.opacity = '0.5';
                    nextBtn.style.pointerEvents = 'none';
                }} else {{
                    nextBtn.style.opacity = '1';
                    nextBtn.style.pointerEvents = 'auto';
                }}
            }}
            
            // ページ番号ボタン更新
            for (let i = 1; i <= Math.min(totalPages, 3); i++) {{
                const pageBtn = document.getElementById(`page-${{i}}`);
                if (pageBtn) {{
                    if (i === currentPage) {{
                        pageBtn.classList.add('bg-primary');
                        pageBtn.classList.remove('bg-grey-5');
                    }} else {{
                        pageBtn.classList.remove('bg-primary');
                        pageBtn.classList.add('bg-grey-5');
                    }}
                }}
            }}
        }}
        
        function changePage(direction) {{
            const newPage = currentPage + direction;
            if (newPage >= 1 && newPage <= totalPages) {{
                currentPage = newPage;
                const startIdx = (currentPage - 1) * rowsPerPage;
                const endIdx = startIdx + rowsPerPage;
                const pageData = allData.slice(startIdx, endIdx);
                
                {table_update_function}(pageData);
                updatePaginationInfo();
                updatePaginationButtons();
                
                console.log(`Changed to page ${{currentPage}}`);
            }}
        }}
        
        function goToPage(page) {{
            if (page >= 1 && page <= totalPages && page !== currentPage) {{
                currentPage = page;
                const startIdx = (currentPage - 1) * rowsPerPage;
                const endIdx = startIdx + rowsPerPage;
                const pageData = allData.slice(startIdx, endIdx);
                
                {table_update_function}(pageData);
                updatePaginationInfo();
                updatePaginationButtons();
                
                console.log(`Went to page ${{currentPage}}`);
            }}
        }}
        
        // 初期化
        setTimeout(() => {{
            updatePaginationButtons();
            console.log('Pagination initialized');
        }}, 500);
        </script>
        '''