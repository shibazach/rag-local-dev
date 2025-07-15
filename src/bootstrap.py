# src/bootstrap.py（更新日時: 2025-07-15 18:20 JST）
import os, sys
from db.handler import reset_dev_database  

# REM: プロジェクトルートを sys.path に追加（2階層上）
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

# REM: DBのTruncate処理
reset_dev_database()
