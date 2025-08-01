# REM: schemas.py @2024-12-19  
# REM: Pydantic型定義統一管理（API入出力・データベースモデル）

# ── 標準ライブラリ ──
from datetime import datetime
from typing import Optional, List, Dict, Any, Union
from uuid import UUID

# ── サードパーティ ──
from pydantic import BaseModel, Field, validator

# ──────────────────────────────────────────────────────────
# 認証・ユーザー関連スキーマ
# ──────────────────────────────────────────────────────────

class UserBase(BaseModel):
    """ユーザー基底スキーマ"""
    username: str = Field(..., min_length=1, max_length=50, description="ユーザー名")
    email: Optional[str] = Field(None, description="メールアドレス")

class UserLogin(BaseModel):
    """ログインリクエストスキーマ"""
    username: str = Field(..., description="ユーザー名")
    password: str = Field(..., description="パスワード")

class UserResponse(UserBase):
    """ユーザーレスポンススキーマ"""
    id: int = Field(..., description="ユーザーID")
    role: str = Field(..., description="ユーザーロール")
    created_at: Optional[datetime] = Field(None, description="作成日時")

class UserSession(BaseModel):
    """セッション用ユーザー情報"""
    id: int
    username: str
    role: str
    email: Optional[str] = None

# ──────────────────────────────────────────────────────────
# ファイル関連スキーマ
# ──────────────────────────────────────────────────────────

class FileBase(BaseModel):
    """ファイル基底スキーマ"""
    filename: str = Field(..., description="ファイル名")
    file_path: Optional[str] = Field(None, description="ファイルパス")

class FileCreate(FileBase):
    """ファイル作成スキーマ"""
    checksum: Optional[str] = Field(None, description="チェックサム")
    size: Optional[int] = Field(None, description="ファイルサイズ")

class FileResponse(FileBase):
    """ファイルレスポンススキーマ"""
    id: UUID = Field(..., description="ファイルID")
    status: str = Field(..., description="処理ステータス")
    created_at: datetime = Field(..., description="作成日時")
    updated_at: Optional[datetime] = Field(None, description="更新日時")
    checksum: Optional[str] = Field(None, description="チェックサム")
    size: Optional[int] = Field(None, description="ファイルサイズ")

class FileListResponse(BaseModel):
    """ファイル一覧レスポンススキーマ"""
    files: List[FileResponse]
    total: int = Field(..., description="総件数")
    page: int = Field(..., description="現在ページ")
    per_page: int = Field(..., description="1ページあたり件数")

class FileStatusUpdate(BaseModel):
    """ファイルステータス更新スキーマ"""
    status: str = Field(..., description="新しいステータス")
    message: Optional[str] = Field(None, description="更新メッセージ")

class UploadResponse(BaseModel):
    """アップロードレスポンススキーマ"""
    success: bool = Field(..., description="成功フラグ")
    file_id: Optional[UUID] = Field(None, description="アップロードされたファイルID")
    filename: str = Field(..., description="ファイル名")
    message: str = Field(..., description="メッセージ")

class BatchUploadResponse(BaseModel):
    """バッチアップロードレスポンススキーマ"""
    success: bool = Field(..., description="成功フラグ")
    uploaded_files: List[UploadResponse] = Field([], description="アップロードされたファイル一覧")
    failed_files: List[str] = Field([], description="失敗したファイル一覧")
    message: str = Field(..., description="メッセージ")

# ──────────────────────────────────────────────────────────
# 処理関連スキーマ
# ──────────────────────────────────────────────────────────

class ProcessingConfig(BaseModel):
    """処理設定スキーマ"""
    llm_model: str = Field(..., description="LLMモデル名")
    ocr_engine: str = Field(..., description="OCRエンジン名")
    embedding_model: str = Field(..., description="埋め込みモデル名")
    quality_threshold: float = Field(0.7, ge=0.0, le=1.0, description="品質閾値")

