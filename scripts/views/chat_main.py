# scripts/views/chat_main.py
from .query_input import render_query_input
from .result_chunk import render_chunk_mode
from .result_file import render_file_mode
from .history_panel import render_history_panel
import streamlit as st

def render_chat_view():
    st.title("🔍 ローカルRAGチャット")

    if "searching" not in st.session_state:
        st.session_state.searching = False
    if "history" not in st.session_state:
        st.session_state.history = []
    if "query_input" not in st.session_state:
        st.session_state.query_input = ""

    left_col, right_col = st.columns([1, 1])

    with left_col:
        render_query_input()

        if st.session_state.searching:
            rag_mode = st.session_state.get("selected_mode", "チャンク統合")
            if rag_mode == "チャンク統合":
                render_chunk_mode()
            else:
                render_file_mode()

    with right_col:
        render_history_panel()
