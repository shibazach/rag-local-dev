# REM: config.py @2024-12-19
# REM: アプリケーション設定統一管理（Pydantic BaseSettings採用）

# ── 標準ライブラリ ──
import os
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any

# ── サードパーティ ──
from pydantic import Field
from pydantic_settings import BaseSettings

# ──────────────────────────────────────────────────────────
# 設定クラス定義（Pydantic BaseSettings）
# ──────────────────────────────────────────────────────────
class Settings(BaseSettings):
    """アプリケーション設定（環境変数とデフォルト値の統合管理）"""
    
    # ──── デバッグ・開発設定 ────
    DEBUG_MODE: bool = Field(True, description="デバッグモード有効化")
    DEBUG_PRINT_ENABLED: bool = Field(True, description="デバッグ出力有効化")
    DEVELOPMENT_MODE: bool = Field(True, description="開発モード有効化")
    
    # ──── データベース設定 ────
    DATABASE_URL: str = Field(
        "sqlite:///./new_rag.db",
        description="SQLite接続URL（開発環境用）"
    )
    
    # ──── LLM・AI設定 ────
    LLM_MODEL: str = Field("phi4-mini", description="使用LLMモデル名")
    OLLAMA_MODEL: str = Field("phi4-mini", description="Ollama使用モデル名")
    LLM_TIMEOUT: int = Field(300, description="LLMタイムアウト秒数")
    OLLAMA_BASE_URL: str = Field(
        default_factory=lambda: os.getenv("OLLAMA_BASE_URL", "http://ollama:11434"),
        description="Ollama API URL"
    )
    
    # ──── ファイル・OCR設定 ────
    DEFAULT_OCR_ENGINE: str = Field("ocrmypdf", description="デフォルトOCRエンジン")
    SUPPORTED_EXTENSIONS: List[str] = Field(
        [".pdf", ".docx", ".txt", ".csv", ".json", ".eml"],
        description="サポート対象ファイル拡張子"
    )
    MAX_FILE_SIZE: int = Field(100 * 1024 * 1024, description="最大ファイルサイズ（バイト）")
    UPLOAD_TEMP_DIR: Optional[str] = Field(None, description="アップロード一時ディレクトリ")
    
    # ──── 埋め込み・ベクトル設定 ────
    DEFAULT_EMBEDDING_MODELS: List[str] = Field(
        ["intfloat/e5-large-v2"],
        description="デフォルト埋め込みモデル"
    )
    DEFAULT_QUALITY_THRESHOLD: float = Field(0.7, description="品質スコア閾値")
    
    # ──── 埋め込みオプション設定（OLD系互換） ────
    EMBEDDING_OPTIONS: Dict[str, Dict[str, Any]] = Field(
        {
            "1": {
                "embedder": "SentenceTransformer",
                "model_name": "intfloat/e5-large-v2",
                "dimension": 1024
            },
            "2": {
                "embedder": "SentenceTransformer",
                "model_name": "intfloat/e5-small-v2",
                "dimension": 384
            },
            "3": {
                "embedder": "OllamaEmbeddings",
                "model_name": "nomic-embed-text",
                "dimension": 768
            }
        },
        description="埋め込みモデルオプション"
    )
    DEFAULT_EMBEDDING_OPTION: str = Field("1", description="デフォルト埋め込みオプション")
    
    # ──── パス設定 ────
    BASE_DIR: Path = Field(Path(__file__).parent, description="アプリケーションベースディレクトリ")
    
    @property
    def INPUT_DIR(self) -> Path:
        """入力ファイルディレクトリ"""
        path = self.BASE_DIR / "ignored/input_files"
        path.mkdir(parents=True, exist_ok=True)
        return path
    
    @property 
    def OUTPUT_DIR(self) -> Path:
        """出力ファイルディレクトリ"""
        path = self.BASE_DIR / "ignored/output_files"
        path.mkdir(parents=True, exist_ok=True)
        return path
    
    @property
    def STATIC_DIR(self) -> Path:
        """静的ファイルディレクトリ"""
        return self.BASE_DIR / "static"
    
    @property
    def TEMPLATES_DIR(self) -> Path:
        """テンプレートディレクトリ"""
        return self.BASE_DIR / "templates"
    
    # ──── セキュリティ設定 ────
    SECRET_KEY: str = Field(
        "your-secret-key-change-in-production",
        description="セッション暗号化キー"
    )
    SESSION_COOKIE_NAME: str = Field("rag_session", description="セッションクッキー名")
    SESSION_COOKIE_SECURE: bool = Field(False, description="セキュアクッキー使用")
    SESSION_COOKIE_HTTPONLY: bool = Field(True, description="HTTPOnlyクッキー使用")
    SESSION_COOKIE_SAMESITE: str = Field("lax", description="SameSiteクッキー設定")
    
    # ──── API設定 ────
    API_PREFIX: str = Field("/api", description="API URLプレフィックス")
    CORS_ORIGINS: List[str] = Field(
        ["http://localhost:8000", "http://127.0.0.1:8000"],
        description="CORS許可オリジン"
    )
    
    # ──── ハードウェア設定 ────
    @property
    def CUDA_AVAILABLE(self) -> bool:
        """CUDA利用可能性"""
        try:
            import torch
            return torch.cuda.is_available()
        except ImportError:
            return False
    
    @property
    def MULTIMODAL_ENABLED(self) -> bool:
        """マルチモーダル機能有効性"""
        return self.CUDA_AVAILABLE
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# ──────────────────────────────────────────────────────────
# 設定インスタンス（シングルトン）
# ──────────────────────────────────────────────────────────
settings = Settings()

