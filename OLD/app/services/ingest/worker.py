# app/services/ingest/worker.py @2025-07-18 00:00 UTC +9
"""
1ファイル分のインジェスト処理本体。
StreamingResponse 側へ dict を逐次 yield し、SSE で送出してもらう。
新しい共通OCRサービスを使用。
"""

# ── 標準ライブラリ ────────────────────────────────
import functools, time, unicodedata, os
from typing import Dict, AsyncGenerator, List
import logging

# ── プロジェクト共通 ────────────────────────────────
from OLD.src.config import OLLAMA_MODEL

# ── 新しいIngest処理 ────────────────────────────────
from .processor import IngestProcessor

# ── 定数 ──────────────────────────────────────────
LOGGER = logging.getLogger("ingest_worker")

# グローバルプロセッサインスタンス
_processor = IngestProcessor()


# process_file ─ 1ファイルを処理しイベントを yield（新しいOCRサービス対応）
async def process_file(
    *,
    file_path: str,
    file_name: str,
    index: int,
    total_files: int,
    refine_prompt_key: str,
    refine_prompt_text: str = None,
    embed_models: List[str],
    overwrite_existing: bool,
    quality_threshold: float,
    llm_timeout_sec: int,
    abort_flag: Dict[str, bool],
    ocr_engine_id: str = None,      # 新規追加: OCRエンジン指定
    ocr_settings: Dict = None,      # 新規追加: OCR設定
) -> AsyncGenerator[Dict, None]:
    """新しいIngestProcessorに処理を委譲"""
    async for event in _processor.process_file(
        file_path=file_path,
        file_name=file_name,
        index=index,
        total_files=total_files,
        refine_prompt_key=refine_prompt_key,
        refine_prompt_text=refine_prompt_text,
        embed_models=embed_models,
        overwrite_existing=overwrite_existing,
        quality_threshold=quality_threshold,
        llm_timeout_sec=llm_timeout_sec,
        abort_flag=abort_flag,
        ocr_engine_id=ocr_engine_id,
        ocr_settings=ocr_settings,
    ):
        yield event