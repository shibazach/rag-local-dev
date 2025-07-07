# scripts/views/result_chunk.py
import streamlit as st
import base64
import streamlit.components.v1 as components
import uuid
import numpy as np
from collections import defaultdict
from src.file_embedder import embed_and_insert
from src.config import DB_ENGINE, OLLAMA_BASE, EMBEDDING_OPTIONS
from sqlalchemy import text
from langchain_community.embeddings import OllamaEmbeddings
from sentence_transformers import SentenceTransformer

# REM: NumPy → pgvector 文字列

def to_pgvector_literal(vec):
    if isinstance(vec, np.ndarray):
        vec = vec.tolist()
    return "[" + ",".join(f"{float(x):.6f}" for x in vec) + "]"

# REM: ファイルIDとファイル名から一意キー生成（Streamlitキー衝突防止）

def make_unique_key(file_id, filename):
    safe = filename.replace(".", "_").replace(" ", "_")
    return f"{file_id}_{safe}_{uuid.uuid4().hex[:6]}"

# REM: 類似チャンク検索

def search_similar_documents(query_embedding, tablename, top_k=5):
    embedding_str = to_pgvector_literal(query_embedding)
    sql = f"""
        SELECT e.content AS snippet,
               e.file_id,
               f.filename,
               f.content AS full_text,
               f.file_blob
        FROM "{tablename}" AS e
        JOIN files AS f ON e.file_id = f.file_id
        ORDER BY e.embedding <-> '{embedding_str}'::vector
        LIMIT :top_k
    """
    with DB_ENGINE.connect() as conn:
        result = conn.execute(text(sql), {"top_k": top_k})
        return result.mappings().all()

# REM: チャンク統合モードの描画

def render_chunk_mode():
    query = st.session_state.query_input.strip()
    if not query:
        return

    selected_key = st.session_state["selected_model_key"]
    selected_model = EMBEDDING_OPTIONS[selected_key]
    tablename = st.session_state["embedding_tablename"]

    # --- クエリ埋め込み ---
    if selected_model["embedder"] == "OllamaEmbeddings":
        embedder = OllamaEmbeddings(model=selected_model["model_name"], base_url=OLLAMA_BASE)
        query_embedding = embedder.embed_query(query)
    else:
        embedder = SentenceTransformer(selected_model["model_name"])
        query_embedding = embedder.encode([query], convert_to_numpy=True)[0]

    docs = search_similar_documents(query_embedding, tablename)
    file_list = sorted({d["filename"] for d in docs})
    st.markdown("**対象ファイル**: " + ", ".join(file_list))

    # --- ファイル単位でグループ化 ---
    docs_by_file = defaultdict(list)
    for d in docs:
        docs_by_file[(d["file_id"], d["filename"])].append(d)

    st.markdown("### 🔍 検索結果プレビュー")
    for (file_id, filename), group in docs_by_file.items():
        st.markdown(f"**📄 {filename}**")
        for d in group:
            st.write(f"- {d['snippet']}")
        with st.expander("▶️ 全文をプレビュー"):
            unique_key = make_unique_key(file_id, filename)
            # --- PDF プレビューは別タブリンクに変更 ---
            if filename.lower().endswith(".pdf"):
                b64 = base64.b64encode(group[0]["file_blob"]).decode("utf-8")
                data_url = f"data:application/pdf;base64,{b64}"
                st.markdown(f"[📄 別タブで表示]({data_url})", unsafe_allow_html=True)

            # --- 編集用テキストエリア ---
            edited_text = st.text_area(
                "全文テキスト（編集可能）",
                value=group[0]["full_text"],
                height=200,
                key=f"edit_{unique_key}"
            )
            if st.button("保存して再ベクトル化", key=f"save_{unique_key}"):
                try:
                    with DB_ENGINE.begin() as conn:
                        conn.execute(
                            text("UPDATE files SET content = :content WHERE file_id = :file_id"),
                            {"content": edited_text, "file_id": file_id}
                        )
                        conn.execute(
                            text(f'DELETE FROM "{tablename}" WHERE file_id = :file_id'),
                            {"file_id": file_id}
                        )
                    st.success("✅ contentを更新し、旧ベクトルを削除しました")
                    embed_and_insert(
                        texts=[edited_text], filename=filename,
                        truncate_done_tables=set()
                    )
                    st.success("✅ 再ベクトル化完了！")
                except Exception as e:
                    st.error(f"❌ エラーが発生しました: {e}")

            # --- ダウンロード ---
            st.download_button(
                label="元ファイルをダウンロード",
                data=bytes(group[0]["file_blob"]),
                file_name=filename,
                mime="application/pdf",
                key=f"download_{unique_key}"
            )