class ProcessingRequest(BaseModel):
    """処理リクエストスキーマ"""
    file_ids: List[UUID] = Field(..., description="処理対象ファイルID一覧")
    config: ProcessingConfig = Field(..., description="処理設定")
    save_to_db: bool = Field(True, description="データベース保存フラグ")

class ProcessingProgress(BaseModel):
    """処理進捗スキーマ"""
    file_id: UUID = Field(..., description="ファイルID")
    filename: str = Field(..., description="ファイル名")
    step: str = Field(..., description="処理ステップ")
    progress: float = Field(..., ge=0.0, le=1.0, description="進捗率")
    is_complete: bool = Field(False, description="完了フラグ")
    error: Optional[str] = Field(None, description="エラーメッセージ")

class ProcessingResult(BaseModel):
    """処理結果スキーマ"""
    success: bool = Field(..., description="成功フラグ")
    file_id: UUID = Field(..., description="ファイルID")
    ocr_text: Optional[str] = Field(None, description="OCR抽出テキスト")
    llm_refined_text: Optional[str] = Field(None, description="LLM整形テキスト")
    quality_score: Optional[float] = Field(None, description="品質スコア")
    elapsed_time: Optional[float] = Field(None, description="処理時間（秒）")
    error: Optional[str] = Field(None, description="エラーメッセージ")

# ──────────────────────────────────────────────────────────
# OCR比較関連スキーマ
# ──────────────────────────────────────────────────────────

class OCREngine(BaseModel):
    """OCRエンジン情報スキーマ"""
    id: str = Field(..., description="エンジンID")
    name: str = Field(..., description="エンジン名")
    description: str = Field(..., description="説明")
    is_available: bool = Field(..., description="利用可能フラグ")

class OCRComparisonRequest(BaseModel):
    """OCR比較リクエストスキーマ"""
    file_id: UUID = Field(..., description="対象ファイルID")
    engines: List[str] = Field(..., description="比較対象エンジン一覧")
    apply_correction: bool = Field(True, description="テキスト補正適用フラグ")

class OCRComparisonResult(BaseModel):
    """OCR比較結果スキーマ"""
    engine_id: str = Field(..., description="エンジンID")
    engine_name: str = Field(..., description="エンジン名")
    extracted_text: str = Field(..., description="抽出テキスト")
    corrected_text: Optional[str] = Field(None, description="補正後テキスト")
    corrections: List[Dict[str, Any]] = Field([], description="補正内容一覧")
    processing_time: float = Field(..., description="処理時間（秒）")
    success: bool = Field(..., description="成功フラグ")
    error: Optional[str] = Field(None, description="エラーメッセージ")

# ──────────────────────────────────────────────────────────
# 共通レスポンススキーマ
# ──────────────────────────────────────────────────────────

class SuccessResponse(BaseModel):
    """成功レスポンス基底スキーマ"""
    status: str = Field("success", description="ステータス")
    message: str = Field(..., description="メッセージ")
    data: Optional[Any] = Field(None, description="データ")

class ErrorResponse(BaseModel):
    """エラーレスポンススキーマ"""
    status: str = Field("error", description="ステータス")
    message: str = Field(..., description="エラーメッセージ")
    detail: Optional[str] = Field(None, description="詳細情報")
    error_code: Optional[str] = Field(None, description="エラーコード")

# ──────────────────────────────────────────────────────────
# Pydantic v2 設定
# ──────────────────────────────────────────────────────────

# 全スキーマでORM互換性を有効化（Pydantic v2形式）
UserResponse.model_config = {"from_attributes": True}
FileResponse.model_config = {"from_attributes": True}
ProcessingResult.model_config = {"from_attributes": True}
OCRComparisonResult.model_config = {"from_attributes": True}
SuccessResponse.model_config = {"from_attributes": True}
ErrorResponse.model_config = {"from_attributes": True}