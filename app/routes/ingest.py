# REM: app/routes/ingest.py（更新: 2025-07-15 22:30 JST）
# REM: ルーター & SSE ラッパー専用に簡素化

# ── 標準ライブラリ ───────────────────────────────
import asyncio, glob, json, os, tempfile
from typing import Generator, List, Optional

# ── FastAPI ──────────────────────────────────────
from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import JSONResponse, StreamingResponse

# ── プロジェクト共通 ──────────────────────────────
from src.config import EMBEDDING_OPTIONS, DEVELOPMENT_MODE
from db.handler import reset_dev_database
import logging

# ── サービス層 ────────────────────────────────────
from app.services.ingest_worker import process_file

# ── ルーター定義 ─────────────────────────────────
router = APIRouter(prefix="/ingest", tags=["ingest"])
LOGGER = logging.getLogger("ingest")

# ── 定数 ──────────────────────────────────────────
LLM_TIMEOUT_SEC = int(os.getenv("LLM_TIMEOUT_SEC", "0"))
OK_EXT = {".txt", ".pdf", ".docx", ".csv", ".json", ".eml"}

# ── 直近ジョブ保持 ───────────────────────────────
last_ingest: Optional[dict] = None


# ══════════════════════ /ingest/config ══════════════════════
@router.get("/config", response_class=JSONResponse)
def ingest_config() -> JSONResponse:
    return JSONResponse({
        "prompt_keys": list(EMBEDDING_OPTIONS.keys()),
        "embedding_options": {k: v["model_name"] for k, v in EMBEDDING_OPTIONS.items()},
    })


# ══════════════════════ /ingest POST（キュー投入） ══════════
@router.post("", response_class=JSONResponse)
async def run_ingest_folder(
    *,
    input_mode: str               = Form(...),
    input_folder: str             = Form(""),
    input_files: List[UploadFile] = File(None),
    include_subdirs: bool         = Form(False),
    refine_prompt_key: str        = Form(...),
    embed_models: List[str]       = Form(...),
    overwrite_existing: bool      = Form(False),
    quality_threshold: float      = Form(0.0),
) -> JSONResponse:
    global last_ingest

    # ── 開発モードならここで DB 初期化 ─────────────────
    if DEVELOPMENT_MODE:
        reset_dev_database()

    # --- 対象ファイル列挙 ------------------------------------------------------
    if input_mode == "files":
        if not input_files:
            raise HTTPException(400, "処理対象ファイルが選択されていません")
        tmpdir = tempfile.mkdtemp(prefix="ingest_")
        paths = []
        for up in input_files:
            if os.path.splitext(up.filename)[1].lower() not in OK_EXT:
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

    last_ingest = {
        "files":             [{"path": p, "file_name": os.path.basename(p)} for p in paths],
        "refine_prompt_key": refine_prompt_key,
        "embed_models":      embed_models,
        "overwrite":         overwrite_existing,
        "q_thresh":          quality_threshold,
    }
    return JSONResponse({"status": "started", "count": len(paths), "mode": input_mode})


# ══════════════════════ /ingest/stream SSE ══════════════════
@router.get("/stream")
def ingest_stream(request: Request) -> StreamingResponse:
    if not last_ingest:
        raise HTTPException(400, "No ingest job found")

    files        = last_ingest["files"]
    total_files  = len(files)
    abort_flag   = {"flag": False}

    # --- クライアント切断監視 -----------------------------------------------
    async def monitor_disconnect():
        while not abort_flag["flag"]:
            if await request.is_disconnected():
                abort_flag["flag"] = True
            await asyncio.sleep(0.3)

    # --- SSE ジェネレータ ----------------------------------------------------
    async def event_generator() -> Generator[str, None, None]:
        asyncio.create_task(monitor_disconnect())
        yield f"data: {json.dumps({'start': True, 'total_files': total_files})}\n\n"

        for idx, info in enumerate(files, 1):
            if abort_flag["flag"]:
                break

            for ev in process_file(
                file_path=info["path"],
                file_name=info["file_name"],
                index=idx,
                total_files=total_files,
                refine_prompt_key=last_ingest["refine_prompt_key"],
                embed_models=last_ingest["embed_models"],
                overwrite_existing=last_ingest["overwrite"],
                quality_threshold=last_ingest["q_thresh"],
                llm_timeout_sec=LLM_TIMEOUT_SEC,
                abort_flag=abort_flag,
            ):
                yield f"data: {json.dumps(ev)}\n\n"

        yield "data: {\"done\": true}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
