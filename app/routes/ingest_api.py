# REM: app/routes/ingest_api.py @2025-07-18 00:00 UTC +9

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import PlainTextResponse
import os

router = APIRouter()

# REM: 静的ファイルやフォルダ参照のベースディレクトリ
BASE_DIR = os.environ.get("INGEST_BASE_DIR", os.path.abspath("."))


@router.get("/list-folders")
def list_folders(path: str = Query("", description="ベースディレクトリからの相対パス")):
    # REM: 絶対パスを組み立て
    abs_path = os.path.normpath(os.path.join(BASE_DIR, path))

    # REM: セキュリティチェック：BASE_DIR 配下以外は拒否
    if not abs_path.startswith(BASE_DIR):
        raise HTTPException(400, "不正なパスです")
    if not os.path.isdir(abs_path):
        raise HTTPException(404, "フォルダが存在しません")

    # REM: ディレクトリ一覧を返却
    folders = [
        name
        for name in os.listdir(abs_path)
        if os.path.isdir(os.path.join(abs_path, name))
    ]
    return {"folders": sorted(folders)}


@router.get("/refine_prompt", response_class=PlainTextResponse)
def get_refine_prompt():
    prompt_path = os.path.join(BASE_DIR, "bin", "refine_prompt_multi.txt")
    if not os.path.isfile(prompt_path):
        raise HTTPException(404, "プロンプトファイルが見つかりません")
    with open(prompt_path, encoding="utf-8") as f:
        return f.read()
