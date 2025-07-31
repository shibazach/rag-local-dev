# new/routes/api.py
# APIエンドポイント定義

import logging
import os
import shutil
import time
from typing import List, Optional
import uuid
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, UploadFile, Form, Request
from fastapi.responses import JSONResponse, FileResponse, Response
from urllib.parse import quote
from sqlalchemy.orm import Session

from ..auth import get_current_user, require_admin, login_user, logout_user, User
from ..database import get_db
from ..models import File
from ..services.file_service import FileService
from ..services.chat_service import ChatService
from ..services.search_service import SearchService
from ..db_handler import (
    insert_file_blob_only, insert_file_blob_with_details, get_all_files, get_file_blob, 
    get_file_meta, get_file_text, delete_file, get_file_path
)
from ..services.queue_service import QueueService
from ..config import INPUT_DIR, LOGGER
from ..debug import debug_print, debug_error, debug_function, debug_return, debug_js_error

def get_file_status(file_text_data):
    """ファイルの実際の処理状況に基づいてステータスを判定"""
    if not file_text_data:
        return "pending_processing"  # テキストデータなし = 未処理
    
    raw_text = file_text_data.get("raw_text", "")
    refined_text = file_text_data.get("refined_text", "")
    
    # 実際のテキスト内容をチェック
    has_raw_text = raw_text and raw_text.strip()
    has_refined_text = refined_text and refined_text.strip()
    
    if not has_raw_text:
        return "pending_processing"  # 生テキストなし = 未処理
    elif not has_refined_text:
        return "text_extracted"  # 生テキストあり、整形テキストなし = 未整形
    else:
        # TODO: ベクトル化チェックを後で追加
        return "processed"  # 両方あり = 処理完了（仮）

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
    current_user: User = Depends(get_current_user)
):
    """ファイル一覧取得 - 新DB設計対応"""
    try:
        # 新しいDBハンドラーからファイル一覧を取得
        files = get_all_files()
        
        # ファイル情報を整形
        file_list = []
        for file in files:
            file_data = {
                "id": str(file["blob_id"]),
                "file_name": file["file_name"],
                "file_size": file["size"],
                "status": file["status"],
                "created_at": file["created_at"].isoformat() if file["created_at"] else None,
                "mime_type": file["mime_type"]
            }
            
            # PDFの場合、頁数を取得
            if file["mime_type"] == "application/pdf":
                try:
                    import fitz  # PyMuPDF
                    blob_data = get_file_blob(str(file["blob_id"]))
                    if blob_data:
                        LOGGER.info(f"PDF処理中: {file['file_name']}, blob_size: {len(blob_data)}")
                        # PyMuPDFの正しい呼び出し方法に修正
                        # memoryviewをbytesに変換
                        if isinstance(blob_data, memoryview):
                            blob_data = bytes(blob_data)
                        doc = fitz.open(stream=blob_data, filetype="pdf")
                        file_data["page_count"] = len(doc)
                        doc.close()
                        LOGGER.info(f"PDF頁数取得成功: {file['file_name']} = {file_data['page_count']}頁")
                    else:
                        LOGGER.warning(f"PDFブロブデータなし: {file['file_name']}")
                        file_data["page_count"] = None
                except Exception as e:
                    LOGGER.error(f"PDF頁数取得エラー ({file['file_name']}): {e}")
                    file_data["page_count"] = None
            else:
                file_data["page_count"] = None
            
            file_list.append(file_data)
        
        return {"files": file_list}
    except Exception as e:
        LOGGER.error(f"ファイル一覧取得エラー: {e}")
        raise HTTPException(status_code=500, detail="ファイル一覧の取得に失敗しました")

