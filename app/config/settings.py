"""
基本設定モジュール - Prototype系統合版
app系のエンタープライズ設定 + OLD系の実績ある設定を統合
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
PROTOTYPES_ROOT = PROJECT_ROOT / "prototypes"

class BaseConfig(BaseSettings):
    """統合基本設定クラス"""
    
    # アプリケーション基本情報
    APP_NAME: str = "R&D RAGシステム"
    APP_VERSION: str = "2.0.0"  # prototype統合版
    APP_DESCRIPTION: str = "Enterprise RAG System with NiceGUI - Integrated Edition"
    
    # 環境設定
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = os.getenv("DEBUG", "True").lower() == "true"
    
    # サーバー設定
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8081"))
    
    # セキュリティ
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
    SESSION_SECRET_KEY: str = os.getenv("SESSION_SECRET_KEY", SECRET_KEY)
    ALLOWED_HOSTS: List[str] = ["localhost", "127.0.0.1", "0.0.0.0"]
    
    # データベース（PostgreSQL + pgvector）
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://raguser:ragpass@ragdb:5432/rag")
    
    # API設定
    API_V1_PREFIX: str = "/api/v1"
    API_DOCS_URL: str = "/docs"
    API_REDOC_URL: str = "/redoc"
    
    # 認証設定
    SESSION_COOKIE_NAME: str = "rag_session"
    SESSION_COOKIE_MAX_AGE: int = 3600 * 24 * 7  # 7日間
    SESSION_COOKIE_SECURE: bool = ENVIRONMENT == "production"
    SESSION_COOKIE_HTTPONLY: bool = True
    SESSION_COOKIE_SAMESITE: str = "lax"
    
    # ファイルアップロード
    UPLOAD_DIR: Path = PROJECT_ROOT / "data" / "uploads"
    PROCESSED_DIR: Path = PROJECT_ROOT / "data" / "processed"
    MAX_UPLOAD_SIZE: int = 100 * 1024 * 1024  # 100MB
    # OLD系の実績ある拡張子リスト
    ALLOWED_EXTENSIONS: List[str] = [
        ".pdf", ".docx", ".txt", ".csv", ".json", ".eml",
        ".png", ".jpg", ".jpeg"  # OCR対応画像形式追加
    ]
    
    # GPU/CPU環境判定（OLD系方式）
    @property
    def CUDA_AVAILABLE(self) -> bool:
        """CUDA利用可能性チェック"""
        try:
            import torch
            return torch.cuda.is_available()
        except ImportError:
            return False
    
    # 外部サービス（OLD系実績設定）
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")
    
    @property
    def OLLAMA_MODEL(self) -> str:
        """環境に応じたモデル自動選択"""
        if self.CUDA_AVAILABLE:
            return os.getenv("OLLAMA_MODEL", "gemma:7b")
        else:
            return os.getenv("OLLAMA_MODEL", "phi4-mini")
    
    OLLAMA_TIMEOUT: int = 300
    
    # NiceGUI設定
    NICEGUI_MOUNT_PATH: str = "/ui"
    NICEGUI_TITLE: str = "R&D RAGシステム"
    NICEGUI_FAVICON: Optional[str] = None
    NICEGUI_DARK_MODE: Optional[bool] = None
    
    # ログ設定
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_DIR: Path = PROJECT_ROOT / "data" / "logs"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # CORS設定
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
        "http://localhost:8080",
        "http://localhost:8081",
        "http://127.0.0.1:8000",
        "http://127.0.0.1:8080",
        "http://127.0.0.1:8081"
    ]
    
    # 埋め込みモデル設定（OLD系の実績設定）
    EMBEDDING_OPTIONS: Dict[str, Dict[str, Any]] = {
        "1": {
            "embedder": "SentenceTransformer",
            "model_name": "intfloat/e5-large-v2",  # GPU環境用（高精度）
            "dimension": 1024
        },
        "2": {
            "embedder": "SentenceTransformer", 
            "model_name": "intfloat/e5-small-v2",  # CPU環境用（軽量）
            "dimension": 384
        },
        "3": {
            "embedder": "OllamaEmbeddings",
            "model_name": "nomic-embed-text",
            "dimension": 768
        }
    }
    
    @property
    def DEFAULT_EMBEDDING_OPTION(self) -> str:
        """環境に応じた埋め込みモデル自動選択"""
        if self.CUDA_AVAILABLE:
            return "1"  # GPU環境ではe5-large
        else:
            return "2"  # CPU環境ではe5-small
    
    # OCR設定（OLD系準拠）
    DEFAULT_OCR_ENGINE: str = "ocrmypdf"
    OCR_LANGUAGE: str = "jpn+eng"  # 日本語+英語
    OCR_DPI: int = 300
    OCR_OPTIMIZE: int = 2  # 0-3（圧縮レベル）
    
    # チャンク設定（OLD系実績値）
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200
    
    # 処理設定
    BATCH_SIZE: int = 10
    MAX_WORKERS: int = 4
    
    @field_validator("UPLOAD_DIR", "PROCESSED_DIR", "LOG_DIR", mode="before")
    @classmethod
    def create_directories(cls, v):
        """ディレクトリが存在しない場合は作成"""
        if isinstance(v, str):
            v = Path(v)
        v.mkdir(parents=True, exist_ok=True)
        return v
    
    # プロンプトディレクトリ（OLD系から移植予定）
    PROMPT_DIR: Path = PROTOTYPES_ROOT / "prompts"
    
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
            config.LOG_DIR / "prototypes.log",
            encoding="utf-8"
        )
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(config.LOG_FORMAT)
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    return logger

# デフォルトロガー
logger = setup_logger()

# 環境別設定のロード関数
def get_config() -> BaseConfig:
    """環境に応じた設定を返す"""
    return config

# 設定情報の表示（デバッグ用）
def print_config():
    """現在の設定を表示"""
    logger.info("=" * 50)
    logger.info(f"Environment: {config.ENVIRONMENT}")
    logger.info(f"Debug Mode: {config.DEBUG}")
    logger.info(f"CUDA Available: {config.CUDA_AVAILABLE}")
    logger.info(f"Ollama Model: {config.OLLAMA_MODEL}")
    logger.info(f"Embedding Option: {config.DEFAULT_EMBEDDING_OPTION}")
    logger.info(f"Database: {config.DATABASE_URL}")
    logger.info("=" * 50)