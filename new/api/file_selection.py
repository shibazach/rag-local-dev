# new/api/file_selection.py
# ファイル選択・フィルタリングAPI拡張

from typing import Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query, Depends, Body
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.engine import Connection
from pydantic import BaseModel

from database.connection import get_db_connection
from config import LOGGER

router = APIRouter(prefix="/file-selection", tags=["file-selection"])

class FileSelectionRequest(BaseModel):
    file_ids: List[str]
    processing_options: Dict

class FileStatusSummary(BaseModel):
    status: str
    count: int
    percentage: float

class FileSelectionStats(BaseModel):
    total_files: int
    status_breakdown: List[FileStatusSummary]
    selected_files: int
    estimated_processing_time: float

@router.get("/stats")
async def get_file_selection_stats(
    connection: Connection = Depends(get_db_connection)
) -> JSONResponse:
    """ファイル選択統計情報を取得"""
    try:
        # 総ファイル数とステータス別集計
        stats_query = text("""
            SELECT
                COUNT(*) as total_files,
                COUNT(CASE WHEN ft.raw_text IS NOT NULL AND ft.refined_text IS NOT NULL THEN 1 END) as processed,
                COUNT(CASE WHEN ft.raw_text IS NOT NULL AND ft.refined_text IS NULL THEN 1 END) as text_extracted,
                COUNT(CASE WHEN ft.raw_text IS NULL THEN 1 END) as pending_processing
            FROM files_blob fb
            JOIN files_meta fm ON fb.id = fm.blob_id
            LEFT JOIN files_text ft ON fb.id = ft.blob_id
        """)
        
        result = connection.execute(stats_query).fetchone()
        
        total_files = result.total_files
        processed = result.processed
        text_extracted = result.text_extracted
        pending_processing = result.pending_processing
        
        # ステータス別統計
        status_breakdown = []
        if total_files > 0:
            status_breakdown = [
                {
                    "status": "processed",
                    "count": processed,
                    "percentage": round((processed / total_files) * 100, 1)
                },
                {
                    "status": "text_extracted", 
                    "count": text_extracted,
                    "percentage": round((text_extracted / total_files) * 100, 1)
                },
                {
                    "status": "pending_processing",
                    "count": pending_processing,
                    "percentage": round((pending_processing / total_files) * 100, 1)
                }
            ]
        
        return JSONResponse({
            "total_files": total_files,
            "status_breakdown": status_breakdown,
            "selected_files": 0,  # フロントエンドで更新
            "estimated_processing_time": 0.0
        })
        
    except Exception as e:
        LOGGER.error(f"ファイル選択統計取得エラー: {e}")
        raise HTTPException(status_code=500, detail=f"統計取得エラー: {str(e)}")

@router.get("/filters")
async def get_available_filters(
    connection: Connection = Depends(get_db_connection)
) -> JSONResponse:
    """利用可能なフィルター選択肢を取得"""
    try:
        # ステータス別件数
        status_query = text("""
            SELECT
                CASE
                    WHEN ft.raw_text IS NOT NULL AND ft.refined_text IS NOT NULL THEN 'processed'
                    WHEN ft.raw_text IS NOT NULL THEN 'text_extracted'
                    ELSE 'pending_processing'
                END as status,
                COUNT(*) as count
            FROM files_blob fb
            JOIN files_meta fm ON fb.id = fm.blob_id
            LEFT JOIN files_text ft ON fb.id = ft.blob_id
            GROUP BY
                CASE
                    WHEN ft.raw_text IS NOT NULL AND ft.refined_text IS NOT NULL THEN 'processed'
                    WHEN ft.raw_text IS NOT NULL THEN 'text_extracted'
                    ELSE 'pending_processing'
                END
            ORDER BY count DESC
        """)
        
        status_result = connection.execute(status_query).fetchall()
        status_filters = [{"value": row.status, "count": row.count} for row in status_result]
        
        # ファイル拡張子別件数
        extension_query = text("""
            SELECT
                LOWER(SUBSTRING(fm.file_name FROM '\\.([^.]*)$')) as extension,
                COUNT(*) as count
            FROM files_blob fb
            JOIN files_meta fm ON fb.id = fm.blob_id
            WHERE fm.file_name ~ '\\.[^.]+$'
            GROUP BY LOWER(SUBSTRING(fm.file_name FROM '\\.([^.]*)$'))
            ORDER BY count DESC
            LIMIT 10
        """)
        
        extension_result = connection.execute(extension_query).fetchall()
        extension_filters = [{"value": row.extension, "count": row.count} for row in extension_result]
        
        # ファイルサイズ範囲
        size_query = text("""
            SELECT
                MIN(fm.size) as min_size,
                MAX(fm.size) as max_size,
                AVG(fm.size) as avg_size
            FROM files_blob fb
            JOIN files_meta fm ON fb.id = fm.blob_id
        """)
        
        size_result = connection.execute(size_query).fetchone()
        
        return JSONResponse({
            "status_filters": status_filters,
            "extension_filters": extension_filters,
            "size_range": {
                "min": int(size_result.min_size) if size_result.min_size else 0,
                "max": int(size_result.max_size) if size_result.max_size else 0,
                "avg": int(size_result.avg_size) if size_result.avg_size else 0
            }
        })
        
    except Exception as e:
        LOGGER.error(f"フィルター取得エラー: {e}")
        raise HTTPException(status_code=500, detail=f"フィルター取得エラー: {str(e)}")

