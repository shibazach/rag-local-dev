# REM: app/services/ingest_worker.py @2025-07-18 00:00 UTC +9
"""
1ファイル分のインジェスト処理本体。
StreamingResponse 側へ dict を逐次 yield し、SSE で送出してもらう。
"""

# REM: ── 標準ライブラリ ────────────────────────────────
import functools, time, unicodedata, os
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

# REM: 英語テンプレ誤反映などに該当する典型パターン（lower比較前提）
TEMPLATE_PATTERNS = [
    "certainly", "please provide", "reformat", "i will help",
    "note that this is a translation", "based on your ocr output"
]


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
    yield {"file": file_name, "step": "テキスト抽出開始"}
    
    try:
        # ファイル拡張子を確認
        ext = os.path.splitext(file_path)[1].lower()
        
        if ext == ".pdf":
            # PDFの場合はページごとの進捗を表示
            from fileio.extractor import extract_text_from_pdf_with_progress
            pages = None
            
            for event in extract_text_from_pdf_with_progress(file_path):
                if "progress" in event:
                    # ページごとの進捗をWeb画面に表示
                    yield {"file": file_name, "step": f"テキスト抽出中: {event['progress']}"}
                elif "result" in event:
                    # 最終結果を取得
                    pages = event["result"]
                    break
        elif ext == ".eml":
            # EMLファイルの場合は専用処理
            from fileio.extractor import extract_text_from_eml
            pages = extract_text_from_eml(file_path)
            yield {"file": file_name, "step": "EMLファイル抽出中..."}
        else:
            # その他のファイル形式は従来通り
            pages = extract_text_by_extension(file_path)
            yield {"file": file_name, "step": "テキスト抽出中..."}
            
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
    # EMLファイルの場合は段落別整形処理を適用
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".eml":
        yield {"file": file_name, "step": "📧 EMLファイル段落整形モード適用"}
        
        # 引用記号の除去と段落分割
        corrected = full_text.replace(">>", "").replace("> >", "").replace("> ", "")
        paragraphs = [p.strip() for p in corrected.split("\n\n") if len(p.strip()) > 30]
        
        yield {"file": file_name, "step": f"段落分割完了: {len(paragraphs)}個の段落"}
        
        refined_parts = []
        for i, para in enumerate(paragraphs):
            if abort_flag["flag"]:
                return
                
            yield {"file": file_name, "step": f"📑 段落 {i+1}/{len(paragraphs)} を整形中..."}
            
            try:
                # 段落ごとにLLM整形
                refined, _, score, _ = refine_text_with_llm(
                    para, 
                    model=OLLAMA_MODEL,
                    force_lang=refine_prompt_key,
                    abort_flag=abort_flag
                )
                
                # 不正な整形結果をチェック
                if _is_invalid_llm_output(refined):
                    yield {"file": file_name, "step": f"⚠️ 段落 {i+1}: 不正な整形結果をスキップ"}
                    continue
                    
                refined_parts.append(refined)
                file_min_score = min(file_min_score, score)
                
                yield {"file": file_name, "step": f"✅ 段落 {i+1}/{len(paragraphs)} 整形完了"}
                
            except Exception as e:
                LOGGER.warning(f"段落 {i+1} 整形失敗: {e}")
                yield {"file": file_name, "step": f"⚠️ 段落 {i+1} 整形失敗: {e}"}
                continue
        
        if refined_parts:
            refined_pages = ["\n\n".join(refined_parts)]
            yield {"file": file_name, "step": f"EML段落整形完了: {len(refined_parts)}段落を統合"}
        else:
            yield {"file": file_name, "step": "⚠️ 有効な段落が見つかりませんでした"}
            refined_pages = [full_text]  # フォールバック
    else:
        # 通常のファイル処理
        for pg, block in unit_iter:
            if abort_flag["flag"]:
                return

            label = f"page{pg}" if use_page else "all"
            # REM: 編集ペインのテキストがあればそれを使う（{TEXT}置換のみ）
            if refine_prompt_text:
                cleaned = normalize_empty_lines(correct_text(block))
                prompt_text = refine_prompt_text.replace("{TEXT}", cleaned)
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


# ── _is_invalid_llm_output ──────────────────────────────────────
def _is_invalid_llm_output(text: str) -> bool:
    """LLM整形後の出力がテンプレ・英語・無意味などの不正内容かを判定"""
    try:
        from langdetect import detect
    except ImportError:
        # langdetectがない場合は基本チェックのみ
        if len(text.strip()) < 30:
            return True
        lower = text.lower()
        return any(p in lower for p in TEMPLATE_PATTERNS)

    if len(text.strip()) < 30:
        return True

    lower = text.lower()
    if any(p in lower for p in TEMPLATE_PATTERNS):
        return True

    try:
        if detect(text) == "en":
            return True
    except Exception:
        return True

    return False

# ── _run_with_timeout ──────────────────────────────────────
def _run_with_timeout(func, timeout_sec: int):
    import concurrent.futures
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
        future = ex.submit(func)
        try:
            return future.result(timeout=timeout_sec)
        except concurrent.futures.TimeoutError:
            raise TimeoutError
