# run_app.py
# RAGアプリケーション（FastAPI）の起動スクリプト

import os
import subprocess
import argparse
from OLD.src.utils import debug_print

def run_app(app_type: str = "old"):
    """
    RAGアプリケーションを起動
    
    Args:
        app_type: "old" または "new" (デフォルト: "old")
    """
    if app_type == "old":
        debug_print("🚀 既存のRAG FastAPIアプリ起動中...")
        cmd = [
            "uvicorn",
            "OLD.app.main:app",
            "--host", "0.0.0.0",
            "--port", "8002",
            "--reload",
            "--log-level", "warning",
        ]
    else:
        debug_print("🚀 新しいRAG FastAPIアプリ起動中...")
        cmd = [
            "uvicorn",
            "new.main:app",
            "--host", "0.0.0.0",
            "--port", "8000",
            "--reload",
            "--log-level", "warning",
        ]
    
    debug_print(f"→ Running: {' '.join(cmd)}")
    subprocess.run(cmd)

def main():
    parser = argparse.ArgumentParser(description="RAGアプリケーション起動スクリプト")
    parser.add_argument(
        "--app", 
        choices=["old", "new"], 
        default="old",
        help="起動するアプリケーション (old: 既存, new: 新アーキテクチャ)"
    )
    
    args = parser.parse_args()
    run_app(args.app)

if __name__ == "__main__":
    main()
