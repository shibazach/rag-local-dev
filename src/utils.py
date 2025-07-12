# src/utils.py  最終更新 2025-07-12 17:50
#REM: 

from src.config import DEBUG_MODE
from typing import Sequence, Any
import numpy as np

# REM: デバッグ出力を制御するラッパー関数
def debug_print(*args, **kwargs):
    if DEBUG_MODE:
        print(*args, **kwargs)

# REM: ベクトルを PostgreSQL の pgvector リテラル形式に変換する関数
def to_pgvector_literal(vec: Sequence[float] | np.ndarray) -> str:
    if isinstance(vec, np.ndarray):
        vec = vec.tolist()
    return "[" + ",".join(f"{float(x):.6f}" for x in vec) + "]"