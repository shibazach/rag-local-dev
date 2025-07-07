# scripts/views/chat_main.py
# REM: 左サイドバーで履歴ペインの ON/OFF を切替し、中央ペインを広く使う
import streamlit as st

from .query_input import render_query_input
from .result_chunk import render_chunk_mode
from .result_file import render_file_mode
from .history_panel import render_history_panel

# ───────────────────────────────────────────
#  メインチャットビュー
# ───────────────────────────────────────────

def render_chat_view():
    st.title("🔍 研究部ローカルRAG")

    # REM: セッションステート初期化
    if "searching" not in st.session_state:
        st.session_state.searching = False
    if "history" not in st.session_state:
        st.session_state.history = []
    if "query_input" not in st.session_state:
        st.session_state.query_input = ""
    if "show_history" not in st.session_state:
        st.session_state.show_history = True  # 履歴ペイン表示フラグ

    # REM: サイドバーの履歴ペイン トグル
    st.sidebar.checkbox(
        "📜 履歴ペインを表示",
        key="show_history"
    )

    # REM: 列レイアウトを切替 (中央:右 = 2:1)
    if st.session_state.show_history:
        left_col, right_col = st.columns([2, 1])
    else:
        left_col = st.container()
        right_col = None

    # ─── 検索入力 & 結果 ────────────────────────
    with left_col:
        render_query_input()

        if st.session_state.searching:
            rag_mode = st.session_state.get("selected_mode", "チャンク統合")
            if rag_mode == "チャンク統合":
                render_chunk_mode()
            else:
                render_file_mode()

    # ─── 検索履歴パネル ─────────────────────────
    if st.session_state.show_history and right_col is not None:
        with right_col:
            render_history_panel()
