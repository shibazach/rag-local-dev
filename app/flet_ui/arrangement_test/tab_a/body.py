#!/usr/bin/env python3
"""
Flet RAGシステム - 配置テスト タブA (レイアウト)
4分割レイアウトテスト
"""

import flet as ft


class TabA:
    """タブA: レイアウトテスト"""
    
    def __init__(self):
        pass
    
    def create_content(self, page: ft.Page = None) -> ft.Control:
        """タブAコンテンツ作成"""
        # 4つのペイン作成
        # 左上：日本語フォントテスト表示
        font_test_content = ft.Column([
            ft.Text("日本語フォント表示テスト", size=16, weight=ft.FontWeight.BOLD),
            ft.Divider(height=1, color=ft.Colors.GREY_300),
            
            # デフォルトフォント（2段階拡大+全黒色）
            ft.Text("デフォルト: 日本語テキスト（ひらがな・カタカナ・漢字）", size=16, color=ft.Colors.BLACK),
            ft.Text("Default: 这是中文文本", size=16, color=ft.Colors.BLACK),
            
            # font_family指定テスト（存在する場合）
            ft.Text("Arial指定: 日本語テキスト（ひらがな・カタカナ・漢字）", 
                   size=16, font_family="Arial", color=ft.Colors.BLACK),
            ft.Text("Helvetica指定: 日本語テキスト（ひらがな・カタカナ・漢字）", 
                   size=16, font_family="Helvetica", color=ft.Colors.BLACK),
            ft.Text("Courier指定: 日本語テキスト（ひらがな・カタカナ・漢字）", 
                   size=16, font_family="Courier New", color=ft.Colors.BLACK),
            
            # OCR詳細設定パネルと同じスタイルで表示（2段階拡大+全黒色）
            ft.Text("OCRパネル用統一スタイル:", size=14, color=ft.Colors.BLACK),
            ft.Text("認識言語:", size=18, weight=ft.FontWeight.W_500, color=ft.Colors.BLACK),
            ft.Text("簡易説明テキスト", size=15, color=ft.Colors.BLACK),
            
        ], spacing=4, scroll=ft.ScrollMode.AUTO, tight=True)
        
        # 根本問題修正テスト（Web検索結果の解決法適用）
        def test_dialog_click(e):
            def close_dialog(e):
                page.close(dialog)
                print("ダイアログを閉じました")
            
            def on_dismiss(e):
                print("ダイアログがdismissされました")
            
            dialog = ft.AlertDialog(
                title=ft.Text("🚨 根本問題修正テスト"),
                content=ft.Text("page.open()方式でのダイアログテストです"),
                actions=[ft.TextButton("OK", on_click=close_dialog)],
                on_dismiss=on_dismiss,
                modal=True
            )
            
            # Web検索結果の推奨方法: page.open(dlg)
            page.open(dialog)
            print(f"🔍 page.open()でダイアログを開きました")
        
        # テストボタンをフォントテスト下部に追加
        font_test_content.controls.extend([
            ft.Container(height=16),
            ft.ElevatedButton(
                text="🧪 ダイアログテスト (縦スライダーなし)",
                on_click=test_dialog_click,
                bgcolor=ft.Colors.BLUE_100,
                width=300
            )
        ])
        
        top_left = ft.Container(
            content=font_test_content,
            bgcolor=ft.Colors.RED_100,
            padding=ft.padding.all(12),
            expand=True,
            border=ft.border.all(2, ft.Colors.RED_300)
        )
        
        bottom_left = ft.Container(
            content=ft.Text("左下", size=20, text_align=ft.TextAlign.CENTER),
            bgcolor=ft.Colors.BLUE_100,
            alignment=ft.alignment.center,
            expand=True,
            border=ft.border.all(2, ft.Colors.BLUE_300)
        )
        
        # 右上：自作アコーディオンテスト（関数型）
        from app.flet_ui.shared.custom_accordion import make_accordion
        
        # テスト用コンテンツ
        content1 = ft.Column([
            ft.Text("基本設定のテスト内容"),
            ft.TextField(label="テスト入力", width=200),
            ft.Switch(label="テストスイッチ")
        ])
        
        content2 = ft.Column([
            ft.Text("高精度設定のテスト内容"),
            ft.Slider(min=0, max=100, value=50, label="閾値"),
            ft.Dropdown(
                options=[ft.dropdown.Option("Option1"), ft.dropdown.Option("Option2")],
                value="Option1",
                width=150
            )
        ])
        
        content3 = ft.Column([
            ft.Text("詳細設定のテスト内容"),
            ft.Row([
                ft.Checkbox(label="チェック1"),
                ft.Checkbox(label="チェック2")
            ]),
            ft.ElevatedButton("テストボタン")
        ])
        
        # アコーディオン作成（関数型バージョン）
        # 実際のページインスタンスを使用
        if page is None:
            # フォールバック：ダミーページ（本来は避けるべき）
            test_page = ft.Page()
            test_page.update = lambda: None
            actual_page = test_page
        else:
            actual_page = page
        
        accordion = make_accordion(
            page=actual_page,
            items=[
                ("基本設定", content1, True),
                ("高精度設定", content2, False),
                ("詳細設定", content3, False),
            ],
            single_open=True,
            header_bg=ft.Colors.BLUE_50,
            body_bg=ft.Colors.BLUE_50,
            spacing=4
        )
        
        top_right = ft.Container(
            content=ft.Column([
                ft.Text("自作アコーディオンテスト", size=14, weight=ft.FontWeight.BOLD),
                accordion
            ], spacing=8),
            bgcolor=ft.Colors.GREEN_100,
            padding=ft.padding.all(8),
            expand=True,
            border=ft.border.all(2, ft.Colors.GREEN_300)
        )
        
        # 右下：大容量PDF対応プレビューテスト
        from app.flet_ui.shared.pdf_large_preview import create_large_pdf_preview
        from app.services.file_service import get_file_service
        
        # 大容量PDFプレビュー作成
        pdf_preview = create_large_pdf_preview()
        
        def test_large_pdf_click(e):
            """大容量PDFテストボタン"""
            try:
                from app.core.db_simple import fetch_all
                
                # DB直接アクセスで大容量PDFを取得
                pdf_files = fetch_all('''
                    SELECT fb.id, fm.file_name, fm.mime_type, LENGTH(fb.blob_data) as blob_size
                    FROM files_blob fb
                    LEFT JOIN files_meta fm ON fb.id = fm.blob_id
                    WHERE fm.file_name LIKE '%.pdf' OR fm.mime_type LIKE '%pdf%'
                    ORDER BY LENGTH(fb.blob_data) DESC
                    LIMIT 5
                ''')
                
                if not pdf_files:
                    print("❌ テスト用PDFファイルがDBに存在しません")
                    return
                
                # 最大サイズのPDFでテスト
                largest_pdf = pdf_files[0]
                size_mb = largest_pdf['blob_size'] / (1024 * 1024) if largest_pdf['blob_size'] else 0
                
                # ファイル情報を適切な形式に変換
                file_info = {
                    'id': largest_pdf['id'],
                    'file_name': largest_pdf['file_name'],
                    'mime_type': largest_pdf['mime_type']
                }
                
                print(f"🚀 大容量PDFテスト開始: {file_info['file_name']} ({size_mb:.1f}MB)")
                print(f"   ファイルID: {file_info['id']}")
                pdf_preview.show_pdf_preview(file_info)
                    
            except Exception as e:
                print(f"❌ 大容量PDFテストエラー: {e}")
                import traceback
                traceback.print_exc()
        
        def test_image_mode_click(e):
            """画像モード強制テスト"""
            try:
                from app.core.db_simple import fetch_all
                
                # 中程度サイズのPDFで画像モードテスト（レンダリング時間短縮）
                pdf_files = fetch_all('''
                    SELECT fb.id, fm.file_name, fm.mime_type, LENGTH(fb.blob_data) as blob_size
                    FROM files_blob fb
                    LEFT JOIN files_meta fm ON fb.id = fm.blob_id
                    WHERE fm.file_name LIKE '%.pdf' OR fm.mime_type LIKE '%pdf%'
                    ORDER BY LENGTH(fb.blob_data) ASC
                    LIMIT 5
                ''')
                
                if pdf_files:
                    # 中程度のPDFで画像モードテスト
                    test_pdf = pdf_files[min(2, len(pdf_files)-1)]  # 3番目の小さなPDF
                    size_mb = test_pdf['blob_size'] / (1024 * 1024) if test_pdf['blob_size'] else 0
                    
                    file_info = {
                        'id': test_pdf['id'],
                        'file_name': test_pdf['file_name'],
                        'mime_type': test_pdf['mime_type']
                    }
                    
                    print(f"🖼️ 画像モード強制テスト開始: {file_info['file_name']} ({size_mb:.2f}MB)")
                    print(f"   ファイルID: {file_info['id']}")
                    
                    # 強制的に画像モードに設定
                    pdf_preview._force_image_mode = True
                    pdf_preview.show_pdf_preview(file_info)
                else:
                    print("❌ 画像モードテスト: PDFファイルが見つかりません")
                    
            except Exception as e:
                print(f"❌ 画像モードテストエラー: {e}")
                import traceback
                traceback.print_exc()
        
        def test_stream_server_click(e):
            """PDFストリーミングサーバテスト"""
            try:
                from app.core.db_simple import fetch_one
                import asyncio
                
                # 中程度サイズのPDFでストリーミングテスト
                test_pdf = fetch_one('''
                    SELECT fb.id, fm.file_name, LENGTH(fb.blob_data) as blob_size, fb.blob_data
                    FROM files_blob fb
                    LEFT JOIN files_meta fm ON fb.id = fm.blob_id
                    WHERE fm.file_name LIKE '%.pdf'
                    ORDER BY LENGTH(fb.blob_data)
                    LIMIT 1 OFFSET 3
                ''')
                
                if test_pdf:
                    size_mb = test_pdf['blob_size'] / (1024 * 1024)
                    print(f"🌐 PDFストリーミングサーバテスト: {test_pdf['file_name']} ({size_mb:.2f}MB)")
                    
                    # ストリーミングサーバを直接テスト
                    async def test_streaming():
                        from app.flet_ui.shared.pdf_stream_server import serve_pdf_from_bytes
                        pdf_url, server = await serve_pdf_from_bytes(test_pdf['blob_data'], test_pdf['id'])
                        print(f"✅ PDFストリーミングURL生成完了: {pdf_url}")
                        return pdf_url
                    
                    # 非同期実行
                    try:
                        loop = asyncio.get_event_loop()
                        loop.create_task(test_streaming())
                    except RuntimeError:
                        asyncio.run(test_streaming())
                        
                else:
                    print("❌ ストリーミングテスト用PDFが見つかりません")
                    
            except Exception as e:
                print(f"❌ ストリーミングサーバテストエラー: {e}")
                import traceback
                traceback.print_exc()
        
        def test_clear_preview_click(e):
            """プレビュークリア/リセットテスト"""
            try:
                print("🧹 プレビューをクリアします")
                pdf_preview.show_empty_preview()
                pdf_preview._force_image_mode = False  # 画像モード強制フラグリセット
                print("✅ プレビュークリア完了")
            except Exception as e:
                print(f"❌ プレビュークリアエラー: {e}")
        
        test_buttons = ft.Column([
            ft.Text("大容量PDF対応テスト", size=14, weight=ft.FontWeight.BOLD),
            ft.Row([
                ft.ElevatedButton(
                    text="最大サイズPDFテスト",
                    on_click=test_large_pdf_click,
                    width=180,
                    bgcolor=ft.Colors.ORANGE_100
                ),
                ft.ElevatedButton(
                    text="画像モード強制テスト",
                    on_click=test_image_mode_click,
                    width=180,
                    bgcolor=ft.Colors.PURPLE_100
                )
            ], spacing=8),
            ft.Row([
                ft.ElevatedButton(
                    text="ストリーミング直接テスト",
                    on_click=test_stream_server_click,
                    width=180,
                    bgcolor=ft.Colors.BLUE_100
                ),
                ft.ElevatedButton(
                    text="プレビュークリア",
                    on_click=test_clear_preview_click,
                    width=180,
                    bgcolor=ft.Colors.GREY_200
                )
            ], spacing=8),
            pdf_preview
        ], tight=True, spacing=8)
        
        bottom_right = ft.Container(
            content=test_buttons,
            bgcolor=ft.Colors.YELLOW_100,
            padding=ft.padding.all(8),
            expand=True,
            border=ft.border.all(2, ft.Colors.YELLOW_600)
        )
        
        # 左ペイン（上下分割）
        left_column = ft.Column([
            top_left,
            ft.Divider(height=1, thickness=1, color=ft.Colors.GREY_400),
            bottom_left
        ], expand=True, spacing=0)
        
        # 右ペイン（上下分割）
        right_column = ft.Column([
            top_right,
            ft.Divider(height=1, thickness=1, color=ft.Colors.GREY_400),
            bottom_right
        ], expand=True, spacing=0)
        
        # メインレイアウト（左右分割）
        main_layout = ft.Row([
            left_column,
            ft.VerticalDivider(width=1, thickness=1, color=ft.Colors.GREY_400),
            right_column
        ], spacing=0, expand=True)
        
        return ft.Container(
            content=main_layout,
            expand=True,
            padding=ft.padding.all(8)
        )