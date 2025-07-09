# /workspace/llm/refiner.py
# REM: LangChain による LLM 整形処理（Ollama 利用）
from langchain_core.output_parsers import StrOutputParser
from langchain.prompts import PromptTemplate
from langchain_community.chat_models import ChatOllama

from src.config import OLLAMA_BASE, OLLAMA_MODEL
from bin.llm_text_refiner import detect_language
from llm.prompt_loader import get_prompt_by_lang
from llm.scorer import score_text_quality
from ocr import correct_text

import re

# REM: 空白のみの行を空行に変換し、連続空行を最大 1 行に
def normalize_empty_lines(text: str) -> str:
    text = re.sub(r'^[\s\u3000]+$', '', text, flags=re.MULTILINE)
    return re.sub(r'\n{2,}', '\n', text)

# REM: 原文テキストを埋め込んだプロンプトを生成
def build_prompt(raw_text: str, lang: str = "ja") -> str:
    _, base_prompt = get_prompt_by_lang(lang)
    user_prompt = "次の出力は必ず日本語で行ってください。\n" + base_prompt
    if ("{TEXT}" not in user_prompt) and ("{input_text}" not in user_prompt):
        user_prompt += "\n\n【原文テキスト】\n{TEXT}"
    return (user_prompt.replace("{TEXT}", raw_text)
                       .replace("{input_text}", raw_text))

# REM: LLM による整形処理
def refine_text_with_llm(
    raw_text: str,
    model: str = OLLAMA_MODEL,
    force_lang: str | None = None,
    abort_flag: dict[str, bool] | None = None
):
    """LLM 整形本体

    * abort_flag が True になると InterruptedError を発生させ即中断
    * 戻り値: (refined_text, lang, score, prompt)
    """

    def check_abort():
        if abort_flag and abort_flag.get("flag"):
            raise InterruptedError("処理が中断されました")

    # 1) OCR 誤字補正＋空行整理
    check_abort()
    corrected = normalize_empty_lines(correct_text(raw_text))

    # 2) 言語判定（force_lang 優先）
    check_abort()
    lang = detect_language(corrected, force_lang) or "ja"

    # 3) デバッグ
    txt_len = len(corrected)
    print(f"🧠 LLM整形開始 len={txt_len}", flush=True)

    # 4) プロンプト生成
    check_abort()
    prompt = build_prompt(corrected, lang)

    # 5) 生成パラメータ
    gen_kw = {
        "max_new_tokens": 1024,
        "min_length":     max(1, int(txt_len * 0.8)),
        "temperature":    0.7,
    }

    # 6) LLM インスタンス
    check_abort()
    llm = ChatOllama(model=model, base_url=OLLAMA_BASE, **gen_kw)

    # 7) LangChain チェーン
    safe_prompt = prompt.replace("{", "{{").replace("}", "}}")
    chain = PromptTemplate.from_template(safe_prompt) | llm | StrOutputParser()

    # 8) 推論
    check_abort()
    refined = chain.invoke({})

    # 9) スコアリング
    check_abort()
    score = score_text_quality(corrected, refined, lang)

    return refined, lang, score, prompt
