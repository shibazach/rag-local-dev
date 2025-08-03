"""
テーブルコンポーネント
Reusable table components with pagination, sorting, and filtering
"""

from nicegui import ui
from typing import List, Dict, Any, Optional, Callable
from app.ui.themes.base import RAGTheme

class RAGTable:
    """統一テーブルコンポーネント"""
    
    def __init__(
        self,
        columns: List[Dict[str, Any]],
        rows: List[Dict[str, Any]] = None,
        title: str = "",
        searchable: bool = True,
        sortable: bool = True,
        pagination: bool = True,
        rows_per_page: int = 10,
        selection: str = "none",  # none, single, multiple
        actions: Optional[List[Dict[str, Any]]] = None,
        on_row_click: Optional[Callable] = None,
        on_selection_change: Optional[Callable] = None,
        height: str = "auto",
        dense: bool = True
    ):
        self.columns = columns
        self.rows = rows or []
        self.title = title
        self.searchable = searchable
        self.sortable = sortable
        self.pagination = pagination
        self.rows_per_page = rows_per_page
        self.selection = selection
        self.actions = actions or []
        self.on_row_click = on_row_click
        self.on_selection_change = on_selection_change
        self.height = height
        self.dense = dense
        
        self.search_term = ""
        self.filtered_rows = self.rows.copy()
        
        self.table_element = self._create_table()
    
    def _create_table(self):
        """テーブル作成"""
        with ui.card().classes('rag-card rag-table'):
            # ヘッダー
            if self.title or self.searchable or self.actions:
                self._create_table_header()
            
            # テーブル本体
            table_element = self._create_table_body()
            
            return table_element
    
    def _create_table_header(self):
        """テーブルヘッダー作成"""
        with ui.row().classes('w-full justify-between items-center mb-4'):
            # 左側：タイトル
            if self.title:
                ui.label(self.title).classes('text-lg font-bold')
            
            # 右側：検索とアクション
            with ui.row().classes('gap-4 items-center'):
                # 検索ボックス
                if self.searchable:
                    ui.input(
                        placeholder='検索...',
                        on_change=self._handle_search
                    ).classes('w-64').props('outlined dense')
                
                # アクションボタン
                for action in self.actions:
                    ui.button(
                        action.get('label', ''),
                        on_click=action.get('handler'),
                        icon=action.get('icon')
                    ).classes('rag-button').props('outline')
    
    def _create_table_body(self):
        """テーブル本体作成"""
        # テーブル設定
        table_props = {
            'columns': self._prepare_columns(),
            'rows': self.filtered_rows,
            'row-key': 'id',
            'pagination': {'rowsPerPage': self.rows_per_page} if self.pagination else False,
            'selection': self.selection
        }
        
        table_element = ui.table(**table_props).classes('w-full')
        
        # スタイル設定
        if self.height != "auto":
            table_element.style(f'height: {self.height}; overflow-y: auto')
        
        if self.dense:
            table_element.props('dense')
        
        # カスタムスロット設定
        self._setup_custom_slots(table_element)
        
        # イベントハンドラー設定
        if self.on_row_click:
            table_element.on('row-click', self.on_row_click)
        
        if self.on_selection_change:
            table_element.on('selection', self.on_selection_change)
        
        return table_element
    
    def _prepare_columns(self) -> List[Dict[str, Any]]:
        """カラム設定準備"""
        prepared_columns = []
        
        for col in self.columns:
            column = {
                'name': col['field'],
                'label': col['label'],
                'field': col['field'],
                'align': col.get('align', 'left'),
                'sortable': col.get('sortable', self.sortable)
            }
            
            # カスタムフォーマット
            if col.get('format'):
                column['format'] = col['format']
            
            prepared_columns.append(column)
        
        return prepared_columns
    
    def _setup_custom_slots(self, table_element):
        """カスタムスロット設定"""
        for col in self.columns:
            # ステータス表示用スロット
            if col.get('type') == 'status':
                table_element.add_slot(f'body-cell-{col["field"]}', f'''
                    <q-td :props="props">
                        <q-badge 
                            :color="props.value.color" 
                            :label="props.value.text" 
                        />
                    </q-td>
                ''')
            
            # アクション用スロット
            elif col.get('type') == 'actions':
                actions_html = []
                for action in col.get('actions', []):
                    color_attr = f'color="{action.get("color", "")}"' if action.get("color") else ""
                    btn_html = f'''
                        <q-btn 
                            flat round 
                            icon="{action.get("icon", "more_vert")}" 
                            size="sm" 
                            @click="$parent.$emit('{action.get("event", "action")}', props.row)"
                            {color_attr}
                        />
                    '''
                    actions_html.append(btn_html)
                
                table_element.add_slot(f'body-cell-{col["field"]}', f'''
                    <q-td :props="props">
                        {''.join(actions_html)}
                    </q-td>
                ''')
                
                # イベントハンドラー登録
                for action in col.get('actions', []):
                    if action.get('handler'):
                        table_element.on(action.get('event', 'action'), action['handler'])
            
            # 日付フォーマット用スロット
            elif col.get('type') == 'date':
                table_element.add_slot(f'body-cell-{col["field"]}', f'''
                    <q-td :props="props">
                        {{{{ new Date(props.value).toLocaleDateString('ja-JP') }}}}
                    </q-td>
                ''')
            
            # ファイルサイズフォーマット用スロット
            elif col.get('type') == 'filesize':
                table_element.add_slot(f'body-cell-{col["field"]}', f'''
                    <q-td :props="props">
                        {{{{ (props.value / 1024 / 1024).toFixed(1) }}}} MB
                    </q-td>
                ''')
    
    def _handle_search(self, e):
        """検索ハンドラー"""
        self.search_term = e.value.lower()
        self._filter_rows()
    
    def _filter_rows(self):
        """行フィルタリング"""
        if not self.search_term:
            self.filtered_rows = self.rows.copy()
        else:
            self.filtered_rows = []
            for row in self.rows:
                # 全カラムから検索
                row_text = " ".join(str(row.get(col['field'], '')) for col in self.columns).lower()
                if self.search_term in row_text:
                    self.filtered_rows.append(row)
        
        # テーブル更新
        self.table_element.rows = self.filtered_rows
    
    def add_row(self, row: Dict[str, Any]):
        """行追加"""
        self.rows.append(row)
        self._filter_rows()
    
    def remove_row(self, row_id: Any):
        """行削除"""
        self.rows = [row for row in self.rows if row.get('id') != row_id]
        self._filter_rows()
    
    def update_row(self, row_id: Any, updated_data: Dict[str, Any]):
        """行更新"""
        for row in self.rows:
            if row.get('id') == row_id:
                row.update(updated_data)
                break
        self._filter_rows()
    
    def set_data(self, new_rows: List[Dict[str, Any]]):
        """データ設定"""
        self.rows = new_rows
        self._filter_rows()
    
    def get_selected_rows(self) -> List[Dict[str, Any]]:
        """選択行取得"""
        return self.table_element.selected or []

