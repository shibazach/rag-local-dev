"""
共通レイアウトコンポーネント - new/系templates準拠（実際の認証状態対応）
"""

from nicegui import ui
from typing import Optional, Dict, Any
from app.auth.session import SessionManager
from app.config import logger

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
                self._nav_button('🧪', '配置テスト', '/arrangement-test', self.current_page == "arrangement-test")
                self._nav_button('⚡', '管理', '/admin', self.current_page == "admin")
            
            # 右側：認証部分（固定幅220px・右寄せ・実際の認証状態）
            with ui.element('div').style('width:220px;display:flex;align-items:center;justify-content:flex-end;gap:8px;margin-right:16px;'):
                self._render_auth_section()
    
    def _nav_button(self, icon: str, label: str, path: str, is_current: bool = False):
        """ナビゲーションボタン（現在ページ対応・レスポンシブ・ホバー効果）"""
        # 現在ページかどうかで色とクリック動作を分岐
        text_color = '#ff6b6b' if is_current else 'white'  # 現在ページは赤字
        background_color = 'rgba(255,107,107,0.1)' if is_current else 'transparent'  # 現在ページは薄い赤背景
        cursor_style = 'default' if is_current else 'pointer'
        click_handler = None if is_current else lambda: ui.navigate.to(path)
        
        # ホバー効果用のID生成
        button_id = f'nav-btn-{path.replace("/", "-").replace("-", "")}'
        
        with ui.element('div').style(
            f'display:flex;align-items:center;gap:3px;cursor:{cursor_style};'
            f'padding:2px 6px;border-radius:3px;transition:all 0.2s;'
            f'white-space:nowrap;height:auto;line-height:1;'
            f'background:{background_color};'
        ).props(f'id="{button_id}"').on('click', click_handler):
            ui.label(icon).style(f'color:{text_color};font-size:14px;line-height:1;')
            ui.label(label).style(f'color:{text_color};font-size:12px;line-height:1;')
        
        # ホバー効果CSS追加（現在ページでない場合のみ）
        if not is_current:
            ui.add_head_html(f'''
            <style>
            #{button_id}:hover {{
                background: rgba(255,255,255,0.1) !important;
                transform: translateY(-1px);
            }}
            </style>
            ''')
    
    def _render_auth_section(self):
        """認証セクション描画（シンプルセッション対応）"""
        try:
            from app.auth.session import SessionManager
            current_user = SessionManager.get_current_user()
            
            if current_user:
                # ログイン済みの場合
                username = current_user.get('username', 'ユーザー')
                is_admin = current_user.get('is_admin', False)
                
                # ステータスインジケーター（緑色）
                ui.label('●').style('color:#10b981;font-size:12px;')
                
                # ユーザー名表示
                ui.label(username).style('color:white;font-size:14px;')
                
                # ログアウトボタン
                ui.button('ログアウト', on_click=self._handle_logout).style(
                    'background:#3b82f6;color:white;border:none;'
                    'padding:4px 12px;border-radius:4px;font-size:12px;cursor:pointer;'
                )
                
                logger.debug(f"認証済み表示: {username} (admin: {is_admin})")
            else:
                # 未ログインの場合
                # ステータスインジケーター（赤色）
                ui.label('●').style('color:#ef4444;font-size:12px;')
                
                # 未ログイン表示
                ui.label('未ログイン').style('color:white;font-size:14px;white-space:nowrap;')
                
                # ログインボタン
                ui.button('ログイン', on_click=lambda: ui.navigate.to('/login')).style(
                    'background:#10b981;color:white;border:none;'
                    'padding:4px 12px;border-radius:4px;font-size:12px;cursor:pointer;'
                )
                
                logger.debug("未ログイン状態で表示")
                
        except Exception as e:
            logger.error(f"認証セクション描画エラー: {e}")
            # エラー時は未ログイン扱い
            ui.label('●').style('color:#ef4444;font-size:12px;')
            ui.label('認証エラー').style('color:white;font-size:14px;')
            ui.button('ログイン', on_click=lambda: ui.navigate.to('/login')).style(
                'background:#10b981;color:white;border:none;'
                'padding:4px 12px;border-radius:4px;font-size:12px;cursor:pointer;'
            )
    
    def _handle_logout(self):
        """ログアウト処理（シンプルセッション対応）"""
        try:
            from app.auth.session_simple import SimpleSessionManager
            SimpleSessionManager.destroy_current_session()
            ui.notify('ログアウトしました', color='positive')
            ui.navigate.to('/')  # ログアウト後はトップページへ
            logger.info("🗑️ シンプルログアウト実行")
        except Exception as e:
            logger.error(f"❌ シンプルログアウトエラー: {e}")
            ui.notify('ログアウト処理でエラーが発生しました', color='negative')


