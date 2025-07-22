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
from app.services.ingest.worker import process_file
from app.services.ocr import OCREngineFactory
from app.services.ingest import IngestSettingsManager

# REM: ルーター定義
router    = APIRouter(prefix="/ingest", tags=["ingest"])

BASE_DIR      = os.path.dirname(__file__) 
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
templates = Jinja2Templates(directory=TEMPLATES_DIR)

LOGGER    = logging.getLogger("ingest")

# REM: 定数
LLM_TIMEOUT_SEC = int(os.getenv("LLM_TIMEOUT_SEC", "300"))  # デフォルト5分
OK_EXT          = {".txt", ".pdf", ".docx", ".csv", ".json", ".eml"}

# REM: 直近ジョブ保持
last_ingest: Optional[dict] = None

# REM: キャンセル制御用イベント
cancel_event: Optional[asyncio.Event] = None

# REM: OCRファクトリとIngest設定管理
ocr_factory = OCREngineFactory()
ingest_settings = IngestSettingsManager()

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
    """フロント向け設定情報を返す（OCR設定含む）"""
    # OCRエンジン情報を取得
    available_engines = ocr_factory.get_available_engines()
    current_settings = ingest_settings.load_settings()
    
    return JSONResponse({
        "prompt_keys": list(EMBEDDING_OPTIONS.keys()),
        "embedding_options": {k: v["model_name"] for k, v in EMBEDDING_OPTIONS.items()},
        "ocr": {
            "available_engines": available_engines,
            "default_engine": current_settings.get("ocr", {}).get("default_engine", "ocrmypdf"),
            "current_settings": current_settings
        }
    })

# ══════════════════════ 2.1 GET /ingest/ocr/engines (OCRエンジン一覧) ══════════════════════
@router.get("/ocr/engines", response_class=JSONResponse)
def get_ocr_engines() -> JSONResponse:
    """利用可能なOCRエンジン一覧を返す"""
    return JSONResponse(ocr_factory.get_available_engines())

# ══════════════════════ 2.2 GET /ingest/ocr/settings/{engine_id} (OCRエンジン設定取得) ══════════════════════
@router.get("/ocr/settings/{engine_id}", response_class=JSONResponse)
def get_ocr_engine_settings(engine_id: str) -> JSONResponse:
    """指定エンジンの現在の設定を返す"""
    settings = ocr_factory.get_engine_settings(engine_id)
    return JSONResponse({"engine_id": engine_id, "settings": settings})

# ══════════════════════ 2.3 POST /ingest/ocr/settings/{engine_id} (OCRエンジン設定更新) ══════════════════════
@router.post("/ocr/settings/{engine_id}", response_class=JSONResponse)
async def update_ocr_engine_settings(engine_id: str, request: Request) -> JSONResponse:
    """指定エンジンの設定を更新"""
    try:
        settings_data = await request.json()
        ocr_factory.update_engine_settings(engine_id, settings_data)
        return JSONResponse({"status": "success", "engine_id": engine_id})
    except Exception as e:
        raise HTTPException(400, f"設定更新エラー: {str(e)}")

# ══════════════════════ 2.4 GET /ingest/ocr/presets (OCRプリセット一覧) ══════════════════════
@router.get("/ocr/presets", response_class=JSONResponse)
def get_ocr_presets() -> JSONResponse:
    """OCRプリセット一覧を返す"""
    return JSONResponse(ocr_factory.get_presets())

# ══════════════════════ 2.5 POST /ingest/ocr/presets (OCRプリセット保存) ══════════════════════
@router.post("/ocr/presets", response_class=JSONResponse)
async def save_ocr_preset(request: Request) -> JSONResponse:
    """OCRプリセットを保存"""
    try:
        data = await request.json()
        preset_name = data.get("preset_name")
        engine_id = data.get("engine_id")
        settings = data.get("settings", {})
        
        if not preset_name or not engine_id:
            raise HTTPException(400, "preset_name と engine_id は必須です")
        
        ocr_factory.save_preset(preset_name, engine_id, settings)
        return JSONResponse({"status": "success", "preset_name": preset_name})
    except Exception as e:
        raise HTTPException(400, f"プリセット保存エラー: {str(e)}")

# ══════════════════════ 2.6 DELETE /ingest/ocr/presets/{preset_name} (OCRプリセット削除) ══════════════════════
@router.delete("/ocr/presets/{preset_name}", response_class=JSONResponse)
def delete_ocr_preset(preset_name: str) -> JSONResponse:
    """OCRプリセットを削除"""
    try:
        ocr_factory.delete_preset(preset_name)
        return JSONResponse({"status": "success", "preset_name": preset_name})
    except Exception as e:
        raise HTTPException(400, f"プリセット削除エラー: {str(e)}")

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
    llm_timeout: int              = Form(300),   # REM: LLMタイムアウト設定（秒）
    ocr_engine_id: str            = Form(None),  # REM: OCRエンジン指定
    ocr_settings: str             = Form("{}"),  # REM: OCR設定（JSON文字列）
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

    # REM: OCR設定の解析
    try:
        ocr_settings_dict = json.loads(ocr_settings) if ocr_settings else {}
    except json.JSONDecodeError:
        raise HTTPException(400, "OCR設定のJSON形式が不正です")

    # REM: ジョブ情報保持 — 編集ペインのテキストとOCR設定も格納
    last_ingest = {
        "files":                [{"path": p, "file_name": os.path.basename(p)} for p in paths],
        "refine_prompt_key":    refine_prompt_key,
        "refine_prompt_text":   refine_prompt_text,
        "embed_models":         embed_models,
        "overwrite_existing":   overwrite_existing,
        "quality_threshold":    quality_threshold,
        "llm_timeout_sec":      llm_timeout,
        "ocr_engine_id":        ocr_engine_id,
        "ocr_settings":         ocr_settings_dict,
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

            # REM: 編集ペインのテキストとOCR設定を渡す
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
                llm_timeout_sec     = last_ingest["llm_timeout_sec"],
                abort_flag          = abort_flag,
                ocr_engine_id       = last_ingest.get("ocr_engine_id"),
                ocr_settings        = last_ingest.get("ocr_settings", {}),
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
