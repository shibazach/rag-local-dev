# src/bootstrap.py
import os, sys

# プロジェクトルートを sys.path に追加（2階層上）
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
