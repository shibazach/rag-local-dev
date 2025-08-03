"""
データベース接続・初期化
Database connection and initialization
"""

from sqlalchemy import create_engine, MetaData, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from contextlib import contextmanager
from typing import Generator

from app.config import config, logger

# SQLAlchemy設定
engine = create_engine(
    config.DATABASE_URL,
    poolclass=StaticPool,
    connect_args={"check_same_thread": False} if "sqlite" in config.DATABASE_URL else {},
    echo=config.DEBUG  # SQLログ出力（開発時のみ）
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# ベースクラス
Base = declarative_base()

def init_database():
    """データベース初期化"""
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
    with get_db_session() as db:
        # 管理者ユーザー作成チェック
        from app.core.models import User
        from app.auth.session import SessionManager
        
        admin_user = db.query(User).filter(User.username == "admin").first()
        if not admin_user:
            # 管理者ユーザー作成
            password_hash, salt = SessionManager.hash_password("admin")
            admin_user = User(
                username="admin",
                email="admin@example.com",
                password_hash=password_hash,
                password_salt=salt,
                display_name="システム管理者",
                role="admin",
                is_admin=True,
                is_active=True,
                is_verified=True
            )
            db.add(admin_user)
            db.commit()
            logger.info("👤 管理者ユーザー作成完了: admin/admin")

@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """データベースセッション取得（コンテキストマネージャー）"""
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
    FastAPI依存性注入用データベースセッション
    Dependency injection for FastAPI
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def health_check() -> dict:
    """データベースヘルスチェック"""
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

def get_database_info() -> dict:
    """データベース情報取得"""
    try:
        with get_db_session() as db:
            from app.core.models import (
                FilesBlob, FilesMeta, FilesText, 
                User, UserSession, SystemLog
            )
            
            # 各テーブルのレコード数取得
            counts = {
                "files_blob": db.query(FilesBlob).count(),
                "files_meta": db.query(FilesMeta).count(), 
                "files_text": db.query(FilesText).count(),
                "users": db.query(User).count(),
                "user_sessions": db.query(UserSession).count(),
                "system_logs": db.query(SystemLog).count()
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