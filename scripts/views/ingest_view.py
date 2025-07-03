# scripts/views/ingest_view.py

import os
import time
import streamlit as st
from scripts.create_rag_data import extract_text_from_eml
from scripts.llm_text_refiner import refine_text_with_llm
from scripts.refine_prompter import get_prompt_by_lang
from src import bootstrap  # ← 実体は何もimportされないが、パスが通る
from src.config import EMBEDDING_OPTIONS, INPUT_DIR, LOG_DIR
from src.embedder import embed_and_insert
from src.error_handler import install_global_exception_handler
from src.extractor import extract_text_by_extension

# REM: 例外発生時のログをグローバルに記録するハンドラを有効化
install_global_exception_handler()

# REM: デフォルトのログディレクトリを作成
os.makedirs(LOG_DIR, exist_ok=True)

def render_ingest_view():
    st.title("\U0001F4E5 RAG データ投入・整形・ベクトル化")

    # --- サイドバー ---
    st.sidebar.markdown("### \U0001F4C2 処理対象フォルダとオプション")
    input_folder = st.sidebar.text_input("\U0001F4C1 入力フォルダ", value=INPUT_DIR)
    include_subdirs = st.sidebar.checkbox("サブフォルダも含める", value=True)

    # --- モデル選択チェック群 ---
    st.sidebar.markdown("### 💠 使用する埋め込みモデル")
    all_model_keys = list(EMBEDDING_OPTIONS.keys())

    if "selected_models" not in st.session_state:
        st.session_state.selected_models = all_model_keys.copy()

    if st.sidebar.button("✅ 全モデルを選択"):
        st.session_state.selected_models = all_model_keys.copy()

    selected_models = []
    for key in all_model_keys:
        label = f"{EMBEDDING_OPTIONS[key]['model_name']} ({EMBEDDING_OPTIONS[key]['embedder']})"
        if st.sidebar.checkbox(label, value=(key in st.session_state.selected_models), key=f"chk_{key}"):
            selected_models.append(key)
    st.session_state.selected_models = selected_models

    # --- 対象ファイル取得 ---
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

    raw_list = list_files_with_indent(input_folder, include_subdirs)
    clean_to_full = {f.lstrip(): os.path.join(input_folder, f.strip()) for f in raw_list}

    # --- すべて選択オプション or 個別選択 ---
    if st.sidebar.checkbox("📌 フォルダ内ファイルをすべて選択", value=False):
        selected_files = list(clean_to_full.values())
    else:
        selected_raw = st.sidebar.multiselect("処理対象ファイルを選択してください：", raw_list)
        selected_files = [clean_to_full[r] for r in selected_raw]

    # --- 処理開始ボタン ---
    if st.sidebar.button("\U0001F680 処理開始", disabled=not selected_files):
        if not st.session_state.selected_models:
            st.error("❌ 少なくとも1つのモデルを選択してください")
            return

        total = len(selected_files)
        for idx, filepath in enumerate(selected_files, start=1):
            filename = os.path.basename(filepath)
            st.markdown(f"---\n#### \U0001F4C4 {idx}/{total}件目: `{filename}`")

            try:
                ext = os.path.splitext(filename)[1].lower()
                texts = extract_text_from_eml(filepath) if ext == ".eml" else extract_text_by_extension(filepath)
                joined = "\n".join(texts)
                st.markdown(f"📝 文字数: `{len(joined)}`　🧮 トークン目安: `{int(len(joined)/2)}`")
                st.text_area("抽出結果", value=joined, height=300, key=f"extracted_{filename}")

                # --- LLM整形 ---
                st.markdown("##### \U0001F9E0 LLM整形（日本語）")
                with st.spinner("整形中..."):
                    start = time.time()
                    refined, lang, score = refine_text_with_llm(joined)
                    duration = round(time.time() - start, 2)
                    st.success(f"整形完了（{duration} 秒）")
                    st.text_area("整形後テキスト", value=refined, height=300, key=f"refined_{filename}")

                    # --- プロンプト表示 ---
                    st.markdown("##### \U0001F4E9 使用プロンプト")
                    _, prompt = get_prompt_by_lang(lang)
                    prompt = prompt.replace("{TEXT}", joined).replace("{input_text}", joined)
                    with st.expander("▶️ プロンプト全文を表示"):
                        st.text_area("プロンプト", value=prompt, height=300, key=f"prompt_{filename}")

                # --- ベクトル化 ---
                st.markdown("##### \U0001F4CA ベクトル化＆DB登録")
                with st.spinner("ベクトル化中..."):
                    chunks, embeddings = embed_and_insert([refined], filepath, model_keys=st.session_state.selected_models, return_data=True)
                    st.success(f"{len(chunks)} チャンクを登録しました")

                # --- ログ保存 ---
                log_path = os.path.join(LOG_DIR, filename + ".log")
                with open(log_path, "w", encoding="utf-8") as f:
                    f.write(f"📝 整形後:\n{refined}\n\n")
                    f.write("\n=== ✂️ チャンク ===\n" + "\n".join(chunks))
                st.info(f"📦 ログ保存済: `{log_path}`")

            except Exception as e:
                st.error(f"❌ エラー: {e}")
