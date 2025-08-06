"""
BaseDataGridView - VB DataGridView相当の高機能テーブルコンポーネント
NiceGUI準拠 + リアルタイム追従機能

特徴:
- データ動的変更時の自動総頁数更新
- 表示行数の動的調整（縦サイズ変更対応）
- ページネーション手打ち対応（Enter）
- セル内コントロールの柔軟配置
- 継承可能な設計
"""
from nicegui import ui
from typing import List, Dict, Any, Optional, Callable, Union
from ..base import CommonStyles
import json


class BaseDataGridView:
    """
    VB DataGridView相当の高機能テーブルコンポーネント
    
    Usage:
        grid = BaseDataGridView(
            columns=[
                {'field': 'id', 'label': 'ID', 'width': '60px', 'align': 'center'},
                {'field': 'name', 'label': '名前', 'width': '1fr', 'align': 'left'},
                {'field': 'status', 'label': 'ステータス', 'width': '100px', 'align': 'center',
                 'render_type': 'badge', 'badge_colors': {'active': '#22c55e', 'inactive': '#ef4444'}}
            ],
            height='400px',
            auto_rows=True  # 縦サイズに応じて自動行数調整
        )
        
        # データ設定（リアルタイム更新対応）
        grid.set_data(data_list)
        
        # レンダリング
        grid.render()
        
        # データ追加・更新（自動再描画）
        grid.add_row({'id': 10, 'name': '新規ユーザー', 'status': 'active'})
        grid.update_data(new_data_list)
    """
    
    def __init__(
        self,
        columns: List[Dict[str, str]],
        height: str = "400px",
        auto_rows: bool = True,
        min_rows: int = 5,
        max_rows: int = 50,
        default_rows_per_page: int = 15,
        enable_resize_observer: bool = True,
        on_page_change: Optional[Callable] = None,
        on_cell_click: Optional[Callable] = None,
        header_color: str = "#2563eb",
        row_hover_color: str = "#f8f9fa"
    ):
        self.columns = columns
        self.height = height
        self.auto_rows = auto_rows
        self.min_rows = min_rows
        self.max_rows = max_rows
        self.default_rows_per_page = default_rows_per_page
        self.enable_resize_observer = enable_resize_observer
        self.on_page_change = on_page_change
        self.on_cell_click = on_cell_click
        self.header_color = header_color
        self.row_hover_color = row_hover_color
        
        # データ管理
        self.data: List[Dict[str, Any]] = []
        self.current_page = 1
        self.rows_per_page = default_rows_per_page
        self.total_pages = 1
        
        # 一意ID生成
        self.grid_id = f"base-data-grid-{id(self)}"
        
        # Grid columns CSS定義
        self.grid_columns = ' '.join([col.get('width', '1fr') for col in columns])
        
        # レンダリング済みフラグ
        self._rendered = False
        
    def set_data(self, data: List[Dict[str, Any]]):
        """
        データを設定し、リアルタイム更新を実行
        """
        self.data = data or []
        self._recalculate_pagination()
        
        if self._rendered:
            self._update_grid_data()
    
    def add_row(self, row: Dict[str, Any]):
        """
        行を追加し、自動更新
        """
        self.data.append(row)
        self._recalculate_pagination()
        
        if self._rendered:
            self._update_grid_data()
    
    def update_data(self, data: List[Dict[str, Any]]):
        """
        データを完全更新（set_dataのエイリアス）
        """
        self.set_data(data)
    
    def _recalculate_pagination(self):
        """
        ページネーション情報を再計算
        """
        data_length = len(self.data)
        self.total_pages = max(1, (data_length + self.rows_per_page - 1) // self.rows_per_page)
        
        # 現在ページが範囲外の場合は調整
        if self.current_page > self.total_pages:
            self.current_page = max(1, self.total_pages)
    
    def _calculate_dynamic_rows(self) -> int:
        """
        表示エリアの高さから動的に行数を計算
        """
        if not self.auto_rows:
            return self.default_rows_per_page
            
        # JavaScript側で計算される想定値
        # 実際の実装では ResizeObserver で動的計算
        return self.default_rows_per_page
    
    def render(self):
        """
        DataGridをレンダリング
        """
        self._rendered = True
        
        with ui.element('div').style(
            f'width: 100%; height: {self.height}; '
            'display: flex; flex-direction: column; '
            'overflow: hidden; position: relative; '
            'border: 1px solid #e5e7eb; border-radius: 6px; '
            'background: white;'
        ).props(f'id="{self.grid_id}-container"'):
            
            # ヘッダー
            self._render_header()
            
            # テーブル本体
            self._render_body()
            
            # ページネーション
            self._render_pagination()
            
            # JavaScript初期化
            self._add_grid_javascript()
    
    def _render_header(self):
        """
        ヘッダーをレンダリング
        """
        with ui.element('div').style(
            f'background: {self.header_color}; color: white; '
            f'display: grid; grid-template-columns: {self.grid_columns}; '
            'gap: 0; padding: 0; border-bottom: 2px solid #1e40af; '
            'font-weight: bold; font-size: 12px; '
            'flex-shrink: 0; height: 32px;'
        ).props(f'id="{self.grid_id}-header"'):
            
            for col in self.columns:
                align_style = ''
                if col.get('align') == 'center':
                    align_style = 'text-align: center; justify-content: center;'
                elif col.get('align') == 'right':
                    align_style = 'text-align: right; justify-content: flex-end;'
                else:
                    align_style = 'text-align: left; justify-content: flex-start;'
                
                with ui.element('div').style(
                    f'padding: 8px; border-right: 1px solid rgba(255,255,255,0.3); '
                    f'display: flex; align-items: center; {align_style}'
                ).classes('header-cell'):
                    ui.label(col['label'])
    
    def _render_body(self):
        """
        テーブル本体をレンダリング
        """
        with ui.element('div').style(
            'flex: 1; overflow: auto; position: relative;'
        ).props(f'id="{self.grid_id}-body-container"'):
            
            with ui.element('div').style(
                'width: 100%; min-height: 100%;'
            ).props(f'id="{self.grid_id}-body"'):
                
                # 初期データレンダリング
                self._render_current_page_data()
    
    def _render_current_page_data(self):
        """
        現在ページのデータをレンダリング
        """
        start_idx = (self.current_page - 1) * self.rows_per_page
        end_idx = min(start_idx + self.rows_per_page, len(self.data))
        page_data = self.data[start_idx:end_idx]
        
        for row in page_data:
            self._render_row(row)
        
        # 空行パディング（行埋め機能）
        empty_rows = self.rows_per_page - len(page_data)
        for _ in range(empty_rows):
            self._render_empty_row()
    
    def _render_row(self, row: Dict[str, Any]):
        """
        データ行をレンダリング
        """
        with ui.element('div').style(
            f'display: grid; grid-template-columns: {self.grid_columns}; '
            'gap: 0; padding: 0; border-bottom: 1px solid #f3f4f6; '
            'transition: background 0.2s; min-height: 28px;'
        ).classes('data-row'):
            
            for col in self.columns:
                self._render_cell(row, col)
    
    def _render_cell(self, row: Dict[str, Any], col: Dict[str, str]):
        """
        セルをレンダリング（カスタムレンダリング対応）
        """
        field_value = row.get(col['field'], '')
        
        align_style = ''
        if col.get('align') == 'center':
            align_style = 'text-align: center; justify-content: center;'
        elif col.get('align') == 'right':
            align_style = 'text-align: right; justify-content: flex-end;'
        else:
            align_style = 'text-align: left; justify-content: flex-start;'
        
        with ui.element('div').style(
            f'padding: 4px 8px; border-right: 1px solid #f3f4f6; '
            f'font-size: 11px; display: flex; align-items: center; {align_style}'
        ).classes('data-cell'):
            
            # カスタムレンダリング
            if col.get('render_type') == 'badge':
                self._render_badge_cell(field_value, col.get('badge_colors', {}))
            elif col.get('render_type') == 'button':
                self._render_button_cell(field_value, col, row)
            elif col.get('render_type') == 'checkbox':
                self._render_checkbox_cell(field_value, col, row)
            else:
                # デフォルト: テキスト表示
                ui.label(str(field_value))
    
    def _render_badge_cell(self, value: str, colors: Dict[str, str]):
        """
        バッジ形式でセルをレンダリング
        """
        color = colors.get(value, '#6b7280')
        with ui.element('span').style(
            f'background: {color}; color: white; '
            'padding: 2px 8px; border-radius: 4px; '
            'font-size: 10px; font-weight: bold;'
        ):
            ui.label(value)
    
    def _render_button_cell(self, value: str, col: Dict[str, str], row: Dict[str, Any]):
        """
        ボタン形式でセルをレンダリング
        """
        button_color = col.get('button_color', 'primary')
        ui.button(value, color=button_color).style(
            'padding: 2px 8px; font-size: 10px; min-height: 20px;'
        ).on('click', lambda: self._handle_cell_click(col['field'], row))
    
    def _render_checkbox_cell(self, value: bool, col: Dict[str, str], row: Dict[str, Any]):
        """
        チェックボックス形式でセルをレンダリング
        """
        checkbox = ui.checkbox(value=bool(value))
        checkbox.on('change', lambda e: self._handle_cell_change(col['field'], row, e.value))
    
    def _render_empty_row(self):
        """
        空行をレンダリング（行埋め用）
        """
        with ui.element('div').style(
            f'display: grid; grid-template-columns: {self.grid_columns}; '
            'gap: 0; padding: 0; border-bottom: 1px solid #f9fafb; '
            'min-height: 28px; opacity: 0.5;'
        ).classes('empty-row'):
            
            for _ in self.columns:
                ui.element('div').style(
                    'padding: 4px 8px; border-right: 1px solid #f9fafb;'
                )
    
    def _render_pagination(self):
        """
        ページネーションをレンダリング
        """
        with ui.element('div').style(
            f'height: {CommonStyles.FOOTER_HEIGHT}; '
            f'background: {CommonStyles.COLOR_GRAY_50}; '
            f'border-top: 1px solid {CommonStyles.COLOR_GRAY_200}; '
            'display: flex; align-items: center; '
            'justify-content: space-between; '
            f'padding: 0 {CommonStyles.SPACING_MD}; '
            f'font-size: {CommonStyles.FONT_SIZE_XS}; '
            f'color: {CommonStyles.COLOR_GRAY_700}; '
            'flex-shrink: 0;'
        ).props(f'id="{self.grid_id}-pagination"'):
            
            # データ情報表示
            with ui.element('div').props(f'id="{self.grid_id}-info"'):
                start_idx = (self.current_page - 1) * self.rows_per_page + 1
                end_idx = min(self.current_page * self.rows_per_page, len(self.data))
                if len(self.data) > 0:
                    ui.label(f'{start_idx}-{end_idx} of {len(self.data)} items')
                else:
                    ui.label('No data')
            
            # ページ操作コントロール
            with ui.element('div').style('display: flex; gap: 8px; align-items: center;'):
                # 前ページボタン
                prev_btn = ui.button('◀', color='grey').style(
                    'padding: 2px 8px; font-size: 10px; min-width: 24px; height: 24px;'
                ).props(f'id="{self.grid_id}-prev"')
                prev_btn.on('click', lambda: self._change_page(-1))
                
                # ページ入力（手打ち対応）
                with ui.element('div').style(
                    'display: flex; align-items: center; height: 24px;'
                ):
                    page_input = ui.element('input').style(
                        'width: 50px; height: 20px; font-size: 11px; '
                        'text-align: center; padding: 0 4px; margin: 0; '
                        'border: 1px solid #d1d5db; border-radius: 3px; '
                        'outline: none; box-sizing: border-box;'
                    ).props(
                        f'id="{self.grid_id}-input" '
                        f'type="text" value="{self.current_page}" '
                        'onfocus="this.style.borderColor=\'#3b82f6\'" '
                        'onblur="this.style.borderColor=\'#d1d5db\'"'
                    )
                    
                    # Enterキーでページ遷移
                    page_input.on('keyup.enter', lambda e: self._go_to_page_from_input(e.args['target']['value']))
                    # フォーカスアウト時も適用
                    page_input.on('blur', lambda e: self._go_to_page_from_input(e.args['target']['value']))
                
                ui.label('/').style('font-size: 11px; color: #6b7280;')
                
                ui.label(str(self.total_pages)).style(
                    'font-size: 11px; color: #374151; font-weight: bold;'
                ).props(f'id="{self.grid_id}-max"')
                
                # 次ページボタン
                next_btn = ui.button('▶', color='grey').style(
                    'padding: 2px 8px; font-size: 10px; min-width: 24px; height: 24px;'
                ).props(f'id="{self.grid_id}-next"')
                next_btn.on('click', lambda: self._change_page(1))
    
    def _change_page(self, delta: int):
        """
        ページ変更処理
        """
        new_page = self.current_page + delta
        if 1 <= new_page <= self.total_pages:
            self.current_page = new_page
            self._update_page_display()
            
            if self.on_page_change:
                self.on_page_change(self.current_page)
    
    def _go_to_page_from_input(self, input_value: str):
        """
        手打ちページ入力からページ移動
        """
        try:
            page = int(input_value)
            if 1 <= page <= self.total_pages:
                self.current_page = page
                self._update_page_display()
                
                if self.on_page_change:
                    self.on_page_change(self.current_page)
            else:
                # 無効な入力の場合は元に戻す
                self._update_pagination_ui()
        except ValueError:
            # 数値以外の入力の場合は元に戻す
            self._update_pagination_ui()
    
    def _update_page_display(self):
        """
        ページ表示を更新
        """
        if self._rendered:
            self._update_grid_data()
            self._update_pagination_ui()
    
    def _update_grid_data(self):
        """
        グリッドデータをJavaScript経由で更新
        """
        if not self._rendered:
            return
            
        data_json = json.dumps(self.data, ensure_ascii=False)
        columns_json = json.dumps(self.columns, ensure_ascii=False)
        
        ui.run_javascript(f'''
        window.updateBaseDataGrid(
            "{self.grid_id}",
            {data_json},
            {columns_json},
            {self.current_page},
            {self.rows_per_page},
            {self.total_pages}
        );
        ''')
    
    def _update_pagination_ui(self):
        """
        ページネーションUIを更新
        """
        if not self._rendered:
            return
            
        ui.run_javascript(f'''
        window.updateBaseDataGridPagination(
            "{self.grid_id}",
            {self.current_page},
            {self.total_pages},
            {len(self.data)}
        );
        ''')
    
    def _handle_cell_click(self, field: str, row: Dict[str, Any]):
        """
        セルクリックイベント処理
        """
        if self.on_cell_click:
            self.on_cell_click(field, row)
    
    def _handle_cell_change(self, field: str, row: Dict[str, Any], new_value: Any):
        """
        セル値変更イベント処理
        """
        # データを更新
        row[field] = new_value
        
        # 必要に応じてコールバック呼び出し
        if self.on_cell_click:
            self.on_cell_click(field, row)
    
    def _add_grid_javascript(self):
        """
        DataGrid用JavaScriptを追加
        """
        ui.add_head_html(f'''
        <script>
        // BaseDataGrid グローバル関数
        window.updateBaseDataGrid = function(gridId, data, columns, currentPage, rowsPerPage, totalPages) {{
            const bodyContainer = document.getElementById(gridId + '-body');
            if (!bodyContainer) return;
            
            // 現在ページのデータ計算
            const startIdx = (currentPage - 1) * rowsPerPage;
            const endIdx = Math.min(startIdx + rowsPerPage, data.length);
            const pageData = data.slice(startIdx, endIdx);
            
            // グリッドカラム CSS
            const gridColumns = columns.map(col => col.width || '1fr').join(' ');
            
            // 本体クリア
            bodyContainer.innerHTML = '';
            
            // データ行レンダリング
            pageData.forEach(row => {{
                const rowElement = document.createElement('div');
                rowElement.className = 'data-row';
                rowElement.style.cssText = `display: grid; grid-template-columns: ${{gridColumns}}; gap: 0; padding: 0; border-bottom: 1px solid #f3f4f6; transition: background 0.2s; min-height: 28px;`;
                
                // ホバー効果
                rowElement.onmouseover = () => rowElement.style.background = '#f8f9fa';
                rowElement.onmouseout = () => rowElement.style.background = 'white';
                
                columns.forEach(col => {{
                    const cellDiv = document.createElement('div');
                    const alignStyle = col.align === 'center' ? 'text-align: center; justify-content: center;' : 
                                     col.align === 'right' ? 'text-align: right; justify-content: flex-end;' : 
                                     'text-align: left; justify-content: flex-start;';
                    cellDiv.style.cssText = `padding: 4px 8px; border-right: 1px solid #f3f4f6; font-size: 11px; display: flex; align-items: center; ${{alignStyle}}`;
                    
                    const cellValue = row[col.field] || '';
                    
                    if (col.render_type === 'badge' && col.badge_colors) {{
                        const span = document.createElement('span');
                        const color = col.badge_colors[cellValue] || '#6b7280';
                        span.style.cssText = `background: ${{color}}; color: white; padding: 2px 8px; border-radius: 4px; font-size: 10px; font-weight: bold;`;
                        span.textContent = cellValue;
                        cellDiv.appendChild(span);
                    }} else {{
                        cellDiv.textContent = cellValue;
                    }}
                    
                    rowElement.appendChild(cellDiv);
                }});
                
                bodyContainer.appendChild(rowElement);
            }});
            
            // 空行パディング
            const emptyRows = rowsPerPage - pageData.length;
            for (let i = 0; i < emptyRows; i++) {{
                const emptyRowElement = document.createElement('div');
                emptyRowElement.className = 'empty-row';
                emptyRowElement.style.cssText = `display: grid; grid-template-columns: ${{gridColumns}}; gap: 0; padding: 0; border-bottom: 1px solid #f9fafb; min-height: 28px; opacity: 0.5;`;
                
                columns.forEach(() => {{
                    const emptyCell = document.createElement('div');
                    emptyCell.style.cssText = 'padding: 4px 8px; border-right: 1px solid #f9fafb;';
                    emptyRowElement.appendChild(emptyCell);
                }});
                
                bodyContainer.appendChild(emptyRowElement);
            }}
        }};
        
        window.updateBaseDataGridPagination = function(gridId, currentPage, totalPages, dataLength) {{
            // 情報表示更新
            const infoElement = document.querySelector(`#${{gridId}}-info label`);
            if (infoElement) {{
                const startIdx = (currentPage - 1) * {self.rows_per_page} + 1;
                const endIdx = Math.min(currentPage * {self.rows_per_page}, dataLength);
                if (dataLength > 0) {{
                    infoElement.textContent = `${{startIdx}}-${{endIdx}} of ${{dataLength}} items`;
                }} else {{
                    infoElement.textContent = 'No data';
                }}
            }}
            
            // ページ入力更新
            const pageInput = document.getElementById(gridId + '-input');
            if (pageInput) {{
                pageInput.value = currentPage;
            }}
            
            // 最大ページ数更新
            const maxElement = document.querySelector(`#${{gridId}}-max`);
            if (maxElement) {{
                maxElement.textContent = totalPages;
            }}
            
            // ボタン状態更新
            const prevBtn = document.getElementById(gridId + '-prev');
            const nextBtn = document.getElementById(gridId + '-next');
            
            if (prevBtn) {{
                prevBtn.style.opacity = currentPage === 1 ? '0.5' : '1';
                prevBtn.disabled = currentPage === 1;
            }}
            
            if (nextBtn) {{
                nextBtn.style.opacity = currentPage === totalPages ? '0.5' : '1';
                nextBtn.disabled = currentPage === totalPages;
            }}
        }};
        
        // ResizeObserver for dynamic row calculation (future enhancement)
        if (typeof window.baseDataGridResizeObserver === 'undefined') {{
            window.baseDataGridResizeObserver = new ResizeObserver(entries => {{
                entries.forEach(entry => {{
                    const gridId = entry.target.id.replace('-container', '');
                    if (gridId.startsWith('base-data-grid-')) {{
                        // TODO: 動的行数計算の実装
                        // const newRowsPerPage = calculateRowsFromHeight(entry.contentRect.height);
                        // updateRowsPerPage(gridId, newRowsPerPage);
                    }}
                }});
            }});
        }}
        </script>
        ''')