import os
import json
import glob
import uvicorn

from typing import List
from fastapi import FastAPI, Request, Query, UploadFile, File, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse, Response, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import text

import unicodedata

from src.config import EMBEDDING_OPTIONS, DB_ENGINE, OLLAMA_MODEL
from fileio.file_embedder import embed_and_insert, insert_file_and_get_id
from fileio.extractor import extract_text_by_extension
from llm.refiner import refine_text_with_llm, normalize_empty_lines, build_prompt
from llm.prompt_loader import get_prompt_by_lang, list_prompt_keys
from app.fastapi.services.query_handler import handle_query

# REM: FastAPIインスタンスと設定
app = FastAPI()
BASE_INGEST_ROOT = os.path.abspath("ignored/input_files")

# REM: static/templates はこのファイルのあるディレクトリ直下を使う
here = os.path.dirname(__file__)
static_dir = os.path.join(here, "static")
templates_dir = os.path.join(here, "templates")

app.mount("/static", StaticFiles(directory=static_dir), name="static")
templates = Jinja2Templates(directory=templates_dir)

# REM: 最後に実行したingestジョブの情報を保持
last_ingest = None

# ──────────────────────────────────────────────────────────
@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse("index.html", {
        "request": request,
        "embedding_options": EMBEDDING_OPTIONS,
        "prompt_keys": list_prompt_keys(),
    })

# ──────────────────────────────────────────────────────────
@app.get("/chat", response_class=HTMLResponse)
def show_chat_ui(request: Request):
    return templates.TemplateResponse("chat.html", {
        "request": request,
        "embedding_options": EMBEDDING_OPTIONS
    })

# ──────────────────────────────────────────────────────────
@app.get("/ingest", response_class=HTMLResponse)
def show_ingest(request: Request):
    return templates.TemplateResponse("ingest.html", {
        "request": request,
        "embedding_options": EMBEDDING_OPTIONS,
        "prompt_keys": list_prompt_keys(),
    })

# ──────────────────────────────────────────────────────────
@app.post("/ingest", response_class=JSONResponse)
async def run_ingest_folder(
    input_folder: str = Form(...),
    include_subdirs: bool = Form(...),
    refine_prompt_key: str = Form(...),
    embed_models: List[str] = Form(...),
):
    global last_ingest

    # REM: 対象拡張子
    valid_exts = [".txt", ".pdf", ".docx", ".csv", ".json", ".eml"]

    # REM: フォルダ内の対象ファイルを再帰的に取得
    pattern = "**/*" if include_subdirs else "*"
    base_path = os.path.abspath(input_folder)
    all_files = glob.glob(os.path.join(base_path, pattern), recursive=include_subdirs)
    target_files = [
        f for f in all_files
        if os.path.splitext(f)[1].lower() in valid_exts
    ]

    if not target_files:
        raise HTTPException(status_code=400, detail="対象ファイルが見つかりません")

    # REM: 実行対象情報を構造化して保持
    last_ingest = {
        "files": [{"path": f, "filename": os.path.basename(f)} for f in target_files],
        "refine_prompt_key": refine_prompt_key,
        "embed_models": embed_models,
    }

    return JSONResponse({
        "status": "started",
        "count": len(target_files),
        "folder": input_folder
    })

