"""
表示関連の共通コンポーネント
Table、FormElements
"""
from nicegui import ui
from typing import List, Dict, Any, Optional, Callable


class CommonTable:
    """
    共通テーブルコンポーネント（NiceGUI公式準拠）
    
    機能:
    - ヘッダー固定・スクロール対応
    - ページネーション内蔵
    - 行ホバー効果
    - カスタマイズ可能なカラム設定
    
    Usage:
        table = CommonTable(
            columns=[
                {'key': 'id', 'label': 'ID', 'width': '60px', 'align': 'center'},
                {'key': 'name', 'label': '名前', 'width': '1fr'}
            ],
            data=users_data,
            rows_per_page=15
        )
        table.render()
    """
    
    def __init__(
        self,
        columns: List[Dict[str, str]],
        data: List[Dict[str, Any]],
        rows_per_page: int = 15,
        header_color: str = "#3b82f6",
        row_hover_color: str = "#f8f9fa"
    ):
        self.columns = columns
        self.data = data
        self.rows_per_page = rows_per_page
        self.header_color = header_color
        self.row_hover_color = row_hover_color
        self.current_page = 1
        self.total_pages = (len(data) - 1) // rows_per_page + 1 if data else 1
        self.table_id = f"common-table-{id(self)}"
    
    def render(self):
        """テーブル描画"""
        with ui.element('div').style(
            'height: 100%; display: flex; flex-direction: column; overflow: hidden;'
        ):
            # テーブル本体
            with ui.element('div').style('flex: 1; overflow: auto;'):
                self._create_table()
            
            # ページネーション
            self._create_pagination()
            
            # JavaScript追加
            self._add_table_js()
    
    def _create_table(self):
        """テーブル本体作成"""
        # グリッドカラム設定
        grid_columns = ' '.join([col.get('width', '1fr') for col in self.columns])
        
        # ヘッダー固定コンテナ
        with ui.element('div').style(
            'width: 100%; height: 100%; '
            'display: flex; flex-direction: column; '
            'overflow: hidden;'
        ).props(f'id="{self.table_id}-container"'):
            
            # ヘッダー（固定・スクロールバー幅考慮）
            with ui.element('div').style(
                f'flex-shrink: 0; background: {self.header_color}; '
                f'color: white; font-weight: bold; '
                f'font-size: 11px; border-bottom: 1px solid #e5e7eb; '
                f'padding-right: 17px; box-sizing: border-box;'
            ):
                with ui.element('div').style(
                    f'display: grid; '
                    f'grid-template-columns: {grid_columns}; '
                    f'gap: 0; padding: 0;'
                ):
                    for col in self.columns:
                        align_style = 'text-align: center;' if col.get('align') == 'center' else ''
                        with ui.element('div').style(
                            f'padding: 6px 8px; '
                            f'border-right: 1px solid rgba(255,255,255,0.2); '
                            f'{align_style} '
                            f'background: {self.header_color};'
                        ):
                            ui.label(col['label'])
            
            # テーブル本体（スクロール可能）
            with ui.element('div').style(
                'flex: 1; overflow-y: auto; overflow-x: auto; '
                'border: 1px solid #e5e7eb;'
            ).props(f'id="{self.table_id}-body"'):
                self._create_table_rows()
    
    def _create_table_rows(self):
        """テーブル行作成"""
        start_idx = (self.current_page - 1) * self.rows_per_page
        end_idx = min(start_idx + self.rows_per_page, len(self.data))
        current_page_data = self.data[start_idx:end_idx]
        
        grid_columns = ' '.join([col.get('width', '1fr') for col in self.columns])
        
        for row in current_page_data:
            with ui.element('div').style(
                f'display: grid; '
                f'grid-template-columns: {grid_columns}; '
                f'gap: 0; padding: 0; '
                f'border-bottom: 1px solid #f3f4f6; '
                f'transition: background 0.2s; '
                f'min-height: 28px;'
            ).props(f'onmouseover="this.style.background=\'{self.row_hover_color}\'" onmouseout="this.style.background=\'white\'"'):
                
                for col in self.columns:
                    align_style = 'text-align: center;' if col.get('align') == 'center' else ''
                    justify_style = 'justify-content: center;' if col.get('align') == 'center' else ''
                    
                    with ui.element('div').style(
                        f'padding: 4px 8px; border-right: 1px solid #f3f4f6; '
                        f'font-size: 11px; display: flex; align-items: center; '
                        f'{align_style} {justify_style}'
                    ):
                        # セル内容
                        cell_value = row.get(col['key'], '')
                        
                        # 特殊レンダリング（役割・ステータス等）
                        if col.get('render_type') == 'badge':
                            self._render_badge_cell(cell_value, col.get('badge_colors', {}))
                        else:
                            ui.label(str(cell_value))
    
    def _render_badge_cell(self, value: str, colors: Dict[str, str]):
        """バッジ形式セル描画"""
        color = colors.get(value, '#6b7280')
        with ui.element('span').style(
            f'background: {color}; color: white; '
            f'padding: 1px 6px; border-radius: 3px; '
            f'font-size: 9px;'
        ):
            ui.label(value)
    
    def _create_pagination(self):
        """ページネーション作成"""
        with ui.element('div').style(
            'height: 36px; background: #f8f9fa; '
            'border-top: 1px solid #e5e7eb; '
            'display: flex; align-items: center; '
            'justify-content: space-between; '
            'padding: 0 12px; font-size: 12px; '
            'color: #374151; flex-shrink: 0;'
        ).props(f'id="{self.table_id}-pagination"'):
            # 情報表示
            with ui.element('div').props(f'id="{self.table_id}-info"'):
                start_idx = (self.current_page - 1) * self.rows_per_page + 1
                end_idx = min(self.current_page * self.rows_per_page, len(self.data))
                ui.label(f'{start_idx}-{end_idx} of {len(self.data)} items')
            
            # ページ操作
            with ui.element('div').style('display: flex; gap: 4px; align-items: center;'):
                # 前ページボタン
                ui.button('◀', color='grey').style(
                    'padding: 2px 8px; font-size: 10px; min-width: 20px;'
                ).props(f'id="{self.table_id}-prev" onclick="changeTablePage(\'{self.table_id}\', -1)"')
                
                # ページ入力
                with ui.element('div').style('display: flex; align-items: center; gap: 4px;'):
                    ui.input(value=str(self.current_page)).style(
                        'width: 40px; height: 24px; font-size: 11px; '
                        'text-align: center; border: 1px solid #d1d5db; '
                        'border-radius: 3px; padding: 2px;'
                    ).props(f'id="{self.table_id}-input" onchange="goToTablePageFromInput(\'{self.table_id}\')" onkeypress="handleTablePageInputEnter(event, \'{self.table_id}\')"')
                    
                    ui.label('/').style('font-size: 11px; color: #6b7280;')
                    
                    ui.label(str(self.total_pages)).style(
                        'font-size: 11px; color: #374151; font-weight: bold;'
                    ).props(f'id="{self.table_id}-max"')
                
                # 次ページボタン
                ui.button('▶', color='grey').style(
                    'padding: 2px 8px; font-size: 10px; min-width: 20px;'
                ).props(f'id="{self.table_id}-next" onclick="changeTablePage(\'{self.table_id}\', 1)"')
    
    def _add_table_js(self):
        """テーブル用JavaScript"""
        data_js = str(self.data).replace("'", '"').replace('True', 'true').replace('False', 'false')
        
        ui.add_head_html(f'''
        <script>
        // テーブルデータ管理
        const tableData_{self.table_id.replace('-', '_')} = {data_js};
        const tableConfig_{self.table_id.replace('-', '_')} = {{
            currentPage: {self.current_page},
            rowsPerPage: {self.rows_per_page},
            totalPages: {self.total_pages},
            columns: {str(self.columns).replace("'", '"')},
            headerColor: "{self.header_color}",
            hoverColor: "{self.row_hover_color}"
        }};
        
        // グローバル関数（テーブル操作）
        function changeTablePage(tableId, direction) {{
            const config = window['tableConfig_' + tableId.replace('-', '_')];
            const data = window['tableData_' + tableId.replace('-', '_')];
            
            const newPage = config.currentPage + direction;
            if (newPage >= 1 && newPage <= config.totalPages) {{
                config.currentPage = newPage;
                updateTableContent(tableId, data, config);
                updateTablePagination(tableId, config);
            }}
        }}
        
        function goToTablePageFromInput(tableId) {{
            const input = document.getElementById(tableId + '-input');
            const config = window['tableConfig_' + tableId.replace('-', '_')];
            const data = window['tableData_' + tableId.replace('-', '_')];
            
            if (input) {{
                const inputPage = parseInt(input.value);
                if (!isNaN(inputPage) && inputPage >= 1 && inputPage <= config.totalPages) {{
                    config.currentPage = inputPage;
                    updateTableContent(tableId, data, config);
                    updateTablePagination(tableId, config);
                }} else {{
                    input.value = config.currentPage;
                }}
            }}
        }}
        
        function handleTablePageInputEnter(event, tableId) {{
            if (event.key === 'Enter') {{
                goToTablePageFromInput(tableId);
            }}
        }}
        
        function updateTableContent(tableId, data, config) {{
            const tableBody = document.getElementById(tableId + '-body');
            if (!tableBody) return;
            
            // 現在ページのデータ
            const startIdx = (config.currentPage - 1) * config.rowsPerPage;
            const endIdx = Math.min(startIdx + config.rowsPerPage, data.length);
            const pageData = data.slice(startIdx, endIdx);
            
            // テーブル本体をクリア
            tableBody.innerHTML = '';
            
            // グリッドカラム設定
            const gridColumns = config.columns.map(col => col.width || '1fr').join(' ');
            
            pageData.forEach(row => {{
                const rowElement = document.createElement('div');
                rowElement.style.cssText = `display: grid; grid-template-columns: ${{gridColumns}}; gap: 0; padding: 0; border-bottom: 1px solid #f3f4f6; transition: background 0.2s; min-height: 28px;`;
                rowElement.onmouseover = () => rowElement.style.background = config.hoverColor;
                rowElement.onmouseout = () => rowElement.style.background = 'white';
                
                config.columns.forEach(col => {{
                    const cellDiv = document.createElement('div');
                    const alignStyle = col.align === 'center' ? 'text-align: center; justify-content: center;' : '';
                    cellDiv.style.cssText = `padding: 4px 8px; border-right: 1px solid #f3f4f6; font-size: 11px; display: flex; align-items: center; ${{alignStyle}}`;
                    
                    const cellValue = row[col.key] || '';
                    
                    if (col.render_type === 'badge' && col.badge_colors) {{
                        const span = document.createElement('span');
                        const color = col.badge_colors[cellValue] || '#6b7280';
                        span.style.cssText = `background: ${{color}}; color: white; padding: 1px 6px; border-radius: 3px; font-size: 9px;`;
                        span.textContent = cellValue;
                        cellDiv.appendChild(span);
                    }} else {{
                        cellDiv.textContent = cellValue;
                    }}
                    
                    rowElement.appendChild(cellDiv);
                }});
                
                tableBody.appendChild(rowElement);
            }});
        }}
        
        function updateTablePagination(tableId, config) {{
            // 情報更新
            const startIdx = (config.currentPage - 1) * config.rowsPerPage + 1;
            const endIdx = Math.min(config.currentPage * config.rowsPerPage, tableData_{self.table_id.replace('-', '_')}.length);
            const infoElement = document.querySelector(`#${{tableId}}-info label`);
            if (infoElement) {{
                infoElement.textContent = `${{startIdx}}-${{endIdx}} of ${{tableData_{self.table_id.replace('-', '_')}.length}} items`;
            }}
            
            // ページ入力更新
            const pageInput = document.getElementById(tableId + '-input');
            if (pageInput) {{
                pageInput.value = config.currentPage;
            }}
            
            // ボタン状態更新
            const prevBtn = document.getElementById(tableId + '-prev');
            const nextBtn = document.getElementById(tableId + '-next');
            
            if (prevBtn) {{
                prevBtn.style.opacity = config.currentPage === 1 ? '0.5' : '1';
            }}
            
            if (nextBtn) {{
                nextBtn.style.opacity = config.currentPage === config.totalPages ? '0.5' : '1';
            }}
        }}
        </script>
        ''')


