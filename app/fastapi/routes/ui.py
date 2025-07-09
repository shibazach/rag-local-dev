# /workspace/app/fastapi/routes/ui.py
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy import text

from app.fastapi_main import templates
from src.config import EMBEDDING_OPTIONS, DB_ENGINE
from llm.prompt_loader import list_prompt_keys

router = APIRouter()

@router.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse("index.html", {
        "request": request,
        "embedding_options": EMBEDDING_OPTIONS,
        "prompt_keys": list_prompt_keys()
    })

@router.get("/chat", response_class=HTMLResponse)
def chat(request: Request):
    return templates.TemplateResponse("chat.html", {
        "request": request,
        "embedding_options": EMBEDDING_OPTIONS
    })

# UI 用のパスはそのまま /ingest
@router.get("/ingest", response_class=HTMLResponse)
def ingest(request: Request):
    return templates.TemplateResponse("ingest.html", {
        "request": request,
        "embedding_options": EMBEDDING_OPTIONS,
        "prompt_keys": list_prompt_keys()
    })

@router.get("/viewer/{file_id}", response_class=HTMLResponse)
def viewer(request: Request, file_id: int, num: int = 0):
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

@router.get("/edit/{file_id}", response_class=HTMLResponse)
def edit(request: Request, file_id: int):
    from app.fastapi.services.query_handler import get_file_content
    return templates.TemplateResponse("edit.html", {
        "request": request,
        "file_id": file_id,
        "content": get_file_content(file_id)
    })
