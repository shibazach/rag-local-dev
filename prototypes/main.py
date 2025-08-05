"""
RAG System - FastAPI + NiceGUI Router
ルーティング定義のみ、具体的実装は各ui.pagesに分離
"""
from fastapi import FastAPI
from nicegui import ui
import sys
import os

# パス設定
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# FastAPIアプリ
fastapi_app = FastAPI(
    title="RAG System API",
    description="R&D RAGシステム - 企業ナレッジ検索・分析システム",
    version="1.0.0"
)

# グローバルCSS設定（UI設計ポリシー準拠・1箇所のみ定義）
ui.add_head_html('''
<style>
html, body { margin: 0; padding: 0; height: 100vh; overflow: hidden; }
.q-layout { margin: 0; padding: 0; height: 100vh; overflow: hidden; }
.q-page-container { margin: 0; padding: 0; height: 100vh; overflow: hidden; }
.q-page { margin: 0; padding: 0; height: 100vh; overflow: hidden; }
.nicegui-content { margin: 0; padding: 0; height: 100vh; overflow: hidden; }
</style>
''')

# 認証クラス（簡易実装）
class SimpleAuth:
    _authenticated = False
    
    @classmethod
    def login(cls, username: str, password: str) -> bool:
        if username == "admin" and password == "password":
            cls._authenticated = True
            return True
        return False
    
    @classmethod
    def logout(cls):
        cls._authenticated = False
    
    @classmethod
    def is_authenticated(cls) -> bool:
        return cls._authenticated

# チャット状態管理
class ChatState:
    current_pattern = 'no-preview'

# グローバルCSS設定（NiceGUI/Quasarデフォルト完全リセット）
# グローバルCSS削除（simple_testアプローチ）
# NiceGUIのデフォルトのみ使用

# ====== ページルーティング ======

@ui.page('/login')
def login():
    """ログインページ"""
    from ui.pages.auth import LoginPage
    LoginPage().render()

# モーダルダイアログ対応のログイン
def show_login_modal():
    """モーダルダイアログとしてログイン表示"""
    with ui.dialog() as dialog, ui.card():
        ui.label('🏠 R&D RAGシステム').style('font-size:24px;font-weight:bold;text-align:center;margin:0 0 16px 0;color:#334155;')
        ui.label('ログイン').style('font-size:18px;text-align:center;margin:0 0 24px 0;color:#6b7280;')
        
        username_input = ui.input(label='ユーザー名', placeholder='admin').props('outlined dense')
        password_input = ui.input(label='パスワード', placeholder='password', password=True).props('outlined dense')
        
        with ui.row().classes('w-full justify-end gap-2'):
            ui.button('キャンセル', on_click=dialog.close).props('flat')
            ui.button('ログイン', on_click=lambda: handle_modal_login(username_input.value, password_input.value, dialog)).props('color=primary')
    
    dialog.open()

def handle_modal_login(username: str, password: str, dialog):
    """モーダルログイン処理"""
    if username == "admin" and password == "password":
        SimpleAuth.login(username, password)
        dialog.close()
        ui.notify('ログイン成功', type='positive')
        ui.navigate.reload()
    else:
        ui.notify('認証失敗', type='negative')

@ui.page('/')
def index():
    """ホームページ"""
    from ui.pages.index import IndexPage
    IndexPage().render()

@ui.page('/chat')
def chat():
    """チャットページ"""
    from ui.pages.chat import ChatPage
    ChatPage().render()

@ui.page('/files')
def files():
    """ファイル管理ページ"""
    from ui.pages.files import FilesPage
    FilesPage().render()

@ui.page('/upload')
def upload():
    """アップロードページ"""
    from ui.pages.upload import UploadPage
    UploadPage().render()

@ui.page('/ocr-adjustment')
def ocr_adjustment():
    """OCR調整ページ"""
    from ui.pages.ocr_adjustment import OCRAdjustmentPage
    OCRAdjustmentPage().render()

@ui.page('/data-registration')
def data_registration():
    """データ登録ページ"""
    from ui.pages.data_registration import DataRegistrationPage
    DataRegistrationPage().render()

@ui.page('/admin')
def admin():
    """管理ページ"""
    from ui.pages.admin import AdminPage
    AdminPage().render()

@ui.page('/arrangement-test')
def arrangement_test():
    """UI配置テストページ"""
    from ui.pages.arrangement_test import ArrangementTestPage
    ArrangementTestPage(current_page="arrangement-test")

@ui.page('/test-minimal')
def test_minimal():
    """最小限テストページ"""
    from ui.pages.test_minimal import TestMinimalPage
    TestMinimalPage()

# ====== FastAPI エンドポイント ======

@fastapi_app.post("/auth/login")
async def login_api(request: dict):
    """ログインAPI"""
    username = request.get('username')
    password = request.get('password')
    
    if SimpleAuth.login(username, password):
        return {"status": "success", "message": "ログイン成功"}
    else:
        return {"status": "error", "message": "認証失敗"}

@fastapi_app.post("/auth/logout")
async def logout_api():
    """ログアウトAPI"""
    SimpleAuth.logout()
    return {"status": "success", "message": "ログアウト完了"}

@fastapi_app.post("/chat/switch-pattern")
async def switch_chat_pattern(request: dict):
    """チャットレイアウト切り替えAPI"""
    pattern = request.get('pattern', 'no-preview')
    ChatState.current_pattern = pattern
    return {"status": "success", "pattern": pattern}

# ====== NiceGUIフレームワーク制御（公式推奨方法） ======

# GitHub Discussion #2063: NiceGUIの公式解決策
# https://github.com/zauberzeug/nicegui/discussions/2063
ui.query('.nicegui-content').classes('p-0 gap-0')

# 場当たり対応を削除（根本原因を特定するため）

# ====== アプリケーション起動 ======

if __name__ == "__main__":
    # NiceGUI単体実行（開発用）
    ui.run(
        host="0.0.0.0",
        port=8081,
        reload=False,
        show=False,
        title="R&D RAGシステム"
    )