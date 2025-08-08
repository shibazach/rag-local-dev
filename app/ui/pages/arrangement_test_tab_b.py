"""配置テスト - タブB: NiceGUIコンポーネントショーケース"""

from nicegui import ui

class ArrangementTestTabB:
    """タブB: NiceGUIコンポーネント全サンプル展示"""
    
    def render(self):
        """タブBのコンポーネントショーケースを描画"""
        with ui.element('div').style(
            'width: 100%; height: 100%; '
            'overflow-y: auto; padding: 16px; '
            'background: #f8fafc;'
        ):
            ui.label('🎨 NiceGUI コンポーネント全サンプル').style(
                'font-size: 20px; font-weight: bold; '
                'margin-bottom: 16px; color: #1f2937;'
            )
            
            # セクション1: 基本要素
            self._showcase_basic_elements()
            
            # セクション2: 入力コンポーネント
            self._showcase_input_components()
            
            # セクション3: 表示コンポーネント
            self._showcase_display_components()
            
            # セクション4: レイアウトコンポーネント
            self._showcase_layout_components()
            
            # セクション5: ナビゲーション
            self._showcase_navigation_components()
            
            # セクション6: フィードバック
            self._showcase_feedback_components()
            
            # セクション7: メディア
            self._showcase_media_components()
            
            # セクション8: 高度なコンポーネント
            self._showcase_advanced_components()

    def _showcase_basic_elements(self):
        """基本要素サンプル"""
        with ui.card().style('margin-bottom: 16px; padding: 16px;'):
            ui.label('📝 基本要素').style('font-size: 16px; font-weight: bold; margin-bottom: 12px;')
            
            with ui.row().style('gap: 16px; flex-wrap: wrap;'):
                with ui.column().style('min-width: 200px;'):
                    ui.label('ラベル/テキスト')
                    ui.label('通常ラベル')
                    ui.label('太字ラベル').style('font-weight: bold;')
                    ui.label('色付きラベル').style('color: #3b82f6;')
                    ui.html('<b>HTMLテキスト</b> with <i>formatting</i>')
                    ui.html('<strong>Markdown</strong> テキスト with <code>code</code>')
                
                with ui.column().style('min-width: 200px;'):
                    ui.label('ボタン各種')
                    ui.button('デフォルトボタン')
                    ui.button('プライマリボタン', color='primary')
                    ui.button('セカンダリボタン', color='secondary')
                    ui.button('アクセントボタン', color='accent')
                    ui.button('ポジティブボタン', color='positive')
                    ui.button('ネガティブボタン', color='negative')
                    ui.button('警告ボタン', color='warning')
                    ui.button('情報ボタン', color='info')
                    ui.button('無効ボタン').props('disable')
                
                with ui.column().style('min-width: 200px;'):
                    ui.label('アイコン・バッジ')
                    with ui.row():
                        ui.icon('home', size='sm')
                        ui.icon('star', size='md', color='yellow')
                        ui.icon('favorite', size='lg', color='red')
                    
                    with ui.row():
                        ui.badge('バッジ', color='primary')
                        ui.badge('99+', color='red')
                        ui.badge('NEW', color='green')
                    
                    ui.separator()
                    ui.space()

    def _showcase_input_components(self):
        """入力コンポーネントサンプル"""
        with ui.card().style('margin-bottom: 16px; padding: 16px;'):
            ui.label('📝 入力コンポーネント').style('font-size: 16px; font-weight: bold; margin-bottom: 12px;')
            
            with ui.row().style('gap: 16px; flex-wrap: wrap;'):
                with ui.column().style('min-width: 250px;'):
                    ui.label('テキスト入力')
                    ui.input('テキスト入力', placeholder='プレースホルダー')
                    ui.input('パスワード', password=True, password_toggle_button=True)
                    ui.textarea('テキストエリア', placeholder='複数行テキスト')
                    ui.number('数値入力', value=42, min=0, max=100)
                    
                with ui.column().style('min-width: 250px;'):
                    ui.label('選択コンポーネント')
                    ui.select(['選択肢1', '選択肢2', '選択肢3'], label='セレクトボックス')
                    ui.radio(['ラジオ1', 'ラジオ2', 'ラジオ3'], value='ラジオ1').props('inline')
                    ui.checkbox('チェックボックス1', value=True)
                    ui.checkbox('チェックボックス2', value=False)
                    ui.switch('スイッチ', value=True)
                    
                with ui.column().style('min-width: 250px;'):
                    ui.label('スライダー・日付')
                    ui.slider(min=0, max=100, value=50)
                    ui.range(min=0, max=100, value={'min': 20, 'max': 80})
                    ui.knob(0.3, show_value=True)
                    ui.date(value='2024-01-15')
                    ui.time(value='14:30')

    def _showcase_display_components(self):
        """表示コンポーネントサンプル"""
        with ui.card().style('margin-bottom: 16px; padding: 16px;'):
            ui.label('📊 表示コンポーネント').style('font-size: 16px; font-weight: bold; margin-bottom: 12px;')
            
            with ui.row().style('gap: 16px; flex-wrap: wrap;'):
                with ui.column().style('min-width: 300px;'):
                    ui.label('テーブル')
                    columns = [
                        {'name': 'name', 'label': '名前', 'field': 'name'},
                        {'name': 'age', 'label': '年齢', 'field': 'age'},
                    ]
                    rows = [
                        {'name': '太郎', 'age': 25},
                        {'name': '花子', 'age': 30},
                        {'name': '次郎', 'age': 35},
                    ]
                    ui.table(columns=columns, rows=rows, row_key='name').props('dense')
                
                with ui.column().style('min-width: 300px;'):
                    ui.label('リスト・ツリー')
                    with ui.list().props('bordered separator'):
                        ui.item('アイテム1')
                        ui.item('アイテム2')
                        ui.item('アイテム3')
                    
                    ui.tree([
                        {'id': 'root', 'label': 'ルート', 'children': [
                            {'id': 'child1', 'label': '子1'},
                            {'id': 'child2', 'label': '子2', 'children': [
                                {'id': 'grandchild', 'label': '孫'}
                            ]}
                        ]}
                    ], label_key='label', on_select=lambda e: print(f'選択: {e}'))

    def _showcase_layout_components(self):
        """レイアウトコンポーネントサンプル"""
        with ui.card().style('margin-bottom: 16px; padding: 16px;'):
            ui.label('📐 レイアウトコンポーネント').style('font-size: 16px; font-weight: bold; margin-bottom: 12px;')
            
            with ui.row().style('gap: 16px; flex-wrap: wrap;'):
                with ui.column().style('min-width: 300px;'):
                    ui.label('カード・パネル')
                    with ui.card().style('padding: 16px; margin-bottom: 8px;'):
                        ui.label('カード内容')
                        ui.button('カードボタン')
                    
                    with ui.expansion('展開パネル', icon='info'):
                        ui.label('展開された内容がここに表示されます')
                        ui.button('パネル内ボタン')
                
                with ui.column().style('min-width: 300px;'):
                    ui.label('グリッド・スプリッター')
                    with ui.grid(columns=2).style('gap: 8px;'):
                        ui.card().style('padding: 16px; height: 60px;').props('flat bordered')
                        ui.card().style('padding: 16px; height: 60px;').props('flat bordered')
                        ui.card().style('padding: 16px; height: 60px;').props('flat bordered')
                        ui.card().style('padding: 16px; height: 60px;').props('flat bordered')
                    
                    with ui.splitter().style('height: 100px;') as splitter:
                        with splitter.before:
                            ui.label('左パネル').style('padding: 8px;')
                        with splitter.after:
                            ui.label('右パネル').style('padding: 8px;')

    def _showcase_navigation_components(self):
        """ナビゲーションコンポーネントサンプル"""
        with ui.card().style('margin-bottom: 16px; padding: 16px;'):
            ui.label('🧭 ナビゲーション').style('font-size: 16px; font-weight: bold; margin-bottom: 12px;')
            
            with ui.row().style('gap: 16px; flex-wrap: wrap;'):
                with ui.column().style('min-width: 300px;'):
                    ui.label('タブ')
                    with ui.tabs().classes('w-full') as tabs:
                        ui.tab('タブ1')
                        ui.tab('タブ2')
                        ui.tab('タブ3')
                    with ui.tab_panels(tabs, value='タブ1').classes('w-full'):
                        with ui.tab_panel('タブ1'):
                            ui.label('タブ1の内容')
                        with ui.tab_panel('タブ2'):
                            ui.label('タブ2の内容')
                        with ui.tab_panel('タブ3'):
                            ui.label('タブ3の内容')
                
                with ui.column().style('min-width: 300px;'):
                    ui.label('ステップ・ページネーション')
                    # ステップコンポーネント（簡略版）
                    with ui.element('div').style('height: 150px; background: #f3f4f6; border-radius: 8px; padding: 16px;'):
                        ui.label('ステップ 1/3: 開始')
                        ui.label('ステップ 2/3: 進行中')
                        ui.label('ステップ 3/3: 完了')
                    
                    # ページネーション（簡略版）
                    with ui.element('div').style('display: flex; gap: 8px; align-items: center;'):
                        ui.button('◀', color='grey')
                        ui.button('1', color='primary')
                        ui.button('2', color='grey')
                        ui.button('3', color='grey')
                        ui.button('▶', color='grey')

    def _showcase_feedback_components(self):
        """フィードバックコンポーネントサンプル"""
        with ui.card().style('margin-bottom: 16px; padding: 16px;'):
            ui.label('💬 フィードバック').style('font-size: 16px; font-weight: bold; margin-bottom: 12px;')
            
            with ui.row().style('gap: 16px; flex-wrap: wrap;'):
                with ui.column().style('min-width: 300px;'):
                    ui.label('プログレス・スピナー')
                    ui.linear_progress(value=0.3)
                    ui.circular_progress(value=0.7, size='lg')
                    ui.spinner(size='lg')
                    
                    ui.button('通知表示', on_click=lambda: ui.notify('これは通知メッセージです'))
                    ui.button('エラー通知', on_click=lambda: ui.notify('エラーメッセージ', type='negative'))
                    ui.button('成功通知', on_click=lambda: ui.notify('成功メッセージ', type='positive'))
                
                with ui.column().style('min-width: 300px;'):
                    ui.label('ツールチップ・バナー')
                    ui.button('ツールチップ付き').tooltip('これはツールチップです')
                    
                    # バナー（簡略版）
                    with ui.element('div').style('background: #dbeafe; border: 1px solid #3b82f6; border-radius: 8px; padding: 12px;'):
                        ui.label('ℹ️ 重要な情報をお知らせします').style('color: #1d4ed8;')

    def _showcase_media_components(self):
        """メディアコンポーネントサンプル"""
        with ui.card().style('margin-bottom: 16px; padding: 16px;'):
            ui.label('🎵 メディア').style('font-size: 16px; font-weight: bold; margin-bottom: 12px;')
            
            with ui.row().style('gap: 16px; flex-wrap: wrap;'):
                with ui.column().style('min-width: 300px;'):
                    ui.label('画像・アバター')
                    ui.image('https://picsum.photos/200/100').style('width: 200px; height: 100px;')
                    ui.avatar('U', color='primary')
                    ui.avatar(icon='person', color='secondary')
                
                with ui.column().style('min-width: 300px;'):
                    ui.label('チャート')
                    # EChartsプロット例
                    echart_options = {
                        'xAxis': {'type': 'category', 'data': ['Mon', 'Tue', 'Wed', 'Thu', 'Fri']},
                        'yAxis': {'type': 'value'},
                        'series': [{'data': [120, 200, 150, 80, 70], 'type': 'line'}]
                    }
                    ui.echart(echart_options).style('height: 200px;')

    def _showcase_advanced_components(self):
        """高度なコンポーネントサンプル"""
        with ui.card().style('margin-bottom: 16px; padding: 16px;'):
            ui.label('🚀 高度なコンポーネント').style('font-size: 16px; font-weight: bold; margin-bottom: 12px;')
            
            with ui.row().style('gap: 16px; flex-wrap: wrap;'):
                with ui.column().style('min-width: 300px;'):
                    ui.label('メニュー・ドロップダウン')
                    with ui.button('メニューボタン', icon='menu'):
                        with ui.menu():
                            ui.menu_item('メニュー項目1', on_click=lambda: ui.notify('項目1選択'))
                            ui.menu_item('メニュー項目2', on_click=lambda: ui.notify('項目2選択'))
                            ui.separator()
                            ui.menu_item('メニュー項目3', on_click=lambda: ui.notify('項目3選択'))
                    
                    with ui.dropdown_button('ドロップダウン', auto_close=True):
                        ui.item('選択肢A', on_click=lambda: ui.notify('A選択'))
                        ui.item('選択肢B', on_click=lambda: ui.notify('B選択'))
                
                with ui.column().style('min-width: 300px;'):
                    ui.label('ダイアログ・その他')
                    ui.button('通知表示', on_click=lambda: ui.notify('ダイアログ風通知'))
                    ui.button('情報表示', on_click=lambda: ui.notify('情報メッセージ', type='info'))
                    
                    # カラーピッカー
                    ui.color_input('色選択', value='#3b82f6')
                    
                    # ファイルアップロード（簡略版）
                    with ui.element('div').style('border: 2px dashed #d1d5db; border-radius: 8px; padding: 16px; text-align: center;'):
                        ui.label('📁 ファイルアップロード').style('color: #6b7280;')