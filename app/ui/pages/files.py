"""ファイル管理ページ - ui.table版"""

from nicegui import ui
from app.ui.components.layout import RAGHeader, RAGFooter, MainContentArea
from app.ui.components.elements import CommonPanel, CommonSplitter
from app.ui.components.base.button import BaseButton
from app.ui.components.pdf_viewer import PDFViewer, PDFViewerDialog
from app.core.db_simple import get_file_list
from app.services.file_service import get_file_service
import logging
import traceback

logger = logging.getLogger(__name__)

class FilesPage:
    def __init__(self):
        """ファイルページの初期化"""
        self.file_data = []
        self.original_data = []
        self.status_filter = '全て'
        self.search_query = ''
        self.selected_files = set()
        self.selected_count_label = None
        self.pdf_dialog = None
        self.pdf_viewer = None
        self.file_service = get_file_service()
        self.data_table = None
    
    def render(self):
        """ページレンダリング"""
        # 認証チェック
        from app.auth.session import SessionManager
        
        current_user = SessionManager.get_current_user()
        if not current_user:
            ui.navigate.to('/login?redirect=/files')
            return
        
        RAGHeader(current_page="files")
        
        with MainContentArea():
            self._create_layout()
        
        RAGFooter()
    
    def _create_layout(self):
        """レイアウト作成 - スプリッター分割"""
        from app.ui.components.common.layout import CommonSplitter
        
        # テーブルヘッダー固定用のスタイル
        ui.add_sass('''
        .sticky-header-table
          thead tr:first-child th
            background-color: #f3f4f6
          thead tr th
            position: sticky
            z-index: 11
          thead tr:first-child th
            top: 0
        ''')
        
        # スプリッタースタイルとJSを追加
        CommonSplitter.add_splitter_styles()
        CommonSplitter.add_splitter_javascript()
        
        # レイアウトコンテナ
        with ui.element('div').style(
            'width: 100%; height: 100%; '
            'display: flex; flex-direction: row; '
            'margin: 0; padding: 4px; gap: 4px;'  # upload.pyと同じ設定
        ):
            # 左ペイン：ファイル一覧（50%幅）
            with ui.element('div').style(
                'width: 50%; height: 100%; '
                'display: flex; flex-direction: column;'
            ).props('id="files-left-pane"'):
                self._create_file_list_pane()
            
            # 縦スプリッター
            CommonSplitter.create_vertical(splitter_id="files-vsplitter", width="4px")
            
            # 右ペイン：PDFプレビュー（50%幅）
            with ui.element('div').style(
                'width: 50%; height: 100%; '
                'display: flex; flex-direction: column;'
            ).props('id="files-right-pane"'):
                self._create_pdf_preview_pane()
    
    def _create_file_list_pane(self):
        """ファイル一覧ペイン"""
        with CommonPanel(
            title="📁 ファイル一覧",
            gradient="#334155",  # メニューと同じ色
            header_color="white",  # 文字色を白
            width="100%",
            height="100%",
            content_padding="0"  # paddingゼロに
        ) as self.panel:
            # content_elementに追加スタイルを適用
            self.panel.content_element.style('position: relative;')
            # ヘッダーにフィルタリングUI追加
            with self.panel.header_element:
                with ui.element('div').style(
                    'display: flex; gap: 8px; align-items: center; '
                    'flex: 1; margin-right: 8px; height: 100%;'
                ):
                    # ステータスフィルタ
                    self.status_select = ui.select(
                        options=[
                            '全て',
                            '処理完了',
                            '処理中', 
                            '未処理',
                            '未整形',
                            '未ベクトル化',
                            'エラー'
                        ],
                        value=self.status_filter,
                        on_change=lambda e: self._apply_filters()
                    ).style(
                        'width: 120px; flex-shrink: 0; '
                        'background-color: white; color: black; '
                        'border-radius: 0;'  # 角丸をなくす
                    ).props('outlined dense square').classes('q-ma-none')
                    
                    # 検索ボックス
                    self.search_input = ui.input(
                        placeholder='ファイル名で検索...',
                        on_change=lambda e: self._apply_filters()
                    ).style(
                        'flex: 1; min-width: 120px; '
                        'background-color: white; color: black; '
                        'border-radius: 0;'  # 角丸をなくす
                    ).props('outlined dense bg-white square').classes('q-ma-none')
                    
                    # 選択数表示
                    with ui.element('div').style(
                        'display: flex; align-items: center; gap: 4px; '
                        'margin: 0 8px; color: #6b7280; font-size: 14px;'
                    ):
                        ui.label('選択中:').style('margin: 0;')
                        self.selected_count_label = ui.label('0').style('margin: 0; font-weight: 600;')
                        ui.label('件').style('margin: 0;')
            
            # ファイルデータをロード
            self._load_file_data()
            
            # データグリッドをコンテンツに追加
            with self.panel.content_element:
                self._setup_data_grid()
            
            # PDFダイアログを初期化
            self.pdf_dialog = PDFViewerDialog()
    
    def _load_file_data(self):
        """ファイルデータをロード - シンプルDB接続版"""
        try:
            # シンプルなDB接続でファイルリストを取得
            result = get_file_list(limit=1000, offset=0)
            if result and 'files' in result:
                self.file_data = []
                for file in result['files']:
                    # ステータス判定
                    status_value = file.get('status', 'pending')
                    if status_value == 'processed':
                        status = '処理完了'
                    elif status_value == 'processing':
                        status = '処理中'
                    else:
                        status = '未処理'
                    
                    # ファイルサイズのフォーマット
                    size = file.get('file_size', 0)
                    if size < 1024:
                        size_str = f"{size}B"
                    elif size < 1024 * 1024:
                        size_str = f"{size / 1024:.1f}KB"  
                    elif size < 1024 * 1024 * 1024:
                        size_str = f"{size / 1024 / 1024:.1f}MB"
                    else:
                        size_str = f"{size / 1024 / 1024 / 1024:.1f}GB"
                    
                    self.file_data.append({
                        'file_id': file.get('file_id'),
                        'filename': file.get('filename', '不明'),
                        'size': size_str,
                        'status': status,
                        'created_at': file.get('created_at', '').split('T')[0] if file.get('created_at') else '',
                        'raw_data': file  # 元データを保持
                    })
                
                logger.info(f"ファイルデータ読み込み完了: {len(self.file_data)}件")
        except Exception as e:
            logger.error(f"ファイルデータ読み込みエラー: {str(e)}")
            logger.error(f"トレースバック:\n{traceback.format_exc()}")
            ui.notify(f'ファイルデータの読み込みに失敗しました: {str(e)}', type='error')
    
    def _setup_data_grid(self):
        """データグリッド設定 - ui.table版"""
        # データ設定
        self.original_data = self.file_data.copy()
        
        # 各行にIDを追加
        for idx, row in enumerate(self.file_data):
            row['id'] = idx
        
        # カラム定義
        columns = [
            {'name': 'filename', 'label': 'ファイル名', 'field': 'filename', 'sortable': True, 'align': 'left'},
            {'name': 'size', 'label': 'サイズ', 'field': 'size', 'sortable': True, 'align': 'right'},
            {'name': 'status', 'label': 'ステータス', 'field': 'status', 'sortable': True, 'align': 'center'},
            {'name': 'created_at', 'label': '作成日時', 'field': 'created_at', 'sortable': True, 'align': 'center'}
        ]
        
        # デバッグ：最初の3行のデータ構造を確認
        logger.info("=== Table data structure debug ===")
        for i, row in enumerate(self.file_data[:3]):
            logger.info(f"Row {i}: {row}")
            logger.info(f"Row {i} keys: {list(row.keys())}")
        
        # ui.table作成（シンプル版）
        self.file_table = ui.table(
            columns=columns,
            rows=self.file_data,
            row_key='id',
            pagination=20,  # シンプルなページネーション設定
            selection='multiple'  # 複数選択可能
        ).classes('w-full sticky-header-table').style(
            'height: 100%; margin: 0; '
        ).props('dense flat virtual-scroll :virtual-scroll-sticky-size-start="48"')
        
        # 行クリックイベント（選択切り替え）
        self.file_table.on('row-click', self._on_row_click)
        
        # 行ダブルクリックイベント（PDFプレビュー）
        self.file_table.on('row-dblclick', self._on_row_double_click)
        
        # デバッグ用：クリックイベントのデータ構造を確認
        ui.run_javascript('''
            setTimeout(() => {
                const table = document.querySelector('.q-table');
                if (table) {
                    table.addEventListener('dblclick', (e) => {
                        const row = e.target.closest('tr');
                        if (row && row.rowIndex > 0) {
                            console.log('=== Double click debug ===');
                            console.log('Row index:', row.rowIndex - 1);
                            console.log('Row HTML:', row.innerHTML);
                            console.log('Table data available in NiceGUI:', row._vnode);
                        }
                    });
                }
            }, 1000);
        ''')
        
        # 選択変更イベント（選択数更新）
        self.file_table.on('selection', self._on_selection_change)
        
        # データテーブルを保持
        self.data_table = self.file_table
    

    
    async def _on_row_double_click(self, e):
        """行ダブルクリック時の処理 - PDFプレビュー"""
        if e.args:
            logger.info(f"Double click event args in files.py: {e.args}")
            
            if len(e.args) > 0:
                row_data = e.args[0]
                logger.info(f"Row data type: {type(row_data)}")
                logger.info(f"Row data keys: {row_data.keys() if isinstance(row_data, dict) else 'Not a dict'}")
                logger.info(f"Row data: {row_data}")
                
                if isinstance(row_data, dict):
                    # file_idは直接データに含まれているはず
                    file_id = row_data.get('file_id')
                    
                    # もし見つからない場合はraw_dataから探す
                    if not file_id and 'raw_data' in row_data:
                        file_id = row_data.get('raw_data', {}).get('file_id')
                    
                    filename = row_data.get('filename', '')
                    
                    logger.info(f"Extracted file_id: {file_id}, filename: {filename}")
                    logger.info(f"Available keys in row_data: {list(row_data.keys())}")
                    
                    if file_id:
                        try:
                            # ファイル情報を取得してblobデータで判定
                            file_info = self.file_service.get_file_info(file_id)
                            if file_info:
                                blob_data = file_info.get('blob_data')
                                
                                # blobデータの内容でPDF判定
                                is_pdf = self.file_service.is_pdf_by_content(blob_data)
                                
                                logger.info(f"File: {filename}, ID: {file_id}, is_pdf_by_content: {is_pdf}")
                                
                                if is_pdf:
                                    if self.pdf_viewer:
                                        logger.info(f"Loading PDF in preview pane: {filename}")
                                        # 右ペインにPDFを表示
                                        await self.pdf_viewer.load_pdf(file_id, self.file_service)
                                    else:
                                        logger.warning(f"PDF viewer not initialized")
                                        ui.notify("PDFプレビューの初期化に失敗しました", type='error')
                                else:
                                    ui.notify(f"このファイルはPDFではありません: {filename}", type='warning')
                            else:
                                ui.notify(f"ファイル情報を取得できませんでした", type='error')
                        except Exception as ex:
                            logger.error(f"Error checking PDF: {ex}")
                            ui.notify(f"エラーが発生しました: {str(ex)}", type='error')
                    else:
                        ui.notify("ファイルIDが見つかりません", type='error')
    
    def _create_pdf_preview_pane(self):
        """PDFプレビューペイン"""
        with CommonPanel(
            title="📄 PDFプレビュー",
            gradient="#334155",
            header_color="white",
            width="100%",
            height="100%",
            content_padding="0"
        ) as panel:
            # PDFビューアを配置
            self.pdf_viewer = PDFViewer(panel.content_element, height="100%", width="100%")
    
    def _apply_filters(self):
        """フィルタを適用"""
        status_filter = self.status_select.value
        search_query = self.search_input.value.lower()
        
        filtered_data = []
        for row in self.original_data:
            # ステータスフィルタ
            if status_filter != '全て' and row['status'] != status_filter:
                continue
            
            # 検索フィルタ
            if search_query and search_query not in row['filename'].lower():
                continue
            
            filtered_data.append(row)
        
        # 各行のIDを再設定
        for idx, row in enumerate(filtered_data):
            row['id'] = idx
        
        # ui.tableの行データを更新（NiceGUIの標準的な方法）
        self.file_table.rows[:] = filtered_data
        self.file_table.update()
    
    def _on_row_click(self, e):
        """行クリック時の処理 - 選択切り替え"""
        if e.args and len(e.args) > 0:
            row_data = e.args[0]
            file_id = row_data.get('file_id') or (row_data.get('raw_data', {}).get('file_id') if 'raw_data' in row_data else None)
            
            if file_id:
                # 選択状態を切り替え
                if file_id in self.selected_files:
                    self.selected_files.remove(file_id)
                else:
                    self.selected_files.add(file_id)
                
                # テーブルの選択状態を更新
                selected_rows = []
                for row in self.file_table.rows:
                    row_file_id = row.get('file_id') or (row.get('raw_data', {}).get('file_id') if 'raw_data' in row else None)
                    if row_file_id and row_file_id in self.selected_files:
                        selected_rows.append(row)
                
                self.file_table.selected = selected_rows
                self._update_selection_count()
    
    def _on_selection_change(self, e):
        """選択変更時の処理"""
        self.selected_files.clear()
        if e.args:
            for row in e.args:
                file_id = row.get('file_id') or (row.get('raw_data', {}).get('file_id') if 'raw_data' in row else None)
                if file_id:
                    self.selected_files.add(file_id)
        
        self._update_selection_count()
    
    def _update_selection_count(self):
        """選択数を更新"""
        if self.selected_count_label:
            self.selected_count_label.text = str(len(self.selected_files))
    
