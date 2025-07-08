# scripts/llm_text_refiner.py

from src.ocr_utils.spellcheck import correct_text
from scripts.refine_prompter import get_prompt_by_lang
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langdetect import detect_langs
from langchain_ollama import ChatOllama

from src import bootstrap  # パス設定のみ
from src.error_handler import install_global_exception_handler
from src.config import OLLAMA_BASE, OLLAMA_MODEL

# REM: 例外発生時のログをグローバルに記録するハンドラを有効化
install_global_exception_handler()

def detect_language(text: str, force_lang=None) -> str:
    if force_lang:
        return force_lang
    try:
        lang = detect_langs(text)[0].lang
        return "en" if lang == "en" else "ja"
    except Exception:
        return "ja"

def refine_text_with_llm(raw_text: str,
                         model: str = OLLAMA_MODEL,
                         force_lang: str = None):
    # 1) OCR誤字補正
    corrected = correct_text(raw_text)

    # 2) 言語判定／強制（ここでは日本語固定）
    lang = detect_language(corrected, force_lang)
    lang = "ja"

    # 3) デバッグ出力：文字数と推定トークン数
    text_len       = len(corrected)
    token_estimate = int(text_len * 1.6)
    print(f"🧠 LLM整形を開始（文字数: {text_len}, 推定トークン: {token_estimate}）", flush=True)
    print(f"🔤 整形言語: {lang}", flush=True)

    # 4) プロンプト取得
    _, base_prompt = get_prompt_by_lang(lang)

    # 5) 日本語回答を強制
    user_prompt = "次の出力は必ず日本語で行ってください。\n" + base_prompt

    # 6) プロンプト合成（{TEXT} と {input_text} の両方に対応）
    prompt = user_prompt.replace("{TEXT}", corrected).replace("{input_text}", corrected)
    print(f"🧾 プロンプト合成後の文字数: {len(prompt)}", flush=True)

    # 7) 生成パラメータ拡張
    generation_kwargs = {
        "max_new_tokens": 1024,
        "min_length": max(1, int(len(corrected) * 0.8)),
        "temperature": 0.7,
        # "top_p": 0.9,  # 必要なら追加
    }

    # 8) Ollama LLM インスタンス生成
    llm = ChatOllama(
        model=model,
        base_url=OLLAMA_BASE,
        **generation_kwargs
    )

    # 9) LangChain チェーン構築
    prompt_template = PromptTemplate.from_template(user_prompt)
    chain = prompt_template | llm | StrOutputParser()

    # 10) 推論実行
    refined_text = chain.invoke({"TEXT": corrected})

    # 11) 品質スコア算出
    score = score_text_quality(corrected, refined_text, lang)
    return refined_text, lang, score

def score_text_quality(original: str, refined: str, lang: str) -> float:
    import re
    from langdetect import detect_langs

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
