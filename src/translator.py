# src/translator.py
from langchain_ollama import OllamaLLM

from src import bootstrap  # ← 実体は何もimportされないが、パスが通る
from src.error_handler import install_global_exception_handler

install_global_exception_handler()

def translate_to_english(japanese_text: str, model: str = "phi4-mini") -> str:
    prompt = f"""
Please translate the following Japanese business document into clear, professional English.
Preserve the structure and meaning as much as possible, including any itemized lists or field-value pairs.

--- Japanese Original ---
{japanese_text}

--- English Translation ---
""".strip()

    llm = OllamaLLM(model=model, base_url="http://172.18.0.1:11434")
    result = llm.invoke(prompt).strip()
    print("\n🌐 翻訳結果（EN）:\n" + "-" * 40)
    print(result)
    print("-" * 40 + "\n")
    return result