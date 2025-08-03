"""
API共通依存性
Common dependencies for API endpoints
"""

from typing import Dict, Any, Optional
from fastapi import Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from app.core import get_db
from app.auth import (
    get_current_user_required,
    get_current_user_optional,
    require_admin
)
from datetime import datetime
from app.config import logger

# ========== データベース依存性 ==========

DatabaseSession = Depends(get_db)

# ========== ページネーション依存性 ==========

class PaginationParams:
    """ページネーション パラメータ"""
    
    def __init__(
        self,
        page: int = Query(1, ge=1, description="ページ番号"),
        per_page: int = Query(20, ge=1, le=100, description="1ページあたり件数"),
        sort_by: Optional[str] = Query(None, description="ソートフィールド"),
        sort_order: str = Query("desc", regex="^(asc|desc)$", description="ソート順序")
    ):
        self.page = page
        self.per_page = per_page
        self.sort_by = sort_by
        self.sort_order = sort_order
        
    @property
    def offset(self) -> int:
        """オフセット計算"""
        return (self.page - 1) * self.per_page
    
    @property
    def limit(self) -> int:
        """リミット"""
        return self.per_page

Pagination = Depends(PaginationParams)

# ========== フィルタリング依存性 ==========

class FileFilterParams:
    """ファイルフィルター パラメータ"""
    
    def __init__(
        self,
        status: Optional[str] = Query(None, description="処理ステータス"),
        file_type: Optional[str] = Query(None, description="ファイルタイプ"),
        date_from: Optional[str] = Query(None, description="開始日（YYYY-MM-DD）"),
        date_to: Optional[str] = Query(None, description="終了日（YYYY-MM-DD）"),
        search: Optional[str] = Query(None, description="ファイル名検索")
    ):
        self.status = status
        self.file_type = file_type
        self.date_from = date_from
        self.date_to = date_to
        self.search = search

FileFilters = Depends(FileFilterParams)

# ========== 検索依存性 ==========

class SearchParams:
    """検索パラメータ"""
    
    def __init__(
        self,
        q: str = Query(..., min_length=1, max_length=1000, description="検索クエリ"),
        search_type: str = Query("semantic", regex="^(semantic|keyword|hybrid)$", description="検索タイプ"),
        limit: int = Query(10, ge=1, le=100, description="結果件数"),
        min_score: float = Query(0.0, ge=0.0, le=1.0, description="最小スコア"),
        include_metadata: bool = Query(False, description="メタデータ含める")
    ):
        self.q = q
        self.search_type = search_type
        self.limit = limit
        self.min_score = min_score
        self.include_metadata = include_metadata

SearchParameters = Depends(SearchParams)

# ========== リクエスト情報依存性 ==========

def get_request_info(request: Request) -> Dict[str, Any]:
    """リクエスト情報取得"""
    return {
        "ip_address": request.client.host if request.client else "unknown",
        "user_agent": request.headers.get("user-agent", "unknown"),
        "method": request.method,
        "url": str(request.url),
        "headers": dict(request.headers)
    }

RequestInfo = Depends(get_request_info)

# ========== バリデーション・チェック ==========

def validate_file_access(
    file_id: str,
    current_user = Depends(get_current_user_required),
    db: Session = DatabaseSession
) -> Dict[str, Any]:
    """ファイルアクセス権限チェック"""
    from app.core.models import FilesMeta
    from uuid import UUID
    
    try:
        file_uuid = UUID(file_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="無効なファイルIDです")
    
    file_meta = db.query(FilesMeta).filter(FilesMeta.blob_id == file_uuid).first()
    if not file_meta:
        raise HTTPException(status_code=404, detail="ファイルが見つかりません")
    
    # TODO: ファイル所有者・権限チェック実装
    # if not current_user.get("is_admin") and file_meta.user_id != current_user.get("id"):
    #     raise HTTPException(status_code=403, detail="ファイルへのアクセス権限がありません")
    
    logger.debug(f"ファイルアクセス許可: {file_id} by {current_user.get('username')}")
    return {"file_meta": file_meta, "user": current_user}

# ========== レート制限・セキュリティ ==========

class RateLimitChecker:
    """レート制限チェッカー（将来拡張用）"""
    
    def __init__(self, max_requests: int = 100, window_seconds: int = 3600):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
    
    def __call__(self, request: Request) -> bool:
        # TODO: レート制限実装（Redis使用）
        # 現在は常にTrue返却
        return True

rate_limiter = RateLimitChecker()
RateLimit = Depends(rate_limiter)

# ========== 例外ハンドラー用 ==========

def create_error_response(
    status_code: int,
    error_code: str,
    message: str,
    details: Optional[Dict[str, Any]] = None
) -> HTTPException:
    """統一エラーレスポンス作成"""
    return HTTPException(
        status_code=status_code,
        detail={
            "success": False,
            "error_code": error_code,
            "error_message": message,
            "details": details or {},
            "timestamp": str(datetime.utcnow())
        }
    )

# ========== ヘルパー関数 ==========

def log_api_request(
    request: Request,
    user: Optional[Dict[str, Any]] = None,
    action: str = "api_call"
):
    """APIリクエストログ記録"""
    user_info = user.get("username", "anonymous") if user else "anonymous"
    logger.info(
        f"API {action}: {request.method} {request.url.path} - "
        f"User: {user_info} - "
        f"IP: {request.client.host if request.client else 'unknown'}"
    )