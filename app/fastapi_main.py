# REM: app/fastapi_main.py @2025-07-18 00:00 UTC +9
# REM: FastAPI 起動エントリ。ここではアプリ生成 & ルーター登録だけを行う。
import os
import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# REM: 共有設定
BASE_DIR      = os.path.dirname(__file__)         # /workspace/app
STATIC_DIR    = os.path.join(BASE_DIR, "static")
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")

app = FastAPI()

# REM: テンプレートディレクトリ設定
templates = Jinja2Templates(directory=TEMPLATES_DIR)

# REM: staticファイル配信設定
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# REM: 既存ルーター一括登録
from app.routes import router as api_router
app.include_router(api_router)

# REM: プロンプト配信用エンドポイント登録
from app.routes.ingest_api import router as ingest_api_router
# prefix="/api" の下に "/refine_prompt" をマウント
app.include_router(ingest_api_router, prefix="/api")

# REM: 開発用スタンドアロン実行
if __name__ == "__main__":
    uvicorn.run(
        "app.fastapi_main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
