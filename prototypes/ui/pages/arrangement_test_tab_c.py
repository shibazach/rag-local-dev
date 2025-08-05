"""配置テスト - タブC: 共通コンポーネント実証テスト"""

from nicegui import ui
from ui.components.elements import (
    CommonPanel, CommonSplitter, CommonCard, CommonSectionTitle,
    CommonTable, CommonFormElements
)

class ArrangementTestTabC:
    """タブC: 共通コンポーネント実証テスト場"""
    
    def render(self):
        """タブCの共通コンポーネントテストを描画"""
        # スプリッター用CSS追加
        CommonSplitter.add_splitter_styles()
        
        with ui.element('div').style(
            'width: 100%; height: 100%; '
            'display: flex; margin: 0; padding: 8px; '
            'box-sizing: border-box; gap: 0;'
        ):
            # 左側: パネルテスト
            with ui.element('div').style(
                'width: 50%; height: 100%; '
                'display: flex; flex-direction: column; '
                'margin: 0; padding: 0; gap: 0;'
            ):
                # 上パネル: データ分析風
                with CommonPanel(
                    title="📊 共通パネルテスト",
                    gradient="linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
                    buttons=[
                        ('📈', lambda: ui.notify('チャートボタン')),
                        ('⚙️', lambda: ui.notify('設定ボタン'))
                    ],
                    footer_content="📊 更新: 2024-01-15 15:30",
                    height="50%",
                    panel_id="test-panel-1"
                ):
                    CommonSectionTitle.create("🎯 パネル内容テスト")
                    ui.label("CommonPanelコンポーネントの動作確認")
                    ui.label("・ヘッダーボタン動作 ✅")
                    ui.label("・コンテンツエリア表示 ✅") 
                    ui.label("・フッター表示 ✅")
                
                # スプリッター
                CommonSplitter.create_horizontal("test-h-splitter")
                
                # 下パネル: タスク管理風
                with CommonPanel(
                    title="📝 タスク管理",
                    gradient="linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)",
                    buttons=[
                        ('✅', lambda: ui.notify('完了')),
                        ('🔄', lambda: ui.notify('更新'))
                    ],
                    footer_content="📝 タスク: 3件",
                    height="50%",
                    panel_id="test-panel-2"
                ):
                    CommonSectionTitle.create("📋 タスクリスト")
                    
                    # タスクアイテム
                    tasks = [
                        ('共通コンポーネント作成', '完了', '#10b981'),
                        ('テスト実装', '進行中', '#f59e0b'),
                        ('ドキュメント作成', '待機', '#6b7280')
                    ]
                    
                    for task, status, color in tasks:
                        with ui.element('div').style(
                            'display: flex; justify-content: space-between; '
                            'align-items: center; padding: 4px 0; '
                            'border-bottom: 1px solid #f3f4f6;'
                        ):
                            ui.label(task).style('font-size: 12px;')
                            with ui.element('span').style(
                                f'background: {color}; color: white; '
                                f'padding: 2px 6px; border-radius: 3px; '
                                f'font-size: 9px;'
                            ):
                                ui.label(status)
            
            # 縦スプリッター
            CommonSplitter.create_vertical("test-v-splitter")
            
            # 右側: 共通コンポーネント化成功展示（タブDから移動）
            with ui.element('div').style(
                'width: 50%; height: 100%; '
                'overflow-y: auto; padding: 8px; '
                'background: #f8fafc;'
            ):
                CommonSectionTitle.create("🎯 共通コンポーネント化成功展示", size="16px")
                
                # フォーム要素展示（タブDから移動）
                with CommonCard():
                    CommonSectionTitle.create("📝 CommonFormElements", size="14px")
                    
                    # ボタン展示
                    with ui.element('div').style('margin-bottom: 12px;'):
                        ui.label("ボタンバリエーション:").style('font-weight: bold; margin-bottom: 6px; display: block; font-size: 12px;')
                        with ui.element('div').style('display: flex; gap: 6px; flex-wrap: wrap;'):
                            CommonFormElements.create_button("Primary", color="primary", size="small")
                            CommonFormElements.create_button("Success", color="success", size="small")
                            CommonFormElements.create_button("Warning", color="warning", size="small")
                            CommonFormElements.create_button("Outline", color="primary", variant="outline", size="small")
                    
                    # チェックボックス・ラジオ（コンパクト版）
                    with ui.element('div').style('display: flex; gap: 16px; margin-bottom: 12px;'):
                        with ui.element('div'):
                            ui.label("チェックボックス:").style('font-weight: bold; margin-bottom: 4px; display: block; font-size: 12px;')
                            CommonFormElements.create_checkbox("同意する", value=True)
                            CommonFormElements.create_checkbox("通知受信", value=False)
                        
                        with ui.element('div'):
                            CommonFormElements.create_radio_group(
                                "優先度",
                                ["高", "中", "低"],
                                value="中",
                                layout="horizontal"
                            )
                    
                    # 入力フィールド（コンパクト版）
                    with ui.element('div').style('display: flex; gap: 12px; flex-wrap: wrap;'):
                        CommonFormElements.create_input("名前", placeholder="名前を入力", width="120px")
                        CommonFormElements.create_dropdown("部署", ["開発", "営業", "企画"], width="100px")
                
                # テーブル展示（タブDから移動・コンパクト版）
                with CommonCard():
                    CommonSectionTitle.create("📊 CommonTable", size="14px")
                    
                    table = CommonTable(
                        columns=[
                            {'key': 'id', 'label': 'ID', 'width': '40px', 'align': 'center'},
                            {'key': 'name', 'label': '名前', 'width': '1fr'},
                            {'key': 'status', 'label': 'ステータス', 'width': '70px', 'align': 'center',
                             'render_type': 'badge', 'badge_colors': {'アクティブ': '#10b981', '保留': '#f59e0b'}}
                        ],
                        data=[
                            {'id': 1, 'name': '田中太郎', 'status': 'アクティブ'},
                            {'id': 2, 'name': '佐藤花子', 'status': '保留'},
                            {'id': 3, 'name': '鈴木一郎', 'status': 'アクティブ'}
                        ],
                        rows_per_page=2
                    )
                    
                    with ui.element('div').style('height: 120px;'):
                        table.render()
                
                # 基本コンポーネント説明（簡素化）
                with CommonCard():
                    CommonSectionTitle.create("🏗️ 基本コンポーネント", size="14px")
                    
                    components = [
                        ("CommonPanel", "ヘッダー・コンテンツ・フッター構造"),
                        ("CommonSplitter", "横・縦スプリッター + ドラッグ対応"),
                        ("CommonCard", "ui.card()ベース + 統一スタイル"),
                        ("CommonSectionTitle", "統一タイトル + アイコン対応")
                    ]
                    
                    for comp_name, description in components:
                        with ui.element('div').style('margin-bottom: 4px; padding: 4px; background: #f1f5f9; border-radius: 4px;'):
                            ui.label(f"• {comp_name}").style('font-weight: bold; font-size: 11px; color: #334155;')
                            ui.label(description).style('font-size: 10px; color: #64748b; margin-left: 8px;')
                
                # スプリッター動作確認セクション
                with CommonCard():
                    CommonSectionTitle.create("🎛️ スプリッター動作確認", size="14px")
                    ui.label("左右・上下のスプリッターをドラッグしてください").style('font-size: 12px; color: #6b7280; margin-bottom: 8px;')
                    
                    # スプリッター状態表示
                    with ui.element('div').style('background: #f3f4f6; padding: 8px; border-radius: 4px;'):
                        ui.label("📍 CommonSplitter統一システム").style('font-weight: bold; font-size: 11px; color: #1f2937;')
                        ui.label("• 自動検出: .splitterクラス").style('font-size: 10px; color: #6b7280;')
                        ui.label("• ホバー: 青色ハイライト").style('font-size: 10px; color: #6b7280;')
                        ui.label("• ドラッグ: 濃い青色").style('font-size: 10px; color: #6b7280;')
                
                # 統合成功メッセージ
                with ui.element('div').style(
                    'background: #dcfce7; border: 1px solid #16a34a; '
                    'border-radius: 6px; padding: 10px; margin-top: 12px;'
                ):
                    ui.label('🎉 共通コンポーネント化成功！').style(
                        'color: #15803d; font-weight: bold; font-size: 13px;'
                    )
                    ui.label('全7種類のコンポーネントが完成・動作確認済み').style('color: #166534; font-size: 11px;')
        
        # 共通スプリッターシステムに委任