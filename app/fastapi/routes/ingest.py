# app/fastapi/routes/ingest.py
# REM: 最終更新 2025-07-10 17:47 JST
"""
フォルダ内ファイルを一括インジェスト → OCR → LLM 整形 → ベクトル化
SSE で進捗を返却する FastAPI ルーター
"""

# REM: 標準ライブラリ
import os
import re
import json
import glob
import time
import asyncio
from typing import List

# REM: FastAPI
from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import StreamingResponse, JSONResponse

# REM: プロジェクト共通設定
from sqlalchemy import text
from src.config import DB_ENGINE, EMBEDDING_OPTIONS, OLLAMA_MODEL

# REM: ファイル入出力／OCR抽出
from fileio.file_embedder import embed_and_insert
from fileio.extractor import extract_text_by_extension

# REM: DB操作（ファイル仮登録）
from db.handler import upsert_file

# REM: LLM整形ユーティリティ
from llm.refiner import refine_text_with_llm, build_prompt
from llm.prompt_loader import list_prompt_keys

# REM: FastAPIルーター初期化
router = APIRouter()

# REM: 直近実行ジョブ情報
last_ingest: dict | None = None


# ──────────────────────────────────────────────────────────
# REM: JS側設定取得API（プロンプト一覧・埋め込みモデル名を返却）
@router.get("/ingest/config", response_class=JSONResponse)
def ingest_config():
    return JSONResponse({
        "prompt_keys":       list_prompt_keys(),
        "embedding_options": {k: v["model_name"] for k, v in EMBEDDING_OPTIONS.items()}
    })


# ──────────────────────────────────────────────────────────
# REM: ingest登録API（処理対象フォルダなどフォームデータを保存）
@router.post("/ingest", response_class=JSONResponse)
async def run_ingest_folder(
    input_folder:      str        = Form(...),
    include_subdirs:   bool       = Form(...),
    refine_prompt_key: str       = Form(...),
    embed_models:      List[str] = Form(...),
    overwrite_existing: bool     = Form(False),
    quality_threshold:  float    = Form(0.0),
):
    global last_ingest

    # REM: 対象拡張子フィルタ
    ok_ext  = [".txt", ".pdf", ".docx", ".csv", ".json", ".eml"]
    pattern = "**/*" if include_subdirs else "*"
    base    = os.path.abspath(input_folder)
    files   = [
        f for f in glob.glob(os.path.join(base, pattern), recursive=include_subdirs)
        if os.path.splitext(f)[1].lower() in ok_ext
    ]

    if not files:
        raise HTTPException(400, "対象ファイルが見つかりません")

    # REM: 実行パラメータをメモリに保持
    last_ingest = {
        "files":             [{"path": f, "filename": os.path.basename(f)} for f in files],
        "refine_prompt_key": refine_prompt_key,
        "embed_models":      embed_models,
        "overwrite":         overwrite_existing,
        "q_thresh":          quality_threshold,
    }
    return {"status": "started", "count": len(files), "folder": input_folder}


