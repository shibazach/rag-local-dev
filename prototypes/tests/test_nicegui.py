#!/usr/bin/env python3
"""
最小限のNiceGUIテスト
"""
from nicegui import ui

@ui.page('/')
def index():
    ui.label('Hello NiceGUI!')
    ui.button('Test', on_click=lambda: ui.notify('動作中!'))

if __name__ == "__main__":
    print("NiceGUI starting...")
    ui.run(port=8080, host='0.0.0.0')
    print("NiceGUI stopped.")