#!/usr/bin/env python3
# reset_db.py
# データベースをリセットするスクリプト

import psycopg2
from new.config import DATABASE_URL, LOGGER

def reset_database():
    """データベースをリセット"""
    try:
        # データベースURLから接続情報を抽出
        # postgresql://username:password@host:port/database
        url_parts = DATABASE_URL.replace('postgresql://', '').split('/')
        connection_info = url_parts[0].split('@')
        credentials = connection_info[0].split(':')
        host_port = connection_info[1].split(':')
        
        username = credentials[0]
        password = credentials[1]
        host = host_port[0]
        port = host_port[1] if len(host_port) > 1 else '5432'
        database = url_parts[1]
        
        # データベースに接続
        conn = psycopg2.connect(
            host=host,
            port=port,
            database=database,
            user=username,
            password=password
        )
        
        cursor = conn.cursor()
        
        # 既存のテーブルを削除（新しいテーブルを含む）
        tables = [
            'chat_messages',
            'chat_sessions', 
            'embeddings',
            'file_texts',
            'file_images',
            'files',
            'processing_queue',
            'system_config'
        ]
        
        for table in tables:
            try:
                cursor.execute(f"DROP TABLE IF EXISTS {table} CASCADE")
                LOGGER.info(f"テーブル {table} を削除しました")
            except Exception as e:
                LOGGER.warning(f"テーブル {table} の削除に失敗: {e}")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        LOGGER.info("✅ データベースリセット完了")
        
    except Exception as e:
        LOGGER.error(f"❌ データベースリセットエラー: {e}")
        raise

if __name__ == "__main__":
    reset_database() 