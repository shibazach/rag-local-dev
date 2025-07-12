# /workspace/app/fastapi/routes/ui.py
from fastapi import APIRouter, Request, HTTPException, Form
from fastapi.responses import HTMLResponse
from sqlalchemy import text

from app.fastapi_main import templates
from src.config import EMBEDDING_OPTIONS, DB_ENGINE
from llm.prompt_loader import list_prompt_keys
from fileio.file_embedder import embed_and_insert  # REM: 保存後に再ベクトル化用

router = APIRouter()

# ──────────────────────────────────────────────────────────
# REM: ポータルトップ
@router.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse("index.html", {
        "request": request,
        "embedding_options": EMBEDDING_OPTIONS,
        "prompt_keys": list_prompt_keys()
    })

# ──────────────────────────────────────────────────────────
# REM: チャット画面
@router.get("/chat", response_class=HTMLResponse)
def chat(request: Request):
    return templates.TemplateResponse("chat.html", {
        "request": request,
        "embedding_options": EMBEDDING_OPTIONS
    })


# ──────────────────────────────────────────────────────────
# REM: Ingest 画面
@router.get("/ingest", response_class=HTMLResponse)
def ingest(request: Request):
    return templates.TemplateResponse("ingest.html", {
        "request": request,
        "embedding_options": EMBEDDING_OPTIONS,
        "prompt_keys": list_prompt_keys()
    })


# ──────────────────────────────────────────────────────────
# REM: ビューア画面（PDF プレビュー）
@router.get("/viewer/{file_id}", response_class=HTMLResponse)
def viewer(request: Request, file_id: str, num: int = 0):
    row = DB_ENGINE.connect().execute(
        text("SELECT filename FROM files WHERE file_id=:id"),
        {"id": file_id}
    ).fetchone()
    if not row:
        raise HTTPException(404, "File not found")
    return templates.TemplateResponse("viewer.html", {
        "request": request,
        "file_id": file_id,
        "filename": row[0],
        "num": num
    })


# ──────────────────────────────────────────────────────────
# REM: 編集画面（内容取得）
@router.get("/edit/{file_id}", response_class=HTMLResponse)
def edit(request: Request, file_id: str):
    from app.fastapi.services.query_handler import get_file_content
    content = get_file_content(file_id)
    return templates.TemplateResponse("edit.html", {
        "request": request,
        "file_id": file_id,
        "content": content
    })


# ──────────────────────────────────────────────────────────
# REM: 編集画面保存 & 再ベクトル化
@router.post("/edit/{file_id}", response_class=HTMLResponse)
def edit_save(request: Request, file_id: str, content: str = Form(...)):
    # REM: ファイル名取得
    fname = DB_ENGINE.connect().execute(
        text("SELECT filename FROM files WHERE file_id=:id"),
        {"id": file_id}
    ).scalar()
    if not fname:
        raise HTTPException(404, "File not found")
    # REM: content を更新
    with DB_ENGINE.begin() as tx:
        tx.execute(
            text("UPDATE files SET content=:c WHERE file_id=:id"),
            {"c": content, "id": file_id}
        )
    # REM: 保存後に再ベクトル化
    embed_and_insert([content], fname, None, 0.0)
    # REM: 更新後も同テンプレートを返して編集継続可能に
    return templates.TemplateResponse("edit.html", {
        "request": request,
        "file_id": file_id,
        "content": content
    })
