# new/database/schemas.py
# データベーススキーマ初期化・管理

from sqlalchemy import text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

from .models import metadata, files_blob, files_meta, files_text
from config import DB_ENGINE, DEBUG_MODE


def init_schema(engine: Engine = DB_ENGINE) -> bool:
    """
    データベーススキーマを初期化する
    
    Args:
        engine: SQLAlchemyエンジン
        
    Returns:
        bool: 初期化成功時True、失敗時False
    """
    try:
        # pgvector拡張の確認・有効化
        _ensure_pgvector_extension(engine)
        
        # テーブル作成（存在しない場合のみ）
        metadata.create_all(engine)
        
        if DEBUG_MODE:
            print("[database] Schema initialized successfully")
        
        return True
        
    except SQLAlchemyError as e:
        if DEBUG_MODE:
            print(f"[database] Schema initialization failed: {e}")
        return False


def _ensure_pgvector_extension(engine: Engine) -> None:
    """
    pgvector拡張を有効化する（将来のベクトル検索用）
    
    Args:
        engine: SQLAlchemyエンジン
    """
    try:
        with engine.connect() as conn:
            # 拡張の存在確認
            result = conn.execute(
                text("SELECT 1 FROM pg_extension WHERE extname = 'vector'")
            )
            
            if result.fetchone() is None:
                # 拡張が存在しない場合は作成を試行
                try:
                    conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
                    conn.commit()
                    if DEBUG_MODE:
                        print("[database] pgvector extension enabled")
                except SQLAlchemyError as e:
                    if DEBUG_MODE:
                        print(f"[database] Warning: pgvector extension not available: {e}")
            else:
                if DEBUG_MODE:
                    print("[database] pgvector extension already enabled")
                    
    except SQLAlchemyError as e:
        if DEBUG_MODE:
            print(f"[database] Warning: Could not check pgvector extension: {e}")


def drop_all_tables(engine: Engine = DB_ENGINE, confirm: bool = False) -> bool:
    """
    全テーブルを削除する（開発用）
    
    Args:
        engine: SQLAlchemyエンジン
        confirm: 削除確認フラグ
        
    Returns:
        bool: 削除成功時True、失敗時False
    """
    if not confirm:
        raise ValueError("drop_all_tables requires confirm=True for safety")
    
    try:
        metadata.drop_all(engine)
        
        if DEBUG_MODE:
            print("[database] All tables dropped")
        
        return True
        
    except SQLAlchemyError as e:
        if DEBUG_MODE:
            print(f"[database] Failed to drop tables: {e}")
        return False


def get_table_info(engine: Engine = DB_ENGINE) -> dict:
    """
    テーブル情報を取得する
    
    Args:
        engine: SQLAlchemyエンジン
        
    Returns:
        dict: テーブル情報
    """
    try:
        with engine.connect() as conn:
            # テーブル一覧取得
            tables_result = conn.execute(
                text("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_type = 'BASE TABLE'
                    ORDER BY table_name
                """)
            )
            tables = [row[0] for row in tables_result.fetchall()]
            
            # 各テーブルの行数取得
            table_counts = {}
            for table in tables:
                if table.startswith('files_'):  # 関連テーブルのみ
                    try:
                        count_result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                        table_counts[table] = count_result.fetchone()[0]
                    except SQLAlchemyError:
                        table_counts[table] = "error"
            
            return {
                "tables": tables,
                "table_counts": table_counts,
                "status": "healthy"
            }
            
    except SQLAlchemyError as e:
        return {
            "tables": [],
            "table_counts": {},
            "status": f"error: {str(e)}"
        }


def reset_dev_database(engine: Engine = DB_ENGINE) -> bool:
    """
    開発用データベースリセット（全データ削除）
    
    Args:
        engine: SQLAlchemyエンジン
        
    Returns:
        bool: リセット成功時True、失敗時False
    """
    try:
        with engine.connect() as conn:
            # 外部キー制約を無効化してから削除
            conn.execute(text("SET foreign_key_checks = 0"))
            
            # データのみ削除（テーブル構造は保持）
            conn.execute(text("TRUNCATE TABLE files_text CASCADE"))
            conn.execute(text("TRUNCATE TABLE files_meta CASCADE")) 
            conn.execute(text("TRUNCATE TABLE files_blob CASCADE"))
            
            conn.commit()
            
            if DEBUG_MODE:
                print("[database] Development database reset completed")
        
        return True
        
    except SQLAlchemyError as e:
        if DEBUG_MODE:
            print(f"[database] Failed to reset database: {e}")
        return False