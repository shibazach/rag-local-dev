# new/routes/__init__.py
# ルーター初期化ファイル

from fastapi import APIRouter

# 各ルーターをインポート
from .api import router as api_router
from .ui import router as ui_router

# ルーターをエクスポート
__all__ = ["api_router", "ui_router"] 