@router.get("/files/{file_id}")
async def get_file(
    file_id: str,
    current_user: User = Depends(get_current_user)
):
    """ファイル詳細取得 - 新DB設計対応"""
    try:
        # 新しいDBハンドラーでファイル詳細を取得
        file_meta = get_file_meta(file_id)
        if not file_meta:
            raise HTTPException(status_code=404, detail="ファイルが見つかりません")
        
        file_text = get_file_text(file_id)
        
        # ファイル詳細情報を構築
        file_detail = {
            "id": file_id,
            "file_name": file_meta["file_name"],
            "mime_type": file_meta["mime_type"],
            "size": file_meta["size"],
            "created_at": file_meta["created_at"].isoformat() if file_meta["created_at"] else None,
            "status": get_file_status(file_text),
            "raw_text": file_text["raw_text"] if file_text else None,
            "refined_text": file_text["refined_text"] if file_text else None,
            "quality_score": file_text["quality_score"] if file_text else None,
            "tags": file_text["tags"] if file_text else []
        }
        
        # PDFの場合、頁数を取得
        if file_meta["mime_type"] == "application/pdf":
            try:
                import fitz  # PyMuPDF
                blob_data = get_file_blob(file_id)
                if blob_data:
                    LOGGER.info(f"PDF詳細処理中: {file_meta['file_name']}, blob_size: {len(blob_data)}")
                    # PyMuPDFの正しい呼び出し方法に修正
                    # memoryviewをbytesに変換
                    if isinstance(blob_data, memoryview):
                        blob_data = bytes(blob_data)
                    doc = fitz.open(stream=blob_data, filetype="pdf")
                    file_detail["page_count"] = len(doc)
                    doc.close()
                    LOGGER.info(f"PDF詳細頁数取得成功: {file_meta['file_name']} = {file_detail['page_count']}頁")
                else:
                    LOGGER.warning(f"PDF詳細ブロブデータなし: {file_meta['file_name']}")
                    file_detail["page_count"] = None
            except Exception as e:
                LOGGER.error(f"PDF詳細頁数取得エラー ({file_meta['file_name']}): {e}")
                file_detail["page_count"] = None
        else:
            file_detail["page_count"] = None
        
        return {"file": file_detail}
    except HTTPException:
        raise
    except Exception as e:
        LOGGER.error(f"ファイル詳細取得エラー: {e}")
        raise HTTPException(status_code=500, detail="ファイル詳細の取得に失敗しました")

@router.delete("/files/{file_id}")
async def delete_file_endpoint(
    file_id: str,
    current_user: User = Depends(get_current_user)
):
    """ファイル削除 - 新DB設計対応"""
    try:
        debug_function("delete_file", file_id=file_id, user_id=current_user.id)
        
        # 新しいDBハンドラーでファイル削除
        success = delete_file(file_id)
        
        if success:
            return {"success": True, "message": "ファイルを削除しました"}
        else:
            raise HTTPException(status_code=404, detail="ファイルが見つかりません")
            
    except HTTPException:
        raise
    except Exception as e:
        debug_error(e, "delete_file")
        LOGGER.error(f"ファイル削除エラー: {e}")
        raise HTTPException(status_code=500, detail="ファイル削除に失敗しました")

