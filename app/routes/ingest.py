# REM: app/routes/ingest.py @2025-07-18 00:00 UTC +9
# REM: SSE を使ったデータ整形／登録ルーター

# REM: ── 標準ライブラリ ───────────────────────────────────
import asyncio
import glob
import json
import os
import tempfile
from typing import List, Optional

# REM: ── FastAPI ────────────────────────────────────────
from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import JSONResponse, StreamingResponse, HTMLResponse
from fastapi.templating import Jinja2Templates

# REM: ── プロジェクト共通 ───────────────────────────────
from src.config import EMBEDDING_OPTIONS, DEVELOPMENT_MODE, OLLAMA_MODEL
from db.handler import reset_dev_database
import logging

# REM: ── サービス層 ───────────────────────────────────
from app.services.ingest_worker import process_file

# REM: ルーター定義
router    = APIRouter(prefix="/ingest", tags=["ingest"])
templates = Jinja2Templates(directory="app/fastapi/templates")
LOGGER    = logging.getLogger("ingest")

# REM: 定数
LLM_TIMEOUT_SEC = int(os.getenv("LLM_TIMEOUT_SEC", "0"))
OK_EXT          = {".txt", ".pdf", ".docx", ".csv", ".json", ".eml"}

# REM: 直近ジョブ保持
last_ingest: Optional[dict] = None

# REM: キャンセル制御用イベント
cancel_event: Optional[asyncio.Event] = None

# ══════════════════════ 1. GET /ingest (管理画面表示) ══════════════════════
@router.get("", response_class=HTMLResponse)
def ingest_page(request: Request):
    """管理者モードのデータ整形／登録画面を返す"""
    return templates.TemplateResponse("ingest.html", {
        "request": request,
        "llm_model": OLLAMA_MODEL,
        "prompt_keys": list(EMBEDDING_OPTIONS.keys()),
        "embedding_options": EMBEDDING_OPTIONS,
    })

# ══════════════════════ 2. GET /ingest/config (UI 設定取得) ══════════════════════
@router.get("/config", response_class=JSONResponse)
def ingest_config() -> JSONResponse:
    """フロント向け設定情報を返す"""
    return JSONResponse({
        "prompt_keys": list(EMBEDDING_OPTIONS.keys()),
        "embedding_options": {k: v["model_name"] for k, v in EMBEDDING_OPTIONS.items()},
    })

# ══════════════════════ 3. POST /ingest (ジョブ登録) ══════════════════════
@router.post("", response_class=JSONResponse)
async def run_ingest_folder(
    *,
    input_mode: str               = Form(...),
    input_folder: str             = Form(""),
    input_files: List[UploadFile] = File(None),
    include_subdirs: bool         = Form(False),
    refine_prompt_key: str        = Form(...),
    refine_prompt_text: str       = Form(None),  # REM: 編集ペインのテキストを受け取る
    embed_models: List[str]       = Form(...),
    overwrite_existing: bool      = Form(False),
    quality_threshold: float      = Form(0.0),
) -> JSONResponse:
    """ジョブ情報を保持し即時返却"""
    global last_ingest, cancel_event

    # REM: キャンセルフラグ初期化
    cancel_event = asyncio.Event()

    # REM: 開発モードなら DB 初期化
    if DEVELOPMENT_MODE:
        reset_dev_database()

    # REM: 対象ファイル列挙
    if input_mode == "files":
        if not input_files:
            raise HTTPException(400, "処理対象ファイルが選択されていません")
        tmpdir = tempfile.mkdtemp(prefix="ingest_")
        paths  = []
        for up in input_files:
            ext = os.path.splitext(up.filename)[1].lower()
            if ext not in OK_EXT:
                continue
            dst = os.path.join(tmpdir, up.filename)
            with open(dst, "wb") as fp:
                fp.write(await up.read())
            paths.append(dst)
    else:
        pattern = "**/*" if include_subdirs else "*"
        base    = os.path.abspath(input_folder)
        paths   = [
            f for f in glob.glob(os.path.join(base, pattern), recursive=include_subdirs)
            if os.path.splitext(f)[1].lower() in OK_EXT
        ]

    if not paths:
        raise HTTPException(400, "対象ファイルが見つかりません")

    # REM: ジョブ情報保持 — 編集ペインのテキストも格納
    last_ingest = {
        "files":                [{"path": p, "file_name": os.path.basename(p)} for p in paths],
        "refine_prompt_key":    refine_prompt_key,
        "refine_prompt_text":   refine_prompt_text,
        "embed_models":         embed_models,
        "overwrite_existing":   overwrite_existing,
        "quality_threshold":    quality_threshold,
    }

    return JSONResponse({"status": "started", "count": len(paths), "mode": input_mode})

