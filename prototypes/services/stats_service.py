"""
統計情報サービス - システム状況取得
"""

from typing import Dict, Any
import asyncio
import time

# 起動時間記録
_start_time = time.time()

async def get_system_stats() -> Dict[str, Any]:
    """
    システム統計情報取得
    new/index.htmlのstats-grid相当のデータを提供
    """
    
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
    
    # ダミー統計データ（後で実際のDB統計に置き換え）
    return {
        "file_count": 42,
        "processed_files": 38,
        "session_count": 3,
        "uptime": uptime,
        "total_chunks": 1547,
        "total_images": 123,
        "vectorized_files": 35,
        "processing_rate": "90.5%",
        "system_status": "正常",
        "db_status": "接続中",
        "api_status": "稼働中"
    }