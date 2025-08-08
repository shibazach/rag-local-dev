#!/usr/bin/env python3
"""
テーブル構造確認スクリプト
"""
from sqlalchemy import text, inspect
from app.core.database import engine

def check_table_structure():
    """files_imageテーブルの構造を確認"""
    with engine.connect() as conn:
        # files_imageテーブルの構造を確認
        result = conn.execute(text("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'files_image'
            ORDER BY ordinal_position;
        """))
        
        print("files_imageテーブルの構造:")
        print("-" * 50)
        for row in result:
            print(f"{row.column_name}: {row.data_type} (nullable: {row.is_nullable})")
        
        print("\n既存のテーブル一覧:")
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        for table in sorted(tables):
            print(f"  - {table}")

if __name__ == "__main__":
    check_table_structure()