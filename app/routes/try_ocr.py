# app/routes/try_ocr.py
# OCR比較用ルート

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from starlette.requests import Request
import os
import tempfile
import time
from typing import List

from app.try_ocr.ocr_engines import get_available_engines, get_engine_by_name
from db.handler import get_all_files

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/try_ocr", response_class=HTMLResponse)
async def try_ocr_page(request: Request):
    """OCR比較ページ"""
    # 利用可能なOCRエンジンを取得
    engines = get_available_engines()
    engine_names = [engine.name for engine in engines]
    
    # データベースからファイル一覧を取得
    files = get_all_files()
    
    return templates.TemplateResponse("try_ocr.html", {
        "request": request,
        "engines": engine_names,
        "files": files
    })

@router.post("/api/try_ocr/process")
async def process_ocr(
    file_id: str = Form(...),
    engine_name: str = Form(...),
    page_num: int = Form(0)
):
    """指定されたファイルとエンジンでOCR処理を実行"""
    try:
        # ファイル情報を取得
        from db.handler import get_file_path
        file_path = get_file_path(file_id)
        
        if not file_path or not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="ファイルが見つかりません")
        
        # OCRエンジンを取得
        engine = get_engine_by_name(engine_name)
        
        # 処理時間を測定
        start_time = time.time()
        result = engine.process(file_path, page_num)
        processing_time = time.time() - start_time
        
        # 処理時間を結果に追加
        result["processing_time"] = round(processing_time, 2)
        result["engine_name"] = engine_name
        result["page_num"] = page_num
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/try_ocr/engines")
async def get_engines():
    """利用可能なOCRエンジン一覧を取得"""
    engines = get_available_engines()
    return [
        {
            "name": engine.name,
            "available": engine.is_available()
        }
        for engine in engines
    ]