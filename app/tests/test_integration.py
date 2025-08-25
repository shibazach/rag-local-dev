#!/usr/bin/env python3
"""
統合テスト - 同期版
データベース接続とFiles3兄弟の動作確認
"""

import sys
import tempfile
from pathlib import Path

# パス設定
sys.path.append(str(Path(__file__).parent))

from config import config, logger
from core.database import init_database, get_db_session, health_check, get_database_info
from core.db_handler import FileDBHandler
from core.models import FilesBlob, FilesMeta, FilesText


def test_database_connection():
    """データベース接続テスト"""
    logger.info("=== データベース接続テスト ===")
    
    try:
        # ヘルスチェック
        health_status = health_check()
        logger.info(f"ヘルスチェック結果: {health_status}")
        
        if health_status["status"] != "healthy":
            logger.error("データベース接続に失敗しました")
            return False
        
        # データベース情報取得
        db_info = get_database_info()
        logger.info(f"データベース情報:")
        logger.info(f"  - URL: {db_info.get('database_url')}")
        logger.info(f"  - テーブル数: {db_info.get('table_counts', {})}")
        
        return True
    except Exception as e:
        logger.error(f"❌ データベース接続エラー: {e}")
        return False


def test_file_operations():
    """ファイル操作テスト（Files3兄弟）"""
    logger.info("\n=== ファイル操作テスト ===")
    
    try:
        with get_db_session() as db:
            handler = FileDBHandler(db)
            
            # テスト用一時ファイル作成
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                f.write("これはテストファイルです。\nRAGシステムの統合テスト。")
                test_file_path = f.name
            
            try:
                # 1. ファイル登録
                logger.info("1. ファイル登録テスト")
                blob_id, is_new = handler.insert_file_full(
                    file_path=test_file_path,
                    raw_text="これはテストファイルです。\nRAGシステムの統合テスト。",
                    refined_text="これはテストファイルです。RAGシステムの統合テスト。",
                    quality_score=0.95,
                    tags=["テスト", "統合", "RAG"],
                    original_filename="test_integration.txt"
                )
                logger.info(f"✅ ファイル登録成功: {blob_id} (新規: {is_new})")
                
                # 2. 重複チェック
                logger.info("\n2. 重複チェックテスト")
                checksum = handler.calc_checksum(test_file_path)
                existing_id = handler.find_existing_by_checksum(checksum)
                logger.info(f"✅ 重複チェック: {existing_id}")
                
                # 3. ファイル情報取得
                logger.info("\n3. ファイル情報取得テスト")
                file_info = handler.get_file_by_id(blob_id)
                if file_info:
                    logger.info(f"✅ ファイル情報取得成功:")
                    logger.info(f"  - ファイル名: {file_info['file_name']}")
                    logger.info(f"  - サイズ: {file_info['size']} bytes")
                    logger.info(f"  - MIME: {file_info['mime_type']}")
                    logger.info(f"  - タグ: {file_info['tags']}")
                    logger.info(f"  - 品質スコア: {file_info['quality_score']}")
                
                # 4. ファイルリスト取得
                logger.info("\n4. ファイルリスト取得テスト")
                files = handler.list_files(limit=10)
                logger.info(f"✅ ファイルリスト: {len(files)}件")
                for file in files[:3]:  # 最初の3件を表示
                    logger.info(f"  - {file['file_name']} ({file['size']} bytes)")
                
                # 5. タグ更新
                logger.info("\n5. タグ更新テスト")
                success = handler.update_tags(blob_id, ["更新", "テスト完了"], append=True)
                logger.info(f"✅ タグ更新: {success}")
                
                # 6. 統計情報
                logger.info("\n6. 統計情報取得テスト")
                stats = handler.get_statistics()
                logger.info(f"✅ 統計情報:")
                logger.info(f"  - 総ファイル数: {stats.get('total_files', 0)}")
                logger.info(f"  - 総サイズ: {stats.get('total_size_mb', 0)} MB")
                logger.info(f"  - テキストありファイル: {stats.get('files_with_text', 0)}")
                logger.info(f"  - 整形済みテキスト: {stats.get('files_with_refined_text', 0)}")
                logger.info(f"  - ユニークタグ数: {stats.get('unique_tags', 0)}")
                
                return True
                
            finally:
                # テストファイル削除
                Path(test_file_path).unlink(missing_ok=True)
                
    except Exception as e:
        logger.error(f"❌ ファイル操作エラー: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_database_init():
    """データベース初期化テスト"""
    logger.info("\n=== データベース初期化テスト ===")
    
    try:
        # テーブル作成（既存の場合はスキップ）
        init_database()
        logger.info("✅ データベース初期化成功")
        return True
    except Exception as e:
        logger.error(f"❌ データベース初期化エラー: {e}")
        return False


def main():
    """メインテスト実行"""
    logger.info("========================================")
    logger.info("統合テスト - 同期版")
    logger.info("========================================")
    
    results = []
    
    # 各テスト実行
    results.append(test_database_connection())
    results.append(test_database_init())
    results.append(test_file_operations())
    
    # 結果集計
    logger.info("\n========================================")
    logger.info("テスト結果サマリー")
    logger.info("========================================")
    
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        logger.info(f"✅ 全テスト成功 ({passed}/{total})")
    else:
        logger.warning(f"⚠️ 一部テスト失敗 ({passed}/{total})")
    
    logger.info("\n統合テスト完了")
    
    # 終了コード
    return 0 if passed == total else 1


if __name__ == "__main__":
    exit(main())