class RAGFooter:
    """共通フッター - ステータスバー形式"""
    
    def __init__(self, show_status: bool = True):
        self.show_status = show_status
        if show_status:
            self.create_status_bar()
    
    def create_status_bar(self):
        """ステータスバー作成（完全画面幅・隙間ゼロ）"""
        with ui.element('div').style('position:fixed;bottom:0;left:0;right:0;width:100%;height:24px;background:#374151;color:white;display:flex;align-items:center;justify-content:space-between;padding:0;margin:0;font-size:12px;z-index:999;'):
            ui.label('システム: 正常稼働中').style('color:white;margin-left:16px;')
            ui.label('接続: OK').style('color:white;margin-right:16px;')

# RAGLayoutクラスは廃止
# 理由: main.pyでの一元的CSS管理と矛盾、!important濫用でUI設計ポリシー違反
# 代替: 各ページでRAGHeader + MainContentArea + RAGFooterを直接使用

class MainContentArea_back:
    """メインコンテンツエリア - c13方式完全制御コンテナ（バックアップ版）"""
    
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


class MainContentArea:
    """
    FixedHeaderFooterContainer - simple_test.py成功実装ベース
    
    simple_test.pyでピクセル完璧を実現した手法を共通コンポーネント化：
    1. ui.query().style()でフレームワーク要素を完全制御
    2. calc(100vh - 48px - 24px)による正確な高さ計算
    3. position:fixedヘッダー・フッター対応の完全レイアウト
    
    Usage:
        RAGHeader()
        with MainContentArea():
            # コンテンツ配置
        RAGFooter()
    """
    
    def __init__(self, content_padding: str = "8px"):
        """
        Args:
            content_padding: メインコンテンツエリアの内部パディング（デフォルト8px）
        """
        self.content_padding = content_padding
        self.container = None
        
    def __enter__(self):
        """フレームワーク制御 + メインコンテンツエリア作成"""
        
        # simple_test.py成功パターン: ui.query().style()でフレームワーク完全制御
        ui.query('html').style('margin: 0; padding: 0; height: 100vh; overflow: hidden;')
        ui.query('body').style('margin: 0; padding: 0; height: 100vh; overflow: hidden;')
        ui.query('.q-layout').style('margin: 0; padding: 0; height: 100vh; overflow: hidden;')
        ui.query('.q-page-container').style('margin: 0; padding: 0; height: 100vh; overflow: hidden;')
        ui.query('.q-page').style('margin: 0; padding: 0; height: 100vh; overflow: hidden;')
        ui.query('.nicegui-content').style('margin: 0; padding: 0; height: 100vh; overflow: hidden;')
        
        # メインコンテンツエリア（simple_testと同じ計算式）
        self.container = ui.element('div').style(
            'margin: 48px 0 24px 0;'                    # ヘッダー48px + フッター24px分のマージン
            'padding: 0;'                               # 外部パディングゼロ
            'width: 100%;'                              # 全幅使用
            'height: calc(100vh - 48px - 24px);'        # 正確な高さ計算（simple_testと同じ）
            'overflow: hidden;'                         # オーバーフロー制御
            'position: relative;'                       # 子要素基準
            'box-sizing: border-box;'                   # ボックスサイズ計算
        )
        
        return self.container.__enter__()
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """メインコンテンツエリア終了"""
        return self.container.__exit__(exc_type, exc_val, exc_tb)