# new/routes/ingest.py
# インジェスト機能の実装

from fastapi import APIRouter, HTTPException, Request, Form, File, UploadFile, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
import tempfile
import os
import asyncio
import json

from new.database import get_db
from new.auth import get_current_user, require_admin
from new.debug import debug_function, debug_error

router = APIRouter()

@router.get("/ingest", response_class=HTMLResponse)
async def ingest_page(
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """インジェスト画面"""
    from new.main import templates
    
    # 埋め込みモデルオプション
    embedding_options = {
        "sentence-transformers": {
            "models": ["intfloat/e5-large-v2", "intfloat/e5-small-v2"],
            "default": "intfloat/e5-small-v2"
        },
        "ollama": {
            "models": ["nomic-embed-text"],
            "default": "nomic-embed-text"
        }
    }
    
    return templates.TemplateResponse("ingest.html", {
        "request": request,
        "embedding_options": embedding_options,
        "current_user": current_user
    })

@router.post("/ingest")
async def process_ingest(
    files: List[UploadFile] = File(...),
    refine_prompt_key: str = Form(...),
    embed_models: List[str] = Form(...),
    overwrite_existing: bool = Form(False),
    quality_threshold: float = Form(0.0),
    llm_timeout: int = Form(300),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """ファイルインジェスト処理"""
    try:
        debug_function("process_ingest", file_count=len(files), user_id=current_user.get('id'))
        
        # 一時ディレクトリ作成
        tmpdir = tempfile.mkdtemp(prefix="ingest_")
        file_paths = []
        
        # ファイル保存
        for uploaded_file in files:
            file_path = os.path.join(tmpdir, uploaded_file.filename)
            with open(file_path, "wb") as f:
                content = await uploaded_file.read()
                f.write(content)
            file_paths.append(file_path)
        
        # インジェスト処理をバックグラウンドで実行
        asyncio.create_task(run_ingest_background(
            file_paths=file_paths,
            refine_prompt_key=refine_prompt_key,
            embed_models=embed_models,
            overwrite_existing=overwrite_existing,
            quality_threshold=quality_threshold,
            llm_timeout=llm_timeout,
            user_id=current_user.get('id'),
            tmpdir=tmpdir
        ))
        
        return JSONResponse({
            "status": "started",
            "message": f"{len(files)}個のファイルの処理を開始しました",
            "file_count": len(files)
        })
        
    except Exception as e:
        debug_error(e, "process_ingest")
        raise HTTPException(status_code=500, detail="インジェスト処理の開始に失敗しました")

async def run_ingest_background(
    file_paths: List[str],
    refine_prompt_key: str,
    embed_models: List[str],
    overwrite_existing: bool,
    quality_threshold: float,
    llm_timeout: int,
    user_id: int,
    tmpdir: str
):
    """バックグラウンドでインジェスト処理を実行"""
    try:
        # ここで実際のインジェスト処理を実行
        # 旧mainのロジックを移植
        debug_function("run_ingest_background", file_count=len(file_paths))
        
        # TODO: 実際のインジェスト処理を実装
        # - ファイルテキスト抽出
        # - LLMによるテキスト精製
        # - 埋め込み生成
        # - データベース保存
        
        await asyncio.sleep(1)  # 一時的な処理時間のシミュレーション
        
    except Exception as e:
        debug_error(e, "run_ingest_background")
    finally:
        # 一時ディレクトリクリーンアップ
        import shutil
        if os.path.exists(tmpdir):
            shutil.rmtree(tmpdir)

@router.get("/ingest/status")
async def get_ingest_status(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """インジェスト処理状況取得"""
    # TODO: 実際の処理状況を返す
    return {
        "status": "idle",
        "progress": 0,
        "message": "待機中"
    }

@router.post("/ingest/cancel")
async def cancel_ingest(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """インジェスト処理キャンセル"""
    # TODO: 実際のキャンセル処理を実装
    return {"status": "cancelled"} 