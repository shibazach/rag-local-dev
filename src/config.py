# src/config.py（更新日時: 2025-07-15 18:20 JST）
import os, torch
from sqlalchemy import create_engine
from langchain_ollama import OllamaLLM
import logging

# REM: 環境変数から設定を取得
MECAB_DICT_PATH = "/var/lib/mecab/dic/ipadic-utf8"

# REM: 開発モード時のDB初期化制御フラグ（TrueならTRUNCATEされる）
DEVELOPMENT_MODE = True

# REM: Falseにすればすべてのデバッグ出力が止まる
DEBUG_MODE = True  

# REM: GPU があれば "cuda"、無ければ "cpu"
CUDA_AVAILABLE = True if torch.cuda.is_available() else False

# REM: プロジェクトのルートディレクトリと関連ディレクトリの設定
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BIN_DIR = os.path.join(PROJECT_ROOT, "bin")
PROMPT_FILE_PATH = os.path.join(BIN_DIR, "refine_prompt_multi.txt")

# REM: Ollamaのモデル名とベースURL, 接続エンジン
OLLAMA_BASE = os.getenv("OLLAMA_BASE", "http://ollama:11434")
OLLAMA_MODEL = "gemma:7b" if CUDA_AVAILABLE else "phi4-mini"
LLM_ENGINE = OllamaLLM(model=OLLAMA_MODEL, base_url=OLLAMA_BASE)
print(f"[config.py] LLM_MODEL = {OLLAMA_MODEL}")

#"http://host.docker.internal:11434")

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

# REM: ログ設定
logging.basicConfig(
    level=logging.DEBUG if DEVELOPMENT_MODE else logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
LOGGER = logging.getLogger("rag")
