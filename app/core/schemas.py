"""
Pydantic スキーマ定義
API request/response models and data validation
"""

from datetime import datetime
from typing import Optional, List, Dict, Any, Union
from uuid import UUID
from pydantic import BaseModel, Field, field_validator
from typing import Annotated

# EmailStr を使わずに通常の文字列で代用（開発時）
EmailStr = str

# ========== 共通ベーススキーマ ==========

class BaseResponse(BaseModel):
    """レスポンス基底クラス"""
    success: bool = Field(..., description="成功フラグ")
    message: Optional[str] = Field(None, description="メッセージ")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="レスポンス時刻")

class PaginatedResponse(BaseModel):
    """ページネーション付きレスポンス"""
    total: int = Field(..., description="総件数")
    page: int = Field(..., description="現在ページ")
    per_page: int = Field(..., description="1ページあたり件数")
    total_pages: int = Field(..., description="総ページ数")

# ========== 認証・ユーザー関連スキーマ ==========

class UserBase(BaseModel):
    """ユーザー基底スキーマ"""
    username: str = Field(..., min_length=3, max_length=50, description="ユーザー名")
    email: EmailStr = Field(..., description="メールアドレス")
    display_name: Optional[str] = Field(None, max_length=100, description="表示名")
    department: Optional[str] = Field(None, max_length=100, description="部署")

class UserCreate(UserBase):
    """ユーザー作成スキーマ"""
    password: str = Field(..., min_length=8, description="パスワード")
    role: str = Field("user", description="ユーザーロール")
    
    @field_validator('password', mode='before')
    @classmethod
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('パスワードは8文字以上である必要があります')
        return v

class UserUpdate(BaseModel):
    """ユーザー更新スキーマ"""
    display_name: Optional[str] = Field(None, max_length=100)
    department: Optional[str] = Field(None, max_length=100)
    role: Optional[str] = Field(None)
    is_active: Optional[bool] = Field(None)

class UserLogin(BaseModel):
    """ログインリクエストスキーマ"""
    username: str = Field(..., description="ユーザー名")
    password: str = Field(..., description="パスワード")
    remember_me: bool = Field(False, description="ログイン状態保持")

class UserResponse(UserBase):
    """ユーザーレスポンススキーマ"""
    id: UUID = Field(..., description="ユーザーID")
    role: str = Field(..., description="ユーザーロール")
    is_active: bool = Field(..., description="アクティブフラグ")
    is_admin: bool = Field(..., description="管理者フラグ")
    created_at: datetime = Field(..., description="作成日時")
    last_login_at: Optional[datetime] = Field(None, description="最終ログイン日時")
    
    class Config:
        from_attributes = True

class AuthResponse(BaseResponse):
    """認証レスポンススキーマ"""
    user: Optional[UserResponse] = Field(None, description="ユーザー情報")
    session_id: Optional[str] = Field(None, description="セッションID")

# ========== ファイル関連スキーマ ==========

class FileBase(BaseModel):
    """ファイル基底スキーマ"""
    original_filename: str = Field(..., description="元ファイル名")
    file_name: str = Field(..., description="保存ファイル名")

class FileUpload(BaseModel):
    """ファイルアップロードスキーマ"""
    filename: str = Field(..., description="ファイル名")
    content_type: str = Field(..., description="MIMEタイプ")
    size: int = Field(..., gt=0, description="ファイルサイズ")

class FileResponse(FileBase):
    """ファイルレスポンススキーマ"""
    id: UUID = Field(..., description="ファイルID")
    mime_type: str = Field(..., description="MIMEタイプ")
    file_size: int = Field(..., description="ファイルサイズ")
    processing_status: str = Field(..., description="処理ステータス")
    processing_stage: str = Field(..., description="処理段階")
    created_at: datetime = Field(..., description="作成日時")
    updated_at: datetime = Field(..., description="更新日時")
    processed_at: Optional[datetime] = Field(None, description="処理完了日時")
    
    # 計算プロパティ
    is_processed: bool = Field(..., description="処理完了フラグ")
    page_count: Optional[int] = Field(None, description="ページ数")
    
    class Config:
        from_attributes = True

class FileListResponse(PaginatedResponse):
    """ファイル一覧レスポンススキーマ"""
    files: List[FileResponse] = Field(..., description="ファイル一覧")

class FileTextResponse(BaseModel):
    """ファイルテキストレスポンススキーマ"""
    blob_id: UUID = Field(..., description="ファイルID")
    raw_text: Optional[str] = Field(None, description="生テキスト")
    refined_text: Optional[str] = Field(None, description="精緻化テキスト")
    quality_score: float = Field(..., description="品質スコア")
    confidence_score: float = Field(..., description="信頼度スコア")
    language: str = Field(..., description="言語")
    word_count: int = Field(..., description="単語数")
    character_count: int = Field(..., description="文字数")
    
    class Config:
        from_attributes = True

class UploadResponse(BaseResponse):
    """アップロードレスポンススキーマ"""
    file_id: Optional[UUID] = Field(None, description="ファイルID")
    filename: str = Field(..., description="ファイル名")
    size: int = Field(..., description="ファイルサイズ")
    checksum: str = Field(..., description="チェックサム")

class BatchUploadResponse(BaseResponse):
    """バッチアップロードレスポンススキーマ"""
    uploaded_files: List[UploadResponse] = Field([], description="成功ファイル")
    failed_files: List[str] = Field([], description="失敗ファイル")
    total_uploaded: int = Field(..., description="アップロード成功数")
    total_failed: int = Field(..., description="失敗数")

# エイリアス
FileUploadResponse = UploadResponse

# ========== 処理関連スキーマ ==========

