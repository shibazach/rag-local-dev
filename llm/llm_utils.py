# llm/utils.py

from langdetect import detect_langs

# REM: 言語判定（ja/en）
def detect_language(text: str, force_lang: str = None) -> str:
    """
    テキストの言語を判定し、"ja"または"en"を返す。
    force_langが指定されていればそれを優先。
    """
    if force_lang:
        return force_lang
    try:
        lang = detect_langs(text)[0].lang
        return "en" if lang == "en" else "ja"
    except Exception:
        return "ja"

# REM: 言語判定の確率リスト取得（スコアリング用）
def detect_language_probs(text: str):
    """
    langdetect.detect_langsの結果を返却。エラー時は空リスト。
    """
    try:
        return detect_langs(text)
    except Exception:
        return []

# REM: 安全な文字列長取得（前後空白除去後の長さ）
def safe_len(s: str) -> int:
    """
    文字列の前後空白を除去後の長さを返す。
    Noneまたは空の場合は0。
    """
    return len(s.strip()) if s and s.strip() else 0
