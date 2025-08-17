"""
PDFビューアコンポーネント
"""
from nicegui import ui
from typing import Optional
import base64
from app.config import logger

class PDFViewer:
    """PDFビューアコンポーネント"""
    
    def __init__(self, container=None, height: str = "100%", width: str = "100%"):
        """
        Args:
            container: PDFを表示する親コンテナ（Noneの場合は現在のコンテキスト）
            height: ビューアの高さ
            width: ビューアの幅
        """
        self.container = container
        self.height = height
        self.width = width
        self.current_file_id = None
        self.viewer_element = None
        self._setup_viewer()
    
    def _setup_viewer(self):
        """ビューアのセットアップ"""
        parent = self.container if self.container else ui.element('div')
        
        with parent:
            # ビューアコンテナ
            self.viewer_container = ui.element('div').style(
                f'width: {self.width}; height: {self.height}; '
                'display: flex; flex-direction: column; background: #f3f4f6;'
            )
            
            with self.viewer_container:
                # 初期状態（PDFが選択されていない）
                self.empty_state = ui.element('div').style(
                    'width: 100%; height: 100%; display: flex; '
                    'align-items: center; justify-content: center; color: #9ca3af;'
                )
                with self.empty_state:
                    with ui.element('div').style('text-align: center;'):
                        ui.icon('picture_as_pdf', size='4em').style('opacity: 0.5;')
                        ui.label('PDFを選択してください').style('font-size: 16px; margin-top: 16px;')
                
                # PDFビューア（初期は非表示）
                self.pdf_frame = ui.element('iframe').style(
                    'width: 100%; height: 100%; border: none; display: none;'
                ).props('id="pdf-viewer-frame"')
                
                # エラー状態（初期は非表示）
                self.error_state = ui.element('div').style(
                    'width: 100%; height: 100%; display: none; '
                    'align-items: center; justify-content: center; color: #ef4444;'
                )
                with self.error_state:
                    with ui.element('div').style('text-align: center;'):
                        ui.icon('error_outline', size='4em')
                        self.error_message = ui.label('PDFの読み込みに失敗しました').style(
                            'font-size: 16px; margin-top: 16px;'
                        )
    
    async def load_pdf(self, file_id: str, file_service=None):
        """
        PDFを読み込んで表示
        
        Args:
            file_id: ファイルID
            file_service: ファイルサービスインスタンス
        """
        try:
            if not file_service:
                from app.services.file_service import get_file_service
                file_service = get_file_service()
            
            # ファイル情報を取得
            file_info = file_service.get_file_info(file_id)
            if not file_info:
                await self._show_error("ファイルが見つかりません")
                return
            
            # PDFでない場合はエラー
            mime_type = file_info.get('mime_type', '')
            if not mime_type.startswith('application/pdf'):
                await self._show_error("このファイルはPDFではありません")
                return
            
            # バイナリデータを取得
            blob_data = file_info.get('blob_data')
            if not blob_data:
                await self._show_error("ファイルデータが見つかりません")
                return
            
            # Base64エンコード
            if isinstance(blob_data, memoryview):
                blob_data = blob_data.tobytes()
            pdf_base64 = base64.b64encode(blob_data).decode('utf-8')
            
            # PDFを表示
            await self._display_pdf(pdf_base64, file_info.get('filename', 'document.pdf'))
            self.current_file_id = file_id
            
        except Exception as e:
            logger.error(f"Failed to load PDF: {e}")
            await self._show_error(f"エラー: {str(e)}")
    
    async def _display_pdf(self, pdf_base64: str, filename: str):
        """PDFを表示"""
        # 状態を更新
        self.empty_state.style('display: none;')
        self.error_state.style('display: none;')
        self.pdf_frame.style('display: block;')
        
        # PDFを表示（PDF.jsを使用）
        pdf_url = f'data:application/pdf;base64,{pdf_base64}'
        
        # NiceGUIではiframeのsrcを直接設定できないため、JavaScriptで設定
        ui.run_javascript(f'''
            const frame = document.getElementById("pdf-viewer-frame");
            if (frame) {{
                // PDF.jsビューアを使用（ブラウザ内蔵）
                frame.src = "{pdf_url}";
            }}
        ''')
    
    async def _show_error(self, message: str):
        """エラーを表示"""
        self.empty_state.style('display: none;')
        self.pdf_frame.style('display: none;')
        self.error_state.style('display: flex;')
        self.error_message.text = message
    
    def clear(self):
        """ビューアをクリア"""
        self.empty_state.style('display: flex;')
        self.pdf_frame.style('display: none;')
        self.error_state.style('display: none;')
        self.current_file_id = None
        
        # iframeをクリア
        ui.run_javascript('''
            const frame = document.getElementById("pdf-viewer-frame");
            if (frame) {
                frame.src = "about:blank";
            }
        ''')


class PDFViewerDialog:
    """PDFビューアダイアログ"""
    
    def __init__(self):
        """初期化"""
        self.dialog = None
        self.pdf_viewer = None
        self._setup_dialog()
    
    def _setup_dialog(self):
        """ダイアログのセットアップ"""
        self.dialog = ui.dialog().props('maximized persistent')
        
        with self.dialog:
            with ui.card().style('width: 100%; height: 100%; margin: 0; display: flex; flex-direction: column;'):
                # ヘッダー
                with ui.element('div').style(
                    'display: flex; justify-content: space-between; align-items: center; '
                    'padding: 16px; border-bottom: 1px solid #e5e7eb;'
                ):
                    self.title_label = ui.label('PDFプレビュー').style('font-size: 18px; font-weight: 600;')
                    ui.button(
                        icon='close',
                        on_click=lambda: self.close()
                    ).props('flat round')
                
                # PDFビューアコンテナ
                viewer_container = ui.element('div').style('flex: 1; overflow: hidden; padding: 0;')
                self.pdf_viewer = PDFViewer(viewer_container, height="100%", width="100%")
    
    async def show_pdf(self, file_id: str, filename: str = None, file_service=None):
        """
        PDFを表示
        
        Args:
            file_id: ファイルID
            filename: ファイル名（タイトル表示用）
            file_service: ファイルサービスインスタンス
        """
        if filename:
            self.title_label.text = f'PDFプレビュー - {filename}'
        
        self.dialog.open()
        await self.pdf_viewer.load_pdf(file_id, file_service)
    
    def close(self):
        """ダイアログを閉じる"""
        if self.pdf_viewer:
            self.pdf_viewer.clear()
        self.dialog.close()