class ProcessingConfig(BaseModel):
    """処理設定スキーマ（実際の設定に準拠）"""
    llm_model: str = Field("phi4-mini", description="LLMモデル名（CPU:phi4-mini, GPU:gemma:7b）")
    ocr_engine: str = Field("ocrmypdf", description="OCRエンジン名")
    embedding_model: str = Field("intfloat/e5-large-v2", description="埋め込みモデル名")
    embedding_option: str = Field("1", description="埋め込みオプション（1:e5-large, 2:e5-small, 3:nomic）")
    quality_threshold: float = Field(0.7, ge=0.0, le=1.0, description="品質閾値")
    chunk_size: int = Field(1000, gt=0, le=4000, description="チャンクサイズ")
    chunk_overlap: int = Field(200, ge=0, le=500, description="チャンクオーバーラップ")

class ProcessingRequest(BaseModel):
    """処理リクエストスキーマ"""
    file_ids: List[UUID] = Field(..., min_items=1, description="処理対象ファイルID一覧")
    config: Optional[ProcessingConfig] = Field(None, description="処理設定")
    priority: int = Field(1, ge=1, le=10, description="優先度")

class ProcessingStatus(BaseModel):
    """処理ステータススキーマ"""
    file_id: UUID = Field(..., description="ファイルID")
    status: str = Field(..., description="ステータス")
    stage: str = Field(..., description="処理段階")
    progress: float = Field(0.0, ge=0.0, le=100.0, description="進捗率")
    message: Optional[str] = Field(None, description="メッセージ")
    estimated_remaining: Optional[int] = Field(None, description="推定残り時間（秒）")

class ProcessingEvent(BaseModel):
    """処理イベントスキーマ（SSE用）"""
    event_type: str = Field(..., description="イベントタイプ")
    file_id: Optional[UUID] = Field(None, description="ファイルID")
    data: Dict[str, Any] = Field(..., description="イベントデータ")
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class ProcessingResponse(BaseModel):
    """処理レスポンススキーマ"""
    task_id: str = Field(..., description="タスクID")
    status: str = Field(..., description="ステータス")
    message: str = Field(..., description="メッセージ")
    file_count: int = Field(..., description="処理ファイル数")
    started_at: datetime = Field(default_factory=datetime.utcnow)

# ========== 検索関連スキーマ ==========

class SearchRequest(BaseModel):
    """検索リクエストスキーマ"""
    query: str = Field(..., min_length=1, max_length=1000, description="検索クエリ")
    search_type: str = Field("semantic", description="検索タイプ")
    limit: int = Field(10, ge=1, le=100, description="結果件数")
    min_score: float = Field(0.0, ge=0.0, le=1.0, description="最小スコア")
    file_ids: Optional[List[UUID]] = Field(None, description="検索対象ファイルID")
    filters: Optional[Dict[str, Any]] = Field(None, description="フィルター条件")

class SearchResult(BaseModel):
    """検索結果スキーマ"""
    file_id: UUID = Field(..., description="ファイルID")
    filename: str = Field(..., description="ファイル名")
    chunk_text: str = Field(..., description="マッチしたテキスト")
    score: float = Field(..., description="スコア")
    metadata: Dict[str, Any] = Field(..., description="メタデータ")

class SearchResponse(BaseResponse):
    """検索レスポンススキーマ"""
    results: List[SearchResult] = Field(..., description="検索結果")
    total_found: int = Field(..., description="総マッチ数")
    search_time: float = Field(..., description="検索時間（秒）")
    query: str = Field(..., description="検索クエリ")

# ========== チャット関連スキーマ ==========

class ChatMessage(BaseModel):
    """チャットメッセージスキーマ"""
    role: str = Field(..., description="メッセージロール")  # user, assistant, system
    content: str = Field(..., description="メッセージ内容")
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class ChatRequest(BaseModel):
    """チャットリクエストスキーマ"""
    message: str = Field(..., min_length=1, max_length=2000, description="ユーザーメッセージ")
    conversation_id: Optional[UUID] = Field(None, description="会話ID")
    search_config: Optional[SearchRequest] = Field(None, description="検索設定")
    llm_config: Optional[Dict[str, Any]] = Field(None, description="LLM設定")

class ChatResponse(BaseResponse):
    """チャットレスポンススキーマ"""
    conversation_id: UUID = Field(..., description="会話ID")
    response: str = Field(..., description="アシスタント応答")
    sources: List[SearchResult] = Field([], description="参照ソース")
    response_time: float = Field(..., description="応答時間（秒）")

# ========== システム関連スキーマ ==========

class HealthCheck(BaseModel):
    """ヘルスチェックスキーマ"""
    status: str = Field(..., description="ステータス")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    version: str = Field(..., description="バージョン")
    components: Dict[str, str] = Field(..., description="コンポーネント状態")

class SystemStats(BaseModel):
    """システム統計スキーマ"""
    total_files: int = Field(..., description="総ファイル数")
    processed_files: int = Field(..., description="処理済みファイル数")
    total_users: int = Field(..., description="総ユーザー数")
    active_sessions: int = Field(..., description="アクティブセッション数")
    storage_used: int = Field(..., description="使用ストレージ（bytes）")
    last_updated: datetime = Field(..., description="最終更新日時")

class ErrorResponse(BaseModel):
    """エラーレスポンススキーマ"""
    success: bool = Field(False, description="成功フラグ")
    error_code: str = Field(..., description="エラーコード")
    error_message: str = Field(..., description="エラーメッセージ")
    details: Optional[Dict[str, Any]] = Field(None, description="詳細情報")
    timestamp: datetime = Field(default_factory=datetime.utcnow)