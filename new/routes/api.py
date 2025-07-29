# new/routes/api.py
# APIエンドポイント定義

import logging
import shutil
import time
from typing import List, Optional
import uuid
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, UploadFile, Form, Request
from fastapi.responses import JSONResponse, FileResponse
from sqlalchemy.orm import Session

from ..auth import get_current_user, require_admin, login_user, logout_user, User
from ..database import get_db
from ..models import File
from ..services.file_service import FileService
from ..services.chat_service import ChatService
from ..services.search_service import SearchService
from ..services.queue_service import QueueService
from ..config import INPUT_DIR, LOGGER
from ..debug import debug_print, debug_error, debug_function, debug_return, debug_js_error

router = APIRouter()

# 認証API
@router.post("/auth/login")
async def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...)
):
    """ユーザーログイン"""
    try:
        user = login_user(request, username, password)
        if user:
            return {
                "success": True,
                "message": "ログインに成功しました",
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "role": user.role
                }
            }
        else:
            raise HTTPException(status_code=401, detail="ユーザー名またはパスワードが正しくありません")
    except HTTPException:
        raise
    except Exception as e:
        LOGGER.error(f"ログインエラー: {e}")
        raise HTTPException(status_code=500, detail="ログイン処理中にエラーが発生しました")

@router.post("/auth/logout")
async def logout(request: Request):
    """ユーザーログアウト"""
    try:
        debug_function("logout", user_id=request.session.get("user", {}).get("id", "unknown"))
        
        # セッションを完全にクリア
        request.session.clear()
        
        return {
            "success": True,
            "message": "ログアウトに成功しました"
        }
    except Exception as e:
        LOGGER.error(f"ログアウトエラー: {e}")
        debug_error(e, "ログアウト処理")
        raise HTTPException(status_code=500, detail="ログアウト処理中にエラーが発生しました")

