# new/config.py
# 新系RAGシステム設定ファイル

import os
import torch
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from typing import Dict, Any

# ============================================================================
# 基本設定
# ============================================================================

# デバッグ・開発モード設定
DEBUG_MODE = True
DEVELOPMENT_MODE = os.getenv("DEVELOPMENT_MODE", "false").lower() == "true"

# GPU・マルチモーダル設定
CUDA_AVAILABLE = torch.cuda.is_available()
MULTIMODAL_ENABLED = CUDA_AVAILABLE
MULTIMODAL_MODEL = "Qwen/Qwen-VL-Chat" if CUDA_AVAILABLE else None

print(f"[config.py] CUDA_AVAILABLE = {CUDA_AVAILABLE}")
print(f"[config.py] MULTIMODAL_ENABLED = {MULTIMODAL_ENABLED}")

# ============================================================================
# LLM設定（Ollama）
# ============================================================================

OLLAMA_BASE = os.getenv("OLLAMA_BASE", "http://ollama:11434")
OLLAMA_MODEL = "gemma3" if CUDA_AVAILABLE else "phi4-mini"
LLM_TIMEOUT = int(os.getenv("LLM_TIMEOUT", "300"))

print(f"[config.py] LLM_MODEL = {OLLAMA_MODEL}")

# ============================================================================
# 処理設定
# ============================================================================

# ファイル処理設定
SUPPORTED_EXTENSIONS = {".pdf", ".txt", ".docx", ".csv", ".json", ".eml", ".png", ".jpg", ".jpeg", ".tiff", ".bmp"}
DEFAULT_OCR_ENGINE = os.getenv("DEFAULT_OCR_ENGINE", "ocrmypdf")
DEFAULT_EMBEDDING_MODELS = ["intfloat-e5-large-v2"]
DEFAULT_QUALITY_THRESHOLD = 0.0

# ============================================================================
# データベース設定
# ============================================================================

# PostgreSQL接続設定
DB_HOST = os.getenv("DB_HOST", "ragdb")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_USER = os.getenv("DB_USER", "raguser")
DB_PASSWORD = os.getenv("DB_PASSWORD", "ragpass")
DB_NAME = os.getenv("DB_NAME", "rag")

# 接続URL構築
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# SQLAlchemyエンジン作成
DB_ENGINE: Engine = create_engine(
    DATABASE_URL,
    echo=DEBUG_MODE,  # デバッグモード時にSQL文を出力
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,  # 接続確認
    pool_recycle=3600,   # 1時間で接続リサイクル
)

print(f"[config.py] Database URL: {DATABASE_URL}")

# ============================================================================
# ファイル処理設定
# ============================================================================

# サポートする拡張子
SUPPORTED_EXTENSIONS = {".txt", ".pdf", ".docx", ".csv", ".json", ".eml"}

# ファイルサイズ制限（100MB）
MAX_FILE_SIZE = 100 * 1024 * 1024

# アップロード一時ディレクトリ
UPLOAD_TEMP_DIR = os.getenv("UPLOAD_TEMP_DIR", "/tmp/rag_uploads")
os.makedirs(UPLOAD_TEMP_DIR, exist_ok=True)

# ============================================================================
# 埋め込みモデル設定
# ============================================================================

EMBEDDING_OPTIONS: Dict[str, Dict[str, Any]] = {
    "1": {
        "name": "intfloat/multilingual-e5-large",
        "description": "多言語対応・高精度",
        "model_path": "intfloat/multilingual-e5-large",
        "dimensions": 1024,
    },
    "2": {
        "name": "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2", 
        "description": "軽量・多言語対応",
        "model_path": "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        "dimensions": 384,
    },
    "3": {
        "name": "cl-tohoku/shioriha-large-pt",
        "description": "日本語特化・高精度",
        "model_path": "cl-tohoku/shioriha-large-pt", 
        "dimensions": 768,
    },
}

# ============================================================================
# ログ設定
# ============================================================================

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

# ============================================================================
# セキュリティ設定
# ============================================================================

SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-this-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# セッション設定
SESSION_COOKIE_NAME = "rag_session"
SESSION_COOKIE_SECURE = False  # HTTPSの場合はTrue
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "lax"

# CORS設定
CORS_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:8000", 
    "http://localhost:8001",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:8000",
    "http://127.0.0.1:8001",
]

# ============================================================================
# API・ディレクトリ設定
# ============================================================================

# API設定
API_PREFIX = "/api"

# ディレクトリ設定
BASE_DIR = Path(__file__).parent
STATIC_DIR = BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR / "templates" 

# 入出力ディレクトリ
INPUT_DIR = Path("ignored/input_files")
OUTPUT_DIR = Path("ignored/output_files")

# ディレクトリ作成
INPUT_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ============================================================================
# ログ設定
# ============================================================================

import logging

# ロガー設定
LOGGER = logging.getLogger("rag_system")
LOGGER.setLevel(getattr(logging, LOG_LEVEL))

# ハンドラー設定
if not LOGGER.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    LOGGER.addHandler(handler)