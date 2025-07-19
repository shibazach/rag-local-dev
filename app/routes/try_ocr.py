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
    
    # デバッグ情報
    print(f"🔍 利用可能なOCRエンジン: {engine_names}")
    
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
        
        # ページ番号の処理
        if page_num == -1:  # 全ページ処理
            result = process_all_pages(engine, file_path)
        else:
            result = engine.process(file_path, page_num)
        
        processing_time = time.time() - start_time
        
        # 処理時間を結果に追加
        result["processing_time"] = round(processing_time, 2)
        result["engine_name"] = engine_name
        result["page_num"] = page_num
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/try_ocr/process_file")
async def process_ocr_file(
    file: UploadFile = File(...),
    engine_name: str = Form(...),
    page_num: int = Form(0)
):
    """アップロードされたファイルでOCR処理を実行"""
    try:
        # 一時ファイルに保存
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_path = temp_file.name
        
        try:
            # OCRエンジンを取得
            engine = get_engine_by_name(engine_name)
            
            # 処理時間を測定
            start_time = time.time()
            
            # ページ番号の処理
            if page_num == -1:  # 全ページ処理
                result = process_all_pages(engine, temp_path)
            else:
                result = engine.process(temp_path, page_num)
            
            processing_time = time.time() - start_time
            
            # 処理時間を結果に追加
            result["processing_time"] = round(processing_time, 2)
            result["engine_name"] = engine_name
            result["page_num"] = page_num
            result["file_name"] = file.filename
            
            return result
            
        finally:
            # 一時ファイルを削除
            if os.path.exists(temp_path):
                os.unlink(temp_path)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def process_all_pages(engine, file_path: str) -> dict:
    """全ページをOCR処理"""
    import fitz
    
    try:
        doc = fitz.open(file_path)
        total_pages = len(doc)
        doc.close()
        
        all_text = []
        total_confidence = 0
        confidence_count = 0
        
        for page_num in range(total_pages):
            result = engine.process(file_path, page_num)
            if result["success"]:
                all_text.append(f"=== ページ {page_num + 1} ===")
                all_text.append(result["text"])
                all_text.append("")  # 空行
                
                if result.get("confidence"):
                    total_confidence += result["confidence"]
                    confidence_count += 1
        
        avg_confidence = total_confidence / confidence_count if confidence_count > 0 else None
        
        return {
            "success": True,
            "text": "\n".join(all_text),
            "confidence": avg_confidence,
            "pages_processed": total_pages
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"全ページ処理エラー: {str(e)}",
            "text": ""
        }

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

@router.get("/api/try_ocr/engine_parameters/{engine_name}")
async def get_engine_parameters(engine_name: str):
    """指定されたOCRエンジンのパラメータ定義を取得"""
    try:
        engine = get_engine_by_name(engine_name)
        return {
            "engine_name": engine_name,
            "parameters": engine.get_parameters()
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))