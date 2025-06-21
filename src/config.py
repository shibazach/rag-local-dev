# config.py
# MECAB_DICT_PATH = "/usr/share/mecab/dic/ipadic"
MECAB_DICT_PATH = "/var/lib/mecab/dic/ipadic-utf8"

# REM: 開発モード時のDB初期化制御フラグ（TrueならTRUNCATEされる）
DEVELOPMENT_MODE = True

DEFAULT_LLM_MODEL = "gemma:7b"

DEFAULT_INPUT_DIR = "ignored/input_pdfs"
DEFAULT_OUTPUT_DIR = "ignored/output_pdfs"

