"""
データベース接続・初期化 - Prototype統合版
SQLAlchemy + 非同期対応統合
"""

from sqlalchemy import create_engine, MetaData, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, AsyncEngine
from sqlalchemy.orm import sessionmaker as async_sessionmaker
from sqlalchemy.pool import StaticPool, NullPool
from contextlib import contextmanager, asynccontextmanager
from typing import Generator, AsyncGenerator

from app.config import config, logger

# 同期エンジン（マイグレーション・初期化用）
engine = create_engine(
    config.DATABASE_URL,
    pool_pre_ping=True,  # 接続の健全性チェック
    pool_size=10,        # コネクションプール数
    max_overflow=20,     # 最大オーバーフロー数
    echo=config.DEBUG    # SQLログ出力（開発時のみ）
)

# 非同期エンジン（将来の実装用）
# 現在は同期接続を使用し、安定性と検証性を重視
# 将来的に非同期が必要になった場合はコメントアウトを解除
"""
async_database_url = config.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
async_engine = create_async_engine(
    async_database_url,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    echo=config.DEBUG
)
"""
async_engine = None  # 一時的にNoneに設定

# セッションファクトリー
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# 非同期セッション（将来の実装用）
"""
AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False
)
"""
AsyncSessionLocal = None  # 一時的にNoneに設定

# ベースクラス
Base = declarative_base()

def init_database():
    """データベース初期化（同期版）"""
    try:
        # テーブル作成
        Base.metadata.create_all(bind=engine)
        logger.info("✅ データベース初期化完了")
        
        # 初期データ作成
        create_initial_data()
        
    except Exception as e:
        logger.error(f"❌ データベース初期化エラー: {e}")
        raise

def create_initial_data():
    """初期データ作成"""
    # 現在は初期データなし
    # Files3兄弟は実際のファイルアップロード時に作成される
    logger.info("✅ 初期データ作成完了（現在は初期データなし）")

@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """データベースセッション取得（同期版コンテキストマネージャー）"""
    session = SessionLocal()
    try:
        yield session
    except Exception as e:
        session.rollback()
        logger.error(f"データベースセッションエラー: {e}")
        raise
    finally:
        session.close()

def get_db() -> Generator[Session, None, None]:
    """
    FastAPI依存性注入用データベースセッション（同期版）
    Dependency injection for FastAPI
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 非同期データベース関数（将来の実装用）
# 現在は同期版を使用
"""
@asynccontextmanager
async def get_async_db_session() -> AsyncGenerator[AsyncSession, None]:
    '''データベースセッション取得（非同期版コンテキストマネージャー）'''
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error(f"非同期データベースセッションエラー: {e}")
            raise
        finally:
            await session.close()

async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    '''
    FastAPI依存性注入用データベースセッション（非同期版）
    Async dependency injection for FastAPI
    '''
    async with AsyncSessionLocal() as db:
        try:
            yield db
        finally:
            await db.close()
"""

def health_check() -> dict:
    """データベースヘルスチェック（同期版）"""
    try:
        with get_db_session() as db:
            # 簡単なクエリ実行
            result = db.execute(text("SELECT 1")).scalar()
            return {
                "status": "healthy",
                "database": "connected",
                "query_result": result
            }
    except Exception as e:
        return {
            "status": "unhealthy", 
            "database": "disconnected",
            "error": str(e)
        }

# 非同期ヘルスチェック（将来の実装用）
"""
async def async_health_check() -> dict:
    '''データベースヘルスチェック（非同期版）'''
    try:
        async with get_async_db_session() as db:
            # 簡単なクエリ実行
            result = await db.execute(text("SELECT 1"))
            scalar_result = result.scalar()
            return {
                "status": "healthy",
                "database": "connected",
                "query_result": scalar_result
            }
    except Exception as e:
        return {
            "status": "unhealthy", 
            "database": "disconnected",
            "error": str(e)
        }
"""

def get_database_info() -> dict:
    """データベース情報取得"""
    try:
        with get_db_session() as db:
            from app.core.models import (
                FilesBlob, FilesMeta, FilesText, 
                FileEmbedding, FilesImage
            )
            
            # 各テーブルのレコード数取得
            counts = {
                "files_blob": db.query(FilesBlob).count(),
                "files_meta": db.query(FilesMeta).count(), 
                "files_text": db.query(FilesText).count(),
                "embeddings": db.query(FileEmbedding).count(),
                "files_image": db.query(FilesImage).count()
            }
            
            return {
                "status": "connected",
                "database_url": config.DATABASE_URL.split("://")[0] + "://***",
                "table_counts": counts,
                "engine_info": {
                    "driver": engine.driver,
                    "pool_size": engine.pool.size() if hasattr(engine.pool, 'size') else "N/A"
                }
            }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }

# エイリアス
db_health_check = health_check
# async_db_health_check = async_health_check  # 非同期版は将来実装