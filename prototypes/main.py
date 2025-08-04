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
ui.add_head_html('''
<style>
/* ベースリセット（画面幅全体対応・スクロールバー完全制御） */
html, body {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
    width: 100%;
    height: 100vh;
    overflow-x: hidden;
    overflow-y: auto;
}

/* NiceGUI/Quasarフレームワーク制御（画面幅全体対応） */
#q-app {
    margin: 0;
    padding: 0;
    width: 100%;
    height: 100vh;
    overflow-x: hidden;
}

.q-layout {
    margin: 0;
    padding: 0;
    min-height: 100vh;
    width: 100%;
    overflow-x: hidden;
}

.q-header {
    margin: 0;
    padding: 0;
    width: 100%;
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    z-index: 1000;
    height: 48px;
    overflow: hidden;
}

.q-page-container {
    padding: 0;
    margin: 0;
    width: 100%;
    margin-top: 48px;
}

.q-page {
    padding: 0;
    margin: 0;
    width: 100%;
    min-height: calc(100vh - 48px);
}

.nicegui-content {
    padding: 0;
    margin: 0;
    width: 100%;
    height: 100%;
}

.nicegui-row, .nicegui-column {
    margin: 0;
    padding: 0;
    gap: 0;
}

/* NiceGUI要素の強制リセット */
.nicegui-element, .q-page .q-page-container > * {
    margin: 0;
    padding: 0;
}

/* 全体コンテナの完全制御 */
.q-page-container > .nicegui-content > * {
    margin: 0;
    padding: 0;
}

/* 共通ユーティリティクラス */
.flex-center {
    display: flex;
    justify-content: center;
    align-items: center;
}

.flex-center-column {
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
}

.text-center {
    text-align: center;
}

.zero-spacing {
    margin: 0;
    padding: 0;
    gap: 0;
}

/* レスポンシブナビゲーション対応 */
@media (max-width: 1200px) {
    .q-header {
        height: auto;
        min-height: 48px;
    }
}

@media (max-width: 900px) {
    /* 2行目が表示される場合の調整 */
}

@media (max-width: 600px) {
    /* 3行目が表示される場合の調整 */
}
</style>
''')

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