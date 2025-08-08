"""ファイル管理ページ - ui.table版"""

from nicegui import ui
from app.ui.components.layout import RAGHeader, RAGFooter, MainContentArea
from app.ui.components.elements import CommonPanel
from app.ui.components.base.button import BaseButton
from app.core.db_simple import get_file_list
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
    
    def render(self):
        """ページレンダリング"""
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
            
            # ファイルデータをロード
            self._load_file_data()
            
            # データグリッドをコンテンツに追加
            with self.panel.content_element:
                self._setup_data_grid()
    
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
        
        # ui.table作成（シンプル版）
        self.file_table = ui.table(
            columns=columns,
            rows=self.file_data,
            row_key='id',
            pagination=20  # シンプルなページネーション設定
        ).classes('w-full sticky-header-table').style(
            'height: 100%; margin: 0; '
        ).props('dense flat virtual-scroll :virtual-scroll-sticky-size-start="48"')
        
        # 行ダブルクリックイベントの追加
        self.file_table.on('row-dblclick', lambda e: self._on_row_double_click(e.args[1]))
    
    def _create_pdf_preview_pane(self):
        """PDFプレビューペイン（chatの右下ペインと同構造）"""
        # ヘッダーなしの直接コンテンツ表示
        with ui.element('div').style(
            'width: 100%; height: 100%; '
            'background: white; border-radius: 12px; '
            'box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15); '
            'border: 1px solid #e5e7eb; '
            'display: flex; flex-direction: column; '
            'overflow: hidden;'  # paddingを削除（ocr_adjustment.pyと同じ）
        ):
            # PDFビューアエリア
            self.preview_container = ui.element('div').style(
                'height: 100%; background: #f3f4f6; '
                'display: flex; align-items: center; justify-content: center;'
            )
            with self.preview_container:
                with ui.element('div').style('text-align: center; color: #6b7280;'):
                    ui.icon('picture_as_pdf', size='48px').style('margin-bottom: 12px;')
                    ui.label('PDFプレビュー').style('font-size: 16px; font-weight: 500; margin-bottom: 4px;')
                    ui.label('ファイルを選択してプレビューを表示').style('font-size: 12px;')
    
    def _on_row_double_click(self, row_data):
        """行ダブルクリック時の処理"""
        if row_data and 'raw_data' in row_data:
            file_id = row_data['raw_data'].get('file_id')
            filename = row_data.get('filename', '')
            
            # PDFファイルかチェック
            if filename.lower().endswith('.pdf'):
                # プレビューエリアをクリア
                self.preview_container.clear()
                
                # プレビュー表示
                with self.preview_container:
                    with ui.element('div').style('padding: 20px; text-align: center;'):
                        ui.icon('picture_as_pdf', size='48px', color='blue-6').style('margin-bottom: 16px;')
                        ui.label(f'📄 {filename}').style(
                            'font-size: 18px; font-weight: bold; margin-bottom: 8px; color: #1f2937;'
                        )
                        ui.label(f'ファイルID: {file_id}').style(
                            'font-size: 12px; color: #6b7280; margin-bottom: 16px;'
                        )
                        ui.label('🔍 PDFプレビュー機能は現在実装中です').style(
                            'color: #3b82f6; font-size: 14px;'
                        )
                        # 将来的にはここにPDFビューアを実装
            else:
                ui.notify(f'PDFファイルではありません: {filename}', type='warning')
    
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
    
