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
        
        # 大容量PDFプレビューコンポーネント
        from app.flet_ui.shared.pdf_large_preview import create_large_pdf_preview
        self.pdf_preview = create_large_pdf_preview()
        
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
        
        # テストボタン群
        test_buttons = ft.Row([
            ft.ElevatedButton(
                text="🎯 最大サイズPDFテスト",
                on_click=self._test_largest_pdf,
                bgcolor=ft.Colors.ORANGE_100,
                width=200,
                height=40
            ),
            ft.ElevatedButton(
                text="🖼️ 画像モード強制テスト", 
                on_click=self._test_image_mode,
                bgcolor=ft.Colors.PURPLE_100,
                width=200,
                height=40
            ),
            ft.ElevatedButton(
                text="🌐 ストリーミングテスト",
                on_click=self._test_streaming,
                bgcolor=ft.Colors.BLUE_100,
                width=200,
                height=40
            ),
            ft.ElevatedButton(
                text="🧹 クリア",
                on_click=self._clear_preview,
                bgcolor=ft.Colors.GREY_200,
                width=120,
                height=40
            )
        ], alignment=ft.MainAxisAlignment.CENTER, spacing=10)
        
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
        
        # 右ペイン: PDFプレビューエリア
        pdf_panel = ft.Container(
            content=ft.Column([
                ft.Text("📄 PDFプレビュー", size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_700),
                ft.Container(
                    content=self.pdf_preview,
            expand=True,
                    padding=ft.padding.all(4),
                    bgcolor=ft.Colors.GREY_50,
                    border_radius=4
                )
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
    
    def _test_largest_pdf(self, e):
        """最大サイズPDFテスト"""
        self._add_log("🔍 DB内最大サイズPDFを検索中...")
        self._update_status("DB検索中")
        
        # Flet用非同期実行
        if self.page:
            self.page.run_task(self._async_test_largest_pdf)
        else:
            # フォールバック（通常は使用されない）
            import threading
            threading.Thread(target=lambda: asyncio.run(self._async_test_largest_pdf())).start()
    
    async def _async_test_largest_pdf(self):
        """最大サイズPDF非同期テスト"""
        try:
            from app.core.db_simple import fetch_all
            
            # DB内最大PDFを取得
            pdf_files = fetch_all('''
                SELECT fb.id, fm.file_name, fm.mime_type, LENGTH(fb.blob_data) as blob_size
                FROM files_blob fb
                LEFT JOIN files_meta fm ON fb.id = fm.blob_id
                WHERE fm.file_name LIKE '%.pdf' OR fm.mime_type LIKE '%pdf%'
                ORDER BY LENGTH(fb.blob_data) DESC
                LIMIT 1
            ''')
            
            if not pdf_files:
                self._add_log("❌ PDFファイルが見つかりません")
                self._update_status("エラー: PDFなし")
                return
            
            largest_pdf = pdf_files[0]
            size_mb = largest_pdf['blob_size'] / (1024 * 1024) if largest_pdf['blob_size'] else 0
            
            file_info = {
                'id': largest_pdf['id'],
                'file_name': largest_pdf['file_name'],
                'mime_type': largest_pdf['mime_type']
            }
            
            self._add_log(f"✅ 最大PDF発見: {file_info['file_name']} ({size_mb:.1f}MB)")
            self._update_status("PDF表示準備中")
            
            # PDF表示実行
            self.pdf_preview.show_pdf_preview(file_info)
            self._add_log("🚀 PDF表示コマンド実行完了")
            self._update_status(f"表示中: {size_mb:.1f}MB")
            
        except Exception as e:
            error_msg = f"❌ 最大PDFテストエラー: {str(e)}"
            self._add_log(error_msg)
            self._update_status("エラー発生")
            import traceback
            print(f"[PDF-TEST-ERROR] {traceback.format_exc()}")
    
    def _test_image_mode(self, e):
        """画像モード強制テスト"""
        self._add_log("🖼️ 画像モード強制テスト開始")
        self._update_status("画像モード準備中")
        
        if self.page:
            self.page.run_task(self._async_test_image_mode)
        else:
            import threading
            threading.Thread(target=lambda: asyncio.run(self._async_test_image_mode())).start()
    
    async def _async_test_image_mode(self):
        """画像モード非同期テスト"""
        try:
            from app.core.db_simple import fetch_all
            
            # 中程度サイズのPDFで画像モードテスト
            pdf_files = fetch_all('''
                SELECT fb.id, fm.file_name, fm.mime_type, LENGTH(fb.blob_data) as blob_size
                FROM files_blob fb
                LEFT JOIN files_meta fm ON fb.id = fm.blob_id
                WHERE fm.file_name LIKE '%.pdf'
                ORDER BY LENGTH(fb.blob_data) ASC
                LIMIT 1 OFFSET 2
            ''')
            
            if pdf_files:
                test_pdf = pdf_files[0]
                size_mb = test_pdf['blob_size'] / (1024 * 1024)
                
                file_info = {
                    'id': test_pdf['id'],
                    'file_name': test_pdf['file_name'],
                    'mime_type': test_pdf['mime_type']
                }
                
                self._add_log(f"✅ テスト対象: {file_info['file_name']} ({size_mb:.2f}MB)")
                
                # 強制的に画像モードに設定
                self.pdf_preview._force_image_mode = True
                self.pdf_preview.show_pdf_preview(file_info)
                
                self._add_log("🎯 画像モード強制実行")
                self._update_status("画像レンダリング中")
            else:
                self._add_log("❌ テスト用PDFが見つかりません")
                self._update_status("エラー: ファイルなし")
                
        except Exception as e:
            error_msg = f"❌ 画像モードテストエラー: {str(e)}"
            self._add_log(error_msg)
            self._update_status("エラー発生")
    
    def _test_streaming(self, e):
        """ストリーミング直接テスト"""
        self._add_log("🌐 ストリーミングサーバ直接テスト開始")
        self._update_status("サーバテスト中")
        
        if self.page:
            self.page.run_task(self._async_test_streaming)
        else:
            import threading
            threading.Thread(target=lambda: asyncio.run(self._async_test_streaming())).start()
    
    async def _async_test_streaming(self):
        """ストリーミング直接非同期テスト"""
        try:
            from app.core.db_simple import fetch_one
            
            # テスト用PDFデータ取得
            test_pdf = fetch_one('''
                SELECT fb.id, fm.file_name, LENGTH(fb.blob_data) as blob_size, fb.blob_data
                FROM files_blob fb
                LEFT JOIN files_meta fm ON fb.id = fm.blob_id
                WHERE fm.file_name LIKE '%.pdf'
                ORDER BY LENGTH(fb.blob_data)
                LIMIT 1 OFFSET 1
            ''')
            
            if test_pdf:
                size_mb = test_pdf['blob_size'] / (1024 * 1024)
                self._add_log(f"📄 テスト用PDF: {test_pdf['file_name']} ({size_mb:.2f}MB)")
                
                # PDFストリーミングサーバ開始
                from app.flet_ui.shared.pdf_stream_server import serve_pdf_from_bytes
                pdf_url, server = await serve_pdf_from_bytes(test_pdf['blob_data'], test_pdf['id'])
                
                self._add_log(f"✅ ストリーミングURL生成: {pdf_url}")
                self._update_status("ストリーミング成功")
                
                # HTTPクライアントテスト
                import aiohttp
                async with aiohttp.ClientSession() as session:
                    async with session.get(pdf_url) as response:
                        self._add_log(f"🔗 HTTPテスト: {response.status} ({response.headers.get('Content-Length', '不明')} bytes)")
                        
            else:
                self._add_log("❌ テスト用PDFが見つかりません")
                self._update_status("エラー: ファイルなし")
                
        except Exception as e:
            error_msg = f"❌ ストリーミングテストエラー: {str(e)}"
            self._add_log(error_msg)
            self._update_status("エラー発生")
    
    def _clear_preview(self, e):
        """プレビュークリア"""
        self._add_log("🧹 プレビューをクリア中...")
        self.pdf_preview.show_empty_preview()
        self.pdf_preview._force_image_mode = False  # 画像モード強制フラグをリセット
        self._update_status("待機中")
        self._add_log("✅ クリア完了")