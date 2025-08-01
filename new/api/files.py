# new/api/files.py
# ファイル管理API

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.engine import Connection

from new.database.connection import get_db_connection
from new.database.models import files_meta, files_blob, files_text, FILE_STATUS
from new.config import LOGGER
from new.schemas import FileListResponse, FileResponse, FileStatusUpdate

router = APIRouter(prefix="/files", tags=["files"])


@router.get("")
def get_files_list(
    page: int = Query(1, ge=1, description="ページ番号"),
    page_size: int = Query(100, ge=1, le=500, description="1ページあたりの件数"),
    status: Optional[str] = Query(None, description="ステータスフィルター"),
    search: Optional[str] = Query(None, description="ファイル名検索"),
    connection: Connection = Depends(get_db_connection)
):
    """
    ファイル一覧を取得する
    """
    try:
        # ベースクエリ構築
        base_query = """
            SELECT 
                fb.id,
                fm.file_name,
                fm.mime_type,
                fm.size,
                fm.page_count,
                fm.status,
                fm.created_at,
                fm.updated_at,
                ft.quality_score
            FROM files_blob fb
            JOIN files_meta fm ON fb.id = fm.blob_id
            LEFT JOIN files_text ft ON fb.id = ft.blob_id
        """
        
        # フィルター条件
        conditions = []
        params = {}
        
        if status:
            conditions.append("fm.status = :status")
            params["status"] = status
            
        if search:
            conditions.append("fm.file_name ILIKE :search")
            params["search"] = f"%{search}%"
        
        # WHERE句追加
        if conditions:
            base_query += " WHERE " + " AND ".join(conditions)
        
        # 並び順
        base_query += " ORDER BY fm.created_at DESC"
        
        # 件数取得
        count_query = f"SELECT COUNT(*) FROM ({base_query}) as subquery"
        total_count = connection.execute(text(count_query), params).fetchone()[0]
        
        # ページネーション
        offset = (page - 1) * page_size
        paginated_query = f"{base_query} LIMIT :limit OFFSET :offset"
        params.update({"limit": page_size, "offset": offset})
        
        # データ取得
        result = connection.execute(text(paginated_query), params)
        files = []
        
        for row in result.fetchall():
            files.append({
                "id": str(row[0]),
                "file_name": row[1],
                "mime_type": row[2],
                "size": row[3],
                "page_count": row[4],
                "status": row[5],
                "created_at": row[6].isoformat(),
                "updated_at": row[7].isoformat(),
                "quality_score": row[8]
            })
        
        # レスポンス構築
        total_pages = (total_count + page_size - 1) // page_size
        
        return {
            "files": files,
            "pagination": {
                "current_page": page,
                "page_size": page_size,
                "total_count": total_count,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_prev": page > 1
            },
            "status": "success"
        }
        
    except Exception as e:
        LOGGER.error(f"Failed to get files list: {e}")
        raise HTTPException(status_code=500, detail="ファイル一覧の取得に失敗しました")


