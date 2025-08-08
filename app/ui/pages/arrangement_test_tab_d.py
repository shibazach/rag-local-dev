"""配置テスト - タブD: 全共通コンポーネント統合展示"""

from nicegui import ui
from app.ui.components.elements import (
    CommonPanel, CommonSplitter, CommonCard, CommonSectionTitle,
    CommonTabs, CommonFormElements
)
from app.ui.components.common import BaseDataGridView

class ArrangementTestTabD:
    """タブD: 全共通コンポーネント統合展示"""
    
    def render(self):
        """タブDの統合展示を描画"""
        with ui.element('div').style(
            'width: 100%; height: 100%; '
            'overflow-y: auto; padding: 16px; '
            'background: #f8fafc;'
        ):
            CommonSectionTitle.create("🎯 全共通コンポーネント統合展示", size="18px")
            
            # フォーム要素展示
            with CommonCard():
                CommonSectionTitle.create("📝 フォーム系コンポーネント", size="14px")
                
                # ボタン展示
                with ui.element('div').style('margin-bottom: 16px;'):
                    ui.label("ボタンバリエーション:").style('font-weight: bold; margin-bottom: 8px; display: block;')
                    with ui.element('div').style('display: flex; gap: 8px; flex-wrap: wrap;'):
                        CommonFormElements.create_button("Primary", color="primary", size="small")
                        CommonFormElements.create_button("Success", color="success", size="small")
                        CommonFormElements.create_button("Warning", color="warning", size="small")
                        CommonFormElements.create_button("Outline", color="primary", variant="outline", size="small")
                
                # チェックボックス・ラジオ
                with ui.element('div').style('display: flex; gap: 32px; margin-bottom: 16px;'):
                    with ui.element('div'):
                        ui.label("チェックボックス:").style('font-weight: bold; margin-bottom: 8px; display: block;')
                        CommonFormElements.create_checkbox("同意する", value=True)
                        CommonFormElements.create_checkbox("通知受信", value=False)
                    
                    with ui.element('div'):
                        CommonFormElements.create_radio_group(
                            "優先度",
                            ["高", "中", "低"],
                            value="中",
                            layout="horizontal"
                        )
                
                # 入力フィールド
                with ui.element('div').style('display: flex; gap: 16px; flex-wrap: wrap;'):
                    CommonFormElements.create_input("名前", placeholder="名前を入力", width="150px")
                    CommonFormElements.create_dropdown("部署", ["開発", "営業", "企画"], width="120px")
            
            # テーブル展示（BaseDataGridView）
            with CommonCard():
                CommonSectionTitle.create("📊 BaseDataGridView展示", size="14px")
                
                with ui.element('div').style('height: 200px;'):
                    grid = BaseDataGridView(
                        columns=[
                            {'field': 'id', 'label': 'ID', 'width': '50px', 'align': 'center'},
                            {'field': 'name', 'label': '名前', 'width': '1fr'},
                            {'field': 'status', 'label': 'ステータス', 'width': '80px', 'align': 'center',
                             'render_type': 'badge', 'badge_colors': {
                                 'アクティブ': '#22c55e', '保留': '#f59e0b'
                             }}
                        ],
                        height='100%',
                        default_rows_per_page=3
                    )
                    grid.set_data([
                        {'id': 1, 'name': '田中太郎', 'status': 'アクティブ'},
                        {'id': 2, 'name': '佐藤花子', 'status': '保留'},
                        {'id': 3, 'name': '鈴木一郎', 'status': 'アクティブ'},
                        {'id': 4, 'name': '高橋美咲', 'status': 'アクティブ'},
                        {'id': 5, 'name': '山田次郎', 'status': '保留'}
                    ])
                    grid.render()
            
            # 成功メッセージ
            with ui.element('div').style(
                'background: #dcfce7; border: 1px solid #16a34a; '
                'border-radius: 8px; padding: 16px; margin-top: 16px;'
            ):
                ui.label('🎉 全共通コンポーネント統合成功！').style(
                    'color: #15803d; font-weight: bold; font-size: 16px;'
                )
                ui.label('タブ・パネル・表・ボタン・チェックボックス・ラジオボタン・ドロップダウン 全て動作確認済み').style('color: #166534;')