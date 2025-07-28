# llm/prompt_loader.py  # REM: 最終更新 2025-07-10 22:50 JST
"""
refine_prompt_multi.txt の #lang= セクションを切り出し、
LLM へ渡すテンプレート文字列を取得するモジュール
"""

# REM: 標準ライブラリ
import os
from typing import List

# REM: 設定
from src.config import PROMPT_FILE_PATH

# REM: チャット用プロンプトファイルのパス
CHAT_PROMPT_FILE = os.path.join(os.path.dirname(__file__), "prompts", "chat_prompts.txt")

# REM: プロンプトファイル存在チェック
if not os.path.exists(PROMPT_FILE_PATH):
    raise FileNotFoundError(f"プロンプトファイルが見つかりません: {PROMPT_FILE_PATH}")


def get_prompt_by_lang(lang: str = "ja") -> str:
    """
    refine_prompt_multi.txt から "#lang=lang" セクションを抽出し、
    次の "#lang=" またはファイル末尾までの範囲を
    ・先頭の "lang:" 行
    ・行頭が "#" のコメント行
    を除去して返却する。
    """
    content = open(PROMPT_FILE_PATH, encoding="utf-8").read()
    marker  = f"#lang={lang}"
    start   = content.find(marker)
    if start < 0:
        raise ValueError(f"{lang} 用プロンプトが見つかりません: {PROMPT_FILE_PATH}")
    # マーカー直後から次の #lang= までを抜き出し
    sub     = content[start + len(marker):]
    end     = sub.find("#lang=")
    section = sub if end < 0 else sub[:end]

    # 行ごとにフィルタリング
    lines = section.splitlines()
    cleaned = []
    for ln in lines:
        # 空行はそのまま１行だけ残す
        if not ln.strip():
            if not cleaned or cleaned[-1].strip():
                cleaned.append("")
            continue
        # # で始まるコメント行はスキップ
        if ln.lstrip().startswith("#"):
            continue
        # "ja:" や "en:" ラベルだけの行はスキップ
        if ln.strip().lower() == f"{lang}:":
            continue
        cleaned.append(ln)
    # 重複する先頭空行を削除
    while cleaned and not cleaned[0].strip():
        cleaned.pop(0)
    # 重複する末尾空行を削除
    while cleaned and not cleaned[-1].strip():
        cleaned.pop()

    return "\n".join(cleaned)


def list_prompt_keys() -> List[str]:
    """
    refine_prompt_multi.txt 内の "#lang=キー" を抽出して
    利用可能な言語キー一覧を返却する。
    """
    keys: List[str] = []
    with open(PROMPT_FILE_PATH, encoding="utf-8") as f:
        for line in f:
            if line.startswith("#lang="):
                keys.append(line[len("#lang="):].strip())
    return keys


def get_chat_prompt(section: str) -> str:
    """
    chat_prompts.txt から指定セクションのプロンプトを取得する。
    セクションは <section_name>...</section_name> 形式で定義される。
    """
    if not os.path.exists(CHAT_PROMPT_FILE):
        return ""
    
    with open(CHAT_PROMPT_FILE, encoding="utf-8") as f:
        content = f.read()
    
    # <section>...</section> 形式のセクションを抽出
    import re
    pattern = f"<{section}>(.*?)</{section}>"
    match = re.search(pattern, content, re.DOTALL)
    
    if match:
        return match.group(1).strip()
    else:
        return ""


def list_chat_prompt_keys() -> List[str]:
    """
    chat_prompts.txt 内の利用可能なセクション名一覧を返却する。
    """
    if not os.path.exists(CHAT_PROMPT_FILE):
        return []
    
    with open(CHAT_PROMPT_FILE, encoding="utf-8") as f:
        content = f.read()
    
    # <section_name> タグを抽出
    import re
    sections = re.findall(r'<(\w+)>', content)
    return list(set(sections))  # 重複を除去
