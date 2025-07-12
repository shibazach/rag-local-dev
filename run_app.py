# run_app.py  最終更新 2025-07-12 15:40
# REM: RAGアプリケーションの起動スクリプト

import os
import subprocess
import argparse
from src.utils import debug_print

# REM: Streamlitアプリ起動
def run_streamlit():
    debug_print("📢 Streamlit起動中...")
    env = os.environ.copy()
    env["PYTHONPATH"] = os.getcwd()
    subprocess.run(
        ["streamlit", "run", "app/streamlit_main.py", "--server.fileWatcherType=none"],
        env=env,
        cwd=os.getcwd(),
    )

# REM: FastAPIアプリ起動
def run_fastapi():
    debug_print("🚀 FastAPI起動中...")
    subprocess.run(["uvicorn", "app.fastapi_main:app", "--reload"])

# REM: 起動モード選択
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="RAGアプリを起動")
    parser.add_argument("mode", choices=["streamlit", "fastapi"], help="起動モードを選択")
    args = parser.parse_args()

    if args.mode == "streamlit":
        run_streamlit()
    elif args.mode == "fastapi":
        run_fastapi()