@router.get("/{file_id}")
def get_file_detail(
    file_id: str,
    connection: Connection = Depends(get_db_connection)
):
    """
    ファイル詳細情報を取得する
    """
    try:
        query = """
            SELECT 
                fb.id,
                fb.checksum,
                fb.stored_at,
                fm.file_name,
                fm.mime_type,
                fm.size,
                fm.page_count,
                fm.status,
                fm.created_at,
                fm.updated_at,
                ft.raw_text,
                ft.refined_text,
                ft.quality_score,
                ft.tags,
                ft.processing_log,
                ft.ocr_engine,
                ft.llm_model,
                ft.updated_at as text_updated_at
            FROM files_blob fb
            JOIN files_meta fm ON fb.id = fm.blob_id
            LEFT JOIN files_text ft ON fb.id = ft.blob_id
            WHERE fb.id = :file_id
        """
        
        result = connection.execute(text(query), {"file_id": file_id})
        row = result.fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail="ファイルが見つかりません")
        
        return {
            "id": str(row[0]),
            "checksum": row[1],
            "stored_at": row[2].isoformat(),
            "file_name": row[3],
            "mime_type": row[4],
            "size": row[5],
            "page_count": row[6],
            "status": row[7],
            "created_at": row[8].isoformat(),
            "updated_at": row[9].isoformat(),
            "raw_text": row[10],
            "refined_text": row[11],
            "quality_score": row[12],
            "tags": row[13] or [],
            "processing_log": row[14],
            "ocr_engine": row[15],
            "llm_model": row[16],
            "text_updated_at": row[17].isoformat() if row[17] else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        LOGGER.error(f"Failed to get file detail: {e}")
        raise HTTPException(status_code=500, detail="ファイル詳細の取得に失敗しました")


@router.patch("/{file_id}/status")
def update_file_status(
    file_id: str,
    status_update: FileStatusUpdate,
    connection: Connection = Depends(get_db_connection)
):
    """
    ファイルステータスを更新する
    """
    try:
        # ステータス妥当性チェック
        if status_update.status not in FILE_STATUS.values():
            raise HTTPException(status_code=400, detail="無効なステータスです")
        
        # ファイル存在確認
        check_query = "SELECT 1 FROM files_meta WHERE blob_id = :file_id"
        exists = connection.execute(text(check_query), {"file_id": file_id}).fetchone()
        
        if not exists:
            raise HTTPException(status_code=404, detail="ファイルが見つかりません")
        
        # ステータス更新
        update_query = """
            UPDATE files_meta 
            SET status = :status, updated_at = NOW()
            WHERE blob_id = :file_id
        """
        
        connection.execute(text(update_query), {
            "file_id": file_id,
            "status": status_update.status
        })
        connection.commit()
        
        return JSONResponse({
            "status": "success",
            "message": "ステータスを更新しました",
            "data": {
                "file_id": file_id,
                "status": status_update.status
            }
        })
        
    except HTTPException:
        raise
    except Exception as e:
        connection.rollback()
        LOGGER.error(f"Failed to update file status: {e}")
        raise HTTPException(status_code=500, detail="ステータス更新に失敗しました")


@router.delete("/{file_id}")
def delete_file(
    file_id: str,
    connection: Connection = Depends(get_db_connection)
):
    """
    ファイルを削除する
    """
    try:
        # ファイル存在確認
        check_query = "SELECT file_name FROM files_meta WHERE blob_id = :file_id"
        result = connection.execute(text(check_query), {"file_id": file_id})
        file_info = result.fetchone()
        
        if not file_info:
            raise HTTPException(status_code=404, detail="ファイルが見つかりません")
        
        # ファイル削除（CASCADE制約により関連テーブルも削除される）
        delete_query = "DELETE FROM files_blob WHERE id = :file_id"
        connection.execute(text(delete_query), {"file_id": file_id})
        connection.commit()
        
        return JSONResponse({
            "status": "success",
            "message": f"ファイル '{file_info[0]}' を削除しました",
            "data": {
                "file_id": file_id,
                "file_name": file_info[0]
            }
        })
        
    except HTTPException:
        raise
    except Exception as e:
        connection.rollback()
        LOGGER.error(f"Failed to delete file: {e}")
        raise HTTPException(status_code=500, detail="ファイル削除に失敗しました")


@router.get("/status/counts")
def get_status_counts(connection: Connection = Depends(get_db_connection)):
    """
    ステータス別ファイル数を取得する
    """
    try:
        query = """
            SELECT status, COUNT(*) as count
            FROM files_meta
            GROUP BY status
            ORDER BY status
        """
        
        result = connection.execute(text(query))
        status_counts = {}
        
        for row in result.fetchall():
            status_counts[row[0]] = row[1]
        
        return JSONResponse({
            "status": "success",
            "data": status_counts
        })
        
    except Exception as e:
        LOGGER.error(f"Failed to get status counts: {e}")
        raise HTTPException(status_code=500, detail="ステータス集計の取得に失敗しました")