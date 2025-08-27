#!/usr/bin/env python3
"""
Flet RAGシステム - 配置テスト タブC (大容量PDF表示テスト)
全面的な大容量PDF対応機能テスト
"""

import flet as ft
import asyncio
from typing import Optional


class TabC:
    """タブC: 大容量PDF表示テスト（全面表示）"""
    
    def __init__(self):
        self.current_status = "待機中"
        self.log_messages = []
        
    def create_content(self, page: ft.Page = None) -> ft.Control:
        """タブCコンテンツ作成"""
        self.page = page  # ページ参照を保存
        
        # V3版PDFプレビューコンポーネント（プラットフォーム適応版）
        from app.flet_ui.shared.pdf_large_preview_v3 import create_large_pdf_preview_v3
        self.pdf_preview_v3 = create_large_pdf_preview_v3(self.page)
        
        self.current_pdf_version = "v3"  # V3版のみ使用
        
        # ステータス表示
        self.status_text = ft.Text(
            value=f"ステータス: {self.current_status}",
            size=14,
            weight=ft.FontWeight.BOLD,
            color=ft.Colors.BLUE_700
        )
        
        # ログ表示エリア（大きなサイズ）
        self.log_display = ft.Column(
            controls=[],
            scroll=ft.ScrollMode.ALWAYS,
            spacing=4,
            expand=True  # 親コンテナに合わせて拡張
        )
        
        # シンプルテストボタン（V3版のみ）
        test_buttons = ft.Row([
            ft.ElevatedButton(
                text="🚀 V3版PDFテスト実行",
                on_click=self._simple_v3_test,
                bgcolor=ft.Colors.GREEN_100,
                width=200,
                height=50,
                style=ft.ButtonStyle(
                    text_style=ft.TextStyle(size=16, weight=ft.FontWeight.BOLD)
                )
            ),
            ft.ElevatedButton(
                text="🗑️ クリア",
                on_click=self._clear_preview,
                bgcolor=ft.Colors.GREY_200,
                width=120,
                height=50
            )
        ], alignment=ft.MainAxisAlignment.CENTER, spacing=20)
        
        # 上部コントロールバー（薄く）
        control_bar = ft.Container(
            content=ft.Column([
                ft.Text("大容量PDF対応機能テスト（左右ペイン表示）", size=16, weight=ft.FontWeight.BOLD),
                test_buttons,
                self.status_text
            ], spacing=6),
            padding=ft.padding.all(12),
            bgcolor=ft.Colors.WHITE,
            border=ft.border.only(bottom=ft.BorderSide(2, ft.Colors.BLUE_200))
        )
        
        # 左ペイン: ログ表示エリア（大きく）
        log_panel = ft.Container(
            content=ft.Column([
                ft.Text("🔍 実行ログ", size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_700),
                ft.Container(
                    content=self.log_display,
                    bgcolor=ft.Colors.GREY_50,
                    padding=ft.padding.all(8),
                    border=ft.border.all(1, ft.Colors.GREY_300),
                    border_radius=4,
                    expand=True
                )
            ], spacing=8, expand=True),
            padding=ft.padding.all(8),
            width=400,  # 固定幅
            bgcolor=ft.Colors.WHITE,
            border=ft.border.only(right=ft.BorderSide(2, ft.Colors.GREY_300))
        )
        
                # 右ペイン: PDFプレビューエリア（V3版専用・シンプル）
        self.pdf_container = ft.Container(
            content=self.pdf_preview_v3,  # V3版のみ使用
            expand=True,
            padding=ft.padding.all(4),
            bgcolor=ft.Colors.GREY_50,
            border_radius=4
        )
        
        pdf_panel = ft.Container(
            content=ft.Column([
                ft.Text("📄 PDFプレビュー", size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_700),
                self.pdf_container
            ], spacing=8, expand=True),
            padding=ft.padding.all(8),
            expand=True,  # 残り全幅を使用
            bgcolor=ft.Colors.WHITE
        )
        
        # 左右分割メインエリア
        main_content = ft.Row([
            log_panel,
            pdf_panel
        ], expand=True, spacing=0)
        
        # 全体レイアウト（上部コントロール + 左右分割エリア）
        main_layout = ft.Column([
            control_bar,
            main_content
        ], expand=True, spacing=0)
        
        # 初期メッセージ
        self._add_log("🟢 大容量PDF表示システム初期化完了")
        
        return main_layout
    
    def _add_log(self, message: str):
        """ログメッセージ追加"""
        import datetime
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        
        # メッセージタイプ別の色分け
        if "✅" in message or "成功" in message:
            text_color = ft.Colors.GREEN_700
        elif "❌" in message or "エラー" in message:
            text_color = ft.Colors.RED_700
        elif "🔍" in message or "検索" in message:
            text_color = ft.Colors.BLUE_700
        elif "🖼️" in message or "画像" in message:
            text_color = ft.Colors.PURPLE_700
        elif "🌐" in message or "ストリーミング" in message:
            text_color = ft.Colors.CYAN_700
        else:
            text_color = ft.Colors.GREY_700
        
        log_text = ft.Text(
            value=f"[{timestamp}] {message}",
            size=12,  # 少し大きく
            color=text_color,
            weight=ft.FontWeight.W_400
        )
        
        self.log_messages.append(log_text)
        self.log_display.controls = self.log_messages[-20:]  # 最新20件表示
        
        if hasattr(self, 'log_display'):
            try:
                self.log_display.update()
            except:
                pass
        
        # コンソールにも出力
        print(f"[PDF-TEST] {message}")
    
    def _update_status(self, status: str):
        """ステータス更新"""
        self.current_status = status
        self.status_text.value = f"ステータス: {status}"
        try:
            self.status_text.update()
        except:
            pass
        self._add_log(f"ステータス変更: {status}")
    
    # ==================== V1/V2 メソッド削除（V3専用化） ==================== 
    
    # V1用メソッド削除済み
    
    def _simple_v3_test(self, e):
        """シンプルV3版PDFテスト（ワンクリック）"""
        self._add_log("🚀 V3版PDFテスト開始")
        self._update_status("PDFテスト実行中")
        
        if self.page:
            self.page.run_task(self._async_simple_v3_test)
        else:
            import threading
            threading.Thread(target=lambda: asyncio.run(self._async_simple_v3_test())).start()

    async def _async_simple_v3_test(self):
        """シンプルV3版非同期テスト"""
        try:
            from app.core.db_simple import fetch_one
            
            # 適度なサイズのPDFを自動選択
            test_pdf = fetch_one('''
                SELECT fb.id, fm.file_name, LENGTH(fb.blob_data) as blob_size, fb.blob_data
                FROM files_blob fb
                LEFT JOIN files_meta fm ON fb.id = fm.blob_id
                WHERE fm.file_name LIKE '%.pdf' AND LENGTH(fb.blob_data) < 10000000
                ORDER BY LENGTH(fb.blob_data) DESC
                LIMIT 1
            ''')
            
            if not test_pdf:
                self._add_log("❌ テスト用PDFが見つかりません")
                self._update_status("エラー発生")
                return
            
            size_mb = test_pdf['blob_size'] / (1024 * 1024)
            self._add_log(f"📄 テスト用PDF: {test_pdf['file_name']} ({size_mb:.2f}MB)")
            
            # V3版で直接表示
            self._add_log("⚡ V3版でPDF表示中...")
            await self.pdf_preview_v3.load_pdf(test_pdf, test_pdf['blob_data'])
            
            self._add_log("✅ V3版PDF表示完了")
            self._update_status("PDF表示完了")
            
        except Exception as e:
            error_msg = f"❌ V3版PDFテストエラー: {str(e)}"
            self._add_log(error_msg)
            self._update_status("エラー発生")
            import traceback
            print(f"[PDF-V3-SIMPLE-ERROR] {traceback.format_exc()}")

    def _clear_preview(self, e=None):
        """プレビュークリア（V3版専用・シンプル）"""
        if e is not None:
            self._add_log("🗑️ クリア実行中...")
        
        # V3版プレビューをクリア
        self.pdf_preview_v3.clear_preview()
            
        if e is not None:
            self._update_status("待機中")
            self._add_log("✅ クリア完了")

    # V1/V2 切り替えメソッド削除済み（V3専用化）

    # V2/V3 重複メソッド削除済み（_simple_v3_testに統一）