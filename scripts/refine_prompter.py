# scripts/refine_prompter.py

import os
import re

# このスクリプトと同じディレクトリ内の refine_prompt_multi.txt を参照
PROMPT_FILE = os.path.join(os.path.dirname(__file__), "refine_prompt_multi.txt")

if not os.path.exists(PROMPT_FILE):
    raise FileNotFoundError(f"プロンプトファイルが見つかりません: {PROMPT_FILE}")

def get_prompt_by_lang(lang="ja"):
    """
    refine_prompt_multi.txt から lang セクションのプロンプトを抽出して返す。
    戻り値: (system_prompt, user_prompt_body)
    """
    content = open(PROMPT_FILE, encoding="utf-8").read()
    for section in content.split("#lang="):
        if section.startswith(lang):
            parts = section.split("---", 1)
            body = parts[1].strip() if len(parts) > 1 else "\n".join(section.splitlines()[1:])
            return "", body
    raise ValueError(f"{lang} 用プロンプトが見つかりません: {PROMPT_FILE}")

def list_prompt_keys():
    """
    refine_prompt_multi.txt の "#lang=キー" 行を拾ってキー一覧を返す。
    """
    text = open(PROMPT_FILE, encoding="utf-8").read()
    keys = re.findall(r"^#lang=([^\s]+)", text, flags=re.MULTILINE)
    return keys
