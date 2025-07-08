# llm/scorer.py
# REM: LLM整形後のテキスト品質をスコアリングする関数を定義

import re
from bin.llm_text_refiner import detect_langs

# REM: 整形前後の比較、句読点率、混入言語などからスコアを算出
def score_text_quality(original: str, refined: str, lang: str) -> float:
    def safe_len(s: str) -> int:
        return len(s.strip()) if s else 0

    orig_len = safe_len(original)
    ref_len  = safe_len(refined)
    compression = ref_len / orig_len if orig_len > 0 else 1.0

    # 句点で終わる行の比率
    lines = [line for line in refined.splitlines() if line.strip()]
    end_punct_rate = len([l for l in lines if re.search(r"[。．！!？?]$", l)]) / max(1, len(lines))

    # 英語混入の比率
    lang_ratio = detect_langs(refined)
    en_ratio = next((r.prob for r in lang_ratio if r.lang == "en"), 0.0)

    score = 1.0
    if compression < 0.8:
        score -= 0.2
    if end_punct_rate < 0.3:
        score -= 0.2
    if lang == "ja" and en_ratio > 0.4:
        score -= 0.2

    return round(max(score, 0.0), 3)
