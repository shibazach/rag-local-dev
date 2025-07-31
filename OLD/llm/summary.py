# llm/summary.py  最終更新 2025-07-12 17:50
# REM: LLM を用いた要約と一致度スコアの計算

from typing import Tuple
import re
from OLD.src.config import LLM_ENGINE

def llm_summarize_with_score(query: str, content: str) -> Tuple[str, float]:
    prompt = f"""
以下はユーザーの質問と文書の内容です。

【質問】
{query}

【文書】
{content[:3000]}

この文書が質問にどの程度一致しているか（0.0〜1.0）で評価し、次の形式で出力してください：

一致度: <score>
要約: <summary>
"""
    result = LLM_ENGINE.invoke(prompt)
    m = re.search(r"一致度[:：]\s*([0-9.]+).*?要約[:：]\s*(.+)", result, re.DOTALL)
    if m:
        return m.group(2).strip(), float(m.group(1))
    return result.strip(), 0.0