class CommonFormElements:
    """
    共通フォーム要素コンポーネント（NiceGUI公式準拠）
    
    機能:
    - ボタン・チェックボックス・ラジオボタン・ドロップダウン
    - 統一されたスタイル・色・サイズ
    - バリデーション・状態管理対応
    - アクセシビリティ配慮
    
    Usage:
        CommonFormElements.create_button("保存", color="primary", size="medium")
        CommonFormElements.create_checkbox("同意する", on_change=callback)
        CommonFormElements.create_radio_group("選択肢", ["A", "B", "C"])
        CommonFormElements.create_dropdown("選択", ["オプション1", "オプション2"])
    """
    
    # カラーパレット
    COLORS = {
        'primary': '#3b82f6',
        'secondary': '#6b7280', 
        'success': '#10b981',
        'warning': '#f59e0b',
        'danger': '#ef4444',
        'info': '#06b6d4',
        'light': '#f8f9fa',
        'dark': '#374151'
    }
    
    # サイズ設定
    SIZES = {
        'small': {'padding': '4px 8px', 'font_size': '11px', 'height': '24px'},
        'medium': {'padding': '8px 16px', 'font_size': '14px', 'height': '32px'},
        'large': {'padding': '12px 24px', 'font_size': '16px', 'height': '40px'}
    }
    
    @staticmethod
    def create_button(
        text: str,
        color: str = "primary",
        size: str = "medium",
        variant: str = "solid",  # solid, outline, ghost
        icon: Optional[str] = None,
        disabled: bool = False,
        on_click: Optional[Callable] = None
    ):
        """統一ボタン作成"""
        base_color = CommonFormElements.COLORS.get(color, CommonFormElements.COLORS['primary'])
        size_config = CommonFormElements.SIZES.get(size, CommonFormElements.SIZES['medium'])
        
        # バリアント別スタイル
        if variant == "solid":
            button_style = (
                f'background: {base_color}; color: white; '
                f'border: 1px solid {base_color};'
            )
            hover_style = f'background: {base_color}dd; border-color: {base_color}dd;'
        elif variant == "outline":
            button_style = (
                f'background: transparent; color: {base_color}; '
                f'border: 1px solid {base_color};'
            )
            hover_style = f'background: {base_color}11; color: {base_color};'
        else:  # ghost
            button_style = (
                f'background: transparent; color: {base_color}; '
                f'border: 1px solid transparent;'
            )
            hover_style = f'background: {base_color}11;'
        
        # 無効化スタイル
        disabled_style = 'opacity: 0.5; cursor: not-allowed;' if disabled else ''
        
        # ボタンテキスト
        button_text = f'{icon} {text}' if icon else text
        
        return ui.button(
            button_text,
            on_click=on_click if not disabled else None
        ).style(
            f'{button_style} '
            f'padding: {size_config["padding"]}; '
            f'font-size: {size_config["font_size"]}; '
            f'height: {size_config["height"]}; '
            f'border-radius: 6px; '
            f'font-weight: 500; '
            f'cursor: {"pointer" if not disabled else "not-allowed"}; '
            f'transition: all 0.2s ease; '
            f'display: inline-flex; align-items: center; '
            f'justify-content: center; gap: 4px; '
            f'{disabled_style}'
        ).props(f'onmouseover="this.style.cssText+=\'{hover_style}\'" onmouseout="this.style.cssText=this.style.cssText.replace(\'{hover_style}\',\'\')"' if not disabled else '')
    
    @staticmethod
    def create_checkbox(
        label: str,
        value: bool = False,
        disabled: bool = False,
        on_change: Optional[Callable] = None,
        size: str = "medium"
    ):
        """統一チェックボックス作成"""
        size_config = CommonFormElements.SIZES.get(size, CommonFormElements.SIZES['medium'])
        
        with ui.element('div').style(
            'display: flex; align-items: center; gap: 8px; '
            f'font-size: {size_config["font_size"]}; '
            f'opacity: {"0.5" if disabled else "1"};'
        ):
            checkbox = ui.checkbox(value=value, on_change=on_change).style(
                'margin: 0; accent-color: #3b82f6;'
            )
            
            if disabled:
                checkbox.props('disabled')
            
            ui.label(label).style(
                f'margin: 0; cursor: {"pointer" if not disabled else "not-allowed"}; '
                f'user-select: none;'
            ).props(f'onclick="document.querySelector(\'#{checkbox.id}\').click()"' if not disabled else '')
            
            return checkbox
    
    @staticmethod
    def create_radio_group(
        label: str,
        options: List[str],
        value: Optional[str] = None,
        disabled: bool = False,
        on_change: Optional[Callable] = None,
        layout: str = "horizontal"  # horizontal, vertical
    ):
        """統一ラジオボタングループ作成"""
        with ui.element('div').style('margin-bottom: 8px;'):
            ui.label(label).style(
                'font-weight: 500; margin-bottom: 4px; '
                'display: block; font-size: 14px;'
            )
            
            layout_style = (
                'display: flex; gap: 16px; flex-wrap: wrap;' 
                if layout == "horizontal" 
                else 'display: flex; flex-direction: column; gap: 8px;'
            )
            
            with ui.element('div').style(layout_style):
                radio_group = ui.radio(
                    options=options,
                    value=value,
                    on_change=on_change
                ).style(
                    'margin: 0; accent-color: #3b82f6;'
                )
                
                if disabled:
                    radio_group.props('disabled')
                    radio_group.style('opacity: 0.5;')
                
                return radio_group
    
    @staticmethod
    def create_dropdown(
        label: str,
        options: List[str],
        value: Optional[str] = None,
        placeholder: str = "選択してください",
        disabled: bool = False,
        on_change: Optional[Callable] = None,
        width: str = "200px"
    ):
        """統一ドロップダウン作成"""
        with ui.element('div').style('margin-bottom: 8px;'):
            ui.label(label).style(
                'font-weight: 500; margin-bottom: 4px; '
                'display: block; font-size: 14px;'
            )
            
            dropdown = ui.select(
                options=options,
                value=value,
                on_change=on_change
            ).style(
                f'width: {width}; '
                f'border: 1px solid #d1d5db; '
                f'border-radius: 6px; '
                f'padding: 8px 12px; '
                f'font-size: 14px; '
                f'background: white; '
                f'transition: border-color 0.2s ease; '
                f'opacity: {"0.5" if disabled else "1"};'
            ).props(f'placeholder="{placeholder}"')
            
            if disabled:
                dropdown.props('disabled')
            
            # フォーカススタイル
            dropdown.props(
                'onfocus="this.style.borderColor=\'#3b82f6\'; this.style.boxShadow=\'0 0 0 3px rgba(59, 130, 246, 0.1)\'" ' 
                'onblur="this.style.borderColor=\'#d1d5db\'; this.style.boxShadow=\'none\'"'
            )
            
            return dropdown
    
    @staticmethod
    def create_input(
        label: str,
        value: str = "",
        placeholder: str = "",
        input_type: str = "text",  # text, email, password, number
        disabled: bool = False,
        required: bool = False,
        on_change: Optional[Callable] = None,
        width: str = "200px",
        validation_pattern: Optional[str] = None
    ):
        """統一入力フィールド作成"""
        with ui.element('div').style('margin-bottom: 8px;'):
            label_text = f'{label}{"*" if required else ""}'
            ui.label(label_text).style(
                'font-weight: 500; margin-bottom: 4px; '
                'display: block; font-size: 14px; '
                f'color: {"#ef4444" if required else "#374151"};'
            )
            
            input_field = ui.input(
                value=value,
                placeholder=placeholder,
                on_change=on_change
            ).style(
                f'width: {width}; '
                f'border: 1px solid #d1d5db; '
                f'border-radius: 6px; '
                f'padding: 8px 12px; '
                f'font-size: 14px; '
                f'background: white; '
                f'transition: border-color 0.2s ease; '
                f'opacity: {"0.5" if disabled else "1"};'
            )
            
            # 入力タイプ設定
            if input_type != "text":
                input_field.props(f'type="{input_type}"')
            
            if disabled:
                input_field.props('disabled')
            
            if required:
                input_field.props('required')
            
            if validation_pattern:
                input_field.props(f'pattern="{validation_pattern}"')
            
            # フォーカススタイル
            input_field.props(
                'onfocus="this.style.borderColor=\'#3b82f6\'; this.style.boxShadow=\'0 0 0 3px rgba(59, 130, 246, 0.1)\'" '
                'onblur="this.style.borderColor=\'#d1d5db\'; this.style.boxShadow=\'none\'"'
            )
            
            return input_field
    
    @staticmethod
    def create_form_row(*elements, gap: str = "16px"):
        """フォーム要素の横並び配置"""
        with ui.element('div').style(
            f'display: flex; gap: {gap}; align-items: end; '
            f'flex-wrap: wrap; margin-bottom: 16px;'
        ):
            for element in elements:
                element