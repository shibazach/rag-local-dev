# src/config.py

import os

from sqlalchemy import create_engine

# REM: 環境変数から設定を取得
MECAB_DICT_PATH = "/var/lib/mecab/dic/ipadic-utf8"

# REM: 開発モード時のDB初期化制御フラグ（TrueならTRUNCATEされる）
DEVELOPMENT_MODE = True

# REM: Ollamaのモデル名とベースURL
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma:7b")
OLLAMA_BASE = os.getenv("OLLAMA_BASE", "http://172.19.0.1:11434")

# REM: デフォルトの入力PDFディレクトリと出力PDFディレクトリ
INPUT_DIR = "ignored/input_pdfs"
OUTPUT_DIR = "ignored/output_pdfs"
LOG_DIR = "logs/full_logs"

# REM: postgreSQLの接続URL
# DB_URL = os.getenv("DB_URL", "postgresql://raguser:ragpass@pgvector-db:5432/ragdb")
DB_ENGINE = create_engine("postgresql://raguser:ragpass@localhost:5432/ragdb")

# REM: 埋め込みモデルの設定
EMBEDDING_OPTIONS = {
    "1": {
        "embedder": "SentenceTransformer",
        "model_name": "intfloat/e5-large-v2",
        "dimension": 1024
    },
    "2": {
        "embedder": "OllamaEmbeddings",
        "model_name": "nomic-embed-text",
        "dimension": 768
    }
}

# REM: デフォルトは e5 を優先（番号順）
DEFAULT_EMBEDDING_OPTION = "1"