# app/services/chat/query_embedder.py
# クエリ埋め込みと検索機能

import logging
from typing import List, Dict, Any
from db.handler import fetch_top_chunks, fetch_top_files
from src.config import EMBEDDING_OPTIONS, DEFAULT_EMBEDDING_OPTION

LOGGER = logging.getLogger("query_embedder")

def get_embedding_model(model_key: str):
    """指定されたモデルキーに対応する埋め込みモデルを取得"""
    if model_key not in EMBEDDING_OPTIONS:
        LOGGER.warning(f"未対応のモデルキー: {model_key}, デフォルトを使用")
        model_key = DEFAULT_EMBEDDING_OPTION
    
    config = EMBEDDING_OPTIONS[model_key]
    
    if config["embedder"] == "SentenceTransformer":
        from sentence_transformers import SentenceTransformer
        return SentenceTransformer(config["model_name"])
    elif config["embedder"] == "OllamaEmbeddings":
        from langchain_ollama import OllamaEmbeddings
        from src.config import OLLAMA_BASE
        return OllamaEmbeddings(model=config["model_name"], base_url=OLLAMA_BASE)
    else:
        raise ValueError(f"未対応の埋め込みモデル: {config['embedder']}")

def generate_embedding(query: str, model_key: str) -> str:
    """クエリの埋め込みベクトルを生成"""
    try:
        model = get_embedding_model(model_key)
        
        if hasattr(model, 'encode'):
            # SentenceTransformer
            embedding = model.encode([query])[0]
        else:
            # OllamaEmbeddings
            embedding = model.embed_query(query)
        
        # ベクトルを文字列形式に変換
        import numpy as np
        if isinstance(embedding, np.ndarray):
            embedding_list = embedding.tolist()
        else:
            embedding_list = embedding
        
        return str(embedding_list)
        
    except Exception as e:
        LOGGER.exception(f"埋め込み生成エラー: {e}")
        raise

def fetch_top_chunks(query: str, model_key: str, table_name: str, limit: int = 5) -> List[Dict[str, Any]]:
    """チャンク単位での近傍検索"""
    try:
        embedding_str = generate_embedding(query, model_key)
        return fetch_top_chunks(embedding_str, table_name, limit)
    except Exception as e:
        LOGGER.exception(f"チャンク検索エラー: {e}")
        return []

def fetch_top_files(query: str, model_key: str, table_name: str, limit: int = 10) -> List[Dict[str, Any]]:
    """ファイル単位での近傍検索"""
    try:
        embedding_str = generate_embedding(query, model_key)
        return fetch_top_files(embedding_str, table_name, limit)
    except Exception as e:
        LOGGER.exception(f"ファイル検索エラー: {e}")
        return [] 