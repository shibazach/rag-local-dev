#!/usr/bin/env python3
"""
Flet RAGシステム - デバッグ専用エントリーポイント
特定コンポーネントの動作確認用
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import flet as ft
import traceback

def debug_tab_d(page: ft.Page):
    """TabD単体デバッグモード"""
    try:
        print("🚀 TabDデバッグモード開始...")
        page.title = "デバッグ: TabD - 縦スライダーレイヤー"
        page.bgcolor = ft.Colors.GREY_50
        page.padding = 0
        
        from flet_ui.arrangement_test.tab_d import TabD
        
        print("🔧 TabD作成中...")
        tab_d = TabD()
        
        print("🎨 コンテンツ作成中...")
        content = tab_d.create_content()
        
        print("📱 ページ追加中...")
        page.add(content)
        
        print("✅ TabD表示完了！")
        print("🔍 動作確認ポイント:")
        print("  - 縦スライダーが青枠ガイドの中央に配置")
        print("  - 左右120pxずつオーバーハング")
        print("  - スライダー操作で4分割パネル比率変更")
        
    except Exception as e:
        print(f"❌ エラー: {e}")
        traceback.print_exc()
        
        error_display = ft.Container(
            content=ft.Column([
                ft.Text("❌ TabDデバッグエラー", size=20, color=ft.Colors.RED),
                ft.Text(str(e), size=14),
                ft.Text("コンソール詳細確認", size=12, color=ft.Colors.GREY_600)
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            padding=20,
            alignment=ft.alignment.center,
            expand=True
        )
        page.add(error_display)

def debug_menu(page: ft.Page):
    """デバッグメニュー"""
    page.title = "Fletデバッグメニュー"
    page.bgcolor = ft.Colors.GREY_50
    
    def navigate_to_tab_d(e):
        page.clean()
        debug_tab_d(page)
    
    menu_content = ft.Container(
        content=ft.Column([
            ft.Text("🔧 Flet RAGシステム - デバッグメニュー", 
                   size=24, weight=ft.FontWeight.BOLD),
            ft.Container(height=20),
            ft.ElevatedButton(
                "📋 TabD - 縦スライダーレイヤー検討",
                on_click=navigate_to_tab_d,
                width=300,
                height=50
            ),
            ft.Container(height=10),
            ft.Text("各コンポーネントの単体動作確認", 
                   size=14, color=ft.Colors.GREY_600),
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        alignment=ft.alignment.center,
        expand=True
    )
    
    page.add(menu_content)

def main(page: ft.Page):
    """メイン関数 - デバッグ対象を選択"""
    debug_target = sys.argv[1] if len(sys.argv) > 1 else "menu"
    
    print(f"🚀 デバッグモード起動: {debug_target}")
    
    if debug_target == "tab_d":
        debug_tab_d(page)
    else:
        debug_menu(page)

if __name__ == "__main__":
    print("🔧 Flet RAGシステム - デバッグ版起動中...")
    print("📋 使用方法:")
    print("  python main_debug.py        # メニュー表示") 
    print("  python main_debug.py tab_d  # TabD直接起動")
    print("📍 URL: http://localhost:8502")
    
    ft.app(main, port=8502)
