# new/api/ocr_comparison.py
"""
OCR比較検証API
旧系のtry_ocr機能を新系に移植
"""

import os
import time
import tempfile
from typing import List, Dict, Optional
from pathlib import Path

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.engine import Connection

from new.database.connection import get_db_connection
from new.database.models import files_blob, files_meta
from new.services.ocr import OCREngineFactory
from new.config import LOGGER

router = APIRouter(prefix="/ocr-comparison", tags=["OCR Comparison"])


@router.get("/engines")
async def get_available_engines():
    """利用可能なOCRエンジン一覧を取得"""
    try:
        ocr_factory = OCREngineFactory()
        available_engines = ocr_factory.get_available_engines()
        
        engines_list = []
        for engine_id, engine_info in available_engines.items():
            engines_list.append({
                "id": engine_id,
                "name": engine_info['name'],
                "available": engine_info['available'],
                "description": engine_info.get('description', ''),
                "parameters": engine_info.get('parameters', {})
            })
        
        return {
            "engines": engines_list,
            "total_count": len(engines_list),
            "available_count": len([e for e in engines_list if e['available']])
        }
        
    except Exception as e:
        LOGGER.error(f"OCRエンジン一覧取得エラー: {e}")
        raise HTTPException(status_code=500, detail=f"エンジン一覧取得エラー: {str(e)}")


