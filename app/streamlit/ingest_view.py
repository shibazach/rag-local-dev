# app/streamlit/ingest_view.py
import os, time
import streamlit as st

from src import bootstrap
from src.config import EMBEDDING_OPTIONS, INPUT_DIR, LOG_DIR

from bin.create_rag_data import extract_text_from_eml
from llm.refiner import (
    refine_text_with_llm,
    normalize_empty_lines,   # REM: 空行圧縮ユーティリティ
    build_prompt,            # REM: 原文を含むプロンプト生成
)
from fileio.file_embedder import embed_and_insert
from fileio.extractor import extract_text_by_extension

# REM: デフォルトのログディレクトリを作成
os.makedirs(LOG_DIR, exist_ok=True)


def render_ingest_view():
    st.title("\U0001F4E5 RAG データ投入・整形・ベクトル化")

    # --- サイドバー ----------------------------------------------------
    st.sidebar.markdown("### \U0001F4C2 処理対象フォルダとオプション")
    input_folder = st.sidebar.text_input("\U0001F4C1 入力フォルダ", value=INPUT_DIR)
    include_subdirs = st.sidebar.checkbox("サブフォルダも含める", value=True)

    # --- モデル選択チェック群 ------------------------------------------
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

    # --- 対象ファイル取得 ---------------------------------------------
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

    # --- すべて選択オプション or 個別選択 ------------------------------
    if st.sidebar.checkbox("📌 フォルダ内ファイルをすべて選択", value=False):
        selected_files = list(clean_to_full.values())
    else:
        selected_raw = st.sidebar.multiselect("処理対象ファイルを選択してください：", raw_list)
        selected_files = [clean_to_full[r.lstrip()] for r in selected_raw]

    # --- 処理開始ボタン ------------------------------------------------
    if st.sidebar.button("\U0001F680 処理開始", disabled=not selected_files):
        if not st.session_state.selected_models:
            st.error("❌ 少なくとも1つのモデルを選択してください")
            return

        total = len(selected_files)
        for idx, filepath in enumerate(selected_files, start=1):
            filename = os.path.basename(filepath)
            st.markdown(f"---\n#### \U0001F4C4 {idx}/{total}件目: `{filename}`")

            try:
                # REM: 拡張子ごとに抽出
                ext = os.path.splitext(filename)[1].lower()
                texts = (
                    extract_text_from_eml(filepath)
                    if ext == ".eml"
                    else extract_text_by_extension(filepath)
                )
                raw_joined = "\n".join(texts)

                # REM: 空白行正規化（スペースのみ行→空行, 連続空行→1 行）
                joined = normalize_empty_lines(raw_joined)

                st.markdown(
                    f"📝 文字数: `{len(joined)}`　🧮 トークン目安: `{int(len(joined)/2)}`"
                )
                st.text_area(
                    "抽出結果（空行正規化後）",
                    value=joined,
                    height=300,
                    key=f"extracted_{filename}",
                )

                # --- 送信プロンプトのプレビュー -------------------------
                preview_prompt = build_prompt(joined, lang="ja")
                with st.expander("▶️ LLM送信前プロンプト全文（編集不可）"):
                    st.text_area(
                        "送信プロンプト",
                        value=preview_prompt,
                        height=300,
                        key=f"pre_prompt_{filename}",
                    )

                # --- LLM整形 ------------------------------------------
                st.markdown("##### \U0001F9E0 LLM整形（日本語）")
                with st.spinner("整形中..."):
                    start = time.time()
                    # REM: 4 値返却（text, lang, score, prompt）
                    refined, lang, score, used_prompt = refine_text_with_llm(joined)
                    duration = round(time.time() - start, 2)
                    st.success(f"整形完了（{duration} 秒）")

                    st.text_area(
                        "整形後テキスト",
                        value=refined,
                        height=300,
                        key=f"refined_{filename}",
                    )

                    # --- 使用プロンプト（内部実行時） ------------------
                    st.markdown("##### \U0001F4E9 使用プロンプト（実行時）")
                    with st.expander("▶️ プロンプト全文を再確認"):
                        st.text_area(
                            "実際に送信したプロンプト",
                            value=used_prompt,
                            height=300,
                            key=f"prompt_{filename}",
                        )

                # --- ベクトル化 ----------------------------------------
                st.markdown("##### \U0001F4CA ベクトル化＆DB登録")
                with st.spinner("ベクトル化中..."):
                    chunks, embeddings = embed_and_insert(
                        [refined],
                        filepath,
                        model_keys=st.session_state.selected_models,
                        return_data=True,
                    )
                    st.success(f"{len(chunks)} チャンクを登録しました")

                # --- ログ保存 -----------------------------------------
                log_path = os.path.join(LOG_DIR, filename + ".log")
                with open(log_path, "w", encoding="utf-8") as f:
                    f.write(f"📝 整形後:\n{refined}\n\n")
                    f.write("\n=== ✂️ チャンク ===\n" + "\n".join(chunks))
                st.info(f"📦 ログ保存済: `{log_path}`")

            except Exception as e:
                st.error(f"❌ エラー: {e}")
