# src/utils.py
from src.config import DEBUG_MODE

# REM: デバッグ出力を制御するラッパー関数
def debug_print(*args, **kwargs):
    if DEBUG_MODE:
        print(*args, **kwargs)
