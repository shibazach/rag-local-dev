# scripts/app.py

import streamlit as st
from src import bootstrap 
from scripts.views.ingest_view import render_ingest_view
from scripts.views.chat_view import render_chat_view

from src import bootstrap  # ← 実体は何もimportされないが、パスが通る
from src.error_handler import install_global_exception_handler

# REM: 例外発生時のログをグローバルに記録するハンドラを有効化
install_global_exception_handler()

st.set_page_config(page_title="RAGポータル", layout="wide")

# 🔁 モード選択
mode = st.sidebar.radio("モードを選択:", ["整形・登録", "チャット検索"])

# 🔀 モードごとの画面切り替え
if mode == "整形・登録":
    render_ingest_view()
elif mode == "チャット検索":
    render_chat_view()
