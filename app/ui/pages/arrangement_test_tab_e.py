"""配置テスト - タブE: チャットレイアウト実験（Splitter対応）"""

from nicegui import ui
from typing import Optional
from app.ui.components.elements import CommonPanel, ChatSearchResultCard, ChatLayoutButton, ChatSettingsPanel

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
        """ファイル一覧テーブル - NiceGUI ui.table使用"""
        with CommonPanel(
            title="📁 ファイル一覧（ui.table版）",
            gradient="linear-gradient(135deg, #4ade80 0%, #3b82f6 100%)",
            width="100%",
            height="100%"
        ) as panel:
            # パネルのコンテンツエリアのpaddingを調整
            panel.content_element.style('padding: 8px;')
            
            # ダミーデータを生成（files.pyの構造を踏襲）
            self.table_data = self._create_dummy_file_data()
            
            # ui.tableのカラム定義
            columns = [
                {'name': 'select', 'label': '', 'field': 'select', 'sortable': False, 'align': 'center'},
                {'name': 'filename', 'label': 'ファイル名', 'field': 'filename', 'sortable': True, 'align': 'left'},
                {'name': 'size', 'label': 'サイズ', 'field': 'size', 'sortable': True, 'align': 'center'},
                {'name': 'status', 'label': 'ステータス', 'field': 'status', 'sortable': True, 'align': 'center'},
                {'name': 'created_at', 'label': '作成日時', 'field': 'created_at', 'sortable': True, 'align': 'center'},
                {'name': 'actions', 'label': '操作', 'field': 'actions', 'sortable': False, 'align': 'center'}
            ]
            
            # データ行の準備（チェックボックスとアクションボタンを含む）
            rows = []
            for item in self.table_data:
                row = {
                    'select': '',  # チェックボックス用（後でカスタムレンダリング）
                    'filename': item['filename'],
                    'size': item['size'],
                    'status': item['status'],
                    'created_at': item['created_at'],
                    'actions': '',  # アクションボタン用（後でカスタムレンダリング）
                    'id': item['id']  # 行識別用
                }
                rows.append(row)
            
            # テーブル作成
            self.file_table = ui.table(
                columns=columns,
                rows=rows,
                row_key='id',
                pagination={'rowsPerPage': 10, 'sortBy': 'created_at', 'descending': True}
            ).style('width: 100%; height: 100%;')
            
            # カスタムスロットでチェックボックスとアクションボタンをレンダリング
            self._setup_table_slots()
            
            # テーブルヘッダーのスタイル調整
            self.file_table.add_slot('header', '''
                <template v-slot:header="props">
                    <q-tr :props="props">
                        <q-th auto-width />
                        <q-th v-for="col in props.cols" :key="col.name" :props="props" 
                              :style="col.name === 'select' ? 'width: 40px;' : 
                                     col.name === 'actions' ? 'width: 120px;' : ''"
                              class="text-weight-bold" style="background-color: #e5e7eb;">
                            {{ col.label }}
                        </q-th>
                    </q-tr>
                </template>
            ''')
    
    def _create_dummy_file_data(self):
        """ダミーのファイルデータ（files.pyの構造を踏襲）"""
        import datetime
        
        statuses = ['処理完了', '処理中', '未処理', '未整形', '未ベクトル化']
        files = []
        
        # 40件のダミーデータを生成
        for i in range(40):
            now = datetime.datetime.now()
            created = now - datetime.timedelta(days=i, hours=i % 24)
            
            files.append({
                'id': f'file-{i+1}',
                'filename': f'document_{i+1:03d}.pdf',
                'size': f'{(i+1) * 123 % 9999}KB',
                'status': statuses[i % len(statuses)],
                'created_at': created.strftime('%Y-%m-%d %H:%M'),
                'content_type': 'application/pdf'
            })
        
        return files
    
    def _setup_table_slots(self):
        """テーブルのカスタムスロット設定"""
        # チェックボックス列のカスタムレンダリング
        self.file_table.add_slot('body-cell-select', '''
            <template v-slot:body-cell-select="props">
                <q-td :props="props">
                    <q-checkbox v-model="props.row.selected" 
                                @input="$parent.$emit('selection-change', props.row)"
                                dense />
                </q-td>
            </template>
        ''')
        
        # ステータス列のカスタムレンダリング（バッジ風）
        self.file_table.add_slot('body-cell-status', '''
            <template v-slot:body-cell-status="props">
                <q-td :props="props">
                    <q-badge :color="props.value === '処理完了' ? 'green' :
                                    props.value === '処理中' ? 'blue' :
                                    props.value === '未処理' ? 'grey' :
                                    props.value === '未整形' ? 'orange' :
                                    props.value === '未ベクトル化' ? 'purple' :
                                    props.value === 'エラー' ? 'red' : 'grey'" 
                             :label="props.value" 
                             style="padding: 4px 8px;" />
                </q-td>
            </template>
        ''')
        
        # アクション列のカスタムレンダリング
        self.file_table.add_slot('body-cell-actions', '''
            <template v-slot:body-cell-actions="props">
                <q-td :props="props">
                    <div style="display: flex; gap: 4px; justify-content: center;">
                        <q-btn flat round dense icon="visibility" size="sm"
                               @click="$parent.$emit('preview', props.row)"
                               style="color: #6b7280;">
                            <q-tooltip>プレビュー</q-tooltip>
                        </q-btn>
                        <q-btn flat round dense icon="info" size="sm"
                               @click="$parent.$emit('info', props.row)"
                               style="color: #6b7280;">
                            <q-tooltip>詳細情報</q-tooltip>
                        </q-btn>
                        <q-btn flat round dense icon="delete" size="sm"
                               @click="$parent.$emit('delete', props.row)"
                               style="color: #ef4444;">
                            <q-tooltip>削除</q-tooltip>
                        </q-btn>
                    </div>
                </q-td>
            </template>
        ''')
        
        # イベントハンドラーの設定
        self.file_table.on('selection-change', lambda e: self._handle_selection_change(e.args))
        self.file_table.on('preview', lambda e: self._handle_preview(e.args))
        self.file_table.on('info', lambda e: self._handle_info(e.args))
        self.file_table.on('delete', lambda e: self._handle_delete(e.args))
    
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
    
    # テーブル関連のハンドラーメソッド
    def _handle_selection_change(self, row):
        """チェックボックス選択変更時の処理"""
        selected_count = sum(1 for item in self.table_data if item.get('selected', False))
        print(f"選択変更: {row['filename']} - 選択数: {selected_count}")
    
    def _handle_preview(self, row):
        """プレビューボタンクリック時の処理"""
        ui.notify(f"プレビュー: {row['filename']}", type='info')
        print(f"ファイルプレビュー: {row}")
    
    def _handle_info(self, row):
        """詳細情報ボタンクリック時の処理"""
        ui.notify(f"詳細情報: {row['filename']}", type='info')
        print(f"ファイル詳細情報: {row}")
    
    def _handle_delete(self, row):
        """削除ボタンクリック時の処理"""
        ui.notify(f"削除: {row['filename']}", type='warning')
        print(f"ファイル削除: {row}")