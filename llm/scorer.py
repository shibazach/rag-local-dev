# llm/scorer.py
# REM: スコアリング用ユーティリティ

import re
from llm.llm_utils import safe_len, detect_language_probs

def score_text_quality(original: str, refined: str, lang: str) -> float:
    """
    整形後テキストの品質をスコア化し、以下の基準で減点:
    1) 文字数圧縮率が 80% 未満: -0.2
    2) 句点率が 30% 未満: -0.2
    3) 日本語中に英語混入率 > 40%: -0.2
    4) プロンプト出力中の【不明瞭箇所】セクション長比に応じたペナルティ（最大 -0.2）
    """
    # 1) 長さ圧縮率
    orig_len = safe_len(original)
    ref_len  = safe_len(refined)
    compression = ref_len / orig_len if orig_len > 0 else 1.0

    # 2) 句点率
    lines = [l for l in refined.splitlines() if l.strip()]
    end_punct_rate = sum(1 for l in lines if re.search(r"[。．！!？?]$", l)) / max(1, len(lines))

    # 3) 英語混入率
    detections = detect_language_probs(refined)
    en_ratio = next((d.prob for d in detections if d.lang == "en"), 0.0)

    # 基本スコア初期値
    score = 1.0
    if compression    < 0.8: score -= 0.2
    if end_punct_rate < 0.3: score -= 0.2
    if lang == "ja" and en_ratio > 0.4: score -= 0.2

    # 4) 不明瞭箇所ペナルティ
    #    プロンプト出力の末尾にある「【不明瞭箇所】<内容>」を抽出し、全文長に対する比率で減点
    m = re.search(r"【不明瞭箇所】\s*(.+)$", refined, flags=re.DOTALL)
    if m:
        amb_text = m.group(1).strip()
        amb_len  = safe_len(amb_text)
        amb_ratio = amb_len / max(1, ref_len)
        # 10% の不明瞭があれば -0.2、割合に応じて線形ペナルティ
        penalty = min(amb_ratio, 0.1) * 2.0
        score -= penalty

    # 下限 0.0、上限 1.0 に丸め
    return round(max(min(score, 1.0), 0.0), 3)
