# llm/scorer.py

# REM: スコアリング用ユーティリティ
import re
from llm.utils import safe_len, detect_language_probs

# REM: 整形後テキストの品質をスコア化
import re
from llm.utils import safe_len, detect_language_probs

# REM: 整形後テキストの品質をスコア化
def score_text_quality(original: str, refined: str, lang: str) -> float:
    # 1) 長さ圧縮率
    orig_len = safe_len(original)
    ref_len = safe_len(refined)
    compression = ref_len / orig_len if orig_len > 0 else 1.0

    # 2) 句点率
    lines = [l for l in refined.splitlines() if l.strip()]
    end_punct_rate = sum(1 for l in lines if re.search(r"[。．！!？?]$", l)) / max(1, len(lines))

    # 3) 英語混入率
    detections = detect_language_probs(refined)
    en_ratio = next((d.prob for d in detections if d.lang == "en"), 0.0)

    # 4) スコア調整
    score = 1.0
    if compression < 0.8: score -= 0.2
    if end_punct_rate < 0.3: score -= 0.2
    if lang == "ja" and en_ratio > 0.4: score -= 0.2

    return round(max(score, 0.0), 3)
def score_text_quality(original: str, refined: str, lang: str) -> float:
    # 1) 長さ圧縮率
    orig_len = safe_len(original)
    ref_len = safe_len(refined)
    compression = ref_len / orig_len if orig_len > 0 else 1.0

    # 2) 句点率
    lines = [l for l in refined.splitlines() if l.strip()]
    end_punct_rate = sum(1 for l in lines if re.search(r"[。．！!？?]$", l)) / max(1, len(lines))

    # 3) 英語混入率
    detections = detect_language_probs(refined)
    en_ratio = next((d.prob for d in detections if d.lang == "en"), 0.0)

    # 4) スコア調整
    score = 1.0
    if compression < 0.8: score -= 0.2
    if end_punct_rate < 0.3: score -= 0.2
    if lang == "ja" and en_ratio > 0.4: score -= 0.2

    return round(max(score, 0.0), 3)
