"""
Upload関連Pydanticスキーマ - new/系移植版
app/core/schemas.py - Upload API・レスポンス型定義
"""

from datetime import datetime
from typing import Optional, List, Dict, Any, Union
from uuid import UUID
from pydantic import BaseModel, Field

# ──────────────────────────────────────────────────────────
# ファイルアップロード関連スキーマ（new/系移植）
# ──────────────────────────────────────────────────────────

class UploadResponse(BaseModel):
    """単一ファイルアップロードレスポンス"""
    status: str = Field(..., description="処理ステータス (uploaded/duplicate/error)")
    message: str = Field(..., description="処理結果メッセージ")
    file_id: Optional[UUID] = Field(None, description="アップロードされたファイルID")
    file_name: str = Field(..., description="ファイル名")
    size: Optional[int] = Field(None, description="ファイルサイズ（バイト）")
    checksum: Optional[str] = Field(None, description="SHA256チェックサム")
    created_at: Optional[datetime] = Field(None, description="作成/アップロード日時")
    upload_status: str = Field("uploaded", description="アップロードステータス (uploaded/duplicate/error)")
    
    model_config = {"from_attributes": True}

class BatchUploadResponse(BaseModel):
    """バッチアップロードレスポンス"""
    status: str = Field(..., description="全体処理ステータス (success/partial/error)")
    message: str = Field(..., description="全体処理結果メッセージ")
    results: List[UploadResponse] = Field([], description="個別ファイル処理結果一覧")
    success_count: int = Field(0, description="成功件数")
    error_count: int = Field(0, description="失敗件数")
    
    model_config = {"from_attributes": True}

class UploadStatusResponse(BaseModel):
    """アップロード機能ステータス"""
    status: str = Field(..., description="機能ステータス")
    data: Dict[str, Any] = Field(..., description="ステータス詳細情報")
    
    model_config = {"from_attributes": True}

# ──────────────────────────────────────────────────────────
# ファイル管理関連スキーマ
# ──────────────────────────────────────────────────────────

class FileInfoResponse(BaseModel):
    """ファイル情報レスポンス"""
    id: UUID = Field(..., description="ファイルID (FilesBlob.id)")
    file_name: str = Field(..., description="ファイル名")
    mime_type: Optional[str] = Field(None, description="MIMEタイプ")
    size: int = Field(..., description="ファイルサイズ（バイト）")
    checksum: str = Field(..., description="SHA256チェックサム")
    status: str = Field(..., description="処理ステータス")
    created_at: datetime = Field(..., description="作成日時")
    
    # Files Text情報
    has_text: bool = Field(False, description="テキスト抽出済みフラグ")
    text_length: int = Field(0, description="抽出テキスト文字数")
    quality_score: Optional[float] = Field(None, description="品質スコア")
    tags: List[str] = Field([], description="タグ一覧")
    
    model_config = {"from_attributes": True}

class FileListResponse(BaseModel):
    """ファイル一覧レスポンス"""
    files: List[FileInfoResponse] = Field(..., description="ファイル一覧")
    total: int = Field(..., description="総件数")
    limit: int = Field(..., description="1ページあたり件数")
    offset: int = Field(..., description="オフセット")
    
    model_config = {"from_attributes": True}

# ──────────────────────────────────────────────────────────
# 共通レスポンススキーマ
# ──────────────────────────────────────────────────────────

class SuccessResponse(BaseModel):
    """成功レスポンス基底スキーマ"""
    status: str = Field("success", description="ステータス")
    message: str = Field(..., description="メッセージ")
    data: Optional[Any] = Field(None, description="データ")
    
    model_config = {"from_attributes": True}

class ErrorResponse(BaseModel):
    """エラーレスポンススキーマ"""
    status: str = Field("error", description="ステータス")
    message: str = Field(..., description="エラーメッセージ")
    detail: Optional[str] = Field(None, description="詳細情報")
    error_code: Optional[str] = Field(None, description="エラーコード")
    
    model_config = {"from_attributes": True}