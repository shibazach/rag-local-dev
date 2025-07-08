# src/translator.py
from src.config import (OLLAMA_MODEL, LLM_ENGINE)
from src import bootstrap  # ← 実体は何もimportされないが、パスが通る
from src.error_handler import install_global_exception_handler

# REM: 例外発生時のログをグローバルに記録するハンドラを有効化
install_global_exception_handler()

def translate_to_english(japanese_text: str) -> str:
    prompt = f"""
Please translate the following Japanese business document into clear, professional English.
Preserve the structure and meaning as much as possible, including any itemized lists or field-value pairs.

--- Japanese Original ---
{japanese_text}

--- English Translation ---
""".strip()
    result = LLM_ENGINE.invoke(prompt).strip()
    print("\n🌐 翻訳結果（EN）:\n" + "-" * 40)
    print(result)
    print("-" * 40 + "\n")
    return result