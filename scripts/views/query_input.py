# scripts/views/query_input.py

# REM: 検索入力 UI とデバッグパネルを描画するモジュール
import streamlit as st
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from src.config import DB_ENGINE, EMBEDDING_OPTIONS

# REM: サイドバーに埋め込みテーブルの件数を一覧表示するデバッグパネル
def render_debug_panel():
    st.sidebar.markdown("### 🐞 Embedding Tables Debug")
    for key, cfg in EMBEDDING_OPTIONS.items():
        tbl = cfg["model_name"].replace("/", "_").replace("-", "_") + f"_{cfg['dimension']}"
        try:
            with DB_ENGINE.connect() as conn:
                cnt = conn.execute(text(f'SELECT COUNT(*) FROM "{tbl}"')).scalar()
            st.sidebar.write(f"- **{key}** → `{tbl}` : {cnt} 件")
        except SQLAlchemyError as e:
            st.sidebar.write(f"- **{key}** → `{tbl}` : ❌ エラー ({e})")

# REM: 検索モード選択・モデル選択・質問入力・実行ボタンを描画
def render_query_input():
    # ── サイドバー：デバッグパネル表示 ─────────────────────────────
    render_debug_panel()

    # ── 検索モード選択 ───────────────────────────────────────────
    st.radio(
        "検索モードを選択：",
        ("チャンク統合", "ファイル別（要約+一致度）"),
        horizontal=True,
        key="selected_mode"
    )

    # ── 埋め込みモデル選択 ────────────────────────────────────────
    model_choices = {
        f"{v['model_name']} ({v['embedder']})": k
        for k, v in EMBEDDING_OPTIONS.items()
    }
    selected_label = st.selectbox(
        "使用する埋め込みモデルを選択してください：",
        list(model_choices.keys()),
        key="model_label"
    )
    selected_key = model_choices[selected_label]
    st.session_state["selected_model_key"] = selected_key

    # ── 実際に使うテーブル名を生成 ─────────────────────────────────
    sel_model_cfg = EMBEDDING_OPTIONS[selected_key]
    safe = sel_model_cfg["model_name"].replace("/", "_").replace("-", "_")
    st.session_state["embedding_tablename"] = f"{safe}_{sel_model_cfg['dimension']}"

    # ── 質問入力欄 ───────────────────────────────────────────────
    if "query_input" not in st.session_state:
        st.session_state.query_input = ""
    st.text_area(
        "質問を入力してください：",
        value=st.session_state.query_input,
        key="query_input",
        height=120
    )

    # ── 検索実行／キャンセル ボタン ──────────────────────────────
    # 初期状態の searching フラグ
    if "searching" not in st.session_state:
        st.session_state.searching = False

    col1, col2 = st.columns(2)
    with col1:
        run_search = st.button(
            "検索実行",
            key="run_search",
            disabled=st.session_state.searching
        )
    with col2:
        cancel_search = st.button(
            "キャンセル",
            key="cancel_search",
            disabled=not st.session_state.searching
        )

    # ── ボタン押下で検索フラグを切り替え ───────────────────────────
    if run_search:
        st.session_state.searching = True
    if cancel_search:
        st.session_state.searching = False
