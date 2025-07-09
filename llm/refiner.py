# llm/refiner.py

from langchain_core.output_parsers import StrOutputParser
from langchain.prompts import PromptTemplate
from langchain_community.chat_models import ChatOllama

from src.config import OLLAMA_BASE, OLLAMA_MODEL
from llm.utils import detect_language, detect_language_probs  # utils に統合済み
from llm.prompt_loader import get_prompt_by_lang
from llm.scorer import score_text_quality
from ocr import correct_text

# REM: 空白のみの行を空行に変換し、連続空行を1つにまとめる
def normalize_empty_lines(text: str) -> str:
    import re
    text = re.sub(r'^[\s\u3000]+$', '', text, flags=re.MULTILINE)
    text = re.sub(r'\n{2,}', '\n', text)
    return text

# REM: 原文テキストを埋め込んだプロンプトを生成（日本語/英語対応）
def build_prompt(raw_text: str, lang: str = "ja") -> str:
    """
    - 指定言語のテンプレートを取得
    - 日本語は「次の出力は必ず日本語で…」を先頭に付与
    - プレースホルダ {TEXT}/{input_text} で置換
    - 置換対象がなければ末尾に【原文テキスト】セクションを追加
    """
    _, base_prompt = get_prompt_by_lang(lang)
    # prefix は日本語のみ
    prefix = "次の出力は必ず日本語で行ってください。\n" if lang == "ja" else ""
    user_prompt = prefix + base_prompt

    # プレースホルダが無ければ末尾追加
    if ("{TEXT}" not in user_prompt) and ("{input_text}" not in user_prompt):
        user_prompt += "\n\n【原文テキスト】\n{TEXT}"

    # 実テキストを埋め込む
    prompt_filled = (
        user_prompt.replace("{TEXT}", raw_text)
                   .replace("{input_text}", raw_text)
    )
    return prompt_filled

# REM: LLMによる整形処理本体（言語柔軟化対応）
def refine_text_with_llm(raw_text: str,
                         model: str = OLLAMA_MODEL,
                         force_lang: str = None):
    # 1) OCR誤字補正＋空行正規化
    corrected = normalize_empty_lines(correct_text(raw_text))

    # 2) 生テキストの言語確率を取得
    probs = detect_language_probs(corrected)
    detected_lang = probs[0].lang if probs else "ja"
    en_prob = next((p.prob for p in probs if p.lang == "en"), 0.0)

    # 3) force_lang があれば基本はそれを使うが、
    #    force_lang == "ja" でも英語率が高ければ英語に切り替え
    if force_lang:
        lang = force_lang
        if force_lang == "ja" and detected_lang == "en" and en_prob > 0.7:
            lang = "en"
    else:
        lang = detected_lang

    # 4) デバッグ出力
    text_len = len(corrected)
    token_est = int(text_len * 1.6)
    print(f"🧠 LLM整形開始 (文字数: {text_len}, トークン推定: {token_est})", flush=True)
    print(f"🔤 使用言語: {lang}", flush=True)

    # 5) プロンプト生成
    prompt = build_prompt(corrected, lang)

    # 6) 生成パラメータ
    generation_kwargs = {
        "max_new_tokens": 1024,
        "min_length": max(1, int(text_len * 0.8)),
        "temperature": 0.7,
    }

    # 7) Ollama LLM インスタンス
    llm = ChatOllama(model=model, base_url=OLLAMA_BASE, **generation_kwargs)

    # 8) 中括弧エスケープ & チェーン構築
    safe_prompt = prompt.replace("{", "{{").replace("}", "}}")
    prompt_template = PromptTemplate.from_template(safe_prompt)
    chain = prompt_template | llm | StrOutputParser()

    # 9) 推論実行
    refined_text = chain.invoke({})

    # 10) 品質スコア算出
    score = score_text_quality(corrected, refined_text, lang)
    return refined_text, lang, score, prompt
