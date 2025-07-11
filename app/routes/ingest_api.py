# app/fastapi/routes/ingest_api.py  2025-07-11 12:00 JST
from fastapi import APIRouter, HTTPException, Query
import os

router = APIRouter()

# ベースディレクトリをここで決め打ち or 環境変数で取得
BASE_DIR = os.environ.get("INGEST_BASE_DIR", os.path.abspath("."))

@router.get("/api/list-folders")
def list_folders(path: str = Query("", description="ベースディレクトリからの相対パス")):
    # 絶対パスを組み立て
    abs_path = os.path.normpath(os.path.join(BASE_DIR, path))
    # セキュリティチェック：BASE_DIR 配下以外は拒否
    if not abs_path.startswith(BASE_DIR):
        raise HTTPException(400, "不正なパスです")
    if not os.path.isdir(abs_path):
        raise HTTPException(404, "フォルダが存在しません")
    # ディレクトリ一覧を返却
    folders = [
        name for name in os.listdir(abs_path)
        if os.path.isdir(os.path.join(abs_path, name))
    ]
    return {"folders": sorted(folders)}