# ──────────────────────────────────────────────────────────
@app.get("/ingest/stream")
def ingest_stream():
    if not last_ingest:
        raise HTTPException(status_code=400, detail="No ingest job found")

    def event_generator():
        for info in last_ingest["files"]:
            path = info["path"]
            name = info["filename"]

            # REM: files テーブル登録＆file_id取得（初回だけtruncate実施）
            file_id = insert_file_and_get_id(path, "", 0.0, truncate_once=True)
            yield f"data: {json.dumps({'file': name, 'file_id': file_id, 'step': '開始'})}\n\n"

            # REM: 保存完了メッセージ
            yield f"data: {json.dumps({'file': name, 'step': '保存完了', 'detail': path})}\n\n"

            # REM: テキスト抽出
            texts = extract_text_by_extension(path)
            if not texts:
                continue
            texts = list(dict.fromkeys(texts))  # 重複除去

            for idx, block in enumerate(texts, start=1):
                preview = block.strip().replace("\n", " ")[:40]

                # REM: OCR済みページ送信
                step_label = f"OCRページ{idx}"
                yield f"data: {json.dumps({'file': name, 'step': step_label, 'preview': preview, 'full_text': block})}\n\n"

                # --- 使用プロンプトプレビュー --------------------------------
                # 1) 空行正規化
                norm = normalize_empty_lines(block)
                # 2) 数字半角＆全角カタカナ化
                norm = unicodedata.normalize("NFKC", norm)
                # 3) プロンプト全文を組み立て
                prompt_text = build_prompt(norm, last_ingest["refine_prompt_key"])
                # 4) 改行をスペースにして 1 行表示
                prompt_flat = prompt_text.replace("\n", " ")
                step_label = f"使用プロンプトページ{idx}"
                yield f"data: {json.dumps({'file': name, 'step': step_label, 'prompt': prompt_flat})}\n\n"

                # --- LLM整形 ------------------------------------------
                refined, lang, score, used_prompt = refine_text_with_llm(
                    block,
                    model=OLLAMA_MODEL,
                    force_lang=last_ingest["refine_prompt_key"]
                )
                step_label = f"整形ページ{idx}"
                preview_ref = refined[:40].replace("\n", " ") + "..."
                yield f"data: {json.dumps({'file': name, 'step': step_label, 'preview': preview_ref, 'full_text': refined, 'score': round(score,3)})}\n\n"

                # REM: ベクトル化（モデル別）
                for model_key in last_ingest["embed_models"]:
                    embed_and_insert(
                        texts=[refined],
                        filename=path,
                        model_keys={model_key},
                        quality_score=score
                    )
                    step_label = f"ベクトル化ページ{idx}"
                    detail_text = f"{model_key} → 完了"
                    yield f"data: {json.dumps({'file': name, 'step': step_label, 'detail': detail_text})}\n\n"

        # REM: 全バッチ処理完了を一度だけ通知
        yield f"data: {json.dumps({'done': True})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

# ──────────────────────────────────────────────────────────
@app.post("/query")
async def query_handler(
    query: str    = Form(...),
    model_key: str = Form(...),
    mode: str     = Form("チャンク統合")
):
    try:
        result = handle_query(query, model_key, mode)
        return JSONResponse(content=result)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

# ──────────────────────────────────────────────────────────
@app.get("/api/pdf/{file_id}")
def serve_pdf(file_id: int):
    with DB_ENGINE.connect() as conn:
        row = conn.execute(
            text("SELECT file_blob, filename FROM files WHERE file_id = :fid"),
            {"fid": file_id}
        ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="File not found")
    return Response(content=row[0], media_type="application/pdf")

# ──────────────────────────────────────────────────────────
@app.get("/api/content/{file_id}")
def api_content(file_id: int):
    with DB_ENGINE.connect() as conn:
        row = conn.execute(
            text("SELECT content FROM files WHERE file_id = :fid"),
            {"fid": file_id}
        ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Content not found")
    return JSONResponse({"content": row[0]})

# ──────────────────────────────────────────────────────────
@app.get("/viewer/{file_id}", response_class=HTMLResponse)
def pdf_viewer(request: Request, file_id: int, num: int = 0):
    with DB_ENGINE.connect() as conn:
        row = conn.execute(
            text("SELECT filename FROM files WHERE file_id = :fid"),
            {"fid": file_id}
        ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="File not found")
    return templates.TemplateResponse("viewer.html", {
        "request": request,
        "file_id": file_id,
        "filename": row[0],
        "num": num
    })

# ──────────────────────────────────────────────────────────
@app.get("/edit/{file_id}", response_class=HTMLResponse)
def show_edit(request: Request, file_id: int):
    from app.fastapi.services.query_handler import get_file_content
    content = get_file_content(file_id)
    return templates.TemplateResponse("edit.html", {
        "request": request,
        "file_id": file_id,
        "content": content
    })

# ──────────────────────────────────────────────────────────
@app.post("/api/save/{file_id}")
def api_save(
    file_id: int,
    content: str = Form(...),
):
    with DB_ENGINE.connect() as conn:
        row = conn.execute(
            text("SELECT filename FROM files WHERE file_id = :fid"),
            {"fid": file_id}
        ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="File not found")
    filename = row[0]

    with DB_ENGINE.begin() as conn:
        conn.execute(
            text("UPDATE files SET content = :c WHERE file_id = :fid"),
            {"c": content, "fid": file_id}
        )
    embed_and_insert(
        texts=[content],
        filename=filename,
        model_keys=None,
        quality_score=0.0
    )
    return JSONResponse({"status": "started"})

# ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    uvicorn.run("app.fastapi_main:app", host="0.0.0.0", port=8000, reload=True)
