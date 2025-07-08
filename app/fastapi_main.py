# app/fastapi_main.py

import os, json, glob, uvicorn
from typing import List
from fastapi import (FastAPI, Request, Query, UploadFile, File, Form, HTTPException)
from fastapi.responses import (
    HTMLResponse, RedirectResponse, JSONResponse, Response, 
    StreamingResponse)
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import text

from src.config import EMBEDDING_OPTIONS, DB_ENGINE, OLLAMA_MODEL
from fileio.file_embedder import embed_and_insert, insert_file_and_get_id
from fileio.extractor import extract_text_by_extension
from llm.refiner import refine_text_with_llm
from llm.prompt_loader import get_prompt_by_lang, list_prompt_keys
from app.fastapi.services.query_handler import handle_query

# REM: FastAPIインスタンスと設定
app = FastAPI()
BASE_INGEST_ROOT = os.path.abspath("ignored/input_files")

app.mount("/static", StaticFiles(directory="app/fastapi/static"), name="static")
templates = Jinja2Templates(directory="app/fastapi/templates")

# ──────────────────────────────────────────────────────────
# REM: 最後に実行したingestジョブの情報を保持
last_ingest = None

# ──────────────────────────────────────────────────────────
# REM: ① ルートでポータル用 index.html を返す
@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse("index.html", {
        "request": request,
        "embedding_options": EMBEDDING_OPTIONS,
        "prompt_keys": list_prompt_keys(),
    })

# ──────────────────────────────────────────────────────────
# REM: ② チャットUI
@app.get("/chat", response_class=HTMLResponse)
def show_chat_ui(request: Request):
    return templates.TemplateResponse("chat.html", {
        "request": request,
        "embedding_options": EMBEDDING_OPTIONS
    })

# ──────────────────────────────────────────────────────────
# REM: ③ Ingest UI
@app.get("/ingest", response_class=HTMLResponse)
def show_ingest(request: Request):
    return templates.TemplateResponse("ingest.html", {
        "request": request,
        "embedding_options": EMBEDDING_OPTIONS,
        "prompt_keys": list_prompt_keys(),
    })

# ──────────────────────────────────────────────────────────
# REM: フォルダ指定 ingest 実行（ファイルアップロード不要）
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
# REM: ⑤ Ingest ストリーム：SSE で逐次進捗を返却
@app.get("/ingest/stream")
def ingest_stream():
    if not last_ingest:
        raise HTTPException(status_code=400, detail="No ingest job found")

    # REM: ingestストリーム（逐次処理）をクライアントへ送る
    def event_generator():
        if not last_ingest:
            print("[DEBUG] last_ingest が存在しない")
            raise HTTPException(status_code=400, detail="No ingest job found")

        for info in last_ingest["files"]:
            print("[DEBUG] ファイル処理開始:", info)
            path = info["path"]
            name = info["filename"]

            # REM: files テーブル登録＆file_id取得（初回だけtruncate実施）
            file_id = insert_file_and_get_id(path, "", 0.0, truncate_once=True)
            # REM: ファイル行ヘッダとして最初に送信
            yield f"data: {json.dumps({'file': name, 'file_id': file_id, 'step': '開始'})}\n\n"

            # REM: 保存完了メッセージ
            yield f"data: {json.dumps({'file': name, 'step': '保存完了', 'detail': path})}\n\n"

            # REM: テキスト抽出
            texts = extract_text_by_extension(path)
            if not texts:
                print("[DEBUG] 抽出テキストが空:", path)
                continue
            # 🔧 重複ブロック除去（順序保持）
            texts = list(dict.fromkeys(texts))
            print(f"[DEBUG] テキスト抽出完了 ({len(texts)} ページ):", name)

            # REM: 各ページごとの処理
            for idx, block in enumerate(texts, start=1):
                preview = block.strip().replace("\n", " ")[:40]

                # REM: OCR済みメッセージ（全文も送信）
                step_label = "OCRページ" + str(idx)
                detail_text = preview + "..." if preview else preview
                yield f"data: {json.dumps({'file': name, 'step': step_label, 'preview': detail_text, 'full_text': block})}\n\n"

                # REM: プロンプト生成
                _, prompt_template = get_prompt_by_lang(last_ingest["refine_prompt_key"])
                prompt = prompt_template.replace("{TEXT}", block).replace("{input_text}", block)

                # REM: プロンプト表示用メッセージ
                step_label = "プロンプトページ" + str(idx)
                detail_text = prompt[:80].replace("\n", " ") + "..."
                yield f"data: {json.dumps({'file': name, 'step': step_label, 'detail': detail_text})}\n\n"

                # REM: LLM整形
                refined, lang, score = refine_text_with_llm(
                    block,
                    model=OLLAMA_MODEL,
                    force_lang=last_ingest["refine_prompt_key"]
                )
                step_label = "整形ページ" + str(idx)
                detail_text = refined[:80].replace("\n", " ") + "..."
                score_val = round(score, 3)
                yield f"data: {json.dumps({'file': name, 'step': step_label, 'preview': detail_text, 'full_text': refined, 'score': score_val})}\n\n"
                
                # REM: ベクトル化（モデル別）
                for model_key in last_ingest["embed_models"]:
                    embed_and_insert(
                        texts=[refined],
                        filename=path,
                        model_keys={model_key},
                        quality_score=score
                    )
                    step_label = "ベクトル化ページ" + str(idx)
                    detail_text = model_key + " → 完了"
                    yield f"data: {json.dumps({'file': name, 'step': step_label, 'detail': detail_text})}\n\n"

        # REM: 全バッチ処理完了を一度だけ通知
        yield f"data: {json.dumps({'done': True})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

# ──────────────────────────────────────────────────────────
# REM: ⑥ クエリ処理
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
# REM: ⑦ PDFバイナリ返却
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
# REM: ⑧ コンテンツ取得
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
# REM: ⑨ PDFビューア
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
# REM: ⑩ 編集画面
@app.get("/edit/{file_id}", response_class=HTMLResponse)
def show_edit(request: Request, file_id: int):
    from test.services.query_handler import get_file_content
    content = get_file_content(file_id)
    return templates.TemplateResponse("edit.html", {
        "request": request,
        "file_id": file_id,
        "content": content
    })

# ──────────────────────────────────────────────────────────
# REM: ⑪ 保存 & 再ベクトル化
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
# REM: 開発用エントリポイント
if __name__ == "__main__":
    uvicorn.run("test.main:app", host="0.0.0.0", port=8000, reload=True)
