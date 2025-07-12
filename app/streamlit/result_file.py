# app/streamlit/result_file.py  最終更新 2025-07-13 18:00
# REM: ファイル別の検索結果を表示するモード

import base64
import streamlit as st
import streamlit.components.v1 as components

from langchain_community.embeddings import OllamaEmbeddings
from sentence_transformers import SentenceTransformer
from src.config import EMBEDDING_OPTIONS, OLLAMA_BASE

from db.handler import fetch_top_files
from src.utils import to_pgvector_literal
from llm.summary import llm_summarize_with_score

def render_file_mode():
    query = st.session_state.query_input.strip()
    if not query:
        return

    selected_key   = st.session_state["selected_model_key"]
    selected_model = EMBEDDING_OPTIONS[selected_key]
    tablename      = st.session_state["embedding_tablename"]

    # クエリのベクトル化
    if selected_model["embedder"] == "OllamaEmbeddings":
        embedder       = OllamaEmbeddings(model=selected_model["model_name"], base_url=OLLAMA_BASE)
        query_embedding = embedder.embed_query(query)
    else:
        embedder        = SentenceTransformer(selected_model["model_name"])
        query_embedding = embedder.encode([query], convert_to_numpy=True)[0]

    embedding_str = to_pgvector_literal(query_embedding)

    # REM: ファイル別トップK取得
    rows = fetch_top_files(embedding_str, tablename, limit=10)

    st.markdown("### 📑 ファイル別の結果（スコア順）")
    for row in rows:
        summary, score = llm_summarize_with_score(query, row["content"])
        st.markdown(f"**📄 {row['filename']}（一致度: {score:.2f}）**")

        if row['filename'].lower().endswith(".pdf"):
            b64    = base64.b64encode(row["file_blob"]).decode("utf-8")
            iframe = (
                f'<iframe src="data:application/pdf;base64,{b64}" '
                f'width="100%" height="600px" style="border:none;"></iframe>'
            )
            components.html(iframe, height=600)
            st.download_button(
                label=f"Download {row['filename']}",
                data=bytes(row["file_blob"]),
                file_name=row["filename"],
                mime="application/pdf",
                key=f"dl_{row['file_id']}"
            )
        else:
            st.write(summary)

        if st.button("✏️ 編集する", key=f"edit_{row['file_id']}"):
            st.session_state.edit_target_file_id = row["file_id"]
            st.session_state.mode               = "ファイル編集"
            st.experimental_rerun()
