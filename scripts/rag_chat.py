# scripts/rag_chat.py

import time
import datetime
import threading
import streamlit as st
import numpy as np
from sqlalchemy import create_engine, text
from langchain_community.embeddings import OllamaEmbeddings
from langchain_ollama import OllamaLLM
from sentence_transformers import SentenceTransformer
from io import BytesIO

from src import bootstrap
from src.embedding_config import embedding_options
from src.error_handler import install_global_exception_handler
from src.embedder import embed_and_insert

install_global_exception_handler()

# 🆕 Ollamaをスリープさせないバックグラウンドスレッド
def keep_ollama_warm():
    llm_ping = OllamaLLM(model="phi4-mini", base_url="http://172.18.0.1:11434")
    while True:
        try:
            llm_ping.invoke("ping")
            print("✅ Ollama keep-alive sent.")
        except Exception as e:
            print("⚠️ Ollama keep-alive failed:", e)
        time.sleep(600)  # 10分ごとにPing

# 🔁 起動時に開始（daemon=True なのでバックグラウンド）
threading.Thread(target=keep_ollama_warm, daemon=True).start()

st.set_page_config(page_title="ローカルRAGチャット", layout="wide")

engine = create_engine("postgresql://raguser:ragpass@pgvector-db:5432/ragdb")

if "history" not in st.session_state:
    st.session_state.history = []
if "query_input" not in st.session_state:
    st.session_state.query_input = ""

st.title("🔍 ローカルRAGチャット")

model_choices = {
    f"{v['model_name']} ({v['embedder']})": k
    for k, v in embedding_options.items()
}
selected_label = st.selectbox("使用する埋め込みモデルを選択してください：", list(model_choices.keys()))
selected_key = model_choices[selected_label]
selected_model = embedding_options[selected_key]

model_safe = selected_model["model_name"].replace("/", "_").replace("-", "_")
tablename = f"{model_safe}_{selected_model['dimension']}"

def to_pgvector_literal(vec):
    if isinstance(vec, np.ndarray):
        vec = vec.tolist()
    return "[" + ",".join(f"{float(x):.6f}" for x in vec) + "]"

def search_similar_documents(query_embedding, top_k=5):
    embedding_str = to_pgvector_literal(query_embedding)
    sql = f"""
        SELECT
          e.content   AS snippet,
          e.file_id   AS file_id,
          f.filename  AS filename,
          f.content   AS full_text,
          f.file_blob AS file_blob
        FROM "{tablename}" AS e
        JOIN files AS f
          ON e.file_id = f.file_id
        ORDER BY e.embedding <-> '{embedding_str}'::vector
        LIMIT :top_k
    """
    with engine.connect() as conn:
        result = conn.execute(text(sql), {"top_k": top_k})
        return [dict(row) for row in result]

llm = OllamaLLM(model="phi4-mini", base_url="http://172.18.0.1:11434")

left_col, right_col = st.columns([1, 1])

