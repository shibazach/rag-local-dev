#!/usr/bin/env python3
"""
embeddingsテーブルのマイグレーションスクリプト
既存のテーブルをバックアップして、新しい構造で再作成
"""

from sqlalchemy import create_engine, text
from config import config, logger
from core.database import Base, init_database
from core.models import FileEmbedding
import datetime


def migrate_embeddings_table():
    """embeddingsテーブルをマイグレーション"""
    engine = create_engine(config.DATABASE_URL)
    
    with engine.begin() as conn:
        try:
            # 1. 既存のテーブルをバックアップ
            logger.info("既存のembeddingsテーブルをバックアップ中...")
            
            # バックアップテーブル名
            backup_table = f"embeddings_backup_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # テーブルの存在確認
            result = conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'embeddings'
                );
            """))
            table_exists = result.scalar()
            count = 0  # レコード数の初期値
            
            if table_exists:
                # バックアップテーブル作成
                conn.execute(text(f"""
                    CREATE TABLE {backup_table} AS 
                    SELECT * FROM embeddings;
                """))
                logger.info(f"バックアップテーブル作成完了: {backup_table}")
                
                # レコード数確認
                count_result = conn.execute(text(f"SELECT COUNT(*) FROM {backup_table}"))
                count = count_result.scalar()
                logger.info(f"バックアップレコード数: {count}")
                
                # 既存のテーブルを削除
                conn.execute(text("DROP TABLE IF EXISTS embeddings CASCADE;"))
                logger.info("既存のembeddingsテーブルを削除")
            
            # 2. 新しい構造でテーブル作成
            logger.info("新しい構造でembeddingsテーブルを作成中...")
            
            # pgcrypto拡張を有効化（gen_random_uuid用）
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS pgcrypto;"))
            
            # テーブル定義を直接SQLで作成（より確実）
            conn.execute(text("""
                CREATE TABLE embeddings (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    blob_id UUID NOT NULL REFERENCES files_blob(id) ON DELETE CASCADE,
                    chunk_index INTEGER NOT NULL,
                    chunk_text TEXT NOT NULL,
                    chunk_start INTEGER,
                    chunk_end INTEGER,
                    vector_json TEXT,
                    embedding_model VARCHAR(100),
                    embedding_dimension INTEGER,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                );
            """))
            
            # 3. インデックス作成
            logger.info("インデックスを作成中...")
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_embeddings_blob_id ON embeddings(blob_id);
                CREATE INDEX IF NOT EXISTS idx_embeddings_chunk_index ON embeddings(blob_id, chunk_index);
            """))
            
            # 4. データ移行（既存データがある場合）
            if table_exists and count > 0:
                logger.info("既存データを新しい構造に移行中...")
                
                # 既存データの構造に応じて移行
                # contentフィールドをchunk_textに、その他のフィールドも適切にマッピング
                conn.execute(text(f"""
                    INSERT INTO embeddings (id, blob_id, chunk_index, chunk_text, embedding_model, created_at)
                    SELECT 
                        id,
                        blob_id,
                        ROW_NUMBER() OVER (PARTITION BY blob_id ORDER BY created_at) - 1 as chunk_index,
                        content as chunk_text,
                        embedding_model,
                        created_at
                    FROM {backup_table}
                    WHERE blob_id IS NOT NULL;
                """))
                
                # 移行後のレコード数確認
                new_count_result = conn.execute(text("SELECT COUNT(*) FROM embeddings"))
                new_count = new_count_result.scalar()
                logger.info(f"移行完了: {new_count}レコード")
            
            logger.info("マイグレーション完了!")
            
        except Exception as e:
            logger.error(f"マイグレーションエラー: {e}")
            raise


if __name__ == "__main__":
    migrate_embeddings_table()