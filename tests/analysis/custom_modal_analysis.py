#!/usr/bin/env python3
"""
Flet カスタムモーダルオーバーレイ実装分析
ドラッグ&リサイズ可能なダイアログの実現可能性検証
"""

import flet as ft

def create_custom_modal_overlay(
    page: ft.Page,
    title: str,
    content: ft.Control,
    width: int = 800,
    height: int = 600,
    resizable: bool = True,
    draggable: bool = True
):
    """
    カスタムモーダルオーバーレイの実装テスト
    
    実装方針:
    1. page.overlay にStack追加
    2. 背景Container（半透明）+ メインContainer（ダイアログ風）
    3. GestureDetectorでドラッグ機能
    4. 右下角でリサイズハンドル
    """
    
    # ダイアログ位置・サイズ状態
    dialog_left = (page.window_width - width) // 2 if hasattr(page, 'window_width') else 100
    dialog_top = (page.window_height - height) // 2 if hasattr(page, 'window_height') else 50
    dialog_width = width
    dialog_height = height
    
    def on_drag_start(e):
        """ドラッグ開始処理"""
        pass
    
    def on_drag_update(e):
        """ドラッグ中の位置更新"""
        nonlocal dialog_left, dialog_top
        dialog_left = max(0, min(dialog_left + e.delta_x, page.window_width - dialog_width))
        dialog_top = max(0, min(dialog_top + e.delta_y, page.window_height - dialog_height))
        dialog_container.left = dialog_left
        dialog_container.top = dialog_top
        page.update()
    
    def on_resize_update(e):
        """リサイズ中のサイズ更新"""
        nonlocal dialog_width, dialog_height
        dialog_width = max(400, dialog_width + e.delta_x)
        dialog_height = max(300, dialog_height + e.delta_y) 
        dialog_container.width = dialog_width
        dialog_container.height = dialog_height
        page.update()
    
    def close_modal(e=None):
        """モーダルを閉じる"""
        page.overlay.clear()
        page.update()
    
    # ヘッダー（ドラッグ可能エリア）
    header = ft.Container(
        content=ft.Row([
            ft.Text(title, size=16, weight=ft.FontWeight.BOLD, expand=True),
            ft.IconButton(ft.Icons.CLOSE, on_click=close_modal, tooltip="閉じる")
        ]),
        bgcolor=ft.Colors.BLUE_100,
        padding=ft.padding.all(12),
        height=50
    )
    
    if draggable:
        header = ft.GestureDetector(
            content=header,
            on_pan_start=on_drag_start,
            on_pan_update=on_drag_update,
            mouse_cursor=ft.MouseCursor.MOVE
        )
    
    # リサイズハンドル（右下角）
    resize_handle = None
    if resizable:
        resize_handle = ft.Container(
            content=ft.Icon(ft.Icons.DRAG_HANDLE, size=16, color=ft.Colors.GREY),
            width=20,
            height=20,
            bgcolor=ft.Colors.GREY_200,
            border_radius=4,
            alignment=ft.alignment.center
        )
        resize_handle = ft.GestureDetector(
            content=resize_handle,
            on_pan_update=on_resize_update,
            mouse_cursor=ft.MouseCursor.RESIZE_DOWN_RIGHT
        )
    
    # メインダイアログContainer
    dialog_content = ft.Column([
        header,
        ft.Container(
            content=content,
            expand=True,
            padding=ft.padding.all(16)
        ),
        ft.Container(
            content=ft.Row([
                ft.Container(expand=True),  # スペーサー
                resize_handle
            ] if resize_handle else []),
            height=20 if resize_handle else 0
        )
    ], spacing=0, expand=True)
    
    dialog_container = ft.Container(
        content=dialog_content,
        width=dialog_width,
        height=dialog_height,
        left=dialog_left,
        top=dialog_top,
        bgcolor=ft.Colors.WHITE,
        border_radius=8,
        shadow=ft.BoxShadow(
            spread_radius=1,
            blur_radius=10,
            color=ft.Colors.BLACK26
        )
    )
    
    # 背景オーバーレイ（半透明、クリックで閉じる）
    background_overlay = ft.Container(
        content=ft.Stack([dialog_container]),
        expand=True,
        bgcolor=ft.Colors.BLACK38,  # 半透明背景
        on_click=close_modal  # 背景クリックで閉じる
    )
    
    return background_overlay


def test_custom_modal(page: ft.Page):
    """カスタムモーダルのテスト実装"""
    
    def show_modal(e):
        # テスト用コンテンツ
        test_content = ft.Column([
            ft.Text("カスタムモーダルダイアログのテスト", size=18),
            ft.TextField(
                label="サンプルテキスト",
                multiline=True,
                min_lines=10,
                expand=True
            ),
            ft.Row([
                ft.ElevatedButton("キャンセル", on_click=lambda e: page.overlay.clear()),
                ft.ElevatedButton("保存", on_click=lambda e: page.overlay.clear())
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
        ], expand=True)
        
        modal = create_custom_modal_overlay(
            page=page,
            title="カスタムモーダルテスト",
            content=test_content,
            width=600,
            height=500,
            resizable=True,
            draggable=True
        )
        
        page.overlay.append(modal)
        page.update()
    
    # テスト用ボタン
    page.add(
        ft.Column([
            ft.Text("カスタムモーダルオーバーレイ実装テスト", size=20),
            ft.ElevatedButton("モーダルを開く", on_click=show_modal),
            ft.Text("特徴:"),
            ft.Text("• ドラッグ移動可能（ヘッダー部分）"),
            ft.Text("• リサイズ可能（右下角ハンドル）"),
            ft.Text("• 背景クリック/×ボタンで閉じる"),
            ft.Text("• Stackベースの完全カスタム実装")
        ])
    )


if __name__ == "__main__":
    ft.app(target=test_custom_modal)

