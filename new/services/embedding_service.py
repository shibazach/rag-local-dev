#!/usr/bin/env python3
# new/services/embedding_service.py
# ベクトル化サービス

import logging
import json
import numpy as np
from typing import List, Dict, Any, Optional
from pathlib import Path

from ..config import LOGGER

class EmbeddingService:
    """ベクトル化サービス"""
    
    def __init__(self):
        self.default_model = "sentence-transformers"
        self.models = {
            "sentence-transformers": self._get_sentence_transformers_embedding,
            "ollama": self._get_ollama_embedding
        }
    
    def create_embeddings(self, texts: List[str], model_name: str = None) -> List[List[float]]:
        """テキストリストをベクトル化"""
        try:
            model_name = model_name or self.default_model
            LOGGER.info(f"🧠 ベクトル化開始: {len(texts)}個のテキスト, モデル={model_name}")
            
            if model_name not in self.models:
                raise ValueError(f"未対応のモデル: {model_name}")
            
            embeddings = []
            for i, text in enumerate(texts):
                try:
                    embedding = self.models[model_name](text)
                    embeddings.append(embedding)
                    LOGGER.info(f"✅ ベクトル化完了: {i+1}/{len(texts)}")
                except Exception as e:
                    LOGGER.error(f"❌ ベクトル化エラー: テキスト{i+1} - {e}")
                    # エラーの場合はゼロベクトルを追加
                    embeddings.append([0.0] * 768)  # デフォルト次元数
            
            LOGGER.info(f"🎉 ベクトル化完了: {len(embeddings)}個")
            return embeddings
            
        except Exception as e:
            LOGGER.error(f"ベクトル化エラー: {e}")
            raise
    
    def _get_sentence_transformers_embedding(self, text: str) -> List[float]:
        """sentence-transformersを使用したベクトル化"""
        try:
            from sentence_transformers import SentenceTransformer
            
            # モデルの初期化（初回のみ）
            if not hasattr(self, '_sentence_model'):
                self._sentence_model = SentenceTransformer('intfloat/e5-large-v2')
            
            # テキストの前処理
            if not text.strip():
                return [0.0] * 1024  # 空テキストの場合はゼロベクトル
            
            # ベクトル化
            embedding = self._sentence_model.encode(text)
            return embedding.tolist()
            
        except ImportError:
            LOGGER.error("sentence-transformersが見つかりません")
            return [0.0] * 1024
        except Exception as e:
            LOGGER.error(f"sentence-transformersエラー: {e}")
            return [0.0] * 1024
    
    def _get_ollama_embedding(self, text: str) -> List[float]:
        """Ollamaを使用したベクトル化"""
        try:
            from langchain_community.embeddings import OllamaEmbeddings
            
            # モデルの初期化（初回のみ）
            if not hasattr(self, '_ollama_model'):
                self._ollama_model = OllamaEmbeddings(model="nomic-embed-text")
            
            # ベクトル化
            embedding = self._ollama_model.embed_query(text)
            return embedding
            
        except ImportError:
            LOGGER.error("langchain_communityが見つかりません")
            return [0.0] * 768
        except Exception as e:
            LOGGER.error(f"Ollamaエラー: {e}")
            return [0.0] * 768
    
    def calculate_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """コサイン類似度を計算"""
        try:
            vec1 = np.array(embedding1)
            vec2 = np.array(embedding2)
            
            # 正規化
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            # コサイン類似度
            similarity = np.dot(vec1, vec2) / (norm1 * norm2)
            return float(similarity)
            
        except Exception as e:
            LOGGER.error(f"類似度計算エラー: {e}")
            return 0.0
    
    def find_similar_chunks(self, query_embedding: List[float], chunk_embeddings: List[List[float]], top_k: int = 5) -> List[Dict[str, Any]]:
        """類似チャンクを検索"""
        try:
            similarities = []
            
            for i, chunk_embedding in enumerate(chunk_embeddings):
                similarity = self.calculate_similarity(query_embedding, chunk_embedding)
                similarities.append({
                    "index": i,
                    "similarity": similarity
                })
            
            # 類似度でソート
            similarities.sort(key=lambda x: x["similarity"], reverse=True)
            
            # top_kを返す
            return similarities[:top_k]
            
        except Exception as e:
            LOGGER.error(f"類似チャンク検索エラー: {e}")
            return []
    
    def batch_create_embeddings(self, chunks: List[Dict[str, Any]], model_name: str = None) -> List[Dict[str, Any]]:
        """チャンクリストを一括ベクトル化"""
        try:
            LOGGER.info(f"🧠 一括ベクトル化開始: {len(chunks)}個のチャンク")
            
            # テキストを抽出
            texts = [chunk["text"] for chunk in chunks]
            
            # ベクトル化
            embeddings = self.create_embeddings(texts, model_name)
            
            # 結果を構築
            results = []
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                result = {
                    **chunk,
                    "embedding_vector": json.dumps(embedding),
                    "embedding_model": model_name or self.default_model,
                    "embedding_size": len(embedding)
                }
                results.append(result)
            
            LOGGER.info(f"🎉 一括ベクトル化完了: {len(results)}個")
            return results
            
        except Exception as e:
            LOGGER.error(f"一括ベクトル化エラー: {e}")
            raise 