@router.post("/files/upload")
async def upload_files(
    files: List[UploadFile],
    current_user: User = Depends(get_current_user)
):
    """ファイルアップロード処理 - DBにblobとして保存"""
    try:
        debug_function("upload_files", file_count=len(files), user_id=current_user.id)
        
        # アップロード結果を格納するリスト
        upload_results = []
        
        for file in files:
            try:
                # ファイルデータを読み込み
                file_data = await file.read()
                
                # DBにblobとして保存（詳細情報付き）
                result = insert_file_blob_with_details(
                    file_name=file.filename,
                    file_data=file_data,
                    mime_type=file.content_type
                )
                
                upload_results.append({
                    "id": result["blob_id"],
                    "filename": file.filename,
                    "size": len(file_data),
                    "success": True,
                    "is_existing": result["is_existing"],
                    "file_info": result["file_info"],
                    "message": "既存ファイル" if result["is_existing"] else "新規保存完了"
                })
                
            except Exception as e:
                debug_error(e, f"ファイルアップロードエラー: {file.filename}")
                upload_results.append({
                    "filename": file.filename,
                    "success": False,
                    "error": str(e)
                })
        
        return {
            "success": True,
            "message": f"{len(upload_results)}個のファイルをDBに保存しました",
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
    current_user: User = Depends(get_current_user)
):
    """ファイルプレビュー（PDF用）- 新DB設計対応"""
    debug_function("preview_file", file_id=file_id, user_id=current_user.id)
    try:
        # DBからファイルデータを取得
        file_meta = get_file_meta(file_id)
        if not file_meta:
            raise HTTPException(status_code=404, detail="ファイルが見つかりません")

        file_blob = get_file_blob(file_id)
        if not file_blob:
            raise HTTPException(status_code=404, detail="ファイルデータが見つかりません")

        file_name = file_meta["file_name"]
        mime_type = file_meta["mime_type"]

        if mime_type == "application/pdf":
            quoted = quote(file_name)
            return Response(
                content=file_blob,
                media_type="application/pdf",
                headers={
                    "Content-Disposition": f"inline; file_name*=UTF-8''{quoted}",
                    "X-Content-Type-Options": "nosniff"
                    # X-Frame-Optionsを削除してiframe表示を可能にする
                }
            )
        else:
            # テキストファイルの場合
            try:
                content = file_blob.decode("utf-8")
            except UnicodeDecodeError:
                content = file_blob.decode("utf-8", errors="ignore")
            return {"type": "text", "content": content}
    except HTTPException:
        raise
    except Exception as e:
        debug_error(e, "preview_file")
        LOGGER.error(f"ファイルプレビューエラー: {e}")
        raise HTTPException(status_code=500, detail="ファイルプレビューに失敗しました")

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

@router.get("/config/prompts")
async def get_prompt_config(
    current_user: User = Depends(get_current_user)
):
    """プロンプト設定情報を取得"""
    try:
        from ..config import CUDA_AVAILABLE, OLLAMA_MODEL, EMBEDDING_OPTIONS
        
        return {
            "cuda_available": CUDA_AVAILABLE,
            "current_model": OLLAMA_MODEL,
            "embedding_options": EMBEDDING_OPTIONS
        }
    except Exception as e:
        LOGGER.error(f"設定情報取得エラー: {e}")
        raise HTTPException(status_code=500, detail="設定情報の取得に失敗しました")

@router.get("/list-folders")
async def list_folders(
    path: str = "",
    current_user: User = Depends(get_current_user)
):
    """フォルダ一覧を取得（フォルダブラウザ用）"""
    try:
        # セキュリティ上、ルートを /workspace に制限
        base_root = "/workspace"
        
        if path:
            # 相対パスの場合は /workspace からの相対として処理
            if not path.startswith('/'):
                full_path = os.path.join(base_root, path)
            else:
                # 絶対パスの場合は /workspace 以下のみ許可
                if not path.startswith(base_root):
                    raise HTTPException(status_code=400, detail="アクセスが許可されていないパスです")
                full_path = path
        else:
            full_path = base_root
        
        # パスの正規化とセキュリティチェック
        full_path = os.path.abspath(full_path)
        if not full_path.startswith(base_root):
            raise HTTPException(status_code=400, detail="アクセスが許可されていないパスです")
        
        if not os.path.isdir(full_path):
            raise HTTPException(status_code=400, detail=f"ディレクトリが見つかりません: {path}")
        
        try:
            entries = os.listdir(full_path)
        except PermissionError:
            raise HTTPException(status_code=403, detail="ディレクトリへのアクセス権限がありません")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"ディレクトリ一覧取得エラー: {e}")
        
        # フォルダのみを抽出してソート
        folders = sorted([
            entry for entry in entries 
            if os.path.isdir(os.path.join(full_path, entry)) and not entry.startswith('.')
        ])
        
        return {"folders": folders}
        
    except HTTPException:
        raise
    except Exception as e:
        LOGGER.error(f"フォルダ一覧取得エラー: {e}")
        raise HTTPException(status_code=500, detail="フォルダ一覧取得に失敗しました") 