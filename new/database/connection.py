# new/database/connection.py
# データベース接続管理

import asyncio
from typing import Generator
from sqlalchemy import text
from sqlalchemy.engine import Connection
from sqlalchemy.exc import SQLAlchemyError

from new.config import DB_ENGINE, DEBUG_MODE

def get_db_connection() -> Generator[Connection, None, None]:
    """
    データベース接続を取得する（コンテキストマネージャー）
    
    Yields:
        Connection: SQLAlchemy接続オブジェクト
    """
    connection = None
    try:
        connection = DB_ENGINE.connect()
        yield connection
    except SQLAlchemyError as e:
        if DEBUG_MODE:
            print(f"[database] Connection error: {e}")
        if connection:
            connection.rollback()
        raise
    finally:
        if connection:
            connection.close()


def test_connection() -> bool:
    """
    データベース接続をテストする
    
    Returns:
        bool: 接続成功時True、失敗時False
    """
    try:
        connection = DB_ENGINE.connect()
        result = connection.execute(text("SELECT 1"))
        row = result.fetchone()
        success = row is not None and row[0] == 1
        connection.close()
        
        if DEBUG_MODE:
            print(f"[database] Connection test: {'SUCCESS' if success else 'FAILED'}")
        
        return success
        
    except Exception as e:
        if DEBUG_MODE:
            print(f"[database] Connection test failed: {e}")
        return False


async def test_connection_async() -> bool:
    """
    非同期でデータベース接続をテストする
    
    Returns:
        bool: 接続成功時True、失敗時False
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, test_connection)


def get_database_info() -> dict:
    """
    データベースの基本情報を取得する
    
    Returns:
        dict: データベース情報
    """
    try:
        connection = DB_ENGINE.connect()
        
        # PostgreSQLバージョン取得
        version_result = connection.execute(text("SELECT version()"))
        version = version_result.fetchone()[0]
        
        # pgvector拡張の確認
        pgvector_result = connection.execute(
            text("SELECT 1 FROM pg_extension WHERE extname = 'vector'")
        )
        has_pgvector = pgvector_result.fetchone() is not None
        
        # データベース名取得
        db_result = connection.execute(text("SELECT current_database()"))
        database_name = db_result.fetchone()[0]
        
        connection.close()
        
        return {
            "version": version,
            "database_name": database_name,
            "has_pgvector": has_pgvector,
            "connection_status": "healthy"
        }
        
    except Exception as e:
        return {
            "version": None,
            "database_name": None,
            "has_pgvector": False,
            "connection_status": f"error: {str(e)}"
        }