# ──────────────────────────────────────────────────────────
# REM: SSE ストリームAPI（/ingest/stream で進捗を逐次送信）
@router.get("/ingest/stream")
def ingest_stream(request: Request):
    if not last_ingest:
        raise HTTPException(400, "No ingest job found")

    files       = last_ingest["files"]
    overwrite_f = last_ingest["overwrite"]
    q_thresh    = last_ingest["q_thresh"]
    total       = len(files)
    abort_flag  = {"flag": False}

    # REM: クライアント切断検知タスク
    async def monitor_disconnect():
        while not abort_flag["flag"]:
            if await request.is_disconnected():
                abort_flag["flag"] = True
                break
            await asyncio.sleep(0.1)

    # REM: SSEイベント発行コルーチン
    async def event_generator():
        dc_task = asyncio.create_task(monitor_disconnect())
        try:
            # REM: 各ファイルを順次処理
            for idx, info in enumerate(files, start=1):
                if abort_flag["flag"]:
                    break
                fp, name = info["path"], info["filename"]

                # REM: ① ファイル仮登録（空コンテンツでレコード作成）
                fid = upsert_file(fp, "", 0.0, truncate_once=True)
                yield f"data: {json.dumps({'file':name,'file_id':fid,'step':'ファイル登録中','index':idx,'total':total})}\n\n"
                yield f"data: {json.dumps({'file':name,'step':'登録完了'})}\n\n"

                # REM: ② テキスト抽出（OCR＋PDF）
                yield f"data: {json.dumps({'file':name,'step':'テキスト抽出中…'})}\n\n"
                t0    = time.time()
                texts = extract_text_by_extension(fp)
                dur   = round(time.time() - t0, 2)
                yield f"data: {json.dumps({'file':name,'step':'テキスト抽出完了','duration':dur})}\n\n"
                if abort_flag["flag"] or not texts:
                    continue
                texts = list(dict.fromkeys(texts))  # REM: 重複ブロック除去

                # REM: ③ ページ単位整理
                refined_pages = []
                file_min_score = 1.0

                for pg, block in enumerate(texts, start=1):
                    if abort_flag["flag"]:
                        break

                    # REM: ページ開始通知
                    yield f"data: {json.dumps({'file':name,'step':f'Page {pg} 処理開始'})}\n\n"

                    # REM: OCR結果表示（誤記訂正＋空行圧縮）
                    import unicodedata
                    from ocr.spellcheck import correct_text
                    from llm.refiner import normalize_empty_lines
                    # ① 半角⇔全角・辞書ベース誤字訂正
                    normed = unicodedata.normalize("NFKC", block)
                    # ② 辞書ベースの誤字訂正
                    corrected_text = correct_text(normed)
                    # ③ 空白行削除＋連続空行圧縮
                    block_clean = normalize_empty_lines(corrected_text)

                    preview = block_clean.strip().replace("\n", " ")[:40]
                    yield f"data: {json.dumps({'file':name,'step':f'OCR page{pg}','preview':preview,'full_text':block_clean})}\n\n"

                    # REM: ④ プロンプト組み立て／表示
                    prompt_text = build_prompt(block_clean, last_ingest["refine_prompt_key"])
                    prev_p      = prompt_text.strip().replace("\n", " ")[:80]
                    yield f"data: {json.dumps({'file':name,'step':f'使用プロンプト page{pg}','preview':prev_p,'full_text':prompt_text})}\n\n"

                    # REM: ⑤ LLM整形実行
                    yield f"data: {json.dumps({'file':name,'step':'LLM整形中'})}\n\n"
                    t1 = time.time()
                    refined, lang, score, _ = refine_text_with_llm(
                        block_clean,
                        model=OLLAMA_MODEL,
                        force_lang=last_ingest["refine_prompt_key"],
                        abort_flag=abort_flag
                    )
                    dur2 = round(time.time() - t1, 2)

                    # ✅ デバッグ出力：reprで全文の両端を明示（hidden char可視化用）
                    print(f"[DEBUG refined Page{pg}] >>>{repr(refined)}<<<")

                    file_min_score = min(file_min_score, score)
                    refined_pages.append(refined)

                    # REM: ⑥ 整形結果表示
                    prev_r = refined.strip().replace("\n", " ")[:40]
                    yield f"data: {json.dumps({'file':name,'step':f'LLM整形結果 page{pg}','preview':prev_r,'full_text':refined,'duration':dur2})}\n\n"

                    # REM: refined が空の場合はベクトル化をスキップ
                    if not refined.strip():
                        yield f"data: {json.dumps({'file':name,'step':f'LLM結果空のためベクトル化スキップ page{pg}'})}\n\n"
                        continue

                    # REM: ⑦ ベクトル化
                    for mkey in last_ingest["embed_models"]:
                        if abort_flag["flag"]:
                            break
                        embed_and_insert(
                            texts=[refined],
                            filename=fp,
                            model_keys={mkey},
                            quality_score=score,
                            file_id=fid
                        )
                        mname = EMBEDDING_OPTIONS[mkey]["model_name"]
                        yield f"data: {json.dumps({'file':name,'step':f'ベクトル化 ({mname})'})}\n\n"

                # REM: ⑧ 全文保存判定＆更新
                if refined_pages:
                    full_text = "\n\n".join(refined_pages)
                    with DB_ENGINE.begin() as tx:
                        cur = tx.execute(
                            text("SELECT content, quality_score FROM files WHERE file_id=:id"),
                            {"id": fid}
                        ).mappings().first()
                        need_update = (
                            overwrite_f
                            or not cur["content"]
                            or (cur["quality_score"] or 0.0) < q_thresh
                            or file_min_score < (cur["quality_score"] or 1.0)
                        )
                        if need_update:
                            tx.execute(
                                text("""
                                    UPDATE files
                                       SET content       = :c,
                                           quality_score = :qs
                                     WHERE file_id       = :id
                                """),
                                {"c": full_text, "qs": file_min_score, "id": fid}
                            )
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
