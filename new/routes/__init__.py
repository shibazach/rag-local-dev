# new/routes/__init__.py
# ルーター初期化ファイル

from fastapi import APIRouter

# UIルーター以外は使用しないためコメントアウト
# from .api import router as api_router      # ← 相対インポートエラーの原因
# from .ingest import router as ingest_router # ← main.pyで直接管理

# ルーターをエクスポート
__all__ = [] 