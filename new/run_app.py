#!/usr/bin/env python3
"""
新しいRAGシステム起動スクリプト
ユーザーがmain.pyとnew.pyを選択して起動できます
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path

def run_app(app_type: str = "new"):
    """
    RAGアプリケーションを起動
    
    Args:
        app_type: "main" または "new" (デフォルト: "new")
    """
    if app_type == "main":
        print("🚀 既存のRAG FastAPIアプリ起動中...")
        cmd = [
            "uvicorn",
            "app.main:app",
            "--host", "0.0.0.0",
            "--port", "8000",
            "--reload",
            "--log-level", "warning",
        ]
    else:
        print("🚀 新しいRAG FastAPIアプリ起動中...")
        cmd = [
            "uvicorn",
            "new.main:app",
            "--host", "0.0.0.0",
            "--port", "8000",
            "--reload",
            "--log-level", "warning",
        ]
    
    print(f"→ Running: {' '.join(cmd)}")
    subprocess.run(cmd)

def main():
    parser = argparse.ArgumentParser(description="RAGアプリケーション起動スクリプト")
    parser.add_argument(
        "--app", 
        choices=["main", "new"], 
        default="new",
        help="起動するアプリケーション (main: 既存, new: 新アーキテクチャ)"
    )
    
    args = parser.parse_args()
    run_app(args.app)

if __name__ == "__main__":
    main() 