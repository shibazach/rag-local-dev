# scripts/refine_prompter.py

import os

# REM: refine_prompt_multi.txt から言語別プロンプトを抽出
def get_prompt_by_lang(lang="ja"):
    base_dir = os.path.dirname(__file__)
    path = os.path.join(base_dir, "refine_prompt_multi.txt")
    if not os.path.exists(path):
        raise FileNotFoundError(f"プロンプトが見つかりません: {path}")

    with open(path, encoding="utf-8") as f:
        content = f.read()

    for section in content.split("#lang="):
        if section.startswith(lang):
            body = section.split("---", 1)[1].strip()
            return "", body  # system_promptは現時点で未使用（空）

    raise ValueError(f"{lang} 用のプロンプトが見つかりません")
