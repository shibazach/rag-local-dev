# new/database/__init__.py
# データベース関連モジュール

from .models import *
from .connection import get_db_connection, test_connection
from .schemas import init_schema

def init_db():
    """データベース初期化関数"""
    return init_schema()

__all__ = [
    "get_db_connection",
    "test_connection", 
    "init_schema",
    "init_db",
    "files_blob",
    "files_meta", 
    "files_text",
]