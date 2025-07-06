# REM: ファイル別モードの検索 → 要約＋一致度表示
# scripts/views/result_file.py
import streamlit as st
import streamlit.components.v1 as components
import base64
import numpy as np
import time  # REM: 時間計測用
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from src.config import DB_ENGINE, EMBEDDING_OPTIONS, LLM_ENGINE
from langchain_community.embeddings import OllamaEmbeddings
from sentence_transformers import SentenceTransformer

# REM: numpy配列→pgvectorリテラル
def to_pgvector_literal(vec):
    if isinstance(vec, np.ndarray):
        vec = vec.tolist()
    return "[" + ",".join(f"{float(x):.6f}" for x in vec) + "]"

# REM: LLM による要約＋一致度スコア取得
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
""".strip()
    return_data = LLM_ENGINE.invoke(prompt)
    import re
    m = re.search(r"一致度[:：]\s*([0-9.]+).*?要約[:：]\s*(.+)", return_data, re.DOTALL)
    if m:
        return m.group(2).strip(), float(m.group(1))
    return return_data.strip(), 0.0

# REM: ファイル別モードのレンダリング
def render_file_mode():
    # --- セッションステート初期化 ---
    if "history" not in st.session_state:
        st.session_state.history = []
    # --- 質問取得 ---
    query = st.session_state.query_input.strip()
    if not query:
        return

    # --- モデル・テーブル名取得 ---
    selected_key = st.session_state["selected_model_key"]
    selected_model = EMBEDDING_OPTIONS[selected_key]
    tablename = st.session_state["embedding_tablename"]

    # --- デバッグ: テーブル件数とクエリ表示 ---
    try:
        with DB_ENGINE.connect() as conn:
            cnt = conn.execute(text(f'SELECT COUNT(*) FROM "{tablename}"')).scalar()
        st.write(f"🔍 DEBUG — テーブル {tablename} の総レコード数: {cnt} 件")
        st.write(f"🔍 DEBUG — 検索クエリ: “{query}”")
    except SQLAlchemyError as e:
        st.error(f"❌ テーブル件数取得エラー: {e}")
        st.session_state.searching = False
        return

    # --- クエリ埋め込み＆レコード取得 ---
    start_ts = time.time()
    try:
        if selected_model["embedder"] == "OllamaEmbeddings":
            embedder = OllamaEmbeddings(
                model=selected_model["model_name"],
                base_url=selected_model.get("base_url")
            )
            query_embedding = embedder.embed_query(query)
        else:
            embedder = SentenceTransformer(selected_model["model_name"])
            query_embedding = embedder.encode([query], convert_to_numpy=True)[0]

        embedding_str = to_pgvector_literal(query_embedding)

        sql = f"""
            SELECT
                f.file_id,
                f.filename,
                c.refined_text   AS content,
                c.ocr_raw_text,
                c.quality_score,
                b.file_blob,
                MIN(e.embedding <-> '{embedding_str}'::vector) AS distance
            FROM "{tablename}" AS e
            JOIN file_contents AS c ON e.file_id = c.file_id
            JOIN files         AS f ON e.file_id = f.file_id
            JOIN file_blobs    AS b ON e.file_id = b.file_id
            GROUP BY f.file_id, f.filename, c.refined_text, c.ocr_raw_text, c.quality_score, b.file_blob
            ORDER BY distance ASC
            LIMIT 10
        """
        with DB_ENGINE.connect() as conn:
            rows = conn.execute(text(sql)).mappings().all()
    except SQLAlchemyError as e:
        st.error(f"❌ 検索実行時エラー: {e}")
        st.session_state.searching = False
        return

    # --- ゼロ件ハンドリング ---
    if not rows:
        st.warning("⚠️ 該当ファイルが見つかりませんでした。")
        st.session_state.searching = False
        return

    # --- LLM 要約＋スコアリング ---
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

    # --- 表示 ---
    st.markdown("### 📑 ファイル別の結果（スコア順）")
    for s in summaries:
        st.markdown(f"**📄 {s['filename']}（一致度: {s['score']:.2f}）**")
        if s['filename'].lower().endswith(".pdf"):
            b64 = base64.b64encode(s["file_blob"]).decode("utf-8")
            iframe = (
                f'<iframe src="data:application/pdf;base64,{b64}" '
                'width="100%" height="600px" style="border:none;"></iframe>'
            )
            components.html(iframe, height=600)
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

    # --- 履歴登録＆フラグリセット ---
    elapsed = round(time.time() - start_ts, 2)
    response_text = "\n".join(s["summary"] for s in summaries)
    st.session_state.history.append({
        "query": query,
        "response": response_text,
        "model": selected_key,
        "time": elapsed
    })
    st.session_state.searching = False
