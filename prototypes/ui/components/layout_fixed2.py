"""
共通レイアウトコンポーネント - new/系templates準拠（margin-top修正版）
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
                self._nav_button('🧪', '配置テスト', '/test-panel', self.current_page == "test")
                self._nav_button('⚡', '管理', '/admin', self.current_page == "admin")
            
            # 右側：ユーザー情報・ログアウト（固定幅160px）
            with ui.element('div').style('width:160px;display:flex;align-items:center;justify-content:flex-end;gap:8px;margin-right:16px;'):
                # ステータス表示
                ui.label('●').style('color:#10b981;font-size:12px;')
                ui.label('admin').style('color:white;font-size:14px;')
                # ログアウトボタン
                ui.button('ログアウト', on_click=self._logout).style('background:#3b82f6;color:white;border:none;padding:4px 12px;border-radius:4px;font-size:12px;cursor:pointer;')
    
    def _nav_button(self, icon: str, text: str, path: str, is_active: bool = False):
        """ナビゲーションボタン作成"""
        if is_active:
            # アクティブ状態（赤色強調）
            color_style = 'color:#ff6b6b;'
            cursor_style = 'cursor:default;'
        else:
            # 非アクティブ状態（白色・ホバー効果）
            color_style = 'color:white;'
            cursor_style = 'cursor:pointer;'
        
        with ui.element('div').style(f'display:flex;align-items:center;gap:3px;{cursor_style}padding:2px 6px;border-radius:3px;transition:background 0.2s;white-space:nowrap;height:auto;line-height:1;'):
            if not is_active:
                ui.element('div').on('click', lambda: ui.navigate.to(path))
            
            ui.label(icon).style(f'{color_style}font-size:14px;line-height:1;')
            ui.label(text).style(f'{color_style}font-size:12px;line-height:1;')
    
    def _logout(self):
        """ログアウト処理"""
        SimpleAuth.logout()
        ui.navigate.to('/login')

class RAGFooter:
    """new/準拠の共通フッター（ステータスバー24px固定）"""
    
    def __init__(self, show_status: bool = True):
        if show_status:
            self.create_status_bar()
    
    def create_status_bar(self):
        """ステータスバー作成（100%幅で右端隙間ゼロ）"""
        with ui.element('div').style('position:fixed;bottom:0;left:0;width:100%;height:24px;background:#374151;color:white;display:flex;align-items:center;justify-content:space-between;padding:0;margin:0;font-size:12px;z-index:999;'):
            ui.label('システム: 正常稼働中').style('color:white;margin-left:16px;')
            ui.label('接続: OK').style('color:white;margin-right:16px;')

# RAGLayoutクラスは廃止
# 理由: main.pyでの一元的CSS管理と矛盾、!important濫用でUI設計ポリシー違反
# 代替: 各ページでRAGHeader + MainContentArea + RAGFooterを直接使用

class MainContentArea:
    """メインコンテンツエリア - スクロール制御対応（margin-top修正版）"""
    
    def __init__(self, footer_height: str = "24px", allow_overflow: bool = True):
        """
        Args:
            footer_height: フッター高さ（デフォルト24px）
            allow_overflow: オーバーフロー許可（True: 内部スクロール, False: 固定高さ）
        """
        self.footer_height = footer_height
        self.allow_overflow = allow_overflow
        self.container = None
        
    def __enter__(self):
        """メインコンテンツエリア開始 - margin-top修正（48px→32px）"""
        if self.allow_overflow:
            # オーバーフロー許可：内部スクロールバー
            overflow_style = 'overflow-y:auto;overflow-x:hidden;'
        else:
            # オーバーフロー禁止：固定高さ・パネル内スクロール
            overflow_style = 'overflow:hidden;'
        
        # 【修正済み】正確な位置・高さ計算：ヘッダー下からフッター上まで
        # position: ヘッダー下に配置（32px下げる - 調整済み）
        # height: 100vh - ヘッダー(48px) - フッター(24px) = 72px
        height_style = "height:calc(100vh - 72px);"
        
        self.container = ui.element('div').style(
            'margin-top:32px;'                    # ヘッダー高さ分下げる（48px→32px修正）
            'margin-left:0;'                      # 左余白完全ゼロ
            'margin-right:0;'                     # 右余白完全ゼロ  
            'margin-bottom:0px;'                   # position:fixed なので不要
            'padding:0;'                          # 内部余白完全ゼロ
            'width:100%;'                         # 完全幅（100vwではなく100%）
            f'{height_style}'                     # 高さ設定（100vh基準で正確計算）
            f'{overflow_style}'                   # オーバーフロー制御（モード依存）
            'position:relative;'                  # 子要素の基準位置
            'box-sizing:border-box;'              # ボックスサイズ計算明示
        )
        return self.container.__enter__()
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """メインコンテンツエリア終了"""
        return self.container.__exit__(exc_type, exc_val, exc_tb)