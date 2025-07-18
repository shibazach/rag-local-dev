# app/routes/__init__.py  2025-07-11 13:00 JST
from fastapi import APIRouter

# 各ルーターを import
from .ui import router as ui_router
from .ingest import router as ingest_router
from .query import router as query_router
from .file import router as file_router
from .file_browser import router as file_browser_router

# ひとつにまとめる
router = APIRouter()
router.include_router(ui_router,       prefix="", tags=["UI"])
router.include_router(ingest_router,   prefix="", tags=["Ingest"])
router.include_router(query_router,    prefix="", tags=["Query"])
router.include_router(file_router,     prefix="", tags=["File"])
router.include_router(file_browser_router, prefix="", tags=["File Browser"])
