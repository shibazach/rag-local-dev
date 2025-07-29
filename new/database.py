# new/database.py
# データベース接続とセッション管理

import logging
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base

from .config import DATABASE_URL, LOGGER

# データベースエンジン作成
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=300,
    echo=False  # SQLログを無効化
)

# セッションファクトリ作成
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ベースクラス作成
Base = declarative_base()

def get_db() -> Generator[Session, None, None]:
    """
    データベースセッションを取得するジェネレータ
    
    Yields:
        Session: データベースセッション
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        LOGGER.exception(f"データベースエラー: {e}")
        db.rollback()
        raise
    finally:
        db.close()

def init_db():
    """データベーステーブルを初期化"""
    try:
        Base.metadata.create_all(bind=engine)
        LOGGER.info("データベーステーブル初期化完了")
    except Exception as e:
        LOGGER.error(f"データベース初期化エラー: {e}")
        raise 