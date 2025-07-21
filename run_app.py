# run_app.py
# RAGアプリケーション（FastAPI）の起動スクリプト

import os
import subprocess
from src.utils import debug_print

def run_app():
    """FastAPIアプリを起動"""
    debug_print("🚀 RAG FastAPIアプリ起動中...")
    
    # ホスト・ポートは環境変数でもオーバーライド可
    host = os.getenv("FASTAPI_HOST", "0.0.0.0")
    port = os.getenv("FASTAPI_PORT", "8000")
    
    cmd = [
        "uvicorn",
        "app.main:app",
        "--host", host,
        "--port", port,
        "--reload",
        "--log-level", "warning",
    ]
    
    debug_print(f"→ Running: {' '.join(cmd)}")
    subprocess.run(cmd)

if __name__ == "__main__":
    run_app()
