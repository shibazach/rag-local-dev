# scripts/views/ingest_view.py
# REM: =============================================================================
# REM: Streamlit UI — PDF/OCR → LLM 整形 → ベクトル化
# REM: =============================================================================
import os
import itertools
import streamlit as st

from scripts.create_rag_data import extract_text_from_eml
from scripts.llm_text_refiner import (
    build_prompt,
    merge_pdf_ocr,
    refine_text_with_llm,
)
from src.config        import EMBEDDING_OPTIONS, INPUT_DIR
from src.file_embedder import embed_and_insert
from src.extractor     import extract_text_by_extension
from src.error_handler import install_global_exception_handler

# ▲ADDED: 文字種統一に使用（未インストール環境でも動作）
try:
    import jaconv  # type: ignore
except ModuleNotFoundError:
    jaconv = None  # フォールバック

install_global_exception_handler()

# ──────────────────────────────────────────────────────────────────────────────
#  ユーティリティ
# ──────────────────────────────────────────────────────────────────────────────
# REM: 入力ディレクトリを走査し、階層indent付きファイルリストを返す

def list_files(base: str, include_sub=True, exts=None) -> list[str]:
    exts = exts or [".txt", ".pdf", ".docx", ".csv", ".json", ".eml"]
    paths = []
    for root, _, files in os.walk(base):
        indent = " " * (root.replace(base, "").count(os.sep) * 2)
        for f in sorted(files):
            if os.path.splitext(f)[1].lower() in exts:
                rel = os.path.relpath(os.path.join(root, f), base)
                paths.append(f"{indent}{rel}")
        if not include_sub:
            break
    return paths


SPIN = itertools.cycle(["⠋","⠙","⠹","⠸","⠼","⠴","⠦","⠧","⠇","⠏"])

# ──────────────────────────────────────────────────────────────────────────────
#  コールバック（ボタン操作）
# ──────────────────────────────────────────────────────────────────────────────

def _start_process():
    """Start ボタン押下時: 実行フラグを立て再描画"""
    st.session_state.running = True
    st.session_state.cancel = False
    st.experimental_rerun()


def _cancel_process():
    """Cancel ボタン押下時: Cancel フラグを立てる"""
    st.session_state.cancel = True

# ──────────────────────────────────────────────────────────────────────────────
#  メイン表示関数
# ──────────────────────────────────────────────────────────────────────────────

def render_ingest_view():
    st.title("🪄 RAG データ投入・整形・ベクトル化")

    # 初期ステート
    st.session_state.setdefault("running", False)
    st.session_state.setdefault("cancel", False)

    # ----- サイドバー --------------------------------------------------------
    with st.sidebar:
        # 入力フォルダ
        st.markdown("### 📂 入力フォルダ")
        base_dir = st.text_input("フォルダパス", value=INPUT_DIR)
        include_sub = st.checkbox("サブフォルダも含める", value=True)

        # 埋め込みモデル
        st.markdown("### 💠 埋め込みモデル")
        all_keys = list(EMBEDDING_OPTIONS.keys())
        st.session_state.setdefault("selected_models", all_keys.copy())

        if st.button("✅ 全モデル"):
            st.session_state.selected_models = all_keys.copy()

        chosen = []
        for k in all_keys:
            label = f"{EMBEDDING_OPTIONS[k]['model_name']} ({EMBEDDING_OPTIONS[k]['embedder']})"
            if st.checkbox(label, k in st.session_state.selected_models, key=f"chk_{k}"):
                chosen.append(k)
        st.session_state.selected_models = chosen

        # ファイル選択
        file_raw = list_files(base_dir, include_sub)
        file_map = {f.lstrip(): os.path.join(base_dir, f.strip()) for f in file_raw}
        targets = (
            list(file_map.values())
            if st.checkbox("📌 全ファイル選択", False)
            else [file_map[p.lstrip()] for p in st.multiselect("処理対象：", file_raw)]
        )
        st.session_state["current_targets"] = targets  # ▲ADDED: セッションに保持

        # ボタン
        start_dis = st.session_state.running or not targets
        cancel_dis = not st.session_state.running
        col1, col2 = st.columns(2)
        col1.button("🚀 処理開始", disabled=start_dis, key="btn_start", on_click=_start_process)
        col2.button("⏹ キャンセル", disabled=cancel_dis, key="btn_cancel", on_click=_cancel_process)

    # ----- パイプライン実行 ---------------------------------------------------
    if st.session_state.running and not st.session_state.cancel:
        run_pipeline(st.session_state.current_targets)
        st.session_state.running = False
        st.experimental_rerun()

# ──────────────────────────────────────────────────────────────────────────────
#  パイプライン
# ──────────────────────────────────────────────────────────────────────────────

def run_pipeline(files: list[str]) -> None:
    total = len(files)
    bar = st.progress(0, text="準備中…")
    phase = st.empty()

    # REM: 抽出テキスト正規化 + 文字種統一
    def _normalize(txt: str) -> str:
        import re
        lines = ["" if not ln.strip() else ln.rstrip() for ln in txt.splitlines()]
        cleaned = "\n".join(lines)
        cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
        # 文字種統一（jaconv があれば使用）
        if jaconv:
            cleaned = jaconv.h2z(cleaned, kana=True, digit=False, ascii=False)  # ｶﾀｶﾅ→カタカナ
            cleaned = jaconv.z2h(cleaned, kana=False, digit=True, ascii=True)   # Ａ１→A1
        return cleaned

    for idx, path in enumerate(files, 1):
        if st.session_state.cancel:
            phase.status("キャンセルしました", state="error")
            break

        name = os.path.basename(path)
        st.markdown(f"---\n#### 📄 {idx}/{total}: `{name}`")

        # ---------- 抽出 ----------
        spinner_placeholder = st.empty()
        with spinner_placeholder.container():
            with st.spinner("OCR / PDF 抽出中…"):
                ext = os.path.splitext(path)[1].lower()
                pdf_lines = extract_text_by_extension(path)
                ocr_lines = extract_text_from_eml(path) if ext == ".eml" else []
                raw = merge_pdf_ocr(pdf_lines, ocr_lines)
                raw = _normalize(raw)
        spinner_placeholder.empty()
        st.text_area("抽出結果（マージ後）", raw, height=200)

        # ---------- プロンプト ----------
        prompt_full = build_prompt(raw)
        with st.expander("🧐 送信プロンプト全文"):
            st.text_area("プロンプト", prompt_full, height=400)

        # ---------- LLM 整形 ----------
        with st.spinner("LLM 整形中…"):
            refined, _, _ = refine_text_with_llm(raw)
        st.success("整形完了 ✅")

        # 品質情報
        lines = [l for l in refined.splitlines() if l.strip()]
        dup = 1 - len(set(lines)) / max(1, len(lines))
        st.markdown(f"行数: **{len(lines)}**　重複率: **{dup*100:.1f}%**")
        if dup > .2:
            st.warning("⚠️ 重複率が 20% を超えています。")

        st.text_area("整形後テキスト", refined, height=300)

        # ---------- ベクトル化 ----------
        phase.status(f"ベクトル化中 {next(SPIN)}", state="running")
        chunks, _ = embed_and_insert(
            [refined], path,
            model_keys=st.session_state.selected_models,
            return_data=True
        )
        st.success(f"🔗 {len(chunks)} チャンク登録完了")

        bar.progress(idx / total, f"完了 {idx}/{total}")
        phase.status("完了 ✅", state="complete")

    if not st.session_state.cancel:
        phase.status("すべて完了 🎉", state="complete")
        bar.empty()
