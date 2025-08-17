"""
RAG System - FastAPI + NiceGUI Router
ルーティング定義のみ、具体的実装は各ui.pagesに分離
"""
from fastapi import FastAPI, File, Form, UploadFile, HTTPException
from nicegui import ui
import sys
import os
from typing import List
from app.config import logger
from app.services.file_service import get_file_service

# パス設定
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# NiceGUI統合FastAPIアプリ設定
from nicegui import app as nicegui_app
from pathlib import Path

# NiceGUIのFastAPIインスタンスを使用
fastapi_app = nicegui_app

# CORS設定追加（APIアクセスのため）
from fastapi.middleware.cors import CORSMiddleware
fastapi_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 開発環境では全て許可
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# 静的ファイルマウント（外部JS/CSS提供用）
# app/static を /app-static で配信
static_dir = Path(__file__).parent / 'app' / 'static'
static_dir.mkdir(parents=True, exist_ok=True)
nicegui_app.add_static_files('/app-static', str(static_dir))

# セキュリティヘッダーミドルウェア追加
from app.utils.security import add_security_headers
fastapi_app.middleware("http")(add_security_headers)

# APIルーターの追加
from app.api import upload_logs
fastapi_app.include_router(upload_logs.router, prefix="/api/upload", tags=["upload"])

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

# 認証クラスは別モジュールに移動
from app.utils.auth import SimpleAuth

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
    from app.ui.pages.auth import LoginPage
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
    from app.ui.pages.index import IndexPage
    IndexPage().render()

@ui.page('/chat')
def chat():
    """チャットページ"""
    from app.ui.pages.chat import ChatPage
    ChatPage().render()

@ui.page('/files')
def files():
    """ファイル管理ページ"""
    from app.ui.pages.files import FilesPage
    FilesPage().render()

@ui.page('/upload')
def upload():
    """アップロードページ"""
    from app.ui.pages.upload import UploadPage
    UploadPage().render()

@ui.page('/ocr-adjustment')
def ocr_adjustment():
    """OCR調整ページ"""
    from app.ui.pages.ocr_adjustment import OCRAdjustmentPage
    OCRAdjustmentPage().render()

@ui.page('/data-registration')
def data_registration():
    """データ登録ページ"""
    from app.ui.pages.data_registration import DataRegistrationPage
    DataRegistrationPage().render()

@ui.page('/admin')
def admin():
    """管理ページ"""
    from app.ui.pages.admin import AdminPage
    AdminPage().render()

@ui.page('/arrangement-test')
def arrangement_test():
    """UI配置テストページ"""
    from app.ui.pages.arrangement_test import ArrangementTestPage
    ArrangementTestPage(current_page="arrangement-test")

@ui.page('/test-minimal')
def test_minimal():
    """最小限テストページ"""
    from app.ui.pages.test_minimal import TestMinimalPage
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

# ====== ファイルアップロードAPI（new/系移植版） ======

from fastapi import File, UploadFile, HTTPException, Form
from typing import List
from app.services.file_service import get_file_service
from app.core.schemas import UploadResponse, BatchUploadResponse, UploadStatusResponse

@fastapi_app.post("/api/upload/single", response_model=UploadResponse)
async def upload_single_file(file: UploadFile = File(...)):
    """
    単一ファイルアップロード
    
    Args:
        file: アップロードファイル
        
    Returns:
        UploadResponse: アップロード結果
    """
    try:
        file_service = get_file_service()
        result = file_service.upload_file(file)
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"アップロード処理でエラーが発生しました: {str(e)}")

@fastapi_app.post("/api/upload/batch", response_model=BatchUploadResponse)
async def upload_batch_files(files: List[UploadFile] = File(...)):
    """
    バッチファイルアップロード
    
    Args:
        files: アップロードファイルリスト（最大50個）
        
    Returns:
        BatchUploadResponse: バッチアップロード結果
    """
    try:
        if len(files) > 100:  # 制限を100に増やす
            raise HTTPException(status_code=400, detail="一度にアップロードできるファイル数は100個までです")
        
        file_service = get_file_service()
        result = file_service.upload_batch_files(files)
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"バッチアップロード処理でエラーが発生しました: {str(e)}")

