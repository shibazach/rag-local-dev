#!/usr/bin/env python3
"""
アップロードログテーブル作成スクリプト
"""
from sqlalchemy import create_engine, text
from app.config import config

def create_upload_logs_table():
    """アップロードログテーブルを作成"""
    try:
        # データベース接続
        engine = create_engine(config.DATABASE_URL)
        
        with engine.connect() as conn:
            # テーブル作成
            query = text("""
            CREATE TABLE IF NOT EXISTS upload_logs (
                id VARCHAR(36) PRIMARY KEY,
                session_id VARCHAR(36) NOT NULL,
                file_name VARCHAR(255) NOT NULL,
                file_size INTEGER NOT NULL,
                status VARCHAR(20) NOT NULL DEFAULT 'pending',
                progress INTEGER DEFAULT 0,
                message TEXT,
                error_detail TEXT,
                metadata JSON DEFAULT '{}',
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            )
            """)
            conn.execute(query)
            conn.commit()
            print("✅ Table 'upload_logs' created successfully")
            
            # インデックス作成
            indices = [
                "CREATE INDEX IF NOT EXISTS idx_upload_logs_session_id ON upload_logs(session_id)",
                "CREATE INDEX IF NOT EXISTS idx_upload_logs_status ON upload_logs(status)",
                "CREATE INDEX IF NOT EXISTS idx_upload_logs_created_at ON upload_logs(created_at DESC)"
            ]
            
            for idx_query in indices:
                conn.execute(text(idx_query))
                conn.commit()
                print(f"✅ Index created: {idx_query.split()[-3]}")
            
            # PostgreSQL用トリガー作成（エラーが出ても無視）
            try:
                trigger_func = text("""
                CREATE OR REPLACE FUNCTION update_updated_at_column()
                RETURNS TRIGGER AS $$
                BEGIN
                    NEW.updated_at = CURRENT_TIMESTAMP;
                    RETURN NEW;
                END;
                $$ language 'plpgsql'
                """)
                conn.execute(trigger_func)
                conn.commit()
                
                trigger = text("""
                    CREATE TRIGGER update_upload_logs_updated_at 
                    BEFORE UPDATE ON upload_logs 
                    FOR EACH ROW 
                    EXECUTE FUNCTION update_updated_at_column()
                """)
                conn.execute(trigger)
                conn.commit()
                print("✅ Trigger 'update_upload_logs_updated_at' created")
            except Exception as e:
                print(f"⚠️ Trigger creation skipped (may not be supported): {e}")
        
        print("\n✅ Upload logs table setup completed!")
        
    except Exception as e:
        print(f"❌ Error creating table: {e}")

if __name__ == "__main__":
    create_upload_logs_table()
