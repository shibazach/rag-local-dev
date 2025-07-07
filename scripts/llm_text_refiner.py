# scripts/llm_text_refiner.py
# REM: =============================================================================
# REM: OCR / PDF 抽出テキストを「詳細かつ重複のない日本語」に再整形するユーティリティ
# REM:
# REM:     ① OCR 誤字補正（spellcheck）
# REM:     ② PDF 行と OCR 行のマージ（正規化 + 類似度 0.85 以上で OCR 行を排除）
# REM:     ③ プロンプト生成
# REM:           - プレースホルダ置換 {TEXT}/{input_text}/{{OCR_TEXT}}
# REM:           - 置換タグが無いテンプレにも本文を自動注入
# REM:           - 【PDF抽出】【OCR抽出】 ラベル強制削除
# REM:           - テンプレに必須ルールが欠けていれば自動補完
# REM:     ④ Ollama LLM 呼び出し
# REM:           - phi4-mini / gemma どちらでも効く `num_predict`
# REM:           - 本文長 × LLM_LENGTH_RATE（config.py）で短文防止
# REM:     ⑤ ポストフィルタ
# REM:           - 直近 10 行以内に同一行があれば除去（ループ出力対策）
# REM:     ⑥ Quality スコア算出（既存ロジック）
# REM:
# REM: ※ 日本語強制・重複禁止など“欠けたら壊滅的”なルールは MANDATORY_RULES で二重ガード
# REM: =============================================================================

from __future__ import annotations

import re
import unicodedata
from difflib import SequenceMatcher
from typing import List, Tuple

from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langdetect import detect_langs
from langchain_ollama import ChatOllama

from src.ocr_utils.spellcheck import correct_text                        # ①
from scripts.refine_prompter import get_prompt_by_lang                   # テンプレ取得
from src.error_handler import install_global_exception_handler
from src.config import OLLAMA_BASE, OLLAMA_MODEL, LLM_LENGTH_RATE        # 長さ倍率

# REM: 例外発生時はフルスタックトレースを logs/ へ保存
install_global_exception_handler()

# REM --------------------------------------------------------------------
# REM 0. このモジュール内で絶対欠けさせたくないプロンプトルール
# REM --------------------------------------------------------------------
MANDATORY_RULES = [
    "必ず日本語で",
    "同一行・同一段落が複数回現れる場合は、最初の 1 回だけ",
]

# REM --------------------------------------------------------------------
# REM 1. 言語判定ユーティリティ（失敗時は ja）
# REM --------------------------------------------------------------------
def detect_language(text: str) -> str:
    try:
        return "en" if detect_langs(text)[0].lang == "en" else "ja"
    except Exception:
        return "ja"

# REM --------------------------------------------------------------------
# REM 2. PDF + OCR 行マージ（正規化＋類似度 0.85）
# REM --------------------------------------------------------------------
def _norm(s: str) -> str:
    """全角→半角・大文字→小文字・NFKC正規化"""
    return unicodedata.normalize("NFKC", s).lower()

def merge_pdf_ocr(pdf_lines: List[str], ocr_lines: List[str]) -> str:
    """
    PDF 抽出行と OCR 抽出行をマージする。
    類似度 0.85 以上の行は OCR 側を捨て、残りを「OCR 補完セクション」へ。
    """
    merged: List[str] = []
    for pl in pdf_lines:
        if any(SequenceMatcher(None, _norm(pl), _norm(ol)).ratio() > 0.85 for ol in ocr_lines):
            continue
        merged.append(pl)

    merged.append("\n--- OCR 補完セクション ---\n")
    merged.extend(ocr_lines)
    return "\n".join(merged)

# REM --------------------------------------------------------------------
# REM 3. プロンプト生成（タグ置換 + ラベル除去 + 必須ルール検証）
# REM --------------------------------------------------------------------
def build_prompt(text: str, lang: str = "ja") -> str:
    """
    1) 言語別テンプレ取得
    2) プレースホルダ置換
    3) タグが無ければ本文自動挿入
    4) 【PDF抽出】【OCR抽出】強制削除
    5) MANDATORY_RULES が欠けていれば冒頭に補完
    """
    _, template = get_prompt_by_lang(lang)

    prompt = (template
              .replace("{{OCR_TEXT}}", text)
              .replace("{TEXT}", text)
              .replace("{input_text}", text))

    # タグが無いテンプレ用の穴埋め
    if text not in prompt:
        marker = r"(【再構成された本文】\s*\n)"
        prompt = re.sub(marker, r"\1" + text + "\n\n", prompt, 1) if re.search(marker, prompt) \
                 else prompt + "\n\n--- OCR Text ---\n" + text

    # ラベル除去
    prompt = prompt.replace("【PDF抽出】", "").replace("【OCR抽出】", "")

    # MANDATORY_RULES を検証・補完
    missing = [rule for rule in MANDATORY_RULES if rule not in prompt]
    if missing:
        prompt = "\n".join(missing) + "\n" + prompt

    return prompt

# REM --------------------------------------------------------------------
# REM 4. LLM 呼び出し               ★本文長×倍率で詳細化＆短文防止
# REM --------------------------------------------------------------------
def refine_text_with_llm(
    raw_text: str,
    model: str = OLLAMA_MODEL,
) -> Tuple[str, str, float | None]:
    """
    ① OCR 誤字補正
    ② プロンプト生成
    ③ Ollama (phi4-mini / gemma) 推論
    ④ Quality Score
    """
    # ①
    corrected = correct_text(raw_text)

    # ②
    prompt_full = build_prompt(corrected, "ja")

    # ③
    gen_kw = {
        "num_predict": int(len(corrected) * LLM_LENGTH_RATE),  # 本文長×倍率で長さ保証
        "temperature": 0.7,
        "top_p": 0.9,
    }
    llm = ChatOllama(model=model, base_url=OLLAMA_BASE, **gen_kw)
    refined = llm.invoke(prompt_full).content.strip()

    # ---------- ポストフィルタ：直近10行デデュープ ----------
    deduped: List[str] = []
    for line in refined.splitlines():
        if line and line not in deduped[-10:]:
            deduped.append(line)
    refined = "\n".join(deduped)

    # ④ Quality
    score = score_text_quality(corrected, refined, "ja")
    return refined, "ja", score

# REM --------------------------------------------------------------------
# REM 5. Quality スコア（既存）
# REM --------------------------------------------------------------------
def score_text_quality(original: str, refined: str, lang: str) -> float:
    """圧縮率・句読点率・英語混入率で簡易スコア"""
    import re

    def l(s: str) -> int: return len(s.strip())
    orig_len, ref_len = l(original), l(refined)
    compression = ref_len / orig_len if orig_len else 1.0

    lines = [ln for ln in refined.splitlines() if ln.strip()]
    punct_rate = len([ln for ln in lines if re.search(r"[。．！!？?]$", ln)]) / max(1, len(lines))

    try:
        en_ratio = next((p.prob for p in detect_langs(refined) if p.lang == "en"), 0.0)
    except Exception:
        en_ratio = 0.0

    score = 1.0
    if compression < 0.8: score -= 0.2
    if punct_rate < 0.3:  score -= 0.2
    if lang == "ja" and en_ratio > 0.4: score -= 0.2
    return round(max(score, 0.0), 3)