@router.post("/estimate")
async def estimate_processing_time(
    request: FileSelectionRequest,
    connection: Connection = Depends(get_db_connection)
) -> JSONResponse:
    """選択ファイルの処理時間を推定"""
    try:
        if not request.file_ids:
            return JSONResponse({
                "selected_count": 0,
                "estimated_time_seconds": 0,
                "estimated_time_display": "00:00",
                "breakdown": {}
            })
        
        # 選択ファイルの詳細取得
        file_query = text("""
            SELECT
                fb.id,
                fm.file_name,
                fm.size,
                fm.page_count,
                CASE
                    WHEN ft.raw_text IS NOT NULL AND ft.refined_text IS NOT NULL THEN 'processed'
                    WHEN ft.raw_text IS NOT NULL THEN 'text_extracted'
                    ELSE 'pending_processing'
                END as status
            FROM files_blob fb
            JOIN files_meta fm ON fb.id = fm.blob_id
            LEFT JOIN files_text ft ON fb.id = ft.blob_id
            WHERE fb.id::text = ANY(:file_ids)
        """)
        
        result = connection.execute(file_query, {"file_ids": request.file_ids}).fetchall()
        
        # 処理時間推定ロジック
        total_time = 0
        breakdown = {
            "ocr_time": 0,
            "llm_time": 0,
            "embedding_time": 0,
            "overhead_time": 0
        }
        
        for file in result:
            # ファイルサイズベースの推定（秒）
            file_size_mb = file.size / (1024 * 1024)
            page_count = file.page_count or 1
            
            # OCR時間推定（ページ数とサイズベース）
            ocr_time = max(2.0, page_count * 0.5 + file_size_mb * 0.1)
            
            # LLM整形時間推定
            llm_time = max(1.0, page_count * 0.3)
            
            # ベクトル化時間推定
            embedding_time = max(0.5, page_count * 0.1)
            
            # オーバーヘッド
            overhead_time = 1.0
            
            # ステータス考慮
            if file.status == 'processed':
                # 再処理の場合は短縮
                ocr_time *= 0.3
                llm_time *= 0.5
            elif file.status == 'text_extracted':
                # テキスト済みならOCRスキップ
                ocr_time = 0
            
            file_total = ocr_time + llm_time + embedding_time + overhead_time
            total_time += file_total
            
            breakdown["ocr_time"] += ocr_time
            breakdown["llm_time"] += llm_time
            breakdown["embedding_time"] += embedding_time
            breakdown["overhead_time"] += overhead_time
        
        # 並列処理効果を考慮
        if len(result) > 1:
            total_time *= 0.8  # 20%短縮
        
        # 時間表示フォーマット
        minutes = int(total_time // 60)
        seconds = int(total_time % 60)
        time_display = f"{minutes:02d}:{seconds:02d}"
        
        return JSONResponse({
            "selected_count": len(result),
            "estimated_time_seconds": round(total_time, 1),
            "estimated_time_display": time_display,
            "breakdown": {
                "ocr_time": round(breakdown["ocr_time"], 1),
                "llm_time": round(breakdown["llm_time"], 1),
                "embedding_time": round(breakdown["embedding_time"], 1),
                "overhead_time": round(breakdown["overhead_time"], 1)
            }
        })
        
    except Exception as e:
        LOGGER.error(f"処理時間推定エラー: {e}")
        raise HTTPException(status_code=500, detail=f"推定エラー: {str(e)}")

@router.get("/bulk-actions")
async def get_bulk_actions() -> JSONResponse:
    """一括操作の選択肢を取得"""
    return JSONResponse({
        "actions": [
            {
                "id": "process_all",
                "label": "選択ファイルを一括処理",
                "description": "OCR→LLM→ベクトル化の完全処理",
                "icon": "🚀"
            },
            {
                "id": "ocr_only",
                "label": "OCRのみ実行",
                "description": "テキスト抽出のみ実行",
                "icon": "📄"
            },
            {
                "id": "reprocess",
                "label": "再処理",
                "description": "既存結果を上書きして再処理",
                "icon": "🔄"
            },
            {
                "id": "mark_processed",
                "label": "処理済みとしてマーク",
                "description": "手動で処理済みステータスに変更",
                "icon": "✅"
            }
        ]
    })

@router.post("/validate")
async def validate_file_selection(
    request: FileSelectionRequest,
    connection: Connection = Depends(get_db_connection)
) -> JSONResponse:
    """ファイル選択の妥当性チェック"""
    try:
        if not request.file_ids:
            return JSONResponse({
                "valid": False,
                "errors": ["ファイルが選択されていません"],
                "warnings": []
            })
        
        # ファイル存在チェック
        existence_query = text("""
            SELECT fb.id, fm.file_name
            FROM files_blob fb
            JOIN files_meta fm ON fb.id = fm.blob_id
            WHERE fb.id::text = ANY(:file_ids)
        """)
        
        result = connection.execute(existence_query, {"file_ids": request.file_ids}).fetchall()
        found_ids = [str(row.id) for row in result]
        missing_ids = [fid for fid in request.file_ids if fid not in found_ids]
        
        errors = []
        warnings = []
        
        if missing_ids:
            errors.append(f"存在しないファイルID: {', '.join(missing_ids[:3])}{'...' if len(missing_ids) > 3 else ''}")
        
        if len(request.file_ids) > 100:
            warnings.append("大量ファイル選択: 処理に時間がかかる可能性があります")
        
        valid = len(errors) == 0
        
        return JSONResponse({
            "valid": valid,
            "errors": errors,
            "warnings": warnings,
            "found_files": len(found_ids),
            "total_selected": len(request.file_ids)
        })
        
    except Exception as e:
        LOGGER.error(f"ファイル選択検証エラー: {e}")
        raise HTTPException(status_code=500, detail=f"検証エラー: {str(e)}")