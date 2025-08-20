"""
統計情報サービス - システム状況取得（実際のDB統計版）
"""

from typing import Dict, Any
import asyncio
import time
from app.core.db_simple import fetch_one, fetch_all
from app.config import logger

# 起動時間記録
_start_time = time.time()

def get_system_stats() -> Dict[str, Any]:
    """
    システム統計情報取得（実際のデータベース統計）
    new/api/file_selection.py の実装を参考にpsycopg2版で実装
    """
    try:
        # 稼働時間計算
        uptime_seconds = int(time.time() - _start_time)
        if uptime_seconds < 60:
            uptime = f"{uptime_seconds}秒"
        elif uptime_seconds < 3600:
            uptime = f"{uptime_seconds // 60}分"
        else:
            hours = uptime_seconds // 3600
            minutes = (uptime_seconds % 3600) // 60
            uptime = f"{hours}時間{minutes}分"
        
        # 実際のDB統計を取得
        # 総ファイル数とステータス別集計
        stats_query = """
            SELECT
                COUNT(*) as total_files,
                COUNT(CASE WHEN ft.refined_text IS NOT NULL THEN 1 END) as processed_files,
                COUNT(CASE WHEN ft.raw_text IS NOT NULL AND ft.refined_text IS NULL THEN 1 END) as text_extracted,
                COUNT(CASE WHEN ft.raw_text IS NULL THEN 1 END) as pending_processing
            FROM files_blob fb
            JOIN files_meta fm ON fb.id = fm.blob_id
            LEFT JOIN files_text ft ON fb.id = ft.blob_id
        """
        
        file_stats = fetch_one(stats_query)
        
        if file_stats:
            total_files = file_stats.get('total_files', 0)
            processed_files = file_stats.get('processed_files', 0)
            text_extracted = file_stats.get('text_extracted', 0)
            pending_processing = file_stats.get('pending_processing', 0)
        else:
            total_files = processed_files = text_extracted = pending_processing = 0
        
        # ベクトル数取得（embeddings テーブルがある場合）
        try:
            vector_query = "SELECT COUNT(*) as total_vectors FROM embeddings"
            vector_result = fetch_one(vector_query)
            total_chunks = vector_result.get('total_vectors', 0) if vector_result else 0
        except:
            # embeddings テーブルがない場合は0とする
            total_chunks = 0
        
        # チャットセッション数（upload_logsテーブルから推定）
        try:
            session_query = "SELECT COUNT(DISTINCT session_id) as session_count FROM upload_logs"
            session_result = fetch_one(session_query)
            session_count = session_result.get('session_count', 0) if session_result else 0
        except:
            # upload_logsテーブルがない場合は0とする
            session_count = 0
        
        # 処理率計算
        processing_rate = f"{(processed_files / total_files * 100):.1f}%" if total_files > 0 else "0.0%"
        
        logger.info(f"📊 統計取得成功: ファイル={total_files}, 処理済み={processed_files}, ベクトル={total_chunks}, セッション={session_count}")
        
        return {
            "file_count": total_files,
            "processed_files": processed_files,
            "session_count": session_count,
            "uptime": uptime,
            "total_chunks": total_chunks,
            "total_images": 0,  # 画像テーブル未実装のため0
            "vectorized_files": processed_files,  # 処理済み=ベクトル化済みと仮定
            "processing_rate": processing_rate,
            "system_status": "正常",
            "db_status": "接続中",
            "api_status": "稼働中"
        }
        
    except Exception as e:
        logger.error(f"❌ 統計取得エラー: {e}")
        # エラー時はフォールバック値を返す
        return {
            "file_count": 0,
            "processed_files": 0,
            "session_count": 0,
            "uptime": "不明",
            "total_chunks": 0,
            "total_images": 0,
            "vectorized_files": 0,
            "processing_rate": "0.0%",
            "system_status": "エラー",
            "db_status": "接続エラー",
            "api_status": "稼働中"
        }

# 後方互換性のための非同期ラッパー
async def get_system_stats_async() -> Dict[str, Any]:
    """非同期版統計取得（後方互換性用）"""
    return get_system_stats()