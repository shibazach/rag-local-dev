"""
UI用データサービス
Data service for UI components with mock data fallback
"""

from typing import List, Dict, Any, Optional
import httpx
from app.config import config, logger


class UIDataService:
    """UI用統合データサービス"""
    
    def __init__(self):
        self.api_base_url = f"http://localhost:8000{config.API_V1_PREFIX}"
        self.use_mock_data = True  # 開発時はTrue、本番時はFalse
    
    async def get_dashboard_stats(self) -> Dict[str, Any]:
        """ダッシュボード統計取得"""
        if self.use_mock_data:
            return self._get_mock_dashboard_stats()
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.api_base_url}/admin/stats")
                return response.json()
        except Exception as e:
            logger.warning(f"API統計取得失敗、モックデータ使用: {e}")
            return self._get_mock_dashboard_stats()
    
    async def get_files_list(
        self,
        page: int = 1,
        limit: int = 20,
        search: Optional[str] = None,
        status_filter: Optional[str] = None
    ) -> Dict[str, Any]:
        """ファイル一覧取得"""
        if self.use_mock_data:
            return self._get_mock_files_list(page, limit, search, status_filter)
        
        try:
            params = {"page": page, "limit": limit}
            if search:
                params["search"] = search
            if status_filter:
                params["status"] = status_filter
            
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.api_base_url}/files/", params=params)
                return response.json()
        except Exception as e:
            logger.warning(f"APIファイル一覧取得失敗、モックデータ使用: {e}")
            return self._get_mock_files_list(page, limit, search, status_filter)
    
    async def get_recent_activities(self, limit: int = 10) -> List[Dict[str, Any]]:
        """最近の活動取得"""
        if self.use_mock_data:
            return self._get_mock_activities(limit)
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.api_base_url}/admin/activities", params={"limit": limit})
                return response.json()
        except Exception as e:
            logger.warning(f"API活動履歴取得失敗、モックデータ使用: {e}")
            return self._get_mock_activities(limit)
    
    # モックデータ提供メソッド
    
    def _get_mock_dashboard_stats(self) -> Dict[str, Any]:
        """モックダッシュボード統計"""
        return {
            "total_files": {"value": 1234, "change": "+12%", "trend": "up"},
            "processed_files": {"value": 987, "percentage": 80, "trend": "stable"},
            "active_users": {"value": 45, "status": "online", "trend": "up"},
            "storage_usage": {"value": "234 GB", "percentage": 78, "trend": "up"},
            "processing_queue": {"value": 3, "avg_time": "2.5分", "trend": "down"}
        }
    
    def _get_mock_files_list(
        self,
        page: int,
        limit: int,
        search: Optional[str],
        status_filter: Optional[str]
    ) -> Dict[str, Any]:
        """モックファイル一覧"""
        all_files = [
            {
                "id": "1",
                "name": "技術報告書.pdf",
                "size": 2148576,  # 2.1MB
                "status": "processed",
                "created_at": "2024-01-15T10:30:00Z",
                "processed_at": "2024-01-15T10:35:00Z",
                "created_by": "田中太郎"
            },
            {
                "id": "2",
                "name": "研究資料.docx",
                "size": 1887437,  # 1.8MB
                "status": "processing",
                "created_at": "2024-01-15T09:15:00Z",
                "processed_at": None,
                "created_by": "佐藤花子"
            },
            {
                "id": "3",
                "name": "データ分析.xlsx",
                "size": 1258291,  # 1.2MB
                "status": "pending",
                "created_at": "2024-01-14T14:20:00Z",
                "processed_at": None,
                "created_by": "山田次郎"
            },
            {
                "id": "4",
                "name": "会議議事録.pdf",
                "size": 943718,  # 0.9MB
                "status": "error",
                "created_at": "2024-01-14T11:45:00Z",
                "processed_at": None,
                "created_by": "鈴木一郎",
                "error_message": "OCR処理エラー"
            },
            {
                "id": "5",
                "name": "仕様書.docx",
                "size": 1572864,  # 1.5MB
                "status": "uploaded",
                "created_at": "2024-01-13T16:30:00Z",
                "processed_at": None,
                "created_by": "高橋美咲"
            }
        ]
        
        # フィルタリング
        filtered_files = all_files
        if search:
            filtered_files = [f for f in filtered_files if search.lower() in f["name"].lower()]
        if status_filter:
            filtered_files = [f for f in filtered_files if f["status"] == status_filter]
        
        # ページネーション
        start = (page - 1) * limit
        end = start + limit
        page_files = filtered_files[start:end]
        
        return {
            "files": page_files,
            "total": len(filtered_files),
            "page": page,
            "limit": limit,
            "pages": (len(filtered_files) + limit - 1) // limit
        }
    
    def _get_mock_activities(self, limit: int) -> List[Dict[str, Any]]:
        """モック活動履歴"""
        activities = [
            {
                "time": "2分前",
                "action": "ファイルアップロード",
                "user": "田中太郎",
                "details": {"file": "報告書.pdf", "size": "2.1MB"},
                "type": "upload"
            },
            {
                "time": "5分前",
                "action": "検索実行",
                "user": "佐藤花子",
                "details": {"query": "AI技術動向", "results": 15},
                "type": "search"
            },
            {
                "time": "12分前",
                "action": "処理完了",
                "user": "システム",
                "details": {"file": "研究資料.docx", "duration": "3分15秒"},
                "type": "processing"
            },
            {
                "time": "25分前",
                "action": "ユーザーログイン",
                "user": "山田次郎",
                "details": {"ip": "192.168.1.100"},
                "type": "auth"
            },
            {
                "time": "1時間前",
                "action": "バッチ処理開始",
                "user": "システム",
                "details": {"files": 8, "estimated": "25分"},
                "type": "batch"
            }
        ]
        
        return activities[:limit]
    
    def toggle_mock_mode(self, use_mock: bool = None):
        """モックモード切り替え"""
        if use_mock is not None:
            self.use_mock_data = use_mock
        else:
            self.use_mock_data = not self.use_mock_data
        
        logger.info(f"UIデータサービス: {'モック' if self.use_mock_data else 'API'}モード")


# グローバルインスタンス
ui_data_service = UIDataService()