# ファイル管理API
@router.get("/files")
async def get_files(
    current_user = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """ファイル一覧取得"""
    try:
        file_service = FileService()
        files = file_service.get_files(db)
        return {"files": files}
    except Exception as e:
        LOGGER.error(f"ファイル一覧取得エラー: {e}")
        raise HTTPException(status_code=500, detail="ファイル一覧の取得に失敗しました")

@router.get("/files/{file_id}")
async def get_file(
    file_id: str,
    current_user = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """ファイル詳細取得"""
    try:
        file_service = FileService()
        file = file_service.get_file(db, file_id)
        if not file:
            raise HTTPException(status_code=404, detail="ファイルが見つかりません")
        return {"file": file}
    except HTTPException:
        raise
    except Exception as e:
        LOGGER.error(f"ファイル詳細取得エラー: {e}")
        raise HTTPException(status_code=500, detail="ファイル詳細の取得に失敗しました")

@router.post("/files/upload")
async def upload_files(
    files: List[UploadFile],
    folder_path: str = Form(""),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """ファイルアップロード処理"""
    try:
        debug_function("upload_files", file_count=len(files), user_id=current_user.id)
        
        # アップロード結果を格納するリスト
        upload_results = []
        
        for file in files:
            try:
                # ファイル保存処理
                result = await save_uploaded_file(file, folder_path, current_user, db)
                upload_results.append(result)
                
            except Exception as e:
                debug_error(e, f"ファイルアップロードエラー: {file.filename}")
                upload_results.append({
                    "filename": file.filename,
                    "success": False,
                    "error": str(e)
                })
        
        return {
            "success": True,
            "message": f"{len(upload_results)}個のファイルを処理しました",
            "results": upload_results
        }
        
    except Exception as e:
        debug_error(e, "upload_files")
        raise HTTPException(status_code=500, detail="ファイルアップロード処理中にエラーが発生しました")

@router.post("/files/upload-folder")
async def upload_folder(
    folder_path: str = Form(...),
    include_subfolders: bool = Form(False),
    current_user = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """フォルダアップロード"""
    try:
        file_service = FileService()
        results = file_service.upload_folder(db, folder_path, include_subfolders, current_user.id)
        return {"results": results}
    except Exception as e:
        LOGGER.error(f"フォルダアップロードエラー: {e}")
        raise HTTPException(status_code=500, detail="フォルダアップロードに失敗しました")

@router.get("/files/{file_id}/preview")
async def preview_file(
    file_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """ファイルプレビュー（PDF用）"""
    debug_function("preview_file", file_id=file_id, user_id=current_user.id)
    
    try:
        LOGGER.info(f"📄 ファイルプレビュー開始: file_id={file_id}, user_id={current_user.id}")
        debug_print(f"ファイルプレビュー開始: file_id={file_id}, user_id={current_user.id}")
        
        # UUIDの検証と変換
        try:
            file_uuid = uuid.UUID(file_id)
            debug_print(f"UUID変換成功: {file_uuid}")
        except ValueError as uuid_error:
            error_msg = f"無効なファイルID形式: {file_id}"
            LOGGER.error(f"❌ {error_msg}")
            debug_error(uuid_error, "UUID変換")
            raise HTTPException(status_code=422, detail=error_msg)
        
        # ファイル情報を取得
        file_record = db.query(File).filter(File.id == file_uuid, File.user_id == current_user.id).first()
        if not file_record:
            error_msg = f"ファイルが見つかりません: file_id={file_id}, user_id={current_user.id}"
            LOGGER.error(f"❌ {error_msg}")
            debug_error(Exception(error_msg), "ファイル検索")
            raise HTTPException(status_code=404, detail="ファイルが見つかりません")
        
        LOGGER.info(f"📄 ファイル情報取得: {file_record.file_name}, パス: {file_record.file_path}")
        debug_print(f"ファイル情報取得: {file_record.file_name}, パス: {file_record.file_path}")
        
        file_path = Path(file_record.file_path)
        if not file_path.exists():
            error_msg = f"ファイルが存在しません: {file_path}"
            LOGGER.error(f"❌ {error_msg}")
            debug_error(Exception(error_msg), "ファイル存在確認")
            raise HTTPException(status_code=404, detail="ファイルが存在しません")
        
        # ファイルの拡張子を確認
        file_extension = file_path.suffix.lower()
        LOGGER.info(f"📄 ファイル拡張子: {file_extension}")
        debug_print(f"ファイル拡張子: {file_extension}")
        
        if file_extension == '.pdf':
            # PDFファイルの場合、ファイルを直接返す
            LOGGER.info(f"📄 PDFプレビュー: {file_path}")
            debug_print(f"PDFプレビュー: {file_path}")
            try:
                response = FileResponse(
                    path=str(file_path),
                    media_type='application/pdf',
                    filename=file_record.file_name,
                    headers={
                        'Content-Disposition': 'inline',
                        'X-Content-Type-Options': 'nosniff'
                    }
                )
                debug_return("preview_file", f"PDFレスポンス: {file_record.file_name}")
                return response
            except Exception as pdf_error:
                LOGGER.error(f"❌ PDFプレビューエラー: {pdf_error}")
                debug_error(pdf_error, "PDFプレビュー")
                raise HTTPException(status_code=500, detail=f"PDFプレビューエラー: {str(pdf_error)}")
        else:
            # その他のファイルはテキストプレビュー
            LOGGER.info(f"📝 テキストプレビュー: {file_path}")
            debug_print(f"テキストプレビュー: {file_path}")
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                LOGGER.info(f"📝 テキスト読み込み成功: {len(content)} 文字")
                debug_print(f"テキスト読み込み成功: {len(content)} 文字")
                result = {"content": content[:1000], "type": "text"}
                debug_return("preview_file", f"テキストレスポンス: {len(content)} 文字")
                return result
            except UnicodeDecodeError as decode_error:
                LOGGER.warning(f"⚠️ テキストデコードエラー、バイナリとして処理: {decode_error}")
                debug_print(f"テキストデコードエラー、バイナリとして処理: {decode_error}")
                # バイナリファイルの場合
                try:
                    with open(file_path, 'rb') as f:
                        content = f.read(1000)
                    LOGGER.info(f"📝 バイナリ読み込み成功: {len(content)} バイト")
                    debug_print(f"バイナリ読み込み成功: {len(content)} バイト")
                    result = {"content": content.hex(), "type": "binary"}
                    debug_return("preview_file", f"バイナリレスポンス: {len(content)} バイト")
                    return result
                except Exception as binary_error:
                    LOGGER.error(f"❌ バイナリ読み込みエラー: {binary_error}")
                    debug_error(binary_error, "バイナリ読み込み")
                    raise HTTPException(status_code=500, detail=f"ファイル読み込みエラー: {str(binary_error)}")
            except Exception as text_error:
                LOGGER.error(f"❌ テキスト読み込みエラー: {text_error}")
                debug_error(text_error, "テキスト読み込み")
                raise HTTPException(status_code=500, detail=f"ファイル読み込みエラー: {str(text_error)}")
                
    except HTTPException:
        raise
    except Exception as e:
        LOGGER.error(f"❌ ファイルプレビューエラー: {e}")
        LOGGER.error(f"❌ エラー詳細: {type(e).__name__}: {str(e)}")
        debug_error(e, "ファイルプレビュー")
        raise HTTPException(status_code=500, detail="ファイルプレビュー中にエラーが発生しました")

# 検索API
@router.post("/search/text")
async def search_text(
    query: str,
    top_k: int = 5,
    file_ids: List[str] = None,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """テキスト検索"""
    try:
        search_service = SearchService()
        results = search_service.search_text(db, query, top_k, file_ids)
        return {"results": results}
    except Exception as e:
        LOGGER.error(f"テキスト検索エラー: {e}")
        raise HTTPException(status_code=500, detail="テキスト検索に失敗しました")

@router.post("/search/images")
async def search_images(
    query: str,
    top_k: int = 5,
    file_ids: List[str] = None,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """画像検索"""
    try:
        search_service = SearchService()
        results = search_service.search_images(db, query, top_k, file_ids)
        return {"results": results}
    except Exception as e:
        LOGGER.error(f"画像検索エラー: {e}")
        raise HTTPException(status_code=500, detail="画像検索に失敗しました")

@router.post("/search/hybrid")
async def hybrid_search(
    query: str,
    top_k: int = 10,
    file_ids: List[str] = None,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """ハイブリッド検索"""
    try:
        search_service = SearchService()
        results = search_service.hybrid_search(db, query, top_k, file_ids)
        return results
    except Exception as e:
        LOGGER.error(f"ハイブリッド検索エラー: {e}")
        raise HTTPException(status_code=500, detail="ハイブリッド検索に失敗しました")

# 処理キューAPI
@router.get("/queue/pending")
async def get_pending_tasks(
    task_type: str = None,
    limit: int = 10,
    current_user = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """待機中のタスク取得"""
    try:
        queue_service = QueueService()
        tasks = queue_service.get_pending_tasks(db, task_type, limit)
        return {"tasks": tasks}
    except Exception as e:
        LOGGER.error(f"待機タスク取得エラー: {e}")
        raise HTTPException(status_code=500, detail="待機タスクの取得に失敗しました")

@router.post("/queue/process")
async def process_task(
    task_id: int,
    current_user = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """タスク処理"""
    try:
        queue_service = QueueService()
        success = queue_service.process_task(db, task_id)
        return {"success": success}
    except Exception as e:
        LOGGER.error(f"タスク処理エラー: {e}")
        raise HTTPException(status_code=500, detail="タスク処理に失敗しました")

@router.post("/queue/process-all")
async def process_all_tasks(
    current_user = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """全タスク処理"""
    try:
        queue_service = QueueService()
        results = queue_service.process_all_pending_tasks(db)
        return results
    except Exception as e:
        LOGGER.error(f"全タスク処理エラー: {e}")
        raise HTTPException(status_code=500, detail="全タスク処理に失敗しました")

# 統計情報API
@router.get("/stats/search")
async def get_search_stats(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """検索統計情報取得"""
    try:
        search_service = SearchService()
        stats = search_service.get_search_statistics(db)
        return {"stats": stats}
    except Exception as e:
        LOGGER.error(f"検索統計取得エラー: {e}")
        raise HTTPException(status_code=500, detail="検索統計の取得に失敗しました")

@router.get("/files/{file_id}/summary")
async def get_file_summary(
    file_id: str,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """ファイルサマリー取得"""
    try:
        search_service = SearchService()
        summary = search_service.get_file_summary(db, file_id)
        return {"summary": summary}
    except Exception as e:
        LOGGER.error(f"ファイルサマリー取得エラー: {e}")
        raise HTTPException(status_code=500, detail="ファイルサマリーの取得に失敗しました")

# チャットAPI
@router.get("/chat/sessions")
async def get_chat_sessions(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """チャットセッション一覧取得"""
    try:
        chat_service = ChatService()
        sessions = chat_service.get_sessions(db, current_user.id)
        return {"sessions": sessions}
    except Exception as e:
        LOGGER.error(f"チャットセッション取得エラー: {e}")
        raise HTTPException(status_code=500, detail="チャットセッションの取得に失敗しました")

@router.post("/chat/sessions")
async def create_chat_session(
    title: str,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """チャットセッション作成"""
    try:
        chat_service = ChatService()
        session = chat_service.create_session(db, current_user.id, title)
        return {"session": session}
    except Exception as e:
        LOGGER.error(f"チャットセッション作成エラー: {e}")
        raise HTTPException(status_code=500, detail="チャットセッションの作成に失敗しました")

@router.get("/chat/sessions/{session_id}/messages")
async def get_chat_messages(
    session_id: str,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """チャットメッセージ取得"""
    try:
        chat_service = ChatService()
        messages = chat_service.get_messages(db, session_id)
        return {"messages": messages}
    except Exception as e:
        LOGGER.error(f"チャットメッセージ取得エラー: {e}")
        raise HTTPException(status_code=500, detail="チャットメッセージの取得に失敗しました")

@router.post("/chat/sessions/{session_id}/messages")
async def send_message(
    session_id: str,
    message: str,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """チャットメッセージ送信"""
    try:
        chat_service = ChatService()
        response = chat_service.send_message(db, session_id, current_user.id, message)
        return {"response": response}
    except Exception as e:
        LOGGER.error(f"チャットメッセージ送信エラー: {e}")
        raise HTTPException(status_code=500, detail="チャットメッセージの送信に失敗しました")

# 設定API
@router.get("/config")
async def get_config(
    current_user = Depends(get_current_user)
):
    """設定取得"""
    try:
        # 現在の設定を返す
        config = {
            "embedding_models": ["sentence-transformers", "ollama"],
            "default_embedding_model": "sentence-transformers",
            "chunk_size": 1000,
            "overlap_size": 200,
            "max_file_size": 50 * 1024 * 1024,  # 50MB
            "supported_formats": [".pdf", ".txt", ".doc", ".docx", ".jpg", ".png", ".json", ".csv", ".md"]
        }
        return {"config": config}
    except Exception as e:
        LOGGER.error(f"設定取得エラー: {e}")
        raise HTTPException(status_code=500, detail="設定の取得に失敗しました")

# ユーザーAPI
@router.get("/user/profile")
async def get_user_profile(
    current_user = Depends(get_current_user)
):
    """ユーザープロフィール取得"""
    try:
        return {
            "data": {
                "id": current_user.id,
                "username": current_user.username,
                "email": current_user.email,
                "role": current_user.role
            }
        }
    except Exception as e:
        LOGGER.error(f"ユーザープロフィール取得エラー: {e}")
        raise HTTPException(status_code=500, detail="ユーザープロフィールの取得に失敗しました") 

@router.post("/debug/error")
async def log_js_error(request: Request):
    """JavaScriptエラーをログに記録"""
    try:
        debug_function("log_js_error")
        
        # リクエストボディを取得
        body = await request.json()
        
        error_type = body.get('type', 'Unknown')
        message = body.get('message', 'No message')
        details = body.get('details', '')
        url = body.get('url', '')
        user_agent = body.get('userAgent', '')
        
        # JavaScriptエラーをCursorコンソールに出力
        debug_js_error(
            f"Type: {error_type}, Message: {message}, URL: {url}, UserAgent: {user_agent}",
            "JavaScript Error"
        )
        
        if details:
            debug_js_error(f"Details: {details}", "JavaScript Error Details")
        
        return {"success": True, "message": "エラーが記録されました"}
        
    except Exception as e:
        debug_error(e, "log_js_error")
        LOGGER.error(f"JavaScriptエラーログ記録エラー: {e}")
        raise HTTPException(status_code=500, detail="エラーログ記録に失敗しました") 