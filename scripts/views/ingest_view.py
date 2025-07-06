# scripts/views/ingest_view.py
# =======================================================
# REM: ファイル投入  → OCR/抽出 → LLM整形 → ベクトル化ビュー
#       - Streamlit で GUI 操作
#       - texts=[refined_text] だけを embed する
# =======================================================

import os, time, glob, uuid
import streamlit as st

from src.extractor import extract_text_by_extension
from scripts.llm_text_refiner import refine_text_with_llm
from scripts.refine_prompter import get_prompt_by_lang
from src.config import EMBEDDING_OPTIONS, INPUT_DIR, LOG_DIR
from src.file_embedder import embed_and_insert
from src.error_handler import install_global_exception_handler

# REM: 例外ハンドラ
install_global_exception_handler()
os.makedirs(LOG_DIR, exist_ok=True)  # デフォルトログフォルダ

# ---------- EMl 専用抽出（簡易版） ----------
def extract_text_from_eml(path: str) -> list[str]:
    from email import policy
    from email.parser import BytesParser
    with open(path, "rb") as f:
        msg = BytesParser(policy=policy.default).parse(f)
    parts = []
    if msg.is_multipart():
        for p in msg.walk():
            if p.get_content_type() == "text/plain":
                parts.append(p.get_content())
    else:
        parts.append(msg.get_content())
    return parts

# ---------- メインビュー ----------
def render_ingest_view():
    st.title("📂 ファイル整形＆ベクトル登録")

    # --- サイドバー（入力パス）
    st.sidebar.markdown("### 📁 入力フォルダ")
    base_dir = st.sidebar.text_input("フォルダパス", INPUT_DIR)
    include_sub = st.sidebar.checkbox("サブフォルダも含める", True)

    # --- モデル選択
    st.sidebar.markdown("### 💠 埋め込みモデル")
    all_keys = list(EMBEDDING_OPTIONS.keys())
    if "selected_models" not in st.session_state:
        st.session_state.selected_models = all_keys.copy()
    if st.sidebar.button("✅ 全選択"):
        st.session_state.selected_models = all_keys.copy()
    sel = []
    for k in all_keys:
        label = f"{EMBEDDING_OPTIONS[k]['model_name']} ({EMBEDDING_OPTIONS[k]['embedder']})"
        if st.sidebar.checkbox(label, k in st.session_state.selected_models, key=f"chk_{k}"):
            sel.append(k)
    st.session_state.selected_models = sel

    # --- ファイル一覧
    def list_files(base, exts=(".txt",".pdf",".docx",".csv",".json",".eml")):
        out=[]
        for root,_,files in os.walk(base):
            depth = root.replace(base, "").count(os.sep)
            indent= "  "*depth
            for f in sorted(files):
                if os.path.splitext(f)[1].lower() in exts:
                    rel = os.path.relpath(os.path.join(root,f), base)
                    out.append(f"{indent}{rel}")
            if not include_sub: break
        return out

    raw = list_files(base_dir)
    map_clean = {r.lstrip(): os.path.join(base_dir, r.strip()) for r in raw}

    if st.sidebar.checkbox("📌 すべて選択"):
        target_files = list(map_clean.values())
    else:
        picked = st.sidebar.multiselect("処理対象を選択", raw)
        target_files = [map_clean[p.lstrip()] for p in picked]

    # --- 実行ボタン ---
    if st.sidebar.button("🚀 処理開始", disabled=not target_files):
        if not sel:
            st.error("❌ モデルを選択してください"); return

        total=len(target_files)
        for idx, path in enumerate(target_files,1):
            name = os.path.basename(path)
            st.markdown(f"---\n### {idx}/{total}: `{name}`")

            # 1. 抽出
            ext = os.path.splitext(name)[1].lower()
            text_list = extract_text_from_eml(path) if ext==".eml" else extract_text_by_extension(path)
            raw_text  = "\n".join(text_list)
            st.write(f"📝 文字数: {len(raw_text)}")
            st.text_area("抽出結果", raw_text, height=200, key=f"raw_{uuid.uuid4()}")

            # 2. LLM 整形
            st.write("#### 🧠 LLM 整形")
            start=time.time()
            refined, lang, score = refine_text_with_llm(raw_text)
            st.success(f"✅ 整形完了 ({round(time.time()-start,2)}s, score={score:.2f})")
            st.text_area("整形後", refined, height=200, key=f"ref_{uuid.uuid4()}")

            # プロンプト表示
            _, prompt = get_prompt_by_lang(lang)
            prompt = prompt.replace("{TEXT}",raw_text).replace("{input_text}",raw_text)
            with st.expander("▶️ 使用プロンプト全文"):
                st.text_area("prompt", prompt, height=200, key=f"p_{uuid.uuid4()}")

            # 3. ベクトル登録
            st.write("#### 📥 ベクトル化")
            chunks, _ = embed_and_insert([refined], path,
                                         model_keys=sel,
                                         return_data=True,
                                         ocr_raw_text=raw_text)
            st.success(f"{len(chunks)} チャンク登録済み")

            # 4. 簡易ログ
            log_path = os.path.join(LOG_DIR, name+".log")
            with open(log_path,"w",encoding="utf-8") as f:
                f.write(refined)
            st.info(f"📁 ログ保存: {log_path}")