# ══════════════════════ 3.1 POST /ingest/cancel (キャンセル指示) ══════════════════════
@router.post("/cancel", response_class=JSONResponse)
def cancel_ingest() -> JSONResponse:
    """実行中の ingest ジョブのキャンセルを指示"""
    global cancel_event
    if cancel_event is None:
        raise HTTPException(400, "キャンセル対象のジョブがありません")
    cancel_event.set()
    LOGGER.info("ingest job cancellation requested")
    return JSONResponse({"status": "cancelling"})

# ══════════════════════ 3.2 GET /ingest/status (ジョブ状態取得) ══════════════════════
@router.get("/status", response_class=JSONResponse)
def ingest_status() -> JSONResponse:
    """現在の ingest ジョブの状態を返却"""
    if last_ingest is None:
        raise HTTPException(400, "No ingest job found")
    status = "running"
    if cancel_event and cancel_event.is_set():
        status = "cancelling"
    return JSONResponse({"status": status})

# ══════════════════════ 4. GET /ingest/stream (SSE ストリーミング) ══════════════════════
@router.get("/stream")
async def ingest_stream(request: Request) -> StreamingResponse:
    """SSE で進捗イベントをストリーミング"""
    LOGGER.info(f"[SSE] connection from {request.client.host}:{request.client.port}")
    if not last_ingest:
        raise HTTPException(400, "No ingest job found")

    files       = last_ingest["files"]
    total_files = len(files)
    abort_flag  = {"flag": False}

    # REM: クライアント切断監視（非同期）
    async def monitor_disconnect():
        while not abort_flag["flag"]:
            if await request.is_disconnected():
                abort_flag["flag"] = True
            await asyncio.sleep(0.3)

    # REM: SSE イベントジェネレータ
    async def event_generator():
        # 切断監視開始
        asyncio.create_task(monitor_disconnect())

        # REM: 全体開始イベント
        yield f"data: {json.dumps({'start': True, 'total_files': total_files})}\n\n"

        loop = asyncio.get_event_loop()
        for idx, info in enumerate(files, start=1):
            # REM: キャンセルまたは切断検知
            if abort_flag["flag"] or (cancel_event and cancel_event.is_set()):
                # REM: キャンセル開始通知
                yield f"data: {json.dumps({'cancelling': True})}\n\n"
                break

            # REM: 編集ペインのテキストを渡す
            gen = process_file(
                file_path           = info["path"],
                file_name           = info["file_name"],
                index               = idx,
                total_files         = total_files,
                refine_prompt_key   = last_ingest["refine_prompt_key"],
                refine_prompt_text  = last_ingest.get("refine_prompt_text"),
                embed_models        = last_ingest["embed_models"],
                overwrite_existing  = last_ingest["overwrite_existing"],
                quality_threshold   = last_ingest["quality_threshold"],
                llm_timeout_sec     = LLM_TIMEOUT_SEC,
                abort_flag          = abort_flag,
            )

            # REM: ジェネレータからイベントを取り出しストリーミング
            while not abort_flag["flag"] and not (cancel_event and cancel_event.is_set()):
                ev = await loop.run_in_executor(None, lambda: next(gen, None))
                if ev is None:
                    break
                yield f"data: {json.dumps(ev)}\n\n"

        # REM: キャンセル完了通知
        if cancel_event and cancel_event.is_set():
            yield f"data: {json.dumps({'stopped': True})}\n\n"

        # REM: 全体完了イベント
        yield "data: {\"done\": true}\n\n"

    # REM: StreamingResponse による SSE 配信
    return StreamingResponse(event_generator(), media_type="text/event-stream")
