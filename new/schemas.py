# new/schemas.py
# APIレスポンス・リクエストスキーマ定義

from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field
from datetime import datetime


# ============================================================================
# 基本レスポンススキーマ
# ============================================================================

class BaseResponse(BaseModel):
    """基本レスポンススキーマ"""
    status: str = Field(..., description="レスポンスステータス")
    message: Optional[str] = Field(None, description="メッセージ")


class PaginationInfo(BaseModel):
    """ページネーション情報"""
    current_page: int = Field(..., description="現在のページ番号")
    page_size: int = Field(..., description="1ページあたりの件数")
    total_count: int = Field(..., description="総件数")
    total_pages: int = Field(..., description="総ページ数")
    has_next: bool = Field(..., description="次ページの有無")
    has_prev: bool = Field(..., description="前ページの有無")


# ============================================================================
# ファイル関連スキーマ
# ============================================================================

class FileInfo(BaseModel):
    """ファイル基本情報"""
    id: str = Field(..., description="ファイルID")
    file_name: str = Field(..., description="ファイル名")
    mime_type: str = Field(..., description="MIMEタイプ")
    size: int = Field(..., description="ファイルサイズ（バイト）")
    page_count: Optional[int] = Field(None, description="ページ数")
    status: str = Field(..., description="処理ステータス")
    created_at: str = Field(..., description="作成日時")
    updated_at: str = Field(..., description="更新日時")
    quality_score: Optional[float] = Field(None, description="品質スコア")


class FileListResponse(BaseResponse):
    """ファイル一覧レスポンス"""
    files: List[FileInfo] = Field(..., description="ファイル一覧")
    pagination: PaginationInfo = Field(..., description="ページネーション情報")


class FileDetailInfo(FileInfo):
    """ファイル詳細情報"""
    checksum: str = Field(..., description="チェックサム")
    stored_at: str = Field(..., description="格納日時")
    raw_text: Optional[str] = Field(None, description="OCR生テキスト")
    refined_text: Optional[str] = Field(None, description="整形済みテキスト")
    tags: List[str] = Field(default=[], description="タグ一覧")
    processing_log: Optional[str] = Field(None, description="処理ログ")
    ocr_engine: Optional[str] = Field(None, description="使用OCRエンジン")
    llm_model: Optional[str] = Field(None, description="使用LLMモデル")
    text_updated_at: Optional[str] = Field(None, description="テキスト更新日時")


class FileDetailResponse(FileDetailInfo):
    """ファイル詳細レスポンス"""
    pass


class FileStatusUpdate(BaseModel):
    """ファイルステータス更新リクエスト"""
    status: str = Field(..., description="新しいステータス")


# ============================================================================
# ファイルアップロード関連スキーマ
# ============================================================================

class UploadResponse(BaseResponse):
    """アップロードレスポンス"""
    file_id: str = Field(..., description="アップロードされたファイルID")
    file_name: str = Field(..., description="ファイル名")
    size: int = Field(..., description="ファイルサイズ")
    checksum: str = Field(..., description="チェックサム")


class BatchUploadResponse(BaseResponse):
    """一括アップロードレスポンス"""
    results: List[Dict[str, Any]] = Field(..., description="アップロード結果一覧")
    success_count: int = Field(..., description="成功件数")
    error_count: int = Field(..., description="失敗件数")


# ============================================================================
# 処理関連スキーマ
# ============================================================================

class ProcessingRequest(BaseModel):
    """処理リクエスト"""
    file_ids: List[str] = Field(..., description="処理対象ファイルIDリスト")
    process_type: str = Field("default", description="処理タイプ")
    ocr_engine: Optional[str] = Field(None, description="OCRエンジン指定")
    use_llm: bool = Field(True, description="LLM処理使用フラグ")
    embedding_model: Optional[str] = Field(None, description="埋め込みモデル指定")


class ProcessingStatus(BaseModel):
    """処理ステータス"""
    job_id: str = Field(..., description="ジョブID")
    status: str = Field(..., description="処理ステータス")
    progress: int = Field(..., description="進捗率（0-100）")
    current_file: Optional[str] = Field(None, description="現在処理中のファイル")
    completed_files: int = Field(..., description="完了ファイル数")
    total_files: int = Field(..., description="総ファイル数")
    estimated_remaining_time: Optional[int] = Field(None, description="予想残り時間（秒）")
    error_count: int = Field(0, description="エラー件数")


class ProcessingResponse(BaseResponse):
    """処理開始レスポンス"""
    job_id: str = Field(..., description="ジョブID")
    file_count: int = Field(..., description="処理対象ファイル数")


# ============================================================================
# 設定関連スキーマ
# ============================================================================

class SystemConfig(BaseModel):
    """システム設定"""
    cuda_available: bool = Field(..., description="CUDA利用可能性")
    multimodal_enabled: bool = Field(..., description="マルチモーダル処理有効性")
    llm_model: str = Field(..., description="使用LLMモデル")
    embedding_options: Dict[str, Any] = Field(..., description="埋め込みモデル選択肢")
    supported_extensions: List[str] = Field(..., description="サポート拡張子")
    max_file_size: int = Field(..., description="最大ファイルサイズ")


class ConfigResponse(BaseResponse):
    """設定レスポンス"""
    config: SystemConfig = Field(..., description="システム設定")


# ============================================================================
# エラー関連スキーマ
# ============================================================================

class ErrorResponse(BaseResponse):
    """エラーレスポンス"""
    error_code: Optional[str] = Field(None, description="エラーコード")
    details: Optional[Dict[str, Any]] = Field(None, description="エラー詳細")