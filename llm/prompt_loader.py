# llm/prompt_loader.py（旧refine_prompter.py）
import os, re
from src.config import PROMPT_FILE_PATH

# REM: プロンプトファイルの存在確認（なければ即エラー）
if not os.path.exists(PROMPT_FILE_PATH):
    raise FileNotFoundError(f"プロンプトファイルが見つかりません: {PROMPT_FILE_PATH}")

# REM: refine_prompt_multi.txt の内容を読み込み、言語ごとのプロンプトを取得する関数を定義
def get_prompt_by_lang(lang="ja"):
    """
    refine_prompt_multi.txt から lang セクションのプロンプトを抽出して返す。
    戻り値: (system_prompt, user_prompt_body)
    """
    content = open(PROMPT_FILE_PATH, encoding="utf-8").read()
    for section in content.split("#lang="):
        if section.startswith(lang):
            parts = section.split("---", 1)
            body = parts[1].strip() if len(parts) > 1 else "\n".join(section.splitlines()[1:])
            return "", body
    raise ValueError(f"{lang} 用プロンプトが見つかりません: {PROMPT_FILE_PATH}")

# REM: プロンプトファイルから利用可能な言語キーの一覧を取得する関数を定義
def list_prompt_keys():
    """
    refine_prompt_multi.txt の "#lang=キー" 行を拾ってキー一覧を返す。
    """
    text = open(PROMPT_FILE_PATH, encoding="utf-8").read()
    keys = re.findall(r"^#lang=([^\s]+)", text, flags=re.MULTILINE)
    return keys
