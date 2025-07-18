# REM: app/services/ingest_worker.py @2025-07-18 00:00 UTC +9
"""
1ファイル分のインジェスト処理本体。
StreamingResponse 側へ dict を逐次 yield し、SSE で送出してもらう。
"""

# REM: ── 標準ライブラリ ────────────────────────────────
import functools, time, unicodedata
from typing import Dict, Generator, List
import logging

# REM: ── プロジェクト共通 ────────────────────────────────
from src.config import OLLAMA_MODEL

# REM: ── I/O・LLM・DB ─────────────────────────────────
from fileio.extractor     import extract_text_by_extension
from fileio.file_embedder import embed_and_insert
from llm.chunker          import split_into_chunks
from llm.refiner          import (
    normalize_empty_lines,
    refine_text_with_llm,
    build_prompt,
)
from ocr.spellcheck       import correct_text
from db.handler           import (
    insert_file_full,
    update_file_text,
    update_file_status,
    get_file_text,
)

# REM: ── 定数 ──────────────────────────────────────────
TOK_LIMIT    = 8192
CHUNK_SIZE   = 500
OVERLAP_SIZE = 50
LOGGER       = logging.getLogger("ingest_worker")


# REM: process_file ─ 1ファイルを処理しイベントを yield
def process_file(
    *,
    file_path: str,
    file_name: str,
    index: int,
    total_files: int,
    refine_prompt_key: str,
    refine_prompt_text: str = None,        # REM: 追加
    embed_models: List[str],
    overwrite_existing: bool,
    quality_threshold: float,
    llm_timeout_sec: int,
    abort_flag: Dict[str, bool],
) -> Generator[Dict, None, None]:
    t0 = time.perf_counter()

    # ── ① DB 仮登録 ───────────────────────────────────
    try:
        file_id = insert_file_full(file_path, "", "", 0.0)
    except Exception as exc:
        LOGGER.exception("insert_file_full")
        yield {"file": file_name, "step": "DB登録失敗", "detail": str(exc)}
        return

    yield {
        "file": file_name,
        "file_id": file_id,
        "step": "ファイル登録完了",
        "index": index,
        "total": total_files,
    }

    # ── ② テキスト抽出 ─────────────────────────────────
    yield {"file": file_name, "step": "テキスト抽出中…"}
    try:
        pages = extract_text_by_extension(file_path)
    except Exception as exc:
        LOGGER.exception("extract_text_by_extension")
        update_file_status(file_id, status="error", note=str(exc))
        yield {"file": file_name, "step": "テキスト抽出失敗", "detail": str(exc)}
        return

    if not pages:
        update_file_status(file_id, status="error", note="no text")
        yield {"file": file_name, "step": "テキスト無し"}
        return

    yield {"file": file_name, "step": "テキスト抽出完了", "pages": len(pages)}

    # ── ③ 全文生成 → raw_text 保存 ────────────────────
    page_blocks = [
        normalize_empty_lines(correct_text(unicodedata.normalize("NFKC", p)))
        for p in pages
    ]
    full_text = "\n\n".join(page_blocks)
    update_file_text(file_id, raw_text=full_text)

    token_est = int(len(full_text) * 1.6)
    use_page  = token_est > TOK_LIMIT
    unit_iter = enumerate(page_blocks, 1) if use_page else [("all", full_text)]

    refined_pages: List[str] = []
    file_min_score: float = 1.0

    # ── ④ LLM 整形 ─────────────────────────────────────
    for pg, block in unit_iter:
        if abort_flag["flag"]:
            return

        label = f"page{pg}" if use_page else "all"
        # REM: 編集ペインのテキストがあればそれを使う
        if refine_prompt_text:
            prompt_text = refine_prompt_text
        else:
            prompt_text = build_prompt(block, refine_prompt_key)

        # プロンプト見出し（全文用）
        yield {"file": file_name, "step": f"使用プロンプト全文 part:{label}"}
        # プロンプト全文
        yield {
            "file":    file_name,
            "step":    "prompt_text",
            "part":    label,
            "content": prompt_text,
        }

        # 進行中メッセージ（※廃止しない）
        yield {"file": file_name, "step": f"LLM整形中 part:{label}"}

        job = functools.partial(
            refine_text_with_llm,
            block,
            model=OLLAMA_MODEL,
            force_lang=refine_prompt_key,
            abort_flag=abort_flag,
        )
        try:
            refined, _, score, _ = job() if not llm_timeout_sec else \
                _run_with_timeout(job, llm_timeout_sec)
        except TimeoutError:
            update_file_status(file_id, status="error", note="llm timeout")
            yield {"file": file_name, "step": "LLMタイムアウト", "part": label}
            return
        except Exception as exc:
            LOGGER.exception("LLM refine")
            update_file_status(file_id, status="error", note=str(exc))
            yield {"file": file_name, "step": "LLM整形失敗", "detail": str(exc)}
            return

        refined_pages.append(refined)
        file_min_score = min(file_min_score, score)

        # 整形結果見出し（全文）
        yield {"file": file_name, "step": f"LLM整形結果全文 part:{label}"}
        # 整形結果全文
        yield {
            "file":    file_name,
            "step":    "refined_text",
            "part":    label,
            "content": refined,
        }

    if abort_flag["flag"] or not refined_pages:
        return

    # ── ⑤ チャンク分割 ─────────────────────────────────
    final_text = "\n\n".join(refined_pages)
    chunks = split_into_chunks(final_text, chunk_size=CHUNK_SIZE, overlap=OVERLAP_SIZE)
    yield {"file": file_name, "step": f"チャンク分割完了 chunks={len(chunks)}"}

    # ── ⑥ ベクトル化 ───────────────────────────────────
    embed_job = functools.partial(
        embed_and_insert,
        texts=chunks,
        file_name=file_path,
        model_keys=embed_models,
        quality_score=file_min_score,
        file_id=file_id,
    )
    try:
        embed_job()
        yield {"file": file_name, "step": "ベクトル化完了"}
    except Exception as exc:
        LOGGER.exception("embed_and_insert")
        update_file_status(file_id, status="error", note=str(exc))
        yield {"file": file_name, "step": "ベクトル化失敗", "detail": str(exc)}
        return

    # ── ⑦ refined_text 保存 ────────────────────────────
    cur = get_file_text(file_id) or {}
    need_upd = (
        overwrite_existing or not cur.get("refined_text") or
        (cur.get("quality_score") or 0.0) < quality_threshold or
        file_min_score < (cur.get("quality_score") or 1.0)
    )
    if need_upd:
        update_file_text(file_id, refined_text=final_text, quality_score=file_min_score)
        yield {"file": file_name, "step": "全文保存完了（上書き実施）"}
    else:
        yield {"file": file_name, "step": "全文保存スキップ"}

    update_file_status(file_id, status="done")
    yield {
        "file": file_name,
        "step": "file_done",
        "elapsed": round(time.perf_counter() - t0, 2),
    }


# ── _run_with_timeout ──────────────────────────────────────
def _run_with_timeout(func, timeout_sec: int):
    import concurrent.futures
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
        future = ex.submit(func)
        try:
            return future.result(timeout=timeout_sec)
        except concurrent.futures.TimeoutError:
            raise TimeoutError
