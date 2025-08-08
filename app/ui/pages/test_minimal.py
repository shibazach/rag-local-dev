"""最小限のテストページ"""

from nicegui import ui

class TestMinimalPage:
    def __init__(self):
        """最小限のページ"""
        ui.label("テストページ - これが見えれば基本機能は正常").style(
            'font-size: 24px; color: red; margin: 50px;'
        )
        
        with ui.element('div').style('margin: 50px; padding: 20px; border: 2px solid blue;'):
            ui.label("arrangement-testページの問題を調査中")
            ui.button("テストボタン", on_click=lambda: ui.notify("ボタンクリック成功"))