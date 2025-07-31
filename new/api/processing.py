# new/api/processing.py
# ファイル処理関連API

from typing import Dict, List, Optional
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.engine import Connection

from database.connection import get_db_connection
from services.ocr import OCREngineFactory
from config import LOGGER

router = APIRouter(prefix="/processing", tags=["processing"])

# OCRファクトリインスタンス
ocr_factory = OCREngineFactory()

@router.get("/config")
def get_processing_config() -> JSONResponse:
    """処理設定情報を取得"""
    try:
        # OCRエンジン情報
        ocr_engines = ocr_factory.get_available_engines()
        
        # 埋め込みモデル設定（暫定）
        embedding_models = {
            "intfloat-e5-large-v2": {
                "name": "intfloat/e5-large-v2",
                "type": "sentence_transformers",
                "available": True
            },
            "intfloat-e5-small-v2": {
                "name": "intfloat/e5-small-v2", 
                "type": "sentence_transformers",
                "available": True
            },
            "nomic-embed-text": {
                "name": "nomic-embed-text",
                "type": "ollama",
                "available": False  # Ollama接続確認が必要
            }
        }
        
        # LLMモデル設定（暫定）
        llm_models = {
            "phi4-mini": {
                "name": "phi4-mini",
                "available": False  # Ollama接続確認が必要
            }
        }
        
        return JSONResponse({
            "success": True,
            "data": {
                "ocr_engines": ocr_engines,
                "embedding_models": embedding_models,
                "llm_models": llm_models,
                "default_settings": {
                    "ocr_engine": "ocrmypdf",
                    "embedding_models": ["intfloat-e5-large-v2"],
                    "llm_timeout": 300,
                    "quality_threshold": 0.0,
                    "overwrite_existing": True
                }
            }
        })
    
    except Exception as e:
        LOGGER.error(f"処理設定取得エラー: {e}")
        raise HTTPException(status_code=500, detail=f"設定取得エラー: {str(e)}")

@router.get("/ocr/engines")
def get_ocr_engines() -> JSONResponse:
    """利用可能なOCRエンジン一覧を取得"""
    try:
        engines = ocr_factory.get_available_engines()
        return JSONResponse({
            "success": True,
            "data": engines
        })
    except Exception as e:
        LOGGER.error(f"OCRエンジン一覧取得エラー: {e}")
        raise HTTPException(status_code=500, detail=f"OCRエンジン一覧取得エラー: {str(e)}")

@router.get("/ocr/engines/{engine_id}")
def get_ocr_engine_info(engine_id: str) -> JSONResponse:
    """指定OCRエンジンの詳細情報を取得"""
    try:
        engine = ocr_factory.create_engine(engine_id)
        if engine is None:
            raise HTTPException(status_code=404, detail=f"OCRエンジン '{engine_id}' が見つかりません")
        
        return JSONResponse({
            "success": True,
            "data": {
                "id": engine_id,
                "info": engine.get_engine_info()
            }
        })
    except HTTPException:
        raise
    except Exception as e:
        LOGGER.error(f"OCRエンジン情報取得エラー: {e}")
        raise HTTPException(status_code=500, detail=f"OCRエンジン情報取得エラー: {str(e)}")

@router.post("/test/ocr")
async def test_ocr_engine(
    request_data: Dict,
    connection: Connection = Depends(get_db_connection)
) -> JSONResponse:
    """OCRエンジンをテスト"""
    try:
        engine_id = request_data.get("engine_id", "ocrmypdf")
        test_file_id = request_data.get("file_id")
        
        if not test_file_id:
            raise HTTPException(status_code=400, detail="file_idが必要です")
        
        # テストファイルのパスを取得（files_metaから）
        from sqlalchemy import text
        query = text("""
            SELECT fm.file_path, fm.file_name
            FROM files_meta fm
            WHERE fm.file_id = :file_id
        """)
        result = connection.execute(query, {"file_id": test_file_id}).fetchone()
        
        if not result:
            raise HTTPException(status_code=404, detail="指定されたファイルが見つかりません")
        
        file_path = result.file_path
        file_name = result.file_name
        
        # OCR処理実行
        ocr_result = ocr_factory.process_file(file_path, engine_id=engine_id)
        
        return JSONResponse({
            "success": True,
            "data": {
                "file_id": test_file_id,
                "file_name": file_name,
                "engine_id": engine_id,
                "ocr_result": {
                    "success": ocr_result.success,
                    "text_length": len(ocr_result.text) if ocr_result.text else 0,
                    "processing_time": ocr_result.processing_time,
                    "confidence": ocr_result.confidence,
                    "error": ocr_result.error,
                    "text_preview": ocr_result.text[:200] + "..." if ocr_result.text and len(ocr_result.text) > 200 else ocr_result.text
                }
            }
        })
        
    except HTTPException:
        raise
    except Exception as e:
        LOGGER.error(f"OCRテストエラー: {e}")
        raise HTTPException(status_code=500, detail=f"OCRテストエラー: {str(e)}")