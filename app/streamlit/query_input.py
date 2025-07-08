# app/streamlit/query_input.py
import streamlit as st
from src.config import EMBEDDING_OPTIONS

# REM: モード選択と埋め込みモデル選択 UI を描画
def render_query_input():
    rag_mode = st.radio(
        "検索モードを選択：", ("チャンク統合", "ファイル別（要約+一致度）"), horizontal=True, key="selected_mode"
    )

    model_choices = {
        f"{v['model_name']} ({v['embedder']})": k for k, v in EMBEDDING_OPTIONS.items()
    }
    selected_label = st.selectbox(
        "使用する埋め込みモデルを選択してください：", list(model_choices.keys()), key="model_label"
    )
    selected_key = model_choices[selected_label]
    st.session_state["selected_model_key"] = selected_key
    selected_model = EMBEDDING_OPTIONS[selected_key]
    model_safe = selected_model["model_name"].replace("/", "_").replace("-", "_")
    st.session_state["embedding_tablename"] = f"{model_safe}_{selected_model['dimension']}"

    st.session_state.query_input = st.text_area(
        "質問を入力してください:", value=st.session_state.query_input, height=100
    )

    run_search = st.button("検索実行", key="run_search", disabled=st.session_state.searching)
    cancel_search = st.button("キャンセル", key="cancel_search", disabled=not st.session_state.searching)

    if run_search:
        st.session_state.searching = True
    if cancel_search:
        st.session_state.searching = False
