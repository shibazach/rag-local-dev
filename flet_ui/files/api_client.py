#!/usr/bin/env python3
"""
Flet RAGシステム - ファイル管理API クライアント（実DB接続版）
既存のapp/services/file_service.pyを活用
"""

from typing import Dict, List, Optional, Any
from app.services.file_service import get_file_service
from app.config import logger
import math


class FilesDBClient:
    """ファイル管理DBクライアント（既存構造活用版）"""
    
    def __init__(self):
        self.file_service = get_file_service()
    
    def get_files_list(self, page: int = 1, page_size: int = 20, 
                      status: Optional[str] = None, 
                      search: Optional[str] = None) -> Dict[str, Any]:
        """
        ファイル一覧を取得
        
        Args:
            page: ページ番号
            page_size: 1ページあたりの件数
            status: ステータスフィルター
            search: ファイル名検索
            
        Returns:
            ファイル一覧データ（NiceGUIレスポンス形式）
        """
        try:
            # フィルタリングがある場合は全データを取得してクライアント側でフィルタリング
            # フィルタリングがない場合は通常のページネーション
            if search or (status and status != "全て"):
                # 全データを取得
                result = self.file_service.get_file_list(limit=1000, offset=0)  # 十分大きな値
            else:
                # offsetとlimitを計算
                offset = (page - 1) * page_size
                result = self.file_service.get_file_list(limit=page_size, offset=offset)
            
            # db_simpleからのレスポンスを処理
            files_data = result.get("files", [])
            total_count = result.get("total", 0)
            
            if result.get("status") == "success" or files_data:  # 成功またはデータがある場合
                
                # NiceGUI形式に変換
                processed_files = []
                for file_data in files_data:
                    processed_files.append({
                        "id": file_data.get("file_id"),  # file_idキーを使用
                        "file_name": file_data.get("filename", "Unknown"),
                        "file_size": file_data.get("file_size", 0),
                        "status": file_data.get("status", "unknown"),
                        "created_at": file_data.get("created_at", ""),
                        "updated_at": file_data.get("updated_at", ""),
                        "mime_type": file_data.get("content_type", "application/octet-stream")
                    })
                
                # 検索フィルター適用
                if search:
                    processed_files = [
                        f for f in processed_files 
                        if search.lower() in f.get('file_name', '').lower()
                    ]
                
                # ステータスフィルター適用
                if status and status != "全て":
                    processed_files = [
                        f for f in processed_files 
                        if f.get('status') == status
                    ]
                
                # フィルタリングの有無でページネーション計算を分ける
                if search or (status and status != "全て"):
                    # フィルタリング有り：フィルタリング後の件数で計算
                    filtered_count = len(processed_files)
                    total_pages = math.ceil(filtered_count / page_size) if filtered_count > 0 else 1
                    
                    # 現在のページのファイルのみを返す
                    start_idx = (page - 1) * page_size
                    end_idx = start_idx + page_size
                    page_files = processed_files[start_idx:end_idx]
                    
                    return {
                        "files": page_files,
                        "total": total_count,  # DBの元の総数
                        "pagination": {
                            "current_page": page,
                            "page_size": page_size,
                            "total_count": filtered_count,  # フィルタリング後の件数
                            "total_pages": total_pages,
                            "has_next": page < total_pages,
                            "has_prev": page > 1
                        },
                        "status": "success"
                    }
                else:
                    # フィルタリングなし：DBの件数をそのまま使用
                    return {
                        "files": processed_files,
                        "total": total_count,
                        "pagination": {
                            "current_page": page,
                            "page_size": page_size,
                            "total_count": total_count,
                            "total_pages": math.ceil(total_count / page_size) if total_count > 0 else 1,
                            "has_next": (page * page_size) < total_count,
                            "has_prev": page > 1
                        },
                        "status": "success"
                    }
            else:
                logger.error(f"ファイル一覧取得失敗: {result}")
                return {
                    "files": [],
                    "total": 0,
                    "pagination": {
                        "current_page": 1,
                        "page_size": page_size,
                        "total_count": 0,
                        "total_pages": 1,
                        "has_next": False,
                        "has_prev": False
                    },
                    "status": "error",
                    "error": "ファイル一覧の取得に失敗しました"
                }
                
        except Exception as e:
            logger.error(f"ファイル一覧取得エラー: {e}")
            return {
                "files": [],
                "total": 0,
                "status": "error",
                "error": str(e)
            }
    
    def get_file_detail(self, file_id: str) -> Optional[Dict[str, Any]]:
        """
        ファイル詳細情報を取得
        
        Args:
            file_id: ファイルID
            
        Returns:
            ファイル詳細情報
        """
        try:
            file_info = self.file_service.get_file_info(file_id)
            
            if file_info:
                return {
                    "id": file_info.get("file_id", file_id),
                    "file_name": file_info.get("filename", "Unknown"),
                    "file_size": file_info.get("file_size", 0),
                    "mime_type": file_info.get("content_type", "application/octet-stream"),
                    "status": file_info.get("status", "unknown"),
                    "created_at": file_info.get("created_at", ""),
                    "updated_at": file_info.get("updated_at", ""),
                    "checksum": file_info.get("checksum", ""),
                    "quality_score": None  # 今のところ未対応
                }
            else:
                return None
                
        except Exception as e:
            logger.error(f"ファイル詳細取得エラー: {e}")
            return None
    
    def delete_file(self, file_id: str) -> bool:
        """
        ファイルを削除
        
        Args:
            file_id: ファイルID
            
        Returns:
            成功/失敗
        """
        try:
            result = self.file_service.delete_file(file_id)
            return result.get("status") == "success"
            
        except Exception as e:
            logger.error(f"ファイル削除エラー: {e}")
            return False
    
    def get_file_preview(self, file_id: str) -> Optional[Dict[str, Any]]:
        """
        ファイルプレビューデータを取得
        
        Args:
            file_id: ファイルID
            
        Returns:
            プレビューデータ
        """
        try:
            preview = self.file_service.get_file_preview(file_id)
            return preview
            
        except Exception as e:
            logger.error(f"プレビュー取得エラー: {e}")
            return None