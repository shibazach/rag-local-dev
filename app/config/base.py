"""
基本設定モジュール
Environment-agnostic base configuration
"""

import os
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any
try:
    from pydantic_settings import BaseSettings
    from pydantic import field_validator
except ImportError:
    # Fallback for older pydantic versions
    from pydantic import BaseSettings, validator as field_validator

# プロジェクトルート
PROJECT_ROOT = Path(__file__).parent.parent.parent
APP_ROOT = PROJECT_ROOT / "app"

class BaseConfig(BaseSettings):
    """基本設定クラス"""
    
    # アプリケーション基本情報
    APP_NAME: str = "R&D RAGシステム"
    APP_VERSION: str = "1.0.0"
    APP_DESCRIPTION: str = "Enterprise RAG System with NiceGUI"
    
    # 環境設定
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # セキュリティ
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
    SESSION_SECRET_KEY: str = os.getenv("SESSION_SECRET_KEY", SECRET_KEY)
    ALLOWED_HOSTS: List[str] = ["localhost", "127.0.0.1", "0.0.0.0"]
    
    # データベース
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./data/rag_system.db")
    
    # API設定
    API_V1_PREFIX: str = "/api/v1"
    API_DOCS_URL: str = "/docs"
    API_REDOC_URL: str = "/redoc"
    
    # 認証設定
    SESSION_COOKIE_NAME: str = "rag_session"
    SESSION_COOKIE_MAX_AGE: int = 3600 * 24 * 7  # 7日間
    SESSION_COOKIE_SECURE: bool = False  # HTTPS環境ではTrue
    SESSION_COOKIE_HTTPONLY: bool = True
    SESSION_COOKIE_SAMESITE: str = "lax"
    
    # ファイルアップロード
    UPLOAD_DIR: Path = PROJECT_ROOT / "data" / "uploads"
    PROCESSED_DIR: Path = PROJECT_ROOT / "data" / "processed"
    MAX_UPLOAD_SIZE: int = 100 * 1024 * 1024  # 100MB
    # OLD/系の実際のサポート拡張子に準拠
    ALLOWED_EXTENSIONS: List[str] = [".pdf", ".docx", ".txt", ".csv", ".json", ".eml"]
    
    # 外部サービス（実際の設定に基づく）
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")
    # CUDA環境でgemma:7b、CPU環境でphi4-mini（OLD/系と同様）
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "gemma:7b" if os.getenv("CUDA_AVAILABLE") == "true" else "phi4-mini")
    OLLAMA_TIMEOUT: int = 300
    
    # NiceGUI設定
    NICEGUI_MOUNT_PATH: str = "/ui"
    NICEGUI_TITLE: str = "R&D RAGシステム"
    
    # ログ設定
    LOG_LEVEL: str = "INFO"
    LOG_DIR: Path = PROJECT_ROOT / "data" / "logs"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # CORS設定
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000"
    ]
    
    @field_validator("UPLOAD_DIR", "PROCESSED_DIR", "LOG_DIR", mode="before")
    @classmethod
    def create_directories(cls, v):
        """ディレクトリが存在しない場合は作成"""
        if isinstance(v, str):
            v = Path(v)
        v.mkdir(parents=True, exist_ok=True)
        return v
    
    # 埋め込みモデル設定（OLD/系の実際の設定に準拠）
    EMBEDDING_OPTIONS: Dict[str, Dict[str, Any]] = {
        "1": {
            "embedder": "SentenceTransformer",
            "model_name": "intfloat/e5-large-v2",  # GPU環境用（本番）
            "dimension": 1024
        },
        "2": {
            "embedder": "SentenceTransformer", 
            "model_name": "intfloat/e5-small-v2",  # CPU環境用（開発）
            "dimension": 384
        },
        "3": {
            "embedder": "OllamaEmbeddings",
            "model_name": "nomic-embed-text",
            "dimension": 768
        }
    }
    DEFAULT_EMBEDDING_OPTION: str = "1"  # e5を優先（OLD/系と同様）
    
    # OCR設定（OLD/系準拠）
    DEFAULT_OCR_ENGINE: str = "ocrmypdf"
    
    model_config = {"env_file": ".env", "case_sensitive": True}

# 設定インスタンス
config = BaseConfig()

# ロガー設定
def setup_logger(name: str = "rag_system") -> logging.Logger:
    """統一ロガー設定"""
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, config.LOG_LEVEL))
    
    if not logger.handlers:
        # コンソールハンドラー
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(config.LOG_FORMAT)
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
        
        # ファイルハンドラー
        file_handler = logging.FileHandler(
            config.LOG_DIR / "app.log",
            encoding="utf-8"
        )
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(config.LOG_FORMAT)
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    return logger

# デフォルトロガー
logger = setup_logger()