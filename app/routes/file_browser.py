# app/fastapi/routes/file_browser.py  2025-07-11 12:50 JST
from fastapi import APIRouter, Query, HTTPException
from typing import List
import os

router = APIRouter()

@router.get("/api/list-folders", response_model=dict)
def list_folders(path: str = Query("", description="対象フォルダの相対パス")):
    """
    クライアントから渡された path を起点に
    サブフォルダのみを JSON で返却する。
    path="" の場合はカレントディレクトリ。
    """
    # セキュリティ上 必要なら root_dir を制限してください
    base = os.path.abspath(path or ".")
    if not os.path.isdir(base):
        raise HTTPException(400, f"Not a directory: {path}")
    try:
        entries = os.listdir(base)
    except Exception as e:
        raise HTTPException(500, f"Cannot list directory: {e}")
    folders = [e for e in entries if os.path.isdir(os.path.join(base, e))]
    return {"folders": folders}