class RAGDataTable:
    """高度なデータテーブル（サーバーサイドページネーション対応）"""
    
    def __init__(
        self,
        columns: List[Dict[str, Any]],
        data_loader: Callable[[int, int, str, str], Dict[str, Any]],
        title: str = "",
        rows_per_page: int = 20,
        default_sort: str = "",
        default_order: str = "desc"
    ):
        self.columns = columns
        self.data_loader = data_loader
        self.title = title
        self.rows_per_page = rows_per_page
        self.default_sort = default_sort
        self.default_order = default_order
        
        self.current_page = 1
        self.current_sort = default_sort
        self.current_order = default_order
        self.search_term = ""
        self.total_rows = 0
        self.rows = []
        
        self.table_container = self._create_data_table()
        self.load_data()
    
    def _create_data_table(self):
        """データテーブル作成"""
        with ui.card().classes('rag-card'):
            # ヘッダー
            with ui.row().classes('w-full justify-between items-center mb-4'):
                if self.title:
                    ui.label(self.title).classes('text-lg font-bold')
                
                # 検索
                ui.input(
                    placeholder='検索...',
                    on_change=self._handle_search
                ).classes('w-64').props('outlined dense')
            
            # テーブル
            self.table_element = ui.table(
                columns=self._prepare_columns(),
                rows=[],
                pagination={
                    'rowsPerPage': self.rows_per_page,
                    'page': self.current_page
                }
            ).classes('w-full')
            
            # ページネーションイベント
            self.table_element.on('update:pagination', self._handle_pagination)
            
            # ソートイベント  
            self.table_element.on('update:sort-by', self._handle_sort)
            
            return self.table_element
    
    def _prepare_columns(self) -> List[Dict[str, Any]]:
        """カラム設定準備"""
        prepared_columns = []
        
        for col in self.columns:
            column = {
                'name': col['field'],
                'label': col['label'],
                'field': col['field'],
                'align': col.get('align', 'left'),
                'sortable': col.get('sortable', True)
            }
            prepared_columns.append(column)
        
        return prepared_columns
    
    def load_data(self):
        """データ読み込み"""
        try:
            # データローダー呼び出し
            result = self.data_loader(
                self.current_page,
                self.rows_per_page,
                self.current_sort,
                self.current_order,
                self.search_term
            )
            
            # 結果更新
            self.rows = result.get('rows', [])
            self.total_rows = result.get('total', 0)
            
            # テーブル更新
            self.table_element.rows = self.rows
            self.table_element.pagination = {
                'rowsPerPage': self.rows_per_page,
                'page': self.current_page,
                'rowsNumber': self.total_rows
            }
            
        except Exception as e:
            ui.notify(f'データ読み込みエラー: {e}', type='negative')
    
    def _handle_search(self, e):
        """検索ハンドラー"""
        self.search_term = e.value
        self.current_page = 1
        self.load_data()
    
    def _handle_pagination(self, e):
        """ページネーションハンドラー"""
        self.current_page = e.value.get('page', 1)
        self.rows_per_page = e.value.get('rowsPerPage', 20)
        self.load_data()
    
    def _handle_sort(self, e):
        """ソートハンドラー"""
        if e.value:
            self.current_sort = e.value.get('field', '')
            self.current_order = 'desc' if e.value.get('descending') else 'asc'
        else:
            self.current_sort = self.default_sort
            self.current_order = self.default_order
        
        self.current_page = 1
        self.load_data()
    
    def refresh(self):
        """データ更新"""
        self.load_data()

