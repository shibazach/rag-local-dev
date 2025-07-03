# test/main.py
from fastapi import HTTPException
from fastapi.responses import Response
from sqlalchemy import text
from fastapi import FastAPI, Request, Form
from fastapi.responses import (HTMLResponse, JSONResponse, RedirectResponse)
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from src.config import EMBEDDING_OPTIONS, DB_ENGINE
from test.services.query_handler import handle_query
import uvicorn

app = FastAPI()

app.mount("/static", StaticFiles(directory="test/static"), name="static")
templates = Jinja2Templates(directory="test/templates")

@app.get("/", include_in_schema=False)
def root_redirect():
    return RedirectResponse(url="/chat")

@app.get("/chat", response_class=HTMLResponse)
def show_chat_ui(request: Request):
    return templates.TemplateResponse("chat.html", {
        "request": request,
        "embedding_options": EMBEDDING_OPTIONS
    })

@app.post("/query")
async def query_handler(
    query: str = Form(...),
    model_key: str = Form(...),
    mode: str = Form("チャンク統合")
):
    try:
        result = handle_query(query, model_key, mode)
        return JSONResponse(content=result)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

# PDFバイナリを返すエンドポイント
@app.get("/api/pdf/{file_id}")
def serve_pdf(file_id: int):
    with DB_ENGINE.connect() as conn:
        row = conn.execute(
            text("SELECT file_blob, filename FROM files WHERE file_id = :fid"),
            {"fid": file_id}
        ).mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="File not found")
    return Response(content=row["file_blob"], media_type="application/pdf")

# Context編集画面を返すエンドポイント
@app.get("/edit/{file_id}", response_class=HTMLResponse)
def show_edit(request: Request, file_id: int):
    # DBから全文取得するユーティリティ（既存の関数を流用）
    from test.services.query_handler import get_file_content
    content = get_file_content(file_id)
    return templates.TemplateResponse("edit.html", {
        "request": request,
        "file_id": file_id,
        "content": content
    })

# 開発用エントリ
if __name__ == "__main__":
    uvicorn.run("test.main:app", host="0.0.0.0", port=8000, reload=True)
