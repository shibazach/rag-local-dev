

# /workspace/app/fastapi_main.py
# FastAPI 起動エントリ。ここではアプリ生成 & ルーター登録だけを行う。
import os, uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# ── 共有設定 ────────────────────────────────────────────
BASE_DIR       = os.path.dirname(__file__)            # /workspace/app
FASTAPI_DIR    = os.path.join(BASE_DIR, "fastapi")    # /workspace/app/fastapi
STATIC_DIR     = os.path.join(FASTAPI_DIR, "static")
TEMPLATES_DIR  = os.path.join(FASTAPI_DIR, "templates")

app       = FastAPI()
templates = Jinja2Templates(directory=TEMPLATES_DIR)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# ── ルーター登録（app.fastapi.routes.*） ─────────────────
from app.fastapi.routes import ui, ingest, query, file

app.include_router(ui.router)
app.include_router(ingest.router)
app.include_router(query.router)
app.include_router(file.router)

# ── 開発用スタンドアロン実行 ───────────────────────────
if __name__ == "__main__":
    uvicorn.run("app.fastapi_main:app", host="0.0.0.0", port=8000, reload=True)