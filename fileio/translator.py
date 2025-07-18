# fileio/translator.py
# REM: 日→英語翻訳モジュール
from src.config import LLM_ENGINE
from src import bootstrap
from src.utils import debug_print

# REM: ブートストラップの初期化
def translate_to_english(japanese_text: str) -> str:
    prompt = f"""
Please translate the following Japanese business document into clear, professional English.
Preserve the structure and meaning as much as possible, including any itemized lists or field-value pairs.

--- Japanese Original ---
{japanese_text}

--- English Translation ---
""".strip()
    result = LLM_ENGINE.invoke(prompt).strip()
    debug_print("\n🌐 翻訳結果（EN）:\n" + "-" * 40)
    debug_print(result)
    debug_print("-" * 40 + "\n")
    return result