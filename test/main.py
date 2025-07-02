# test/main.py
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from src.config import EMBEDDING_OPTIONS
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

# 開発用エントリ
if __name__ == "__main__":
    uvicorn.run("test.main:app", host="0.0.0.0", port=8000, reload=True)
