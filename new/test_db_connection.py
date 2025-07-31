#!/usr/bin/env python3
# new/test_db_connection.py
# データベース接続テストスクリプト

import sys
import os

# パス追加
sys.path.append(os.path.dirname(__file__))

from config import DB_ENGINE, DEBUG_MODE
from database.connection import test_connection, get_database_info
from database.schemas import init_schema, get_table_info


def main():
    """データベース接続・初期化テスト"""
    
    print("=" * 60)
    print("データベース接続テスト開始")
    print("=" * 60)
    
    # 1. 基本接続テスト
    print("\n1. 基本接続テスト...")
    if test_connection():
        print("✅ データベース接続: 成功")
    else:
        print("❌ データベース接続: 失敗")
        return False
    
    # 2. データベース情報取得
    print("\n2. データベース情報取得...")
    db_info = get_database_info()
    print(f"   データベース名: {db_info['database_name']}")
    print(f"   PostgreSQLバージョン: {db_info['version'][:50]}...")
    print(f"   pgvector拡張: {'✅ 有効' if db_info['has_pgvector'] else '❌ 無効'}")
    print(f"   接続ステータス: {db_info['connection_status']}")
    
    # 3. スキーマ初期化
    print("\n3. スキーマ初期化...")
    if init_schema():
        print("✅ スキーマ初期化: 成功")
    else:
        print("❌ スキーマ初期化: 失敗")
        return False
    
    # 4. テーブル情報確認
    print("\n4. テーブル情報確認...")
    table_info = get_table_info()
    if table_info['status'] == 'healthy':
        print("✅ テーブル情報取得: 成功")
        print(f"   存在するテーブル: {len(table_info['tables'])}個")
        for table in sorted(table_info['tables']):
            if table.startswith('files_'):
                count = table_info['table_counts'].get(table, 'unknown')
                print(f"     - {table}: {count}行")
    else:
        print(f"❌ テーブル情報取得: {table_info['status']}")
        return False
    
    print("\n" + "=" * 60)
    print("✅ データベース接続テスト完了")
    print("=" * 60)
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)