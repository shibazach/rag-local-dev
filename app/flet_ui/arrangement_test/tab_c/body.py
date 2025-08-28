#!/usr/bin/env python3
"""
V5統合PDFテスト - ゼロから作り直し版
V1/V4コンポーネント直接使用・確実動作重視
"""

import flet as ft
from typing import Optional


class TabC:
    """V5統合PDFテスト - ゼロから作り直し版"""
    
    def __init__(self):
        self.log_messages = []
        self.current_mode = "none"  # none, v1, v4
        self.current_pdf_data = None
        self.current_filename = None
        
    def create_content(self, page: ft.Page = None) -> ft.Control:
        """ゼロから作り直し - 確実動作重視"""
        self.page = page
        
        # V1コンポーネント（WebView版）
        from app.flet_ui.shared.pdf_preview import create_pdf_preview
        self.v1_preview = create_pdf_preview()
        
        # V4コンポーネント（画像版）
        from app.flet_ui.shared.pdf_large_preview_v4 import create_large_pdf_preview_v4
        self.v4_preview = create_large_pdf_preview_v4(self.page)
        
        # 初期状態表示
        self.empty_display = ft.Container(
            content=ft.Column([
                ft.Icon(ft.Icons.PICTURE_AS_PDF, size=80, color=ft.Colors.GREY_400),
                ft.Text("PDF未選択", size=16, color=ft.Colors.GREY_600),
                ft.Text("テストボタンでPDFを読み込み", size=12, color=ft.Colors.GREY_500)
            ], 
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER),
            expand=True,
            alignment=ft.alignment.center
        )
        
        # 現在のPDF表示エリア
        self.pdf_display_area = ft.Container(
            content=self.empty_display,
            expand=True,
            bgcolor=ft.Colors.WHITE,
            border=ft.border.all(1, ft.Colors.GREY_300),
            border_radius=8
        )
        
        # ログ表示
        self.log_display = ft.Column(
            controls=[],
            scroll=ft.ScrollMode.ALWAYS,
            spacing=2,
            expand=True
        )
        
        # ステータス
        self.status_text = ft.Text(
            value="ステータス: 待機中",
            size=14,
            weight=ft.FontWeight.BOLD,
            color=ft.Colors.BLUE_700
        )
        
        # 統合テストボタン
        buttons = ft.Column([
            ft.ElevatedButton(
                text="📄 PDF自動判定テスト",
                on_click=self._test_auto,
                bgcolor=ft.Colors.BLUE_500,
                color=ft.Colors.WHITE,
                width=200,
                height=40
            ),
            ft.ElevatedButton(
                text="🗑️ クリア",
                on_click=self._clear,
                bgcolor=ft.Colors.GREY_400,
                color=ft.Colors.WHITE,
                width=200,
                height=40
            ),
        ], spacing=8)
        
        # 左パネル（ログ・コントロール）
        left_panel = ft.Container(
            content=ft.Column([
                # ヘッダー
                ft.Container(
                    content=ft.Column([
                        ft.Text("PDF自動判定テスト", size=16, weight=ft.FontWeight.BOLD),
                        self.status_text,
                        ft.Divider(height=1, color=ft.Colors.GREY_300),
                        buttons
                    ], spacing=8),
                    bgcolor=ft.Colors.BLUE_50,
                    padding=ft.padding.all(16),
                    border_radius=8
                ),
                
                ft.Container(height=16),
                
                # ログエリア
                ft.Container(
                    content=ft.Column([
                        ft.Text("実行ログ", size=14, weight=ft.FontWeight.BOLD),
                        ft.Container(
                            content=self.log_display,
                            expand=True,
                            bgcolor=ft.Colors.GREY_50,
                            border=ft.border.all(1, ft.Colors.GREY_300),
                            border_radius=8,
                            padding=ft.padding.all(12)
                        )
                    ], spacing=4),
                    expand=True
                )
            ], expand=True, spacing=0),
            width=350,
            padding=ft.padding.all(8)
        )
        
        # 右パネル（PDF表示）
        right_panel = ft.Container(
            content=self.pdf_display_area,
            expand=True,
            padding=ft.padding.all(8)
        )
        
        # メインレイアウト
        return ft.Row([
            left_panel,
            ft.VerticalDivider(width=1, color=ft.Colors.GREY_300),
            right_panel
        ], expand=True, spacing=0)

    def _add_log(self, message: str):
        """ログ追加"""
        import datetime
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        
        log_entry = ft.Text(
            f"[{timestamp}] {message}",
            size=11,
            color=ft.Colors.BLACK87,
            selectable=True
        )
        
        self.log_messages.append(log_entry)
        
        # 最新15件のみ保持
        if len(self.log_messages) > 15:
            self.log_messages = self.log_messages[-15:]
        
        self.log_display.controls = self.log_messages
        if self.page:
            self.log_display.update()
        
        print(f"[LOG] [{timestamp}] {message}")

    def _update_status(self, status: str):
        """ステータス更新"""
        self.status_text.value = f"ステータス: {status}"
        if self.page:
            self.status_text.update()

    def _test_auto(self, e):
        """自動判定統合テスト"""
        self._add_log("🔥 PDF自動判定テスト開始")
        self._update_status("PDF取得中")
        
        try:
            from app.core.db_simple import fetch_one
            
            # 任意のPDFを取得
            pdf = fetch_one('''
                SELECT fb.blob_data, fm.file_name, LENGTH(fb.blob_data) as size
                FROM files_blob fb
                LEFT JOIN files_meta fm ON fb.id = fm.blob_id
                WHERE fm.file_name LIKE '%.pdf'
                ORDER BY RANDOM()
                LIMIT 1
            ''')
            
            if pdf:
                size_mb = pdf['size'] / 1024 / 1024
                size_bytes = pdf['size']
                threshold_bytes = 1258291  # 1.2MB
                
                self._add_log(f"📄 取得: {pdf['file_name']}")
                self._add_log(f"📊 サイズ: {size_mb:.2f}MB ({size_bytes:,}bytes)")
                self._add_log(f"📏 閾値: 1.2MB ({threshold_bytes:,}bytes)")
                
                # 自動判定ロジック
                if size_bytes <= threshold_bytes:
                    # V1 (WebView) で表示
                    self._add_log("⚡ 判定: V1 (WebView) 使用")
                    self.current_mode = "v1"
                    self.current_pdf_data = pdf['blob_data']
                    self.current_filename = pdf['file_name']
                    
                    # V1コンポーネントを表示エリアに設定
                    self.pdf_display_area.content = self.v1_preview
                    if self.page:
                        self.pdf_display_area.update()
                    
                    # V1で読み込み実行
                    file_info = {
                        'id': pdf.get('id', 'test'),
                        'file_name': pdf['file_name']
                    }
                    self.v1_preview.show_pdf_preview(file_info)
                    
                    self._add_log("✅ V1 WebView表示完了")
                    self._update_status("V1表示完了")
                    
                else:
                    # V4 (画像) で表示
                    self._add_log("🖼️ 判定: V4 (画像変換) 使用")
                    self.current_mode = "v4"
                    self.current_pdf_data = pdf['blob_data']
                    self.current_filename = pdf['file_name']
                    
                    # V4コンポーネントを表示エリアに設定
                    self.pdf_display_area.content = self.v4_preview
                    if self.page:
                        self.pdf_display_area.update()
                    
                    # V4で読み込み実行（正しいメソッド名）
                    if self.page:
                        async def load_v4():
                            file_info = {
                                'id': pdf.get('id', 'test'),
                                'file_name': pdf['file_name']
                            }
                            await self.v4_preview.load_pdf(file_info, pdf['blob_data'])
                            self._add_log("✅ V4画像表示完了")
                            self._update_status("V4表示完了")
                        
                        self.page.run_task(load_v4)
                
            else:
                self._add_log("❌ PDF見つからず")
                self._update_status("エラー")
                
        except Exception as e:
            self._add_log(f"❌ 自動判定エラー: {str(e)[:50]}")
            self._update_status("エラー")
            print(f"[ERROR] 自動判定: {e}")
            import traceback
            traceback.print_exc()

    def _clear(self, e):
        """クリア"""
        self._add_log("🗑️ クリア実行")
        
        # 表示エリアを初期状態に戻す
        self.pdf_display_area.content = self.empty_display
        self.current_mode = "none"
        self.current_pdf_data = None
        self.current_filename = None
        
        if self.page:
            self.pdf_display_area.update()
        
        self._update_status("待機中")


def create_tab_c_content(page: ft.Page = None) -> ft.Control:
    """タブCコンテンツ作成"""
    tab_c = TabC()
    return tab_c.create_content(page)