@router.get("/file/{file_id}/info")
async def get_file_info(
    file_id: str,
    connection: Connection = Depends(get_db_connection)
):
    """ファイル情報を取得"""
    try:
        # ファイル情報取得
        query = text("""
            SELECT 
                fb.id,
                fm.file_name,
                fm.mime_type,
                fm.size,
                fm.page_count,
                fm.status,
                fm.created_at
            FROM files_blob fb
            JOIN files_meta fm ON fb.id = fm.blob_id
            WHERE fb.id::text = :file_id
        """)
        
        result = connection.execute(query, {"file_id": file_id}).fetchone()
        
        if not result:
            raise HTTPException(status_code=404, detail="ファイルが見つかりません")
        
        return {
            "id": str(result.id),
            "file_name": result.file_name,
            "mime_type": result.mime_type,
            "size": result.size,
            "page_count": result.page_count,
            "status": result.status,
            "created_at": result.created_at.isoformat() if result.created_at else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        LOGGER.error(f"ファイル情報取得エラー [{file_id}]: {e}")
        raise HTTPException(status_code=500, detail=f"ファイル情報取得エラー: {str(e)}")


@router.post("/process")
async def process_ocr_comparison(
    file_id: str = Form(...),
    engines: str = Form(...),  # カンマ区切りのエンジンリスト
    page_num: int = Form(1),
    use_correction: bool = Form(False),
    connection: Connection = Depends(get_db_connection)
):
    """OCR比較処理を実行"""
    try:
        # エンジンリストをパース
        engine_list = [e.strip() for e in engines.split(',') if e.strip()]
        if not engine_list:
            raise HTTPException(status_code=400, detail="OCRエンジンが指定されていません")
        
        LOGGER.info(f"OCR比較開始: file_id={file_id}, engines={engine_list}, page={page_num}")
        
        # ファイル取得
        file_info = await get_file_info(file_id, connection)
        
        # ファイルバイナリ取得
        blob_query = text("SELECT data FROM files_blob WHERE id::text = :file_id")
        blob_result = connection.execute(blob_query, {"file_id": file_id}).fetchone()
        
        if not blob_result:
            raise HTTPException(status_code=404, detail="ファイルデータが見つかりません")
        
        # 一時ファイル作成
        file_ext = Path(file_info['file_name']).suffix
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as temp_file:
            temp_file.write(blob_result.data)
            temp_path = temp_file.name
        
        try:
            # OCRファクトリ初期化
            ocr_factory = OCREngineFactory()
            available_engines = ocr_factory.get_available_engines()
            
            # 比較結果格納
            results = {}
            processing_start = time.time()
            
            # 各エンジンで処理
            for engine_name in engine_list:
                engine_id = None
                for eid, engine_info in available_engines.items():
                    if engine_info['name'] == engine_name and engine_info['available']:
                        engine_id = eid
                        break
                
                if not engine_id:
                    results[engine_name] = {
                        "success": False,
                        "error": f"エンジン '{engine_name}' が利用できません",
                        "text": "",
                        "processing_time": 0,
                        "confidence": 0
                    }
                    continue
                
                # OCR処理実行
                start_time = time.time()
                
                try:
                    if page_num == 0:  # 全ページ処理
                        result = await process_all_pages_async(engine_id, temp_path, ocr_factory)
                    else:
                        result = ocr_factory.process_file(temp_path, engine_id, page_num - 1)  # 0-based
                    
                    processing_time = time.time() - start_time
                    
                    if result.success:
                        processed_text = result.text
                        
                        # 誤字修正処理
                        if use_correction and processed_text:
                            from services.ocr_comparison.correction_service import CorrectionService
                            correction_service = CorrectionService()
                            
                            corrected_text, corrections = correction_service.apply_corrections(processed_text)
                            
                            results[engine_name] = {
                                "success": True,
                                "text": corrected_text,
                                "original_text": processed_text,
                                "corrections": corrections,
                                "correction_count": len(corrections),
                                "processing_time": round(processing_time, 2),
                                "confidence": getattr(result, 'confidence', 0),
                                "error": None
                            }
                        else:
                            results[engine_name] = {
                                "success": True,
                                "text": processed_text,
                                "processing_time": round(processing_time, 2),
                                "confidence": getattr(result, 'confidence', 0),
                                "error": None
                            }
                    else:
                        results[engine_name] = {
                            "success": False,
                            "error": result.error,
                            "text": "",
                            "processing_time": round(processing_time, 2),
                            "confidence": 0
                        }
                        
                except Exception as e:
                    processing_time = time.time() - start_time
                    results[engine_name] = {
                        "success": False,
                        "error": f"処理エラー: {str(e)}",
                        "text": "",
                        "processing_time": round(processing_time, 2),
                        "confidence": 0
                    }
            
            total_processing_time = time.time() - processing_start
            
            # 比較統計生成
            comparison_stats = generate_comparison_stats(results)
            
            return {
                "file_info": file_info,
                "processing_info": {
                    "page_num": page_num,
                    "engines_requested": engine_list,
                    "use_correction": use_correction,
                    "total_processing_time": round(total_processing_time, 2)
                },
                "results": results,
                "comparison": comparison_stats
            }
            
        finally:
            # 一時ファイル削除
            if os.path.exists(temp_path):
                os.unlink(temp_path)
        
    except HTTPException:
        raise
    except Exception as e:
        LOGGER.error(f"OCR比較処理エラー: {e}")
        raise HTTPException(status_code=500, detail=f"OCR比較処理エラー: {str(e)}")


async def process_all_pages_async(engine_id: str, file_path: str, ocr_factory: OCREngineFactory) -> Dict:
    """全ページOCR処理（非同期対応版）"""
    try:
        import fitz  # PyMuPDF
        
        doc = fitz.open(file_path)
        total_pages = len(doc)
        doc.close()
        
        all_text = []
        total_confidence = 0
        confidence_count = 0
        
        for page_num in range(total_pages):
            result = ocr_factory.process_file(file_path, engine_id, page_num)
            
            if result.success:
                all_text.append(f"=== ページ {page_num + 1} ===")
                all_text.append(result.text)
                all_text.append("")  # 空行
                
                if hasattr(result, 'confidence') and result.confidence:
                    total_confidence += result.confidence
                    confidence_count += 1
        
        avg_confidence = total_confidence / confidence_count if confidence_count > 0 else 0
        
        # OCRResult風のオブジェクトを作成
        class AllPagesResult:
            def __init__(self, success, text, confidence=0, error=None):
                self.success = success
                self.text = text
                self.confidence = confidence
                self.error = error
        
        return AllPagesResult(
            success=True,
            text="\n".join(all_text),
            confidence=avg_confidence
        )
        
    except Exception as e:
        class AllPagesResult:
            def __init__(self, success, text, confidence=0, error=None):
                self.success = success
                self.text = text
                self.confidence = confidence
                self.error = error
        
        return AllPagesResult(
            success=False,
            text="",
            error=f"全ページ処理エラー: {str(e)}"
        )


def generate_comparison_stats(results: Dict) -> Dict:
    """比較統計を生成"""
    try:
        successful_results = {k: v for k, v in results.items() if v['success']}
        
        if not successful_results:
            return {
                "total_engines": len(results),
                "successful_engines": 0,
                "failed_engines": len(results),
                "best_engine": None,
                "statistics": {}
            }
        
        # 基本統計
        stats = {
            "total_engines": len(results),
            "successful_engines": len(successful_results),
            "failed_engines": len(results) - len(successful_results)
        }
        
        # 最速エンジン
        fastest_engine = min(successful_results.items(), key=lambda x: x[1]['processing_time'])
        stats["fastest_engine"] = {
            "name": fastest_engine[0],
            "time": fastest_engine[1]['processing_time']
        }
        
        # 最高信頼度エンジン
        if any(r.get('confidence', 0) > 0 for r in successful_results.values()):
            highest_confidence = max(successful_results.items(), key=lambda x: x[1].get('confidence', 0))
            stats["highest_confidence_engine"] = {
                "name": highest_confidence[0],
                "confidence": highest_confidence[1].get('confidence', 0)
            }
        
        # テキスト長統計
        text_lengths = [len(r['text']) for r in successful_results.values()]
        if text_lengths:
            stats["text_statistics"] = {
                "min_length": min(text_lengths),
                "max_length": max(text_lengths),
                "avg_length": round(sum(text_lengths) / len(text_lengths), 1)
            }
        
        # 推奨エンジン（信頼度と速度の組み合わせ）
        best_score = 0
        best_engine = None
        for engine_name, result in successful_results.items():
            # スコア = 信頼度 * 0.7 + (1 / 処理時間) * 0.3
            confidence = result.get('confidence', 0.5)  # デフォルト0.5
            speed_score = 1 / max(result['processing_time'], 0.1)  # 0で割るのを防ぐ
            score = confidence * 0.7 + min(speed_score, 1.0) * 0.3
            
            if score > best_score:
                best_score = score
                best_engine = engine_name
        
        stats["recommended_engine"] = {
            "name": best_engine,
            "score": round(best_score, 3)
        }
        
        return stats
        
    except Exception as e:
        LOGGER.error(f"比較統計生成エラー: {e}")
        return {
            "total_engines": len(results),
            "successful_engines": 0,
            "failed_engines": len(results),
            "error": str(e)
        }