# src/config.py
import os
import torch

from sqlalchemy import create_engine
from langchain_ollama import OllamaLLM

# 既存データを消さずに、起動時のTRUNCATE処理だけ行うか
TRUNCATE_ON_STARTUP = False

# テーブル定義がまるっと変わっても DROP→CREATE でリセットするか
AUTO_INIT_SCHEMA    = True

# REM: 環境変数から設定を取得
MECAB_DICT_PATH = "/var/lib/mecab/dic/ipadic-utf8"

# REM: 開発モード時のDB初期化制御フラグ（TrueならTRUNCATEされる）
DEVELOPMENT_MODE = True

# REM: GPU があれば "cuda"、無ければ "cpu"
CUDA_AVAILABLE = True if torch.cuda.is_available() else False

# REM: Ollamaのモデル名とベースURL, 接続エンジン
OLLAMA_BASE = os.getenv("OLLAMA_BASE", "http://ollama:11434")
OLLAMA_MODEL = "gemma:7b" if CUDA_AVAILABLE else "phi4-mini"
LLM_ENGINE = OllamaLLM(model=OLLAMA_MODEL, base_url=OLLAMA_BASE)
print(f"[config.py] LLM_MODEL = {OLLAMA_MODEL}")
#"http://host.docker.internal:11434")

# 生成トークン長さ倍率（本文長 × 倍率）
LLM_LENGTH_RATE = 1.4

# REM: デフォルトの入力ディレクトリと出力ディレクトリ
INPUT_DIR = "ignored/input_files"
OUTPUT_DIR = "ignored/output_files"
LOG_DIR = "logs/full_logs"

# REM: postgreSQL 接続エンジン
DB_ENGINE = create_engine("postgresql://raguser:ragpass@ragdb:5432/rag")

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