@fastapi_app.get("/api/upload/status", response_model=UploadStatusResponse)
async def get_upload_status():
    """
    アップロード機能ステータス取得
    
    Returns:
        UploadStatusResponse: アップロード機能ステータス
    """
    try:
        file_service = get_file_service()
        status_data = file_service.get_upload_status()
        return UploadStatusResponse(
            status=status_data["status"],
            data=status_data["data"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ステータス取得でエラーが発生しました: {str(e)}")

@fastapi_app.post("/api/upload/folder")
async def upload_folder(
    folder_path: str = Form(...),
    include_subfolders: bool = Form(False)
):
    """
    サーバーフォルダアップロード（new/系移植版）
    
    Args:
        folder_path: サーバー上のフォルダパス
        include_subfolders: サブフォルダも含めるかどうか
    
    Returns:
        Dict: アップロード結果
    """
    try:
        file_service = get_file_service()
        result = file_service.upload_folder(folder_path, include_subfolders)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"フォルダアップロードエラー: {e}")
        raise HTTPException(status_code=500, detail=f"フォルダアップロードに失敗しました: {str(e)}")

@fastapi_app.get("/api/list-folders")
async def list_folders(path: str = ""):
    """
    サーバーフォルダブラウザAPI（new/系移植版）
    
    Args:
        path: フォルダパス
    
    Returns:
        Dict: フォルダリスト
    """
    try:
        file_service = get_file_service()
        result = file_service.list_server_folders(path)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"フォルダリスト取得エラー: {e}")
        raise HTTPException(status_code=500, detail=f"フォルダリストの取得に失敗しました: {str(e)}")

@fastapi_app.get("/api/files/{file_id}/preview")
async def preview_file(file_id: str):
    """
    ファイルプレビューAPI（new/系移植版）
    
    Args:
        file_id: ファイルID
    
    Returns:
        Response: ファイルバイナリまたはJSON
    """
    try:
        file_service = get_file_service()
        result = file_service.get_file_preview(file_id)
        
        if result is None:
            raise HTTPException(status_code=404, detail="ファイルが見つかりません")
        
        if result["type"] == "binary":
            from fastapi import Response
            from urllib.parse import quote
            
            file_name = result["filename"]
            mime_type = result["mime_type"]
            data = result["data"]
            
            if mime_type == "application/pdf":
                quoted = quote(file_name)
                return Response(
                    content=data,
                    media_type="application/pdf",
                    headers={
                        "Content-Disposition": f"inline; filename*=UTF-8''{quoted}",
                        "X-Content-Type-Options": "nosniff"
                    }
                )
            else:
                # その他のバイナリファイル
                quoted = quote(file_name)
                return Response(
                    content=data,
                    media_type=mime_type,
                    headers={
                        "Content-Disposition": f"attachment; filename*=UTF-8''{quoted}",
                        "X-Content-Type-Options": "nosniff"
                    }
                )
        else:
            # JSON形式（テキストファイル等）
            return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"ファイルプレビューエラー: {e}")
        raise HTTPException(status_code=500, detail=f"ファイルプレビューに失敗しました: {str(e)}")



@fastapi_app.post("/api/upload/folder")
async def upload_folder(folder_path: str = Form(...), include_subfolders: bool = Form(False)):
    """フォルダアップロード"""
    try:
        file_service = get_file_service()
        result = file_service.upload_folder(folder_path, include_subfolders)
        return result
    except Exception as e:
        logger.error(f"フォルダアップロードエラー: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@fastapi_app.get("/api/upload/status")
async def get_upload_status():
    """アップロードステータス取得"""
    try:
        file_service = get_file_service()
        result = file_service.get_upload_status()
        return result
    except Exception as e:
        logger.error(f"ステータス取得エラー: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@fastapi_app.get("/api/folders/browse")
async def browse_folders(path: str = "/"):
    """サーバーフォルダブラウズ"""
    try:
        file_service = get_file_service()
        result = file_service.list_server_folders(path)
        return result
    except Exception as e:
        logger.error(f"フォルダブラウズエラー: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ====== NiceGUIフレームワーク制御（公式推奨方法） ======

# GitHub Discussion #2063: NiceGUIの公式解決策
# https://github.com/zauberzeug/nicegui/discussions/2063
ui.query('.nicegui-content').classes('p-0 gap-0')

# 場当たり対応を削除（根本原因を特定するため）

# ====== アプリケーション起動 ======

if __name__ == "__main__":
    # NiceGUI単体実行（FastAPIは別ポート8082で並行実行）
    ui.run(
        host="0.0.0.0",
        port=8081,
        reload=False,
        show=False,
        title="R&D RAGシステム"
    )