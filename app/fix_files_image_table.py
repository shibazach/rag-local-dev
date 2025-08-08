#!/usr/bin/env python3
"""
files_imageテーブルを正しいスキーマで再作成
"""
import logging
from sqlalchemy import text
from app.core.database import engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def recreate_files_image_table():
    """files_imageテーブルをドロップして再作成"""
    
    with engine.begin() as conn:
        # 既存のfiles_imageテーブルをドロップ
        logger.info("既存のfiles_imageテーブルをドロップ")
        conn.execute(text("DROP TABLE IF EXISTS files_image CASCADE"))
        
        # pgcrypto拡張を有効化（UUID生成用）
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS pgcrypto"))
        
        # files_imageテーブルを正しいスキーマで作成
        logger.info("files_imageテーブルを新しいスキーマで作成")
        conn.execute(text("""
            CREATE TABLE files_image (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                blob_id UUID NOT NULL REFERENCES files_blob(id) ON DELETE CASCADE,
                page_number INTEGER NOT NULL,
                image_index INTEGER NOT NULL,
                image_type VARCHAR(50) NOT NULL DEFAULT 'image',
                image_data BYTEA NOT NULL,
                image_format VARCHAR(10),
                width INTEGER,
                height INTEGER,
                caption TEXT,
                extracted_text TEXT,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            )
        """))
        
        # インデックス作成
        conn.execute(text("CREATE INDEX idx_files_image_blob_id ON files_image(blob_id)"))
        conn.execute(text("CREATE INDEX idx_files_image_page ON files_image(page_number)"))
        
        logger.info("✅ files_imageテーブル再作成完了")

if __name__ == "__main__":
    recreate_files_image_table()