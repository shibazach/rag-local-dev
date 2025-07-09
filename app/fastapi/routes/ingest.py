# /workspace/app/fastapi/routes/ingest.py
"""
フォルダ内ファイルを一括インジェスト → OCR → LLM 整形 → ベクトル化
SSE で進捗を返却する FastAPI ルーター
"""

# REM: 標準ライブラリ
import os
import json
import glob
import time
import asyncio
from typing import List

# REM: FastAPI
from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import StreamingResponse, JSONResponse

# REM: プロジェクト共通
from sqlalchemy import text
from src.config import (
    DB_ENGINE,          # files.content 更新に使用
    EMBEDDING_OPTIONS,
    OLLAMA_MODEL
)
from fileio.file_embedder import embed_and_insert
from fileio.extractor import extract_text_by_extension
from db.handler import upsert_file
from llm.refiner import refine_text_with_llm
from llm.prompt_loader import list_prompt_keys, get_prompt_by_lang

router = APIRouter()
last_ingest: dict | None = None           # REM: 直近ジョブのメタ情報


# ──────────────────────────────────────────────────────────
# REM: JS 起動時に送る設定情報
@router.get("/ingest/config", response_class=JSONResponse)
def ingest_config():
    return JSONResponse({
        "prompt_keys":       list_prompt_keys(),
        "embedding_options": {k: v["model_name"] for k, v in EMBEDDING_OPTIONS.items()}
    })


# ──────────────────────────────────────────────────────────
# REM: ingest ジョブ登録（POST /ingest）
@router.post("/ingest", response_class=JSONResponse)
async def run_ingest_folder(
    input_folder:      str         = Form(...),
    include_subdirs:   bool        = Form(...),
    refine_prompt_key: str         = Form(...),
    embed_models:      List[str]   = Form(...)
):
    """
    - input_folder: 解析対象フォルダ（サーバ側パス）
    - include_subdirs: サブディレクトリ再帰フラグ
    - refine_prompt_key: 使用するプロンプトキー
    - embed_models: ベクトル化で使うモデルキー群
    """
    global last_ingest

    ok_ext = [".txt", ".pdf", ".docx", ".csv", ".json", ".eml"]
    pattern = "**/*" if include_subdirs else "*"
    base    = os.path.abspath(input_folder)
    files   = [
        f for f in glob.glob(os.path.join(base, pattern), recursive=include_subdirs)
        if os.path.splitext(f)[1].lower() in ok_ext
    ]

    if not files:
        raise HTTPException(400, "対象ファイルが見つかりません")

    last_ingest = {
        "files":  [{"path": f, "filename": os.path.basename(f)} for f in files],
        "refine_prompt_key": refine_prompt_key,
        "embed_models": embed_models
    }
    return {"status": "started", "count": len(files), "folder": input_folder}


