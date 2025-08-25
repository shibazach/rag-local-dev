#!/usr/bin/env python3
"""
OCR調整ページ単体テスト
実装したレイアウトと機能の動作確認
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import flet as ft
from flet_ui.ocr_adjustment.page import show_ocr_adjustment_page


def main(page: ft.Page):
    """単体テスト用メイン関数"""
    # ページ設定
    page.title = "OCR調整ページ - 単体テスト"
    page.window_width = 1400
    page.window_height = 900
    page.window_resizable = True
    page.padding = 0
    page.bgcolor = ft.Colors.GREY_50
    
    try:
        # OCR調整ページ表示
        layout = show_ocr_adjustment_page(page)
        page.add(layout)
        
        # ステータス表示
        print("✅ OCR調整ページ単体テスト起動完了")
        print("🌐 http://localhost:8501 でアクセス可能")
        print("🎯 実装されたレイアウトと機能:")
        print("   - 左上: OCR設定パネル（ヘッダーボタン付き）")
        print("   - 左下: OCR結果パネル（ヘッダーボタン付き）")
        print("   - 右上: エンジン詳細設定パネル")  
        print("   - 右下: PDFプレビューパネル")
        print("   - 3つのスライダーによる比率制御")
        
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
    print("🚀 OCR調整ページ単体テスト開始...")
    ft.app(target=main, port=8501, view=ft.WEB_BROWSER)
