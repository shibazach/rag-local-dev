# REM: app/routes/ui.py（更新日時: 2025-07-16 03:10 JST）
"""
UI 系ルート

既存機能は維持したうえで…
  • files → files_meta / files_text へ SQL を置き換え
  • 編集保存後のベクトル化も従来通り動く
"""

# REM: ── 標準ライブラリ ────────────────────────────────
import uuid
from typing import Optional

# REM: ── FastAPI ──────────────────────────────────────
from fastapi import APIRouter, HTTPException, Request, Form
from fastapi.responses import HTMLResponse

# REM: ── SQLAlchemy / DB ─────────────────────────────
from sqlalchemy import text as sql_text
from src.config import DB_ENGINE, EMBEDDING_OPTIONS, OLLAMA_MODEL

# REM: ── プロジェクト内 ───────────────────────────────
from app.fastapi_main import templates
from llm.prompt_loader import list_prompt_keys
from fileio.file_embedder import embed_and_insert

router = APIRouter()


# ══════════════════════ ポータル TOP ══════════════════════
@router.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse("index.html", {
        "request": request,
        "embedding_options": EMBEDDING_OPTIONS,
    })


# ══════════════════════ チャット画面 ══════════════════════
@router.get("/chat", response_class=HTMLResponse)
def chat(request: Request):
    return templates.TemplateResponse("chat.html", {
        "request": request,
        "embedding_options": EMBEDDING_OPTIONS,
    })


# ══════════════════════ Ingest 画面 ══════════════════════
@router.get("/ingest", response_class=HTMLResponse)
def ingest(request: Request):
    return templates.TemplateResponse("ingest.html", {
        "request": request,
        "embedding_options": EMBEDDING_OPTIONS,
        "prompt_keys": list_prompt_keys(),
        "llm_model": OLLAMA_MODEL,
    })


# ══════════════════════ ビューア ════════════════════════
@router.get("/viewer/{file_id}", response_class=HTMLResponse)
def viewer(request: Request, file_id: str, num: int = 0):
    """PDF／画像プレビュー用。files_meta に名称を取りに行く。"""
    try:
        uuid.UUID(file_id)
    except ValueError:
        raise HTTPException(400, "bad uuid")

    fname: Optional[str] = DB_ENGINE.connect().execute(
        sql_text("SELECT file_name FROM files_meta WHERE id=:fid"),
        {"fid": file_id},
    ).scalar()

    if not fname:
        raise HTTPException(404, "File not found")

    return templates.TemplateResponse("viewer.html", {
        "request": request,
        "file_id": file_id,
        "file_name": fname,
        "num": num,
    })


# ══════════════════════ 編集画面 (GET) ═══════════════════
@router.get("/edit/{file_id}", response_class=HTMLResponse)
def edit(request: Request, file_id: str):
    row = DB_ENGINE.connect().execute(
        sql_text(
            "SELECT refined_text FROM files_text WHERE file_id=:fid"
        ),
        {"fid": file_id},
    ).scalar()
    if row is None:
        raise HTTPException(404, "File not found")

    return templates.TemplateResponse("edit.html", {
        "request": request,
        "file_id": file_id,
        "content": row,
    })


# ══════════════════════ 編集保存 (POST) ═══════════════════
@router.post("/edit/{file_id}", response_class=HTMLResponse)
def edit_save(request: Request, file_id: str, content: str = Form(...)):
    with DB_ENGINE.begin() as tx:
        # 更新
        rows = tx.execute(
            sql_text(
                "UPDATE files_text SET refined_text=:c, updated_at=NOW() WHERE file_id=:fid"
            ),
            {"c": content, "fid": file_id},
        ).rowcount
    if rows == 0:
        raise HTTPException(404, "File not found")

    # ファイル名取得（再ベクトル化に利用）
    fname = DB_ENGINE.connect().execute(
        sql_text("SELECT file_name FROM files_meta WHERE id=:fid"),
        {"fid": file_id},
    ).scalar()

    # 再ベクトル化
    embed_and_insert([content], fname, None, 0.0)

    return templates.TemplateResponse("edit.html", {
        "request": request,
        "file_id": file_id,
        "content": content,
    })
