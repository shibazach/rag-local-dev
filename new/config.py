# new/config.py
# セキュリティ設計を考慮した設定管理

import os
import logging
from typing import Dict, Any
from pathlib import Path

# プロジェクトルート
PROJECT_ROOT = Path(__file__).parent.parent
NEW_ROOT = Path(__file__).parent

# 環境変数から設定を取得
DEBUG_MODE = os.getenv("DEBUG_MODE", "false").lower() == "true"
DEVELOPMENT_MODE = os.getenv("DEVELOPMENT_MODE", "false").lower() == "true"

# セキュリティ設定
SECURE_COOKIES = os.getenv("SECURE_COOKIES", "false").lower() == "true"  # 開発時はfalse
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:8000,http://localhost:8001").split(",")

# データベース設定
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://raguser:ragpass@ragdb:5432/rag")

# LLM設定
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")

# GPU/CPU環境に応じてモデルを選択
CUDA_AVAILABLE = os.getenv("CUDA_AVAILABLE", "false").lower() == "true"
if CUDA_AVAILABLE:
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma:7b")  # GPU環境
else:
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "phi4-mini")  # CPU環境

# 埋め込みモデル設定
EMBEDDING_OPTIONS = {
    "sentence-transformers": {
        "models": [
            "intfloat/e5-large-v2",
            "intfloat/e5-small-v2"
        ],
        "default": "intfloat/e5-small-v2"
    },
    "ollama": {
        "models": [
            "nomic-embed-text"
        ],
        "default": "nomic-embed-text"
    }
}

DEFAULT_EMBEDDING_OPTION = os.getenv("DEFAULT_EMBEDDING_OPTION", "sentence-transformers")

# ファイルパス設定
INPUT_DIR = PROJECT_ROOT / "ignored" / "input_files"
OUTPUT_DIR = PROJECT_ROOT / "output"
LOG_DIR = PROJECT_ROOT / "logs"

# アプリケーション設定
API_PREFIX = "/api"
STATIC_DIR = NEW_ROOT / "static"
TEMPLATES_DIR = NEW_ROOT / "templates"

# セッション設定
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
SESSION_COOKIE_NAME = "new_rag_session"
SESSION_COOKIE_SECURE = SECURE_COOKIES
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "lax"

# ログ設定
LOGGER = logging.getLogger("new_rag")
LOGGER.setLevel(logging.INFO if not DEBUG_MODE else logging.DEBUG)

# 設定のログ出力
LOGGER.info(f"[new/config.py] DEBUG_MODE = {DEBUG_MODE}")
LOGGER.info(f"[new/config.py] OLLAMA_MODEL = {OLLAMA_MODEL}")
LOGGER.info(f"[new/config.py] SECURE_COOKIES = {SECURE_COOKIES}") 