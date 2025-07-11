# llm/refiner.py
"""
LLM 整形用ユーティリティモジュール
 - normalize_empty_lines: 空行圧縮
 - build_prompt: テンプレートに生テキストを埋め込む
 - refine_text_with_llm: LangChain + Ollama で整形実行
"""

# REM: 標準ライブラリ
import re
import time

# REM: LangChain／Ollama
from langchain_core.output_parsers import StrOutputParser
from langchain.prompts import PromptTemplate
from langchain_community.chat_models import ChatOllama
# REM: Ollamaエンドポイントエラー定義
from langchain_community.llms.ollama import OllamaEndpointNotFoundError

# REM: OCR／LLMユーティリティ
from ocr import correct_text
from llm.prompt_loader import get_prompt_by_lang
from llm.llm_utils import detect_language
from llm.scorer import score_text_quality

# REM: プロジェクト共通設定・ユーティリティ
from src.config import OLLAMA_BASE, OLLAMA_MODEL
from src.utils import debug_print

# REM: 空行圧縮
def normalize_empty_lines(text: str) -> str:
    """
    空白のみの行を削除し、連続空行は最大１行に圧縮する
    """
    text = re.sub(r'^[\s\u3000]+$', '', text, flags=re.MULTILINE)
    return re.sub(r'\n{3,}', '\n\n', text)


# REM: プロンプト組み立て
def build_prompt(raw_text: str, lang: str = "ja") -> str:
    """
    refine_prompt_multi.txt の #lang=lang セクション全体を取得し、
    {TEXT} を置換して返す。
    """
    template = get_prompt_by_lang(lang)
    cleaned = normalize_empty_lines(correct_text(raw_text))
    return template.replace("{TEXT}", cleaned)


# REM: LLM 整形処理
def refine_text_with_llm(
    raw_text: str,
    model: str = OLLAMA_MODEL,
    force_lang: str | None = None,
    abort_flag: dict[str, bool] | None = None
) -> tuple[str, str, float, str]:
    """
    LangChain + Ollama で raw_text を整形。
    戻り値: (refined_text, lang, quality_score, prompt_used)
    * abort_flag が True になると InterruptedError を送出して中断可能
    """
    # REM: 中断チェック
    def check_abort():
        if abort_flag and abort_flag.get("flag"):
            raise InterruptedError("処理が中断されました")

    # REM: 1) OCR 誤字補正＋空行圧縮
    check_abort()
    corrected = normalize_empty_lines(correct_text(raw_text))

    # REM: 2) 言語判定
    check_abort()
    lang = detect_language(corrected, force_lang) or "ja"
    if force_lang == "ja":
        lang = "ja"

    # REM: デバッグ出力（文字数・推定トークン数・整形言語）
    text_len = len(corrected)
    token_estimate = int(text_len * 1.6)
    debug_print(f"🧠 LLM整形を開始（文字数: {text_len}, 推定トークン: {token_estimate}）")
    debug_print(f"🔤 整形言語: {lang}")

    # REM: 3) プロンプト組み立て
    check_abort()
    prompt_text = build_prompt(raw_text, lang)

    # REM: PromptTemplate 用にエスケープ
    safe_prompt = prompt_text.replace("{", "{{").replace("}", "}}")

    # REM: 4) 生成パラメータ
    gen_kw = {
        "max_new_tokens": 1024,
        "min_length":     max(1, int(len(corrected) * 0.8)),
        "temperature":    0.7,
    }

    # REM: 5) LLM インスタンス生成
    check_abort()
    llm = ChatOllama(model=model, base_url=OLLAMA_BASE, **gen_kw)

    # REM: 6) LangChain チェーン構築
    chain = PromptTemplate.from_template(safe_prompt) | llm | StrOutputParser()

    # REM: 7) 推論実行＋debug出力（プロンプト確認＋タイマー＋空応答検知）
    check_abort()
    debug_print(f"[DEBUG invoke LLM model={model} prompt_len={len(prompt_text)}]")
    debug_print(f"[DEBUG prompt preview]\n---\n{prompt_text[:300]}...\n---")
    start_time = time.time()
    try:
        refined = chain.invoke({})
    except OllamaEndpointNotFoundError as e:
        # REM: モデル未ロード時の明示的エラー
        raise RuntimeError(
            f"Ollama モデル '{model}' が見つかりません。`ollama pull {model}` を実行してください。"
        ) from e
    elapsed = time.time() - start_time
    debug_print(f"[DEBUG invoke elapsed: {elapsed:.2f} sec]")
    if not refined.strip():
        debug_print("[WARNING] LLM returned empty response.")
        refined = "[EMPTY]"

    # REM: 8) 品質スコア算出
    check_abort()
    score = score_text_quality(corrected, refined, lang)

    # REM: 返り値に使用プロンプトも含める
    return refined, lang, score, prompt_text