with left_col:
    st.markdown("#### 🔎 質問を入力して検索を実行")
    st.session_state.query_input = st.text_area("質問を入力してください:", value=st.session_state.query_input, height=100)

    if st.button("検索実行"):
        query = st.session_state.query_input.strip()
        if query:
            start_time = time.time()

            if selected_model["embedder"] == "OllamaEmbeddings":
                embedder = OllamaEmbeddings(model=selected_model["model_name"], base_url="http://172.18.0.1:11434")
                query_embedding = embedder.embed_query(query)
            else:
                embedder = SentenceTransformer(selected_model["model_name"])
                query_embedding = embedder.encode([query], convert_to_numpy=True)[0]

            docs = search_similar_documents(query_embedding)

            context = "\n\n".join(f"\U0001F4C4 **{d['filename']}**: {d['snippet']}" for d in docs)

            prompt = f"""
以下の情報を参考にして、質問に答えてください。

情報:
{context}

質問:
{query}
""".strip()

            with st.spinner("考え中..."):
                response = llm.invoke(prompt)

            elapsed_time = round(time.time() - start_time, 2)

            st.markdown(f"### \U0001F9E0 回答（{elapsed_time} 秒）")
            st.write(response)

            st.session_state.history.append({
                "query": query,
                "response": response,
                "model": selected_label,
                "time": elapsed_time
            })

            st.markdown("### \U0001F4D1 検索結果プレビュー")
            for d in docs:
                st.markdown(f"**{d['filename']}**")
                st.write(d["snippet"])
                with st.expander("▶️ 全文をプレビュー"):
                    edited_text = st.text_area("全文テキスト（編集可能）", value=d["full_text"], height=200, key=f"edit_{d['file_id']}")

                    if st.button("保存して再ベクトル化", key=f"save_{d['file_id']}"):
                        try:
                            with engine.begin() as conn:
                                conn.execute(text("UPDATE files SET content = :content WHERE file_id = :file_id"),
                                             {"content": edited_text, "file_id": d["file_id"]})
                                conn.execute(text(f'DELETE FROM "{tablename}" WHERE file_id = :file_id'),
                                             {"file_id": d["file_id"]})
                            st.success("✅ contentを更新し、旧ベクトルを削除しました")

                            embed_and_insert(texts=[edited_text], filename=d["filename"], truncate_done_tables=set())
                            st.success("✅ 再ベクトル化完了！")
                        except Exception as e:
                            st.error(f"❌ エラーが発生しました: {e}")

                    st.download_button("元ファイルをダウンロード", data=d["file_blob"], file_name=d["filename"], mime="application/octet-stream")

with right_col:
    st.markdown("### \U0001F4DC 検索履歴")
    if st.session_state.history:
        for i, item in enumerate(reversed(st.session_state.history), 1):
            with st.expander(f"{i}. 質問: {item['query']}（モデル: {item['model']}）", expanded=False):
                st.markdown(f"\U0001F9E0 回答（{item['time']} 秒）:\n\n{item['response']}")
    else:
        st.write("まだ履歴はありません。")

    st.markdown("### \U0001F4BE 履歴をファイルに保存")
    format_type = st.selectbox("保存形式を選択してください", ["txt", "rtf", "docx"])
    if st.button("📥 ダウンロード"):
        def generate_history_file(format_type="txt"):
            buffer = BytesIO()
            if format_type == "txt":
                content = ""
                for idx, h in enumerate(st.session_state.history, 1):
                    content += f"{idx}. 質問: {h['query']}\nモデル: {h['model']}\n回答（{h['time']} 秒）:\n{h['response']}\n\n"
                buffer.write(content.encode("utf-8"))
            elif format_type == "rtf":
                content = "{\\rtf1\\ansi\n"
                for idx, h in enumerate(st.session_state.history, 1):
                    content += f"\\b {idx}. 質問: {h['query']}\\b0\\line\nモデル: {h['model']}\\line\n\\i 回答（{h['time']} 秒）:\\i0\\line\n{h['response']}\\line\\line\n"
                content += "}"
                buffer.write(content.encode("utf-8"))
            else:
                from docx import Document
                from docx.shared import Pt
                doc = Document()
                for idx, h in enumerate(st.session_state.history, 1):
                    doc.add_heading(f"{idx}. 質問: {h['query']}", level=2)
                    doc.add_paragraph(f"モデル: {h['model']}")
                    p = doc.add_paragraph()
                    run = p.add_run(f"回答（{h['time']} 秒）:\n{h['response']}")
                    run.font.size = Pt(11)
                doc.save(buffer)
            buffer.seek(0)
            return buffer

        file_buffer = generate_history_file(format_type)
        mime_map = {
            "txt": "text/plain",
            "rtf": "application/rtf",
            "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        }
        today_str = datetime.date.today().strftime("%Y-%m-%d")
        st.download_button("ファイルをダウンロード", data=file_buffer, file_name=f"search_history_{today_str}.{format_type}", mime=mime_map[format_type])
