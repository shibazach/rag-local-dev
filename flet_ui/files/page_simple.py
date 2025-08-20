import flet as ft
from .table import FilesTable


def show_files_page():
    """ファイル管理ページのメインコンテンツ"""
    files_page = FilesPageSimple()
    layout = files_page.create_main_layout()
    # レイアウト作成後に初期データ読み込み
    files_page.load_files()
    return layout


class FilesPageSimple:
    """ファイル管理ページ（テーブル分離版）"""
    
    def __init__(self):
        # プレビューコンテナ
        self.preview_container = ft.Container()
        
        # テーブルコンポーネント
        self.files_table = FilesTable(on_file_select_callback=self.on_file_selected)
        
        # UI要素参照
        self.main_container = None
    
    def create_main_layout(self):
        """メインレイアウト作成"""
        # 左ペイン（ファイル一覧）
        left_pane = self.files_table.create_table_widget()
        
        # リサイズハンドル（50:50固定）
        resize_handle = ft.GestureDetector(
            content=ft.Container(
                width=8,
                bgcolor=ft.Colors.GREY_400,
                border_radius=4,
                content=ft.Container(
                    width=2,
                    bgcolor=ft.Colors.GREY_600,
                    margin=ft.margin.symmetric(horizontal=3)
                ),
                height=None
            ),
            mouse_cursor=ft.MouseCursor.RESIZE_COLUMN
        )
        
        # 右ペイン（プレビュー）
        right_pane = self.create_preview_pane()
        
        # 初期プレビュー設定
        self.preview_container.content = ft.Container(
            content=ft.Text("ファイルを選択してプレビューを表示", text_align=ft.TextAlign.CENTER),
            alignment=ft.alignment.center,
            expand=True
        )
        
        # メインレイアウト（8px padding、50:50比率）
        self.main_container = ft.Container(
            content=ft.Row([
                ft.Container(content=left_pane, expand=1),  # 50%
                resize_handle,
                ft.Container(content=right_pane, expand=1)  # 50%
            ], spacing=6),
            padding=ft.padding.all(8),
            expand=True
        )
        
        return self.main_container
    
    def create_preview_pane(self):
        """プレビューペイン作成"""
        return ft.Container(
            content=self.preview_container,
            bgcolor=ft.Colors.WHITE,
            border=ft.border.all(1, ft.Colors.GREY_300),
            border_radius=8,
            padding=ft.padding.all(8),
            expand=True
        )
    
    def load_files(self):
        """ファイル一覧を読み込み"""
        self.files_table.load_files()
    
    def on_file_selected(self, file_id):
        """ファイル選択時のコールバック"""
        if file_id:
            self.show_pdf_preview(file_id)
        else:
            self.show_empty_preview()
    
    def show_empty_preview(self):
        """空のプレビュー表示"""
        self.preview_container.content = ft.Container(
            content=ft.Text("ファイルを選択してプレビューを表示", text_align=ft.TextAlign.CENTER),
            alignment=ft.alignment.center,
            expand=True
        )
        try:
            if self.preview_container and hasattr(self.preview_container, 'page') and self.preview_container.page:
                self.preview_container.update()
        except:
            pass
    
    def show_pdf_preview(self, file_id):
        """PDFプレビュー表示（行選択時）"""
        # 選択されたファイル情報を取得
        file_info = self.files_table.get_selected_file()
        if not file_info:
            return
        
        file_name = file_info.get('file_name', 'Unknown')
        
        # PDFプレビューコンテンツ（シンプル版）
        preview_content = ft.Container(
            content=ft.Column([
                # PDF表示領域（将来的に実際のPDF表示可能）
                ft.Container(
                    content=ft.Column([
                        ft.Icon(ft.Icons.PICTURE_AS_PDF, size=64, color=ft.Colors.RED),
                        ft.Container(height=20),
                        ft.Text(
                            file_name,
                            size=14,
                            weight=ft.FontWeight.BOLD,
                            text_align=ft.TextAlign.CENTER,
                            color=ft.Colors.GREY_700
                        ),
                        ft.Container(height=20),
                        ft.Container(
                            content=ft.Text(
                                "PDFプレビュー機能\n実装予定",
                                text_align=ft.TextAlign.CENTER,
                                size=12,
                                color=ft.Colors.GREY_500
                            ),
                            bgcolor=ft.Colors.GREY_100,
                            padding=ft.padding.all(20),
                            border_radius=8,
                            border=ft.border.all(1, ft.Colors.GREY_300)
                        )
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    alignment=ft.alignment.center,
                    expand=True
                )
            ], spacing=0, expand=True),
            alignment=ft.alignment.center,
            expand=True
        )
        
        self.preview_container.content = preview_content
        try:
            if self.preview_container and hasattr(self.preview_container, 'page') and self.preview_container.page:
                self.preview_container.update()
        except:
            pass