class RAGStatusTable:
    """ステータス表示特化テーブル"""
    
    def __init__(
        self,
        rows: List[Dict[str, Any]],
        status_field: str = "status",
        title: str = "",
        auto_refresh: bool = False,
        refresh_interval: int = 5
    ):
        self.rows = rows
        self.status_field = status_field
        self.title = title
        self.auto_refresh = auto_refresh
        self.refresh_interval = refresh_interval
        
        self.table_element = self._create_status_table()
        
        if self.auto_refresh:
            self._setup_auto_refresh()
    
    def _create_status_table(self):
        """ステータステーブル作成"""
        columns = [
            {'name': 'name', 'label': '名前', 'field': 'name', 'align': 'left'},
            {'name': 'status', 'label': 'ステータス', 'field': self.status_field, 'align': 'center'},
            {'name': 'updated', 'label': '更新日時', 'field': 'updated_at', 'align': 'center'}
        ]
        
        table = RAGTable(
            columns=columns,
            rows=self.rows,
            title=self.title,
            pagination=False,
            dense=True,
            height="400px"
        )
        
        return table.table_element
    
    def _setup_auto_refresh(self):
        """自動更新設定"""
        # TODO: 自動更新タイマー実装
        pass
    
    def update_status(self, item_id: str, new_status: str):
        """ステータス更新"""
        for row in self.rows:
            if row.get('id') == item_id:
                row[self.status_field] = RAGTheme.create_status_badge(new_status)
                break
        
        # テーブル更新
        self.table_element.rows = self.rows