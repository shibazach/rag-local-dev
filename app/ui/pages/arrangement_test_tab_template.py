"""配置テスト - タブテンプレート: 空のテンプレート"""

from nicegui import ui

class ArrangementTestTabTemplate:
    """
    空のタブテンプレート
    
    目的:
    - 新しいタブやコンポーネント実験の出発点
    - 共通コンポーネント化のテスト用ベース
    - 最小限の構造のみ提供
    """
    
    def render(self):
        """空のタブコンテンツ"""
        with ui.element('div').style(
            'width: 100%; height: 100%; '
            'padding: 16px; '
            'background: #f8fafc;'
        ):
            ui.label('空のタブテンプレート').style(
                'font-size: 18px; color: #64748b; text-align: center;'
            )