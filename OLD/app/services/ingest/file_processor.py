# app/services/ingest/file_processor.py
# Ingest処理用のファイル処理ユーティリティ

import os
import time
import unicodedata
from typing import List, Dict

from OLD.llm.refiner import normalize_empty_lines
from OLD.ocr.spellcheck import correct_text

# REM: 英語テンプレ誤反映などに該当する典型パターン（lower比較前提）
TEMPLATE_PATTERNS = [
    "certainly", "please provide", "reformat", "i will help",
    "note that this is a translation", "based on your ocr output"
]

def is_invalid_llm_output(text: str) -> bool:
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

def preprocess_pages(pages: List[str]) -> List[str]:
    """ページテキストの前処理（正規化・スペルチェック）"""
    return [
        normalize_empty_lines(correct_text(unicodedata.normalize("NFKC", p)))
        for p in pages
    ]

def run_with_timeout(func, timeout_sec: int):
    """タイムアウト付きで関数を実行"""
    import concurrent.futures
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
        future = ex.submit(func)
        try:
            return future.result(timeout=timeout_sec)
        except concurrent.futures.TimeoutError:
            raise TimeoutError