# scripts/llm_text_refiner.py

from src.ocr_utils.spellcheck import correct_text
from scripts.refine_prompter import get_prompt_by_lang
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langdetect import detect_langs

from src.config import DEFAULT_LLM_MODEL
from langchain_ollama import ChatOllama

# REM: 言語判定（ja/en）
def detect_language(text: str, force_lang=None):
    if force_lang:
        return force_lang
    try:
        lang = detect_langs(text)[0].lang
        return "en" if lang == "en" else "ja"
    except Exception:
        return "ja"

# REM: LLMで整形し、言語・品質スコアも返す
def refine_text_with_llm(raw_text: str, model=DEFAULT_LLM_MODEL, force_lang=None):
    # REM: OCR誤字補正 + 言語判定
    corrected = correct_text(raw_text)
    lang = detect_language(corrected, force_lang)
    lang = "ja"  # REM: 英語整形は行わず、日本語整形に固定

    # REM: 整形対象の文字数と推定トークン数を事前に表示
    text_len = len(corrected)
    token_estimate = int(text_len * 1.6)

    # ※先頭の改行を削除し、直後に空行を入れたい場合は呼び出し側で print("") で対応
    print(f"🧠 LLM整形を開始（文字数: {text_len}, 推定トークン: {token_estimate}）", flush=True)

    # REM: 整形言語を出力（ja/en）
    print(f"🔤 整形言語: {lang}", flush=True)

    # REM: プロンプトテンプレートに必要な変数名（PromptTemplate 側と統一）
    prompt_variable = "TEXT"

    # REM: プロンプト取得と組み立て
    _, user_prompt = get_prompt_by_lang(lang)
    full_prompt = PromptTemplate.from_template(user_prompt)

    # REM: プレースホルダにテキストを埋め込み、最終プロンプト生成
    prompt = user_prompt.replace("{TEXT}", corrected).replace("{input_text}", corrected)

    # REM: プロンプト合成後の文字数を表示（モデル負荷の指標）
    print(f"🧾 プロンプト合成後の文字数: {len(prompt)}", flush=True)

    # REM: base_url を明示してOllamaと安定接続
    llm = ChatOllama(model=DEFAULT_LLM_MODEL, base_url="http://ollama:11434")

    # REM: LangChainのチェーンで整形実行
    chain = full_prompt | llm | StrOutputParser()
    refined_text = chain.invoke({prompt_variable: corrected})

    # REM: 整形品質スコアを算出して返却
    score = score_text_quality(corrected, refined_text, lang)
    return refined_text, lang, score

# REM: LLM整形結果に対する品質スコアを計算する
def score_text_quality(original: str, refined: str, lang: str) -> float:
    import re
    from langdetect import detect_langs

    def safe_len(s):
        return len(s.strip()) if s else 0

    orig_len = safe_len(original)
    ref_len = safe_len(refined)
    compression = ref_len / orig_len if orig_len > 0 else 1.0

    end_punct_rate = len(
        [line for line in refined.splitlines() if re.search(r"[。．！!？?]$", line)]
    ) / max(1, len(refined.splitlines()))

    lang_ratio = detect_langs(refined)
    en_ratio = next((r.prob for r in lang_ratio if r.lang == "en"), 0.0)

    score = 1.0
    if compression < 0.5:
        score -= 0.2
    if end_punct_rate < 0.3:
        score -= 0.2
    if lang == "ja" and en_ratio > 0.4:
        score -= 0.2

    return round(max(score, 0.0), 3)
