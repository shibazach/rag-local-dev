# llm/refiner.py

# REM: LangChainによるLLM整形処理（Ollama利用）
from langchain_core.output_parsers import StrOutputParser
from langchain.prompts import PromptTemplate
from langchain_community.chat_models import ChatOllama

from src.config import OLLAMA_BASE, OLLAMA_MODEL
from bin.llm_text_refiner import detect_language
from llm.prompt_loader import get_prompt_by_lang
from llm.scorer import score_text_quality
from ocr import correct_text

# REM: 空白のみの行を空行に変換し、連続空行を1つにまとめる
def normalize_empty_lines(text: str) -> str:
    import re
    # 空白（全角含む）のみの行を空行にする
    text = re.sub(r'^[\s\u3000]+$', '', text, flags=re.MULTILINE)
    # 連続する空行を1つにする
    text = re.sub(r'\n{2,}', '\n', text)
    return text


# REM: 原文テキストを埋め込んだプロンプトを生成
def build_prompt(raw_text: str, lang: str = "ja") -> str:
    """
    - `refine_prompt_multi.txt` 側に {TEXT} / {input_text} プレースホルダが
      存在する場合はそのまま置換
    - 存在しない場合は末尾に '【原文テキスト】\\n{TEXT}' を追加
    """
    _, base_prompt = get_prompt_by_lang(lang)
    user_prompt = "次の出力は必ず日本語で行ってください。\n" + base_prompt

    # REM: プレースホルダが無ければ末尾に追加
    if ("{TEXT}" not in user_prompt) and ("{input_text}" not in user_prompt):
        user_prompt += "\n\n【原文テキスト】\n{TEXT}"

    # REM: 2 種類とも置換しておく
    prompt_filled = (
        user_prompt.replace("{TEXT}", raw_text)
        .replace("{input_text}", raw_text)
    )
    return prompt_filled


# REM: LLMによる整形処理本体
def refine_text_with_llm(raw_text: str,
                         model: str = OLLAMA_MODEL,
                         force_lang: str = None):
    # 1) OCR誤字補正、空行正規化
    corrected = normalize_empty_lines(correct_text(raw_text))

    # 2) 言語判定／強制（ここでは日本語固定）
    lang = detect_language(corrected, force_lang)
    lang = "ja"

    # 3) デバッグ出力：文字数と推定トークン数
    text_len       = len(corrected)
    token_estimate = int(text_len * 1.6)
    print(f"🧠 LLM整形を開始（文字数: {text_len}, 推定トークン: {token_estimate}）", flush=True)
    print(f"🔤 整形言語: {lang}", flush=True)

    # 4) プロンプト生成（原文テキストを含む）
    prompt = build_prompt(corrected, lang)

    # 5) 生成パラメータ拡張
    generation_kwargs = {
        "max_new_tokens": 1024,
        "min_length": max(1, int(len(corrected) * 0.8)),
        "temperature": 0.7,
    }

    # 6) Ollama LLM インスタンス生成
    llm = ChatOllama(
        model=model,
        base_url=OLLAMA_BASE,
        **generation_kwargs
    )

    # 7) LangChain チェーン構築
    # REM: build_prompt で {TEXT} を既に置換済みなので
    #      プレースホルダ無しテンプレートとして扱う
    prompt_template = PromptTemplate.from_template(prompt)
    chain = prompt_template | llm | StrOutputParser()

    # 8) 推論実行
    refined_text = chain.invoke({})  # 追加変数なし

    # 9) 品質スコア算出
    score = score_text_quality(corrected, refined_text, lang)
    return refined_text, lang, score, prompt
