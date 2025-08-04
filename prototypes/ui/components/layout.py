"""
共通レイアウトコンポーネント - new/系templates準拠
"""

from nicegui import ui
from typing import Optional, Dict, Any

# 絶対インポートでSimpleAuthを参照（相対インポート回避）
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

class SimpleAuth:
    """簡易認証システム - 一時的に再定義（インポート問題回避）"""
    _current_user: Optional[Dict[str, Any]] = None
    
    @classmethod
    def get_current_user(cls) -> Optional[Dict[str, Any]]:
        return cls._current_user
    
    @classmethod
    def is_admin(cls) -> bool:
        user = cls.get_current_user()
        return user and user.get("role") == "admin"
    
    @classmethod
    def is_authenticated(cls) -> bool:
        return cls._current_user is not None
    
    @classmethod
    def logout(cls):
        cls._current_user = None

class RAGHeader:
    """new/準拠の共通ヘッダー（98点仕様）"""
    
    def __init__(self, show_site_name: bool = True, current_page: str = ""):
        self.show_site_name = show_site_name
        self.current_page = current_page
        self.create_header()
    
    def create_header(self):
        """ヘッダー作成（完全画面幅対応・padding完全ゼロ）"""
        with ui.element('div').style('position:fixed;top:0;left:0;right:0;width:100%;height:48px;background:#334155;z-index:1000;display:flex;align-items:center;padding:0;margin:0;overflow:hidden;'):
            
            # 左側：サイト名（固定幅160px・🏠なし）
            with ui.element('div').style('width:160px;display:flex;align-items:center;'):
                if self.show_site_name:
                    ui.label('R&D RAGシステム').style('color:white;font-size:16px;font-weight:bold;margin-left:16px;')
            
            # 中央：ナビゲーション（レスポンシブ・高さ48px固定・ペッタリ折り返し）
            with ui.element('div').style('flex:1;display:flex;align-items:center;justify-content:center;gap:4px;flex-wrap:wrap;height:48px;padding:0 4px;overflow:hidden;'):
                self._nav_button('🏠', 'ホーム', '/', self.current_page == "index")
                self._nav_button('💬', 'チャット', '/chat', self.current_page == "chat")
                self._nav_button('📁', 'ファイル', '/files', self.current_page == "files")
                self._nav_button('📤', 'アップロード', '/upload', self.current_page == "upload")
                self._nav_button('🔄', 'OCR調整', '/ocr-adjustment', self.current_page == "ocr-adjustment")
                self._nav_button('⚙️', 'データ登録', '/data-registration', self.current_page == "data-registration")
                self._nav_button('🧪', '配置テスト', '/arrangement-test', self.current_page == "test")
                self._nav_button('⚡', '管理', '/admin', self.current_page == "admin")
            
            # 右側：認証部分（固定幅160px・右寄せ）
            with ui.element('div').style('width:160px;display:flex;align-items:center;justify-content:flex-end;gap:8px;margin-right:16px;'):
                ui.label('●').style('color:#10b981;font-size:12px;')
                ui.label('admin').style('color:white;font-size:14px;')
                ui.button('ログアウト', on_click=lambda: ui.navigate.to('/login')).style('background:#3b82f6;color:white;border:none;padding:4px 12px;border-radius:4px;font-size:12px;cursor:pointer;')
    
    def _nav_button(self, icon: str, label: str, path: str, is_current: bool = False):
        """ナビゲーションボタン（現在ページ対応・レスポンシブ）"""
        # 現在ページかどうかで色とクリック動作を分岐
        text_color = '#ff6b6b' if is_current else 'white'  # 現在ページは赤字
        cursor_style = 'default' if is_current else 'pointer'
        click_handler = None if is_current else lambda: ui.navigate.to(path)
        
        with ui.element('div').style(f'display:flex;align-items:center;gap:3px;cursor:{cursor_style};padding:2px 6px;border-radius:3px;transition:background 0.2s;white-space:nowrap;height:auto;line-height:1;').on('click', click_handler):
            ui.label(icon).style(f'color:{text_color};font-size:14px;line-height:1;')
            ui.label(label).style(f'color:{text_color};font-size:12px;line-height:1;')


class RAGFooter:
    """共通フッター - ステータスバー形式"""
    
    def __init__(self, show_status: bool = True):
        self.show_status = show_status
        if show_status:
            self.create_status_bar()
    
    def create_status_bar(self):
        """ステータスバー作成（完全画面幅・隙間ゼロ）"""
        with ui.element('div').style('position:fixed;bottom:0;left:0;right:0;width:100%;height:24px;background:#374151;color:white;display:flex;align-items:center;justify-content:space-between;padding:0;margin:0;font-size:12px;z-index:999;'):
            ui.label('システム: 正常稼働中').style('color:#10b981;margin-left:16px;')
            ui.label('接続: OK').style('color:#3b82f6;margin-right:16px;')

# RAGLayoutクラスは廃止
# 理由: main.pyでの一元的CSS管理と矛盾、!important濫用でUI設計ポリシー違反
# 代替: 各ページでRAGHeader + MainContentArea + RAGFooterを直接使用

class MainContentArea:
    """メインコンテンツエリア - c13方式完全制御コンテナ"""
    
    def __init__(self, content_padding: str = "8px", header_height: str = "48px", footer_height: str = "24px"):
        """
        c13方式: nicegui-contentをリセットし、その中に完全制御されたコンテナを配置
        
        Args:
            content_padding: コンテンツ内部の余白（デフォルト8px）
            header_height: ヘッダー高さ（デフォルト48px）
            footer_height: フッター高さ（デフォルト24px）
        """
        self.content_padding = content_padding
        self.header_height = header_height
        self.footer_height = footer_height
        self.container = None
        
    def __enter__(self):
        """c13方式メインコンテンツエリア開始"""
        # 完全制御コンテナ（c13方式）
        # nicegui-contentは既にmain.pyでリセット済みという前提
        self.container = ui.element('div').style(
            # position:fixedヘッダー・フッターに合わせた配置
            f'margin-top:{self.header_height};'          # ヘッダー分のオフセット
            f'margin-bottom:{self.footer_height};'       # フッター分のスペース確保
            'margin-left:0;'                             # 左右余白ゼロ
            'margin-right:0;'
            'padding:0;'                                 # 外部パディングゼロ
            'width:100%;'                                # 全幅使用
            f'height:calc(100vh - {self.header_height} - {self.footer_height});'  # 正確な高さ計算
            'overflow:hidden;'                           # オーバーフロー制御
            'position:relative;'                         # 子要素基準
            'box-sizing:border-box;'                     # ボックスサイズ計算明示
            'display:flex;'                              # フレックスレイアウト
            'flex-direction:column;'                     # 縦方向配置
        )
        
        # 内部コンテンツエリア（実際のpadding/marginを持つ）
        self.content_area = ui.element('div').style(
            'flex:1;'                                    # 残り空間を全て使用
            f'padding:{self.content_padding};'           # コンテンツ用の適切な余白
            'margin:0;'                                  # 外部マージンゼロ
            'overflow-y:auto;'                           # 内部スクロール
            'overflow-x:hidden;'                         # 横スクロール禁止
            'box-sizing:border-box;'                     # パディング含む計算
        )
        
        # コンテナを開始し、内部エリアのコンテキストを返す
        self.container.__enter__()
        return self.content_area.__enter__()
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """メインコンテンツエリア終了"""
        result = self.content_area.__exit__(exc_type, exc_val, exc_tb)
        self.container.__exit__(exc_type, exc_val, exc_tb)
        return result