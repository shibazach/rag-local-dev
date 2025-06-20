# embedding_config.py

embedding_options = {
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
