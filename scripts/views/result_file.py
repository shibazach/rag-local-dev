# scripts/views/result_file.py
import streamlit as st
import streamlit.components.v1 as components
import base64
from sqlalchemy import text
from src.config import (
    DB_ENGINE, EMBEDDING_OPTIONS,
    LLM_ENGINE, OLLAMA_BASE
)
from langchain_community.embeddings import OllamaEmbeddings
from sentence_transformers import SentenceTransformer
import numpy as np

# REM: pgvector用に NumPy 配列→[1.0,2.0,...] 文字列へ変換

def to_pgvector_literal(vec):
    if isinstance(vec, np.ndarray):
        vec = vec.tolist()
    return "[" + ",".join(f"{float(x):.6f}" for x in vec) + "]"

# REM: LLM で一致度スコア + 要約作成

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
    import re
    m = re.search(r"一致度[:：]\s*([0-9.]+).*?要約[:：]\s*(.+)", result, re.DOTALL)
    if m:
        return m.group(2).strip(), float(m.group(1))
    return result.strip(), 0.0

# REM: ファイル単位の検索結果を表示

def render_file_mode():
    query = st.session_state.query_input.strip()
    if not query:
        return

    selected_key = st.session_state["selected_model_key"]
    selected_model = EMBEDDING_OPTIONS[selected_key]
    tablename = st.session_state["embedding_tablename"]

    if selected_model["embedder"] == "OllamaEmbeddings":
        embedder = OllamaEmbeddings(model=selected_model["model_name"], base_url=OLLAMA_BASE)
        query_embedding = embedder.embed_query(query)
    else:
        embedder = SentenceTransformer(selected_model["model_name"])
        query_embedding = embedder.encode([query], convert_to_numpy=True)[0]

    embedding_str = to_pgvector_literal(query_embedding)
    sql = f"""
        SELECT DISTINCT
            f.file_id,
            f.filename,
            f.content,
            f.file_blob,
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
            "file_id": row["file_id"],
            "filename": row["filename"],
            "summary": summary,
            "score": score,
            "file_blob": row["file_blob"],
        })
    summaries.sort(key=lambda x: x["score"], reverse=True)

    st.markdown("### 📑 ファイル別の結果（スコア順）")
    for s in summaries:
        st.markdown(f"**📄 {s['filename']}（一致度: {s['score']:.2f}）**")
        if s['filename'].lower().endswith(".pdf"):
            # 別タブで開くためのデータURIリンク
            b64 = base64.b64encode(s["file_blob"]).decode("utf-8")
            href = f'<a href="data:application/pdf;base64,{b64}" target="_blank">📄 別タブで表示</a>'
            st.markdown(href, unsafe_allow_html=True)
            st.download_button(
                label=f"Download {s['filename']}",
                data=bytes(s["file_blob"]),
                file_name=s['filename'],
                mime="application/pdf",
                key=f"dl_{s['file_id']}"
            )
        st.write(s["summary"])

        if st.button("✏️ 編集する", key=f"edit_{s['file_id']}"):
            st.session_state.edit_target_file_id = s["file_id"]
            st.session_state.mode = "ファイル編集"
            st.experimental_rerun()