# ──────────────────────────────────────────────────────────
# 後方互換性のための別名定義
# ──────────────────────────────────────────────────────────
DEBUG_MODE = settings.DEBUG_MODE
DEBUG_PRINT_ENABLED = settings.DEBUG_PRINT_ENABLED
DEVELOPMENT_MODE = settings.DEVELOPMENT_MODE
DATABASE_URL = settings.DATABASE_URL
LLM_MODEL = settings.LLM_MODEL
LLM_TIMEOUT = settings.LLM_TIMEOUT
DEFAULT_OCR_ENGINE = settings.DEFAULT_OCR_ENGINE
SUPPORTED_EXTENSIONS = settings.SUPPORTED_EXTENSIONS
MAX_FILE_SIZE = settings.MAX_FILE_SIZE
UPLOAD_TEMP_DIR = settings.UPLOAD_TEMP_DIR
DEFAULT_EMBEDDING_MODELS = settings.DEFAULT_EMBEDDING_MODELS
DEFAULT_QUALITY_THRESHOLD = settings.DEFAULT_QUALITY_THRESHOLD
EMBEDDING_OPTIONS = settings.EMBEDDING_OPTIONS
DEFAULT_EMBEDDING_OPTION = settings.DEFAULT_EMBEDDING_OPTION
BASE_DIR = settings.BASE_DIR
INPUT_DIR = settings.INPUT_DIR
OUTPUT_DIR = settings.OUTPUT_DIR
STATIC_DIR = settings.STATIC_DIR
TEMPLATES_DIR = settings.TEMPLATES_DIR
SECRET_KEY = settings.SECRET_KEY
SESSION_COOKIE_NAME = settings.SESSION_COOKIE_NAME
SESSION_COOKIE_SECURE = settings.SESSION_COOKIE_SECURE
SESSION_COOKIE_HTTPONLY = settings.SESSION_COOKIE_HTTPONLY
SESSION_COOKIE_SAMESITE = settings.SESSION_COOKIE_SAMESITE
API_PREFIX = settings.API_PREFIX
CORS_ORIGINS = settings.CORS_ORIGINS
CUDA_AVAILABLE = settings.CUDA_AVAILABLE
MULTIMODAL_ENABLED = settings.MULTIMODAL_ENABLED

# ──────────────────────────────────────────────────────────
# ロガー設定
# ──────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.DEBUG if DEBUG_MODE else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
LOGGER = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────
# SQLAlchemy エンジン設定
# ──────────────────────────────────────────────────────────
try:
    from sqlalchemy import create_engine
    DB_ENGINE = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_recycle=300,
        echo=False  # SQLログを無効化（パフォーマンス重視）
    )
except ImportError:
    LOGGER.warning("SQLAlchemy未インストール: DB_ENGINEは使用不可")
    DB_ENGINE = None

# ──────────────────────────────────────────────────────────
# グローバル変数として公開（後方互換性）
# ──────────────────────────────────────────────────────────
OLLAMA_MODEL = settings.OLLAMA_MODEL
OLLAMA_BASE = settings.OLLAMA_BASE_URL

# ──────────────────────────────────────────────────────────
# 初期化確認ログ
# ──────────────────────────────────────────────────────────
if DEBUG_PRINT_ENABLED:
    print(f"[config.py] LLM_MODEL = {LLM_MODEL}")
    print(f"[config.py] CUDA_AVAILABLE = {CUDA_AVAILABLE}")
    print(f"[config.py] MULTIMODAL_ENABLED = {MULTIMODAL_ENABLED}")
    print(f"[config.py] Database URL: {DATABASE_URL}")