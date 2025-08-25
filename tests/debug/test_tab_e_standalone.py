#!/usr/bin/env python3
"""
Tab E (総合展示) 単体テスト
総合展示ページの実装状況確認
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import flet as ft
from flet_ui.arrangement_test.tab_e import TabE


def main(page: ft.Page):
    """単体テスト用メイン関数"""
    # ページ設定
    page.title = "Tab E: 総合展示 - 単体テスト"
    page.window_width = 1400
    page.window_height = 900
    page.window_resizable = True
    page.padding = 0
    page.bgcolor = ft.Colors.GREY_50
    
    try:
        # Tab E: 総合展示作成
        tab_e = TabE()
        content = tab_e.create_content()
        page.add(content)
        
        # ステータス表示
        print("✅ Tab E: 総合展示単体テスト起動完了")
        print("🌐 http://localhost:8503 でアクセス可能")
        print("🎯 実装機能:")
        print("   - Fletコントロールギャラリー")
        print("   - 公式サンプル動的ロード")
        print("   - チャート、入力、ダイアログ、レイアウト、ボタンセクション")
        print("   - Fletドキュメント連携")
        
    except Exception as e:
        print(f"❌ エラー発生: {e}")
        import traceback
        traceback.print_exc()
        
        # エラー表示
        page.add(
            ft.Container(
                content=ft.Column([
                    ft.Icon(ft.Icons.ERROR, size=64, color=ft.Colors.RED),
                    ft.Text(f"エラー: {str(e)}", size=16, color=ft.Colors.RED, text_align=ft.TextAlign.CENTER),
                    ft.Text("詳細はターミナルログを確認してください", size=12, color=ft.Colors.GREY_600)
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                alignment=ft.alignment.center,
                expand=True,
                bgcolor=ft.Colors.RED_50,
                padding=20
            )
        )


if __name__ == "__main__":
    print("🚀 Tab E: 総合展示単体テスト開始...")
    ft.app(target=main, port=8503, view=ft.WEB_BROWSER)
