# src/config.py

import os
import torch

from sqlalchemy import create_engine

# REM: 環境変数から設定を取得
MECAB_DICT_PATH = "/var/lib/mecab/dic/ipadic-utf8"

# REM: 開発モード時のDB初期化制御フラグ（TrueならTRUNCATEされる）
DEVELOPMENT_MODE = True

# GPU があれば "cuda"、無ければ "cpu"
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# REM: Ollamaのモデル名とベースURL
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma:7b") #環境変数優先
#OLLAMA_BASE = os.getenv("OLLAMA_BASE", "http://host.docker.internal:11434") #環境変数優先
OLLAMA_BASE = os.getenv("OLLAMA_BASE", "http://ollama:11434")


# REM: デフォルトの入力ディレクトリと出力ディレクトリ
INPUT_DIR = "ignored/input_files"
OUTPUT_DIR = "ignored/output_files"
LOG_DIR = "logs/full_logs"

# REM: postgreSQLの接続URL
DB_URL = os.getenv("DB_URL", "postgresql://raguser:ragpass@ragdb:5432/ragdb") #環境変数優先
DB_ENGINE = create_engine(DB_URL)

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