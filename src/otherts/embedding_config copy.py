embedding_options = {
    "1": {
        "embedder": "SentenceTransformer",
        "model_name": "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        "dimension": 384
    },
    "2": {
        "embedder": "SentenceTransformer",
        "model_name": "intfloat/multilingual-e5-large",
        "dimension": 1024
    },
    "3": {
        "embedder": "SentenceTransformer",
        "model_name": "distiluse-base-multilingual-cased-v1",
        "dimension": 512
    },
    "4": {
        "embedder": "SentenceTransformer",
        "model_name": "sentence-transformers/LaBSE",
        "dimension": 768
    },
    "5": {
        "embedder": "SentenceTransformer",
        "model_name": "sonoisa/sentence-bert-base-ja-mean-tokens",
        "dimension": 768
    },
    "6": {
        "embedder": "OllamaEmbeddings",
        "model_name": "nomic-embed-text",
        "dimension": 768
    }
}
