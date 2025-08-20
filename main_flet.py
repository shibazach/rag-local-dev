#!/usr/bin/env python3
"""
Flet RAGシステム - メインエントリーポイント
リファクタリング済み：各コンポーネントを分離したシンプル版
"""

import flet as ft
from flet_ui.shared.app_state import AppState


def main(page: ft.Page):
    """
    メインアプリケーション関数
    アプリケーションの状態管理を AppState に委譲
    """
    page.title = "RAG System - Refactored"
    page.padding = 0
    
    # アプリケーション状態管理オブジェクト作成
    app_state = AppState(page)
    
    # 初期画面: ログイン画面を表示
    app_state.show_login()


if __name__ == "__main__":
    print("🚀 Flet RAGシステム起動中（リファクタリング版）...")
    print("📍 URL: http://localhost:8500")
    print("📝 ログイン情報: admin / password")
    print("📁 構造: コンポーネント分離済み")
    print("=" * 50)
    
    ft.app(
        target=main,
        port=8500,
        host="0.0.0.0",
        view=ft.WEB_BROWSER
    )