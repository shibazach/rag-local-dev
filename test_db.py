#!/usr/bin/env python3
# test_db.py
# データベーステストスクリプト

import logging
from new.database import get_db
from new.models import File

# ログ設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
LOGGER = logging.getLogger(__name__)

def test_file_insert():
    """ファイル挿入テスト"""
    try:
        db = next(get_db())
        
        # テストファイルデータ
        file_data = {
            "file_name": "test.txt",
            "file_path": "/tmp/test.txt",
            "file_size": 40,
            "status": "uploaded",
            "user_id": 1
        }
        
        LOGGER.info(f"挿入するファイルデータ: {file_data}")
        
        file = File(**file_data)
        db.add(file)
        db.commit()
        db.refresh(file)
        
        LOGGER.info(f"ファイル挿入成功: ID={file.id}")
        
        # 確認
        files = db.query(File).all()
        LOGGER.info(f"データベース内のファイル数: {len(files)}")
        
        for f in files:
            LOGGER.info(f"ファイル: ID={f.id}, 名前={f.file_name}, パス={f.file_path}")
        
        db.close()
        
    except Exception as e:
        LOGGER.error(f"ファイル挿入エラー: {e}")
        import traceback
        LOGGER.error(f"詳細エラー: {traceback.format_exc()}")
        raise

if __name__ == "__main__":
    test_file_insert() 