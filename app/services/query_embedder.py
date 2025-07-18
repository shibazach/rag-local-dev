# app/services/query_embedder.py
import numpy as np
from langchain_community.embeddings import OllamaEmbeddings
from sentence_transformers import SentenceTransformer
from src.config import (EMBEDDING_OPTIONS, OLLAMA_BASE)

def get_query_embedding(query: str, model_key: str):
    selected_model = EMBEDDING_OPTIONS[model_key]
    if selected_model["embedder"] == "OllamaEmbeddings":
        embedder = OllamaEmbeddings(model=selected_model["model_name"], base_url=OLLAMA_BASE)
        return embedder.embed_query(query)
    else:
        embedder = SentenceTransformer(selected_model["model_name"])
        return embedder.encode([query], convert_to_numpy=True)[0]

def get_tablename(model_key: str):
    selected_model = EMBEDDING_OPTIONS[model_key]
    model_safe = selected_model["model_name"].replace("/", "_").replace("-", "_")
    return f"{model_safe}_{selected_model['dimension']}"