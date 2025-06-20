# scripts/rag_ingest.py

import os
import time
import streamlit as st
from src import bootstrap
from src.extractor import extract_text_by_extension
from src.embedder import embed_and_insert
from scripts.llm_text_refiner import refine_text_with_llm
from scripts.refine_prompter import get_prompt_by_lang
from sqlalchemy import create_engine
from scripts.create_rag_data import extract_text_from_eml
from langchain.text_splitter import RecursiveCharacterTextSplitter  # ✅ 追加

engine = create_engine("postgresql://raguser:ragpass@pgvector-db:5432/ragdb")

DEFAULT_INPUT_DIR = "src/input_pdfs"
DEFAULT_LOG_DIR = "logs/full_logs"
os.makedirs(DEFAULT_LOG_DIR, exist_ok=True)

# 📂 再帰的にファイルリストを取得（インデント付き表示用）
def list_files_with_indent(base_dir, include_subdirs=True, exts=None):
    exts = exts or [".txt", ".pdf", ".docx", ".csv", ".json", ".eml"]
    file_list = []
    for root, _, files in os.walk(base_dir):
        depth = root.replace(base_dir, "").count(os.sep)
        indent = " " * (depth * 2)
        for f in sorted(files):
            if os.path.splitext(f)[1].lower() in exts:
                rel_path = os.path.relpath(os.path.join(root, f), base_dir)
                file_list.append(f"{indent}{rel_path}")
        if not include_subdirs:
            break
    return file_list

st.set_page_config(page_title="RAG データ投入・整形・ベクトル化", layout="wide")
st.title("📥 RAG データ投入・整形・ベクトル化")

# サイドバー
st.sidebar.markdown("### 📂 処理対象フォルダとオプション")
input_folder = st.sidebar.text_input("📁 入力フォルダ", value=DEFAULT_INPUT_DIR)
include_subdirs = st.sidebar.checkbox("サブフォルダも含める", value=True)

# ファイルリスト取得
if os.path.isdir(input_folder):
    raw_list = list_files_with_indent(input_folder, include_subdirs)
    clean_to_full = {f.lstrip(): os.path.join(input_folder, f.strip()) for f in raw_list}
    selected_raw = st.sidebar.multiselect("処理対象ファイルを選択してください：", raw_list)
    selected_files = [clean_to_full[r] for r in selected_raw]
else:
    st.sidebar.error("❌ 入力フォルダが存在しません")
    selected_files = []

# 処理開始
if st.sidebar.button("🚀 処理開始", disabled=not selected_files):
    total = len(selected_files)
    for idx, filepath in enumerate(selected_files, start=1):
        filename = os.path.basename(filepath)
        st.markdown(f"---\n#### 📄 {idx}/{total}件目: `{filename}`")

        try:
            ext = os.path.splitext(filename)[1].lower()
            texts = extract_text_from_eml(filepath) if ext == ".eml" else extract_text_by_extension(filepath)
            joined = "\n".join(texts)

            num_chars = len(joined)
            num_tokens = int(len(joined) / 2)
            st.markdown(f"📝 文字数: `{num_chars}`　🧮 トークン目安: `{num_tokens}`")
            st.text_area("抽出結果", value=joined, height=300, key=f"extracted_{filename}")

            # 🔹 LLM整形
            st.markdown("##### 🧠 LLM整形（日本語）")
            with st.spinner("整形中..."):
                start = time.time()
                refined, lang, score = refine_text_with_llm(joined)
                duration = round(time.time() - start, 2)
                st.success(f"整形完了（{duration} 秒）")
                st.text_area("整形後テキスト", value=refined, height=300, key=f"refined_{filename}")

                # 🔹 プロンプト表示
                st.markdown("##### 📩 使用プロンプト")
                _, prompt = get_prompt_by_lang(lang)
                prompt = prompt.replace("{TEXT}", joined).replace("{input_text}", joined)
                with st.expander("▶️ プロンプト全文を表示"):
                    st.text_area("プロンプト", value=prompt, height=300, key=f"prompt_{filename}")

            # ✅ チャンク分割（ここが今回の修正ポイント）
            splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
            refined_chunks = splitter.split_text(refined)

            # 🔹 ベクトル化
            st.markdown("##### 📊 ベクトル化＆DB登録")
            with st.spinner("ベクトル化中..."):
                chunks, embeddings = embed_and_insert(refined_chunks, filepath, return_data=True, quality_score=score)
                st.success(f"{len(chunks)} チャンクを登録しました")

            # 🔹 ログ保存
            log_path = os.path.join(DEFAULT_LOG_DIR, filename + ".log")
            with open(log_path, "w", encoding="utf-8") as f:
                f.write(f"📝 整形後:\n{refined}\n\n")
                f.write("\n=== ✂️ チャンク ===\n" + "\n".join(chunks))
            st.info(f"📦 ログ保存済: `{log_path}`")

        except Exception as e:
            st.error(f"❌ エラー: {e}")
