# REM: app/routes/ingest.py（更新日時: 2025-07-13 00:45JST）
# REM: フォルダ／ファイル一括インジェスト → OCR → LLM 整形 → ベクトル化

# ── 標準ライブラリ ───────────────────────────────
import os, json, glob, time, asyncio, tempfile
from typing import List

# ── FastAPI ─────────────────────────────────────
from fastapi import (
    APIRouter, Form, File, UploadFile, HTTPException, Request
)
from fastapi.responses import StreamingResponse, JSONResponse

# ── プロジェクト共通設定 ────────────────────────
from sqlalchemy import text
from src.config import DB_ENGINE, EMBEDDING_OPTIONS, OLLAMA_MODEL

# ── ファイル I/O & OCR 抽出 ─────────────────────
from fileio.file_embedder import embed_and_insert
from fileio.extractor      import extract_text_by_extension

# ── DB ハンドラ（3 テーブル + UUID 版） ─────────
from db.handler import (
    insert_file_full,
    get_file_text,
    update_file_text
)

# ── LLM ユーティリティ ────────────────────────
from llm.refiner        import refine_text_with_llm, build_prompt
from llm.prompt_loader  import list_prompt_keys

# ── FastAPI ルーター初期化 ───────────────────────
router = APIRouter()

# ── 直近実行ジョブ情報保持 ───────────────────────
last_ingest: dict | None = None


# ────────────────────────────────────────────────
@router.get("/ingest/config", response_class=JSONResponse)
def ingest_config():
    """JS 側設定取得 API"""
    return JSONResponse({
        "prompt_keys":       list_prompt_keys(),
        "embedding_options": {k: v["model_name"] for k, v in EMBEDDING_OPTIONS.items()}
    })


# ────────────────────────────────────────────────
@router.post("/ingest", response_class=JSONResponse)
async def run_ingest_folder(
    input_mode:         str                 = Form(...),   # 'folder' or 'files'
    input_folder:       str                 = Form(""),    # フォルダ指定モード
    input_files:        List[UploadFile]    = File(None),  # ファイル指定モード
    include_subdirs:    bool                = Form(False),
    refine_prompt_key:  str                 = Form(...),
    embed_models:       List[str]           = Form(...),
    overwrite_existing: bool                = Form(False),
    quality_threshold:  float               = Form(0.0),
):
    """インジェスト開始（非同期）"""
    global last_ingest
    ok_ext = {".txt", ".pdf", ".docx", ".csv", ".json", ".eml"}

    # REM: 入力ファイル収集
    if input_mode == "files":
        if not input_files:
            raise HTTPException(400, "処理対象ファイルが選択されていません")
        tmpdir = tempfile.mkdtemp(prefix="ingest_")
        files: List[str] = []
        for upload in input_files:
            ext = os.path.splitext(upload.filename)[1].lower()
            if ext not in ok_ext:
                continue
            dest = os.path.join(tmpdir, upload.filename)
            with open(dest, "wb") as f:
                f.write(await upload.read())
            files.append(dest)
    else:
        pattern = "**/*" if include_subdirs else "*"
        base    = os.path.abspath(input_folder)
        files   = [
            f for f in glob.glob(os.path.join(base, pattern), recursive=include_subdirs)
            if os.path.splitext(f)[1].lower() in ok_ext
        ]

    if not files:
        raise HTTPException(400, "対象ファイルが見つかりません")

    # REM: 実行パラメータ保持
    last_ingest = {
        "files":             [{"path": f, "filename": os.path.basename(f)} for f in files],
        "refine_prompt_key": refine_prompt_key,
        "embed_models":      embed_models,
        "overwrite":         overwrite_existing,
        "q_thresh":          quality_threshold,
    }
    return {"status": "started", "count": len(files), "mode": input_mode}


