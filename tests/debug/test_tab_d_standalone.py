#!/usr/bin/env python3
"""
タブD単体テスト - 真のオーバーレイ縦スライダー動作確認
詳細デバッグ機能付き
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import flet as ft
import traceback

def main(page: ft.Page):
    try:
        print("🚀 タブD単体テスト開始...")
        print(f"📱 Page情報: {page}")
        
        page.title = "タブD単体テスト - 縦スライダーレイヤー検討"
        page.window_width = 1200
        page.window_height = 800
        page.bgcolor = ft.Colors.GREY_50
        
        print("🔧 TabDクラス import 確認...")
        from flet_ui.arrangement_test.tab_d import TabD
        print("✅ import成功")
        
        print("🔧 TabDインスタンス作成中...")
        tab_d = TabD()
        print(f"✅ TabD作成成功: {tab_d}")
        
        print("🎨 レイアウト作成中...")
        content = tab_d.create_content()
        print(f"✅ レイアウト作成成功: {type(content)}")
        
        print("📱 ページ追加中...")
        page.add(content)
        print("✅ ページ追加成功")
        
        print("🎉 タブD起動完了！")
        print("=" * 50)
        print("📋 動作確認ポイント:")
        print("  1. 縦スライダーが青枠の中央に配置されているか")
        print("  2. 左右に120pxずつはみ出しているか") 
        print("  3. スライダー操作で4分割パネルの比率が変わるか")
        print("  4. レスポンシブでレイアウトが崩れないか")
        print("=" * 50)
        
        # デバッグ情報出力
        print("🔍 デバッグ情報:")
        print(f"  - スライダー長さ: 320px")
        print(f"  - スライダー太さ: 22px") 
        print(f"  - オーバーハング: 120px")
        print(f"  - 左右比率: {tab_d.ratios[tab_d.horizontal_level]}")
        print(f"  - 左分割比率: {tab_d.ratios[tab_d.left_split_level]}")
        print(f"  - 右分割比率: {tab_d.ratios[tab_d.right_split_level]}")
        
    except Exception as e:
        print(f"❌ エラー発生: {e}")
        print("📋 トレースバック:")
        traceback.print_exc()
        
        # エラー表示用の簡易画面
        error_content = ft.Container(
            content=ft.Column([
                ft.Text("❌ エラー発生", size=24, color=ft.Colors.RED),
                ft.Text(f"エラー内容: {str(e)}", size=16),
                ft.Text("詳細はコンソールを確認", size=14, color=ft.Colors.GREY_600)
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            padding=20,
            alignment=ft.alignment.center,
            expand=True
        )
        page.add(error_content)

if __name__ == "__main__":
    print("🚀 単体テスト起動中...")
    try:
        ft.app(main, port=8501)  # メインアプリと別ポート
    except Exception as e:
        print(f"❌ アプリケーション起動失敗: {e}")
        traceback.print_exc()
        sys.exit(1)
