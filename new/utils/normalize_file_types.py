#!/usr/bin/env python3
# new/utils/normalize_file_types.py
# ファイルタイプを小文字に統一するスクリプト

import sys
import os
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from new.database import get_db
from new.models import File

def normalize_file_types():
    """ファイルタイプを小文字に統一"""
    print("=== ファイルタイプ正規化スクリプト開始 ===")
    try:
        db = next(get_db())
        
        # 全ファイルを取得
        files = db.query(File).all()
        print(f"総ファイル数: {len(files)}")
        
        # ファイルタイプの統計
        type_stats = {}
        for file in files:
            if file.file_type:
                type_stats[file.file_type] = type_stats.get(file.file_type, 0) + 1
        
        print("現在のファイルタイプ統計:")
        for file_type, count in type_stats.items():
            print(f"- {file_type}: {count}個")
        
        updated_count = 0
        
        for file in files:
            if file.file_type and file.file_type != file.file_type.lower():
                old_type = file.file_type
                new_type = file.file_type.lower()
                
                print(f"更新: {file.file_name} - {old_type} → {new_type}")
                file.file_type = new_type
                updated_count += 1
        
        if updated_count > 0:
            db.commit()
            print(f"更新完了: {updated_count}個のファイルを更新")
        else:
            print("更新対象なし")
        
    except Exception as e:
        print(f"スクリプト実行エラー: {e}")
    finally:
        if 'db' in locals():
            db.close()
        print("=== ファイルタイプ正規化スクリプト終了 ===")

if __name__ == "__main__":
    normalize_file_types() 