# ────────────────────────────────────────────────
@router.get("/ingest/stream")
def ingest_stream(request: Request):
    """SSE で逐次進捗を返すストリーム API"""
    if not last_ingest:
        raise HTTPException(400, "No ingest job found")

    files       = last_ingest["files"]
    overwrite_f = last_ingest["overwrite"]
    q_thresh    = last_ingest["q_thresh"]
    total       = len(files)
    abort_flag  = {"flag": False}

    # REM: クライアント切断監視
    async def monitor_disconnect():
        while not abort_flag["flag"]:
            if await request.is_disconnected():
                abort_flag["flag"] = True
                break
            await asyncio.sleep(0.1)

    # REM: SSE コルーチン
    async def event_generator():
        dc_task = asyncio.create_task(monitor_disconnect())
        try:
            for idx, info in enumerate(files, start=1):
                if abort_flag["flag"]:
                    break
                fp, name = info["path"], info["filename"]

                # REM: ① ファイル仮登録（空コンテンツ挿入 → UUID 取得）
                file_id = insert_file_full(fp, "", "", 0.0, tags=[])
                yield f"data: {json.dumps({'file':name,'file_id':file_id,'step':'ファイル登録完了','index':idx,'total':total})}\n\n"

                # REM: ② テキスト抽出
                yield f"data: {json.dumps({'file':name,'step':'テキスト抽出中…'})}\n\n"
                t0    = time.time()
                texts = extract_text_by_extension(fp)
                dur   = round(time.time() - t0, 2)
                yield f"data: {json.dumps({'file':name,'step':'テキスト抽出完了','duration':dur})}\n\n"
                if abort_flag["flag"] or not texts:
                    continue
                texts = list(dict.fromkeys(texts))  # 重複除去

                # REM: ③ ページ単位整形
                refined_pages = []
                file_min_score = 1.0

                for pg, block in enumerate(texts, start=1):
                    if abort_flag["flag"]:
                        break
                    yield f"data: {json.dumps({'file':name,'step':f'Page {pg} 処理開始'})}\n\n"

                    # --- OCR 誤記訂正 / 空行圧縮 ----------------------------------
                    import unicodedata
                    from ocr.spellcheck import correct_text
                    from llm.refiner   import normalize_empty_lines

                    normed       = unicodedata.normalize("NFKC", block)
                    corrected    = correct_text(normed)
                    block_clean  = normalize_empty_lines(corrected)

                    preview = block_clean.strip().replace("\n", " ")[:40]
                    yield f"data: {json.dumps({'file':name,'step':f'OCR page{pg}','preview':preview})}\n\n"

                    # --- プロンプト生成 ------------------------------------------
                    prompt_text = build_prompt(block_clean, last_ingest["refine_prompt_key"])
                    prev_p      = prompt_text.strip().replace("\n", " ")[:80]
                    yield f"data: {json.dumps({'file':name,'step':f'使用プロンプト page{pg}','preview':prev_p})}\n\n"

                    # --- LLM 整形 -----------------------------------------------
                    yield f"data: {json.dumps({'file':name,'step':'LLM整形中'})}\n\n"
                    t1 = time.time()
                    refined, lang, score, _ = refine_text_with_llm(
                        block_clean,
                        model=OLLAMA_MODEL,
                        force_lang=last_ingest["refine_prompt_key"],
                        abort_flag=abort_flag
                    )
                    dur2 = round(time.time() - t1, 2)
                    file_min_score = min(file_min_score, score)
                    refined_pages.append(refined)

                    prev_r = refined.strip().replace("\n", " ")[:40]
                    yield f"data: {json.dumps({'file':name,'step':f'LLM整形結果 page{pg}','preview':prev_r,'duration':dur2})}\n\n"

                    if not refined.strip():
                        yield f"data: {json.dumps({'file':name,'step':f'LLM結果空 → ベクトル化スキップ page{pg}'})}\n\n"
                        continue

                    # --- ベクトル化 ---------------------------------------------
                    for mkey in last_ingest["embed_models"]:
                        if abort_flag["flag"]:
                            break
                        embed_and_insert(
                            texts=[refined],
                            filename=fp,
                            model_keys={mkey},
                            quality_score=score,
                            file_id=file_id
                        )
                        mname = EMBEDDING_OPTIONS[mkey]["model_name"]
                        yield f"data: {json.dumps({'file':name,'step':f'ベクトル化 ({mname})'})}\n\n"

                # REM: ④ 全文保存判定
                if refined_pages:
                    full_text = "\n\n".join(refined_pages)
                    cur = get_file_text(file_id)
                    need_update = (
                        overwrite_f
                        or not cur["content"]
                        or (cur["quality_score"] or 0.0) < q_thresh
                        or file_min_score < (cur["quality_score"] or 1.0)
                    )
                    if need_update:
                        update_file_text(file_id, full_text, file_min_score)
                        yield f"data: {json.dumps({'file':name,'step':'全文保存完了（上書き実施）'})}\n\n"
                    else:
                        yield f"data: {json.dumps({'file':name,'step':'全文保存スキップ'})}\n\n"

                # REM: ファイル区切り
                yield "\n\n"
        finally:
            dc_task.cancel()

        # REM: 全処理完了通知
        yield f"data: {json.dumps({'done': True})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
