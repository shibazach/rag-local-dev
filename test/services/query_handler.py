# test/services/query_handler.py
from src.config import (EMBEDDING_OPTIONS, DB_ENGINE)
from src.config import (LLM_ENGINE, OLLAMA_BASE)
from langchain_community.embeddings import OllamaEmbeddings
from sentence_transformers import SentenceTransformer
from sqlalchemy import text
import numpy as np
import re

def to_pgvector_literal(vec):
    if isinstance(vec, np.ndarray):
        vec = vec.tolist()
    return "[" + ",".join(f"{float(x):.6f}" for x in vec) + "]"

def handle_query(query: str, model_key: str, mode: str = "チャンク統合"):
    selected_model = EMBEDDING_OPTIONS[model_key]
    tablename = f"{selected_model['model_name'].replace('/', '_').replace('-', '_')}_{selected_model['dimension']}"

    if selected_model["embedder"] == "OllamaEmbeddings":
        embedder = OllamaEmbeddings(model=selected_model["model_name"], base_url=OLLAMA_BASE)
        query_embedding = embedder.embed_query(query)
    else:
        embedder = SentenceTransformer(selected_model["model_name"])
        query_embedding = embedder.encode([query], convert_to_numpy=True)[0]

    embedding_str = to_pgvector_literal(query_embedding)

    if mode == "チャンク統合":
        sql = f"""
            SELECT e.content AS snippet,
                   f.filename
            FROM "{tablename}" AS e
            JOIN files AS f ON e.file_id = f.file_id
            ORDER BY e.embedding <-> '{embedding_str}'::vector
            LIMIT 5
        """
        with DB_ENGINE.connect() as conn:
            rows = conn.execute(text(sql)).mappings().all()
        return {"mode": mode, "results": [dict(r) for r in rows]}

    else:
        sql = f"""
            SELECT DISTINCT f.file_id, f.filename, f.content, f.file_blob,
                   MIN(e.embedding <-> '{embedding_str}'::vector) AS distance
            FROM "{tablename}" AS e
            JOIN files AS f ON e.file_id = f.file_id
            GROUP BY f.file_id, f.filename, f.content, f.file_blob
            ORDER BY distance ASC
            LIMIT 10
        """
        with DB_ENGINE.connect() as conn:
            rows = conn.execute(text(sql)).mappings().all()

        summaries = []
        for row in rows:
            summary, score = llm_summarize_with_score(query, row["content"])
            summaries.append({
                "filename": row["filename"],
                "file_id": row["file_id"],
                "score": score,
                "summary": summary
            })
        summaries.sort(key=lambda x: x["score"], reverse=True)
        return {"mode": mode, "results": summaries}

def llm_summarize_with_score(query, content):
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
