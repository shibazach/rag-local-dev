# new/routes/api.py
# APIエンドポイント定義

import logging
import shutil
import time
from typing import List, Optional
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from ..database import get_db
from ..auth import get_current_user, require_admin
from ..services.file_service import FileService
from ..services.chat_service import ChatService
from ..services.search_service import SearchService
from ..services.queue_service import QueueService
from ..config import INPUT_DIR, LOGGER

router = APIRouter()

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
    files: List[UploadFile] = File(...),
    folder_path: Optional[str] = Form(None),
    current_user = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """ファイルアップロード（複数ファイル対応）"""
    try:
        LOGGER.info("=" * 50)
        LOGGER.info("🚀 ファイルアップロード処理開始")
        LOGGER.info(f"📁 ファイル数: {len(files)}")
        LOGGER.info(f"👤 ユーザーID: {current_user.id}")
        LOGGER.info(f"📂 フォルダパス: {folder_path}")
        LOGGER.info(f"🎯 保存先ディレクトリ: {INPUT_DIR}")
        LOGGER.info(f"🔍 ディレクトリ存在確認: {INPUT_DIR.exists()}")
        LOGGER.info("=" * 50)
        
        file_service = FileService()
        results = []
        
        for i, file in enumerate(files):
            LOGGER.info(f"📄 ファイル {i+1}/{len(files)} 処理開始")
            LOGGER.info(f"📝 ファイル名: {file.filename}")
            LOGGER.info(f"📏 ファイルサイズ: {file.size} bytes")
            LOGGER.info(f"🔧 ファイルタイプ: {file.content_type}")
            
            if not file.filename:
                LOGGER.warning("❌ ファイル名が空です")
                continue
                
            # ファイルサイズチェック（50MB制限）
            if file.size and file.size > 50 * 1024 * 1024:
                LOGGER.warning(f"❌ ファイルサイズ超過: {file.filename} ({file.size} bytes)")
                results.append({
                    "filename": file.filename,
                    "success": False,
                    "error": "ファイルサイズが50MBを超えています"
                })
                continue
            
            # ディレクトリの作成
            try:
                LOGGER.info(f"📂 ディレクトリ作成開始: {INPUT_DIR}")
                INPUT_DIR.mkdir(parents=True, exist_ok=True)
                LOGGER.info(f"✅ ディレクトリ作成完了: {INPUT_DIR}")
                LOGGER.info(f"🔍 ディレクトリ存在確認: {INPUT_DIR.exists()}")
                LOGGER.info(f"📋 ディレクトリ権限確認: {oct(INPUT_DIR.stat().st_mode)[-3:]}")
            except Exception as dir_error:
                LOGGER.error(f"❌ ディレクトリ作成エラー: {dir_error}")
                LOGGER.error(f"📋 エラー詳細: {type(dir_error).__name__}")
                results.append({
                    "filename": file.filename,
                    "success": False,
                    "error": f"ディレクトリ作成に失敗しました: {str(dir_error)}"
                })
                continue
            
            # ファイル保存（既存ファイルの処理）
            timestamp = int(time.time())
            filename_with_timestamp = f"{timestamp}_{file.filename}"
            file_path = INPUT_DIR / filename_with_timestamp
            
            LOGGER.info(f"📝 元ファイル名: {file.filename}")
            LOGGER.info(f"🕒 タイムスタンプ: {timestamp}")
            LOGGER.info(f"📄 新しいファイル名: {filename_with_timestamp}")
            LOGGER.info(f"🎯 保存先パス: {file_path}")
            
            if folder_path:
                try:
                    folder_dir = INPUT_DIR / folder_path
                    LOGGER.info(f"📂 サブフォルダ作成開始: {folder_dir}")
                    folder_dir.mkdir(parents=True, exist_ok=True)
                    file_path = folder_dir / filename_with_timestamp
                    LOGGER.info(f"✅ サブフォルダ作成完了: {folder_dir}")
                    LOGGER.info(f"🎯 更新された保存先パス: {file_path}")
                except Exception as subdir_error:
                    LOGGER.error(f"❌ サブフォルダ作成エラー: {subdir_error}")
                    LOGGER.error(f"📋 エラー詳細: {type(subdir_error).__name__}")
                    results.append({
                        "filename": file.filename,
                        "success": False,
                        "error": f"サブフォルダ作成に失敗しました: {str(subdir_error)}"
                    })
                    continue
            
            # ファイルが既に存在する場合は番号を追加
            counter = 1
            original_path = file_path
            LOGGER.info(f"🔍 ファイル重複チェック開始: {file_path}")
            while file_path.exists():
                stem = original_path.stem
                suffix = original_path.suffix
                file_path = original_path.parent / f"{stem}_{counter}{suffix}"
                LOGGER.info(f"🔄 ファイル重複検出、新しいパス: {file_path}")
                counter += 1
            
            LOGGER.info(f"💾 最終保存先パス: {file_path}")
            LOGGER.info(f"📋 ファイル保存開始...")
            try:
                with open(file_path, "wb") as buffer:
                    shutil.copyfileobj(file.file, buffer)
                LOGGER.info(f"✅ ファイル保存成功: {file_path}")
                LOGGER.info(f"📏 保存されたファイルサイズ: {file_path.stat().st_size} bytes")
            except Exception as save_error:
                LOGGER.error(f"❌ ファイル保存エラー: {save_error}")
                LOGGER.error(f"📋 エラー詳細: {type(save_error).__name__}")
                results.append({
                    "filename": file.filename,
                    "success": False,
                    "error": f"ファイル保存に失敗しました: {str(save_error)}"
                })
                continue
            
            # データベースに記録
            file_data = {
                "file_name": file.filename,  # 元のファイル名を保持
                "file_path": str(file_path),
                "file_size": file.size or 0,
                "status": "uploaded",
                "user_id": current_user.id
            }
            
            LOGGER.info(f"💾 データベース保存開始")
            LOGGER.info(f"📋 保存データ: {file_data}")
            try:
                saved_file = file_service.save_file(db, file_data)
                LOGGER.info(f"✅ データベース保存成功: ID={saved_file.id}")
                
                results.append({
                    "filename": file.filename,
                    "success": True,
                    "file_id": saved_file.id,
                    "status": saved_file.status
                })
                LOGGER.info(f"✅ ファイル {file.filename} の処理完了")
            except Exception as db_error:
                LOGGER.error(f"❌ データベース保存エラー: {db_error}")
                LOGGER.error(f"📋 エラー詳細: {type(db_error).__name__}")
                results.append({
                    "filename": file.filename,
                    "success": False,
                    "error": f"データベース保存に失敗しました: {str(db_error)}"
                })
        
        LOGGER.info("=" * 50)
        LOGGER.info("📊 アップロード結果サマリー")
        success_count = len([r for r in results if r.get("success", False)])
        error_count = len([r for r in results if not r.get("success", False)])
        LOGGER.info(f"✅ 成功: {success_count}件")
        LOGGER.info(f"❌ 失敗: {error_count}件")
        LOGGER.info(f"📋 合計: {len(results)}件")
        LOGGER.info("=" * 50)
        
        return {"results": results}
        
    except Exception as e:
        LOGGER.error("=" * 50)
        LOGGER.error("💥 ファイルアップロード全体エラー")
        LOGGER.error(f"❌ エラー内容: {e}")
        LOGGER.error(f"📋 エラータイプ: {type(e).__name__}")
        import traceback
        LOGGER.error(f"📋 詳細スタックトレース:")
        LOGGER.error(traceback.format_exc())
        LOGGER.error("=" * 50)
        
        # より具体的なエラーメッセージを返す
        error_message = "ファイルアップロードに失敗しました"
        if "No such file or directory" in str(e):
            error_message = "ディレクトリが見つかりません"
        elif "Permission denied" in str(e):
            error_message = "権限がありません"
        elif "Network" in str(e) or "Connection" in str(e):
            error_message = "ネットワークエラーが発生しました"
        elif "timeout" in str(e).lower():
            error_message = "タイムアウトが発生しました"
        
        raise HTTPException(status_code=500, detail=error_message)

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
    current_user = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """ファイルプレビュー"""
    try:
        file_service = FileService()
        preview = file_service.get_file_preview(db, file_id)
        if not preview:
            raise HTTPException(status_code=404, detail="ファイルが見つかりません")
        return {"preview": preview}
    except HTTPException:
        raise
    except Exception as e:
        LOGGER.error(f"ファイルプレビューエラー: {e}")
        raise HTTPException(status_code=500, detail="ファイルプレビューの取得に失敗しました")

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