#!/usr/bin/env python3
"""
テーブル再作成スクリプト
Files4兄弟テーブルを正しい名前で再作成
"""
import logging
from sqlalchemy import text, inspect
from app.core.database import engine
from app.core.models import Base, FilesBlob, FilesMeta, FilesText, FileEmbedding, FilesImage

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def recreate_tables():
    """Files4兄弟テーブルを再作成"""
    
    # 既存のテーブルを確認
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()
    logger.info(f"既存のテーブル: {existing_tables}")
    
    with engine.begin() as conn:
        # 旧テーブル名を新テーブル名にリネーム（可能な場合）
        if 'file_images' in existing_tables and 'files_image' not in existing_tables:
            logger.info("file_images を files_image にリネーム")
            conn.execute(text("ALTER TABLE file_images RENAME TO files_image"))
            
        # その他不要なテーブルを削除
        tables_to_drop = ['users', 'user_sessions', 'system_logs', 'system_metrics']
        for table in tables_to_drop:
            if table in existing_tables:
                logger.info(f"{table} テーブルを削除")
                conn.execute(text(f"DROP TABLE IF EXISTS {table} CASCADE"))
    
    # テーブルが存在しない場合は作成
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()
    
    # Files4兄弟 + Embeddingテーブルのみ作成
    for table_class in [FilesBlob, FilesMeta, FilesText, FileEmbedding, FilesImage]:
        table_name = table_class.__tablename__
        if table_name not in existing_tables:
            logger.info(f"{table_name} テーブルを作成")
            table_class.__table__.create(engine)
    
    logger.info("✅ テーブル再作成完了")
    
    # 最終的なテーブル一覧を表示
    inspector = inspect(engine)
    final_tables = inspector.get_table_names()
    logger.info(f"最終的なテーブル: {final_tables}")

if __name__ == "__main__":
    recreate_tables()