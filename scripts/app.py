# scripts/app.py

import streamlit as st
from src import bootstrap 
from scripts.views.ingest_view import render_ingest_view
from scripts.views.chat_main import render_chat_view

# REM: 例外発生時のログをグローバルに記録するハンドラを有効化
from src.error_handler import install_global_exception_handler
install_global_exception_handler()

# REM: データベーススキーマの初期化
#from src.db_schema import safe_init_schema
#safe_init_schema()

st.set_page_config(page_title="RAGポータル", layout="wide")

# 🔁 モード選択
mode = st.sidebar.radio("モードを選択:", ["整形・登録", "チャット検索"])

# 🔀 モードごとの画面切り替え
if mode == "整形・登録":
    render_ingest_view()
elif mode == "チャット検索":
    render_chat_view()
