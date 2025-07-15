# REM: app/routes/ingest.py（更新日時: 2025-07-15 19:30 JST）
# REM: 1ファイル単位で LLM 整形 → 500+50 チャンク → ベクトル化
# REM: ※ 肥大化が進んでいるため今後 util へ分割予定（現段階は全文掲載）

# REM: ── 標準ライブラリ
import asyncio, functools, glob, json, os, tempfile, time, unicodedata
from typing import Generator, List, Optional

# REM: ── FastAPI
from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import JSONResponse, StreamingResponse

# REM: ── プロジェクト共通
from src.config import EMBEDDING_OPTIONS, OLLAMA_MODEL
import logging

# REM: ── I/O・LLM・DB
from fileio.extractor     import extract_text_by_extension
from fileio.file_embedder import embed_and_insert
from llm.chunker          import split_into_chunks
from llm.prompt_loader    import list_prompt_keys
from llm.refiner          import normalize_empty_lines, refine_text_with_llm, build_prompt
from ocr.spellcheck       import correct_text
from db.handler           import (
    insert_file_full, get_file_text, update_file_text, update_file_status
)

# REM: ── ログ
logging.basicConfig(
    level=logging.DEBUG if os.getenv("RAG_DEBUG") else logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
LOGGER = logging.getLogger("ingest")

# REM: ── FastAPI ルーター
router = APIRouter(prefix="/ingest", tags=["ingest"])

# REM: ── 直近ジョブ
last_ingest: Optional[dict] = None

# REM: ── LLM タイムアウト秒（0 で無制限）
LLM_TIMEOUT_SEC = int(os.getenv("LLM_TIMEOUT_SEC", "0"))   # 例: 300 など

# REM: ==================================================================================
# REM: 設定取得
# REM: ----------------------------------------------------------------------------------
@router.get("/config", response_class=JSONResponse)
def ingest_config() -> JSONResponse:
    return JSONResponse({
        "prompt_keys": list_prompt_keys(),
        "embedding_options": {k: v["model_name"] for k, v in EMBEDDING_OPTIONS.items()},
    })


# REM: ==================================================================================
# REM: キュー投入
# REM: ----------------------------------------------------------------------------------
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
    ok_ext = {".txt", ".pdf", ".docx", ".csv", ".json", ".eml"}

    # REM: 入力ファイル収集
    if input_mode == "files":
        if not input_files:
            raise HTTPException(400, "処理対象ファイルが選択されていません")
        tmpdir = tempfile.mkdtemp(prefix="ingest_")
        files: List[str] = []
        for up in input_files:
            if os.path.splitext(up.filename)[1].lower() not in ok_ext:
                continue
            dst = os.path.join(tmpdir, up.filename)
            with open(dst, "wb") as fp:
                fp.write(await up.read())
            files.append(dst)
    else:
        pattern = "**/*" if include_subdirs else "*"
        base    = os.path.abspath(input_folder)
        files   = [f for f in glob.glob(os.path.join(base, pattern), recursive=include_subdirs)
                   if os.path.splitext(f)[1].lower() in ok_ext]

    if not files:
        raise HTTPException(400, "対象ファイルが見つかりません")

    last_ingest = {
        "files":             [{"path": f, "filename": os.path.basename(f)} for f in files],
        "refine_prompt_key": refine_prompt_key,
        "embed_models":      embed_models,
        "overwrite":         overwrite_existing,
        "q_thresh":          quality_threshold,
    }
    return JSONResponse({"status": "started", "count": len(files), "mode": input_mode})


# REM: ==================================================================================
# REM: SSE ストリーム
# REM: ----------------------------------------------------------------------------------
@router.get("/stream")
def ingest_stream(request: Request) -> StreamingResponse:
    if not last_ingest:
        raise HTTPException(400, "No ingest job found")

    files        = last_ingest["files"]
    overwrite_f  = last_ingest["overwrite"]
    q_thresh     = last_ingest["q_thresh"]
    total_files  = len(files)
    abort_flag   = {"flag": False}

    # REM: クライアント切断監視
    async def monitor_disconnect():
        while not abort_flag["flag"]:
            if await request.is_disconnected():
                abort_flag["flag"] = True
            await asyncio.sleep(0.3)

    # REM: メインジェネレータ
    async def event_generator() -> Generator[str, None, None]:
        asyncio.create_task(monitor_disconnect())
        yield f"data: {json.dumps({'start': True, 'total_files': total_files})}\n\n"

        for idx, info in enumerate(files, 1):
            if abort_flag["flag"]:
                break

            fp, name = info["path"], info["filename"]
            file_t0  = time.perf_counter()

            # --- ① 仮登録
            try:
                file_id = insert_file_full(fp, "", "", 0.0)
            except Exception as exc:
                LOGGER.exception("insert_file_full")
                yield f"data: {json.dumps({'file': name, 'step': 'DB登録失敗', 'detail': str(exc)})}\n\n"
                continue

            yield f"data: {json.dumps({'file': name, 'file_id': file_id, 'step': 'ファイル登録完了', 'index': idx, 'total': total_files})}\n\n"

            # --- ② テキスト抽出
            yield f"data: {json.dumps({'file': name, 'step': 'テキスト抽出中…'})}\n\n"
            try:
                pages = extract_text_by_extension(fp)
            except Exception as exc:
                LOGGER.exception("extract_text_by_extension")
                update_file_status(file_id, status="error", note=str(exc))
                yield f"data: {json.dumps({'file': name, 'step': 'テキスト抽出失敗', 'detail': str(exc)})}\n\n"
                continue

            yield f"data: {json.dumps({'file': name, 'step': 'テキスト抽出完了', 'pages': len(pages)})}\n\n"

            if abort_flag["flag"] or not pages:
                continue

            # --- ③ ページ結合／前処理
            page_blocks = [normalize_empty_lines(correct_text(unicodedata.normalize("NFKC", p)))
                           for p in pages]
            full_text   = "\n\n".join(page_blocks)
            token_est   = int(len(full_text) * 1.6)
            use_page    = token_est > 8192
            unit_iter   = enumerate(page_blocks, 1) if use_page else [("all", full_text)]

            refined_pages, file_min_score = [], 1.0

            # --- ④ LLM 整形ループ
            for pg, block in unit_iter:
                if abort_flag["flag"]:
                    break
                label = f"page{pg}" if use_page else "all"

                prompt_text = build_prompt(block, last_ingest["refine_prompt_key"])
                preview = prompt_text.strip().replace("\n", " ")[:120]
                yield f"data: {json.dumps({'file': name, 'step': f'使用プロンプト part:{label}', 'preview': preview, 'full_text': prompt_text})}\n\n"
                yield f"data: {json.dumps({'file': name, 'step': f'LLM整形中 part:{label}'})}\n\n"

                job = functools.partial(
                    refine_text_with_llm,
                    block,
                    model=OLLAMA_MODEL,
                    force_lang=last_ingest["refine_prompt_key"],
                    abort_flag=abort_flag,
                )
                try:
                    loop = asyncio.get_running_loop()
                    if LLM_TIMEOUT_SEC > 0:
                        refined, _, score, _ = await asyncio.wait_for(
                            loop.run_in_executor(None, job),
                            timeout=LLM_TIMEOUT_SEC,
                        )
                    else:
                        refined, _, score, _ = await loop.run_in_executor(None, job)
                except asyncio.TimeoutError:
                    update_file_status(file_id, status="error", note="llm timeout")
                    yield f"data: {json.dumps({'file': name, 'step': 'LLMタイムアウト', 'part': label})}\n\n"
                    continue
                except Exception as exc:
                    LOGGER.exception("LLM refine")
                    update_file_status(file_id, status="error", note=str(exc))
                    yield f"data: {json.dumps({'file': name, 'step': 'LLM整形失敗', 'detail': str(exc)})}\n\n"
                    continue

                refined_pages.append(refined)
                file_min_score = min(file_min_score, score)
                yield f"data: {json.dumps({'file': name, 'step': f'LLM整形結果 part:{label}'})}\n\n"

            if abort_flag["flag"] or not refined_pages:
                continue

            # --- ⑤ チャンク化
            final_text = "\n\n".join(refined_pages)
            chunks     = split_into_chunks(final_text, 500, 50)
            yield f"data: {json.dumps({'file': name, 'step': f'チャンク分割完了 chunks={len(chunks)}'})}\n\n"

            # --- ⑥ ベクトル化
            job = functools.partial(
                embed_and_insert,
                texts=chunks,
                filename=fp,
                model_keys=last_ingest["embed_models"],
                quality_score=file_min_score,
                file_id=file_id,
            )
            try:
                loop = asyncio.get_running_loop()
                await loop.run_in_executor(None, job)
                yield f"data: {json.dumps({'file': name, 'step': 'ベクトル化完了'})}\n\n"
            except Exception as exc:
                LOGGER.exception("embed_and_insert")
                update_file_status(file_id, status="error", note=str(exc))
                yield f"data: {json.dumps({'file': name, 'step': 'ベクトル化失敗', 'detail': str(exc)})}\n\n"

            # --- ⑦ files_text 更新
            cur = get_file_text(file_id) or {}
            need_update = (
                overwrite_f
                or not cur.get("refined_text")
                or (cur.get("quality_score") or 0.0) < q_thresh
                or file_min_score < (cur.get("quality_score") or 1.0)
            )
            if need_update:
                update_file_text(file_id, final_text, file_min_score)
                yield f"data: {json.dumps({'file': name, 'step': '全文保存完了（上書き実施）'})}\n\n"
            else:
                yield f"data: {json.dumps({'file': name, 'step': '全文保存スキップ'})}\n\n"

            update_file_status(file_id, status="done")
            elapsed = round(time.perf_counter() - file_t0, 2)
            yield f"data: {json.dumps({'file': name, 'step': 'file_done', 'elapsed': elapsed})}\n\n"

        # --- 完了
        yield f"data: {json.dumps({'done': True})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