# ──────────────────────────────────────────────────────────
# REM: ingest 実行 & SSE ストリーム（GET /ingest/stream）
@router.get("/ingest/stream")
def ingest_stream(request: Request):
    if not last_ingest:
        raise HTTPException(400, "No ingest job found")

    files      = last_ingest["files"]
    total      = len(files)
    abort_flag = {"flag": False}          # REM: クライアント切断監視用フラグ

    # REM: クライアント切断を監視するタスク
    async def monitor_disconnect():
        while not abort_flag["flag"]:
            if await request.is_disconnected():
                abort_flag["flag"] = True
                break
            await asyncio.sleep(0.1)

    # REM: SSE イベントを逐次生成
    async def event_generator():
        dc_task = asyncio.create_task(monitor_disconnect())
        try:
            for idx, info in enumerate(files, start=1):
                if abort_flag["flag"]:
                    break

                fp, name = info["path"], info["filename"]

                # ── ① files テーブル登録（初回 TRUNCATE）
                fid = upsert_file(fp, "", 0.0, truncate_once=True)
                yield f"data: {json.dumps({'file':name,'file_id':fid,'step':'ファイル登録中','index':idx,'total':total})}\n\n"
                yield f"data: {json.dumps({'file':name,'step':'登録完了'})}\n\n"

                # ── ② テキスト抽出
                yield f"data: {json.dumps({'file':name,'step':'テキスト抽出中…'})}\n\n"
                t0    = time.time()
                texts = extract_text_by_extension(fp)
                dur   = round(time.time() - t0, 2)
                yield f"data: {json.dumps({'file':name,'step':'テキスト抽出完了','duration':dur})}\n\n"
                if abort_flag["flag"] or not texts:
                    continue
                texts = list(dict.fromkeys(texts))  # REM: 重複除去

                # ── ③ ページ単位処理
                refined_pages: list[str] = []        # REM: 各ページの整形結果を蓄積
                for pg, block in enumerate(texts, start=1):
                    if abort_flag["flag"]:
                        break
                    yield f"data: {json.dumps({'file':name,'step':f'Page {pg} 処理開始'})}\n\n"

                    preview = block.strip().replace("\n", " ")[:40]
                    yield f"data: {json.dumps({'file':name,'step':f'OCR page{pg}','preview':preview,'full_text':block})}\n\n"

                    # --- プロンプト生成
                    yield f"data: {json.dumps({'file':name,'step':'プロンプト生成中'})}\n\n"
                    _, tmpl = get_prompt_by_lang(last_ingest["refine_prompt_key"])
                    clean   = '\n'.join(l for l in block.splitlines() if l.strip())
                    prompt  = tmpl.replace("{TEXT}", clean).replace("{input_text}", clean)
                    prev_p  = (prompt.replace('\n',' ')[:80] + '...') if len(prompt)>80 else prompt
                    yield f"data: {json.dumps({'file':name,'step':f'使用プロンプト page{pg}','preview':prev_p,'full_text':prompt})}\n\n"

                    # --- LLM 整形
                    yield f"data: {json.dumps({'file':name,'step':'LLM整形中'})}\n\n"
                    t1 = time.time()
                    refined, lang, score, _ = refine_text_with_llm(
                        block,
                        model=OLLAMA_MODEL,
                        force_lang=last_ingest["refine_prompt_key"],
                        abort_flag=abort_flag
                    )
                    dur2  = round(time.time() - t1, 2)
                    prev2 = refined.strip().replace("\n"," ")[:40]
                    yield f"data: {json.dumps({'file':name,'step':f'LLM整形 page{pg}','preview':prev2,'full_text':refined,'duration':dur2})}\n\n"

                    refined_pages.append(refined)

                    # --- ベクトル化
                    for mi, mkey in enumerate(last_ingest["embed_models"], start=1):
                        if abort_flag["flag"]:
                            break
                        t2 = time.time()
                        embed_and_insert(
                            texts=[refined],
                            filename=fp,
                            model_keys={mkey},
                            quality_score=score
                        )
                        dur_vec = round(time.time() - t2, 2)
                        mname   = EMBEDDING_OPTIONS[mkey]["model_name"]
                        yield f"data: {json.dumps({'file':name,'step':f'ベクトル化（No.{mi}: {mname}）','duration':dur_vec,'last':mi==len(last_ingest['embed_models'])})}\n\n"

                # ── ④ ファイル単位で全文を結合して files.content を更新
                if refined_pages:  # abort_flag に関わらず更新
                    full_text = "\n\n".join(refined_pages)
                    with DB_ENGINE.begin() as tx:
                        tx.execute(
                            text("UPDATE files SET content=:c WHERE file_id=:id"),
                            {"c": full_text, "id": fid}
                        )
                    yield f"data: {json.dumps({'file':name,'step':'全文保存完了'})}\n\n"

                yield "\n\n"  # REM: ファイル区切り
        finally:
            dc_task.cancel()

        yield f"data: {json.dumps({'done':True})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
