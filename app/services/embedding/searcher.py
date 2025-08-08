"""
ベクトル検索サービス - Prototype統合版
埋め込みベクトルを使用した類似度検索
"""

import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text

from app.config import config, logger
from app.core.models import FileEmbedding, FilesMeta, FilesText
from app.core.database import get_db
from .embedder import get_embedding_service, EmbeddingService

class VectorSearcher:
    """ベクトル検索サービス"""
    
    def __init__(self, db_session: Optional[AsyncSession] = None):
        """
        Args:
            db_session: データベースセッション（オプショナル）
        """
        self.db = db_session
        self.embedding_service = get_embedding_service()
    
    def calculate_similarity(
        self,
        query_vector: np.ndarray,
        target_vectors: np.ndarray
    ) -> np.ndarray:
        """
        コサイン類似度を計算
        
        Args:
            query_vector: クエリベクトル
            target_vectors: 対象ベクトルの配列
            
        Returns:
            類似度スコアの配列
        """
        if len(target_vectors) == 0:
            return np.array([])
        
        # 2次元配列に整形
        if query_vector.ndim == 1:
            query_vector = query_vector.reshape(1, -1)
        if target_vectors.ndim == 1:
            target_vectors = target_vectors.reshape(1, -1)
        
        # コサイン類似度計算
        similarities = cosine_similarity(query_vector, target_vectors)[0]
        
        return similarities
    
    async def search_similar_chunks(
        self,
        query: str,
        model_key: Optional[str] = None,
        limit: int = 10,
        min_score: float = 0.0
    ) -> List[Dict[str, Any]]:
        """
        類似チャンクを検索（データベース使用）
        
        Args:
            query: 検索クエリ
            model_key: 埋め込みモデルキー
            limit: 結果数上限
            min_score: 最小スコア閾値
            
        Returns:
            検索結果のリスト
        """
        # クエリの埋め込みベクトルを生成
        query_vector = self.embedding_service.generate_embedding(
            query,
            model_key=model_key
        )
        
        # TODO: データベースから埋め込みベクトルを取得して検索
        # 現在はモック実装
        logger.info(
            f"ベクトル検索: query='{query}', "
            f"model_key={model_key}, limit={limit}"
        )
        
        # モック結果
        return [
            {
                "chunk_id": "mock-chunk-1",
                "chunk_text": "検索結果のサンプルテキスト",
                "score": 0.95,
                "file_id": "mock-file-1",
                "filename": "sample.pdf",
                "chunk_index": 0
            }
        ]
    
    def search_in_memory(
        self,
        query: str,
        documents: List[str],
        model_key: Optional[str] = None,
        limit: int = 10,
        min_score: float = 0.0
    ) -> List[Dict[str, Any]]:
        """
        メモリ内で類似文書を検索（データベース不要）
        
        Args:
            query: 検索クエリ
            documents: 検索対象文書のリスト
            model_key: 埋め込みモデルキー
            limit: 結果数上限
            min_score: 最小スコア閾値
            
        Returns:
            検索結果のリスト
        """
        if not documents:
            return []
        
        try:
            # クエリの埋め込みベクトルを生成
            query_vector = self.embedding_service.generate_embedding(
                query,
                model_key=model_key
            )
            
            # 文書の埋め込みベクトルを生成
            doc_vectors = self.embedding_service.generate_embeddings(
                documents,
                model_key=model_key
            )
            
            # 類似度計算
            similarities = self.calculate_similarity(query_vector, doc_vectors)
            
            # 結果を整形
            results = []
            for idx, (doc, score) in enumerate(zip(documents, similarities)):
                if score >= min_score:
                    results.append({
                        "index": idx,
                        "text": doc,
                        "score": float(score),
                        "length": len(doc)
                    })
            
            # スコア順にソート
            results.sort(key=lambda x: x["score"], reverse=True)
            
            # 上位N件を返す
            results = results[:limit]
            
            logger.info(
                f"✅ メモリ内検索完了: "
                f"{len(results)}件の結果（全{len(documents)}文書中）"
            )
            
            return results
            
        except Exception as e:
            logger.error(f"メモリ内検索エラー: {e}")
            return []
    
    def rerank_results(
        self,
        query: str,
        results: List[Dict[str, Any]],
        text_key: str = "text",
        model_key: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        検索結果を再ランキング
        
        Args:
            query: 検索クエリ
            results: 検索結果のリスト
            text_key: テキストを含むキー名
            model_key: 埋め込みモデルキー
            
        Returns:
            再ランキングされた結果
        """
        if not results:
            return results
        
        try:
            # テキストを抽出
            texts = [r.get(text_key, "") for r in results]
            
            # クエリと各テキストの埋め込みを生成
            query_vector = self.embedding_service.generate_embedding(
                query,
                model_key=model_key
            )
            text_vectors = self.embedding_service.generate_embeddings(
                texts,
                model_key=model_key
            )
            
            # 類似度を再計算
            similarities = self.calculate_similarity(query_vector, text_vectors)
            
            # 結果を更新
            for result, new_score in zip(results, similarities):
                result["rerank_score"] = float(new_score)
                # 元のスコアがある場合は結合
                if "score" in result:
                    # 元のスコアと再ランキングスコアの加重平均
                    result["combined_score"] = (
                        0.7 * result["score"] + 0.3 * result["rerank_score"]
                    )
                else:
                    result["combined_score"] = result["rerank_score"]
            
            # 結合スコアでソート
            results.sort(key=lambda x: x.get("combined_score", 0), reverse=True)
            
            logger.info("✅ 再ランキング完了")
            
            return results
            
        except Exception as e:
            logger.error(f"再ランキングエラー: {e}")
            return results
    
    def find_similar_documents(
        self,
        reference_text: str,
        documents: List[str],
        model_key: Optional[str] = None,
        threshold: float = 0.8
    ) -> List[Tuple[int, float]]:
        """
        参照テキストに類似した文書を検索
        
        Args:
            reference_text: 参照テキスト
            documents: 検索対象文書のリスト
            model_key: 埋め込みモデルキー
            threshold: 類似度閾値
            
        Returns:
            (インデックス, 類似度)のタプルのリスト
        """
        if not documents:
            return []
        
        try:
            # 埋め込みベクトルを生成
            ref_vector = self.embedding_service.generate_embedding(
                reference_text,
                model_key=model_key
            )
            doc_vectors = self.embedding_service.generate_embeddings(
                documents,
                model_key=model_key
            )
            
            # 類似度計算
            similarities = self.calculate_similarity(ref_vector, doc_vectors)
            
            # 閾値以上の結果を抽出
            similar_docs = []
            for idx, score in enumerate(similarities):
                if score >= threshold:
                    similar_docs.append((idx, float(score)))
            
            # スコア順にソート
            similar_docs.sort(key=lambda x: x[1], reverse=True)
            
            logger.info(
                f"✅ {len(similar_docs)}件の類似文書を検出 "
                f"(閾値: {threshold})"
            )
            
            return similar_docs
            
        except Exception as e:
            logger.error(f"類似文書検索エラー: {e}")
            return []

# サービスインスタンス作成ヘルパー
def get_vector_searcher(db_session: Optional[AsyncSession] = None) -> VectorSearcher:
    """ベクトル検索サービスインスタンス取得"""
    return VectorSearcher(db_session)

async def search_similar_chunks(
    query_text: str,
    embedding_option: str = None,
    limit: int = 10,
    min_score: float = 0.0,
    db_session: Optional[AsyncSession] = None
) -> List[Dict[str, Any]]:
    """
    テキストクエリによる類似チャンク検索（簡易版）
    
    Args:
        query_text: 検索クエリテキスト
        embedding_option: 埋め込みオプション
        limit: 結果数上限
        min_score: 最小スコア
        db_session: データベースセッション
        
    Returns:
        検索結果リスト
    """
    try:
        # Embeddingサービス初期化
        if not embedding_option:
            embedding_option = config.DEFAULT_EMBEDDING_OPTION
        
        embedding_service = EmbeddingService(embedding_option)
        
        # クエリベクトル生成
        query_embedding = embedding_service.generate_single_embedding(query_text)
        if query_embedding is None:
            logger.error("クエリベクトル生成失敗")
            return []
        
        # 検索実行
        if db_session:
            searcher = VectorSearcher(db_session)
        else:
            # 新しいセッションで検索
            async with get_db() as db:
                searcher = VectorSearcher(db)
                return await searcher.search_similar_chunks(
                    query_embedding,
                    limit=limit,
                    threshold=min_score
                )
        
        # 既存セッションで検索
        return await searcher.search_similar_chunks(
            query_embedding,
            limit=limit,
            threshold=min_score
        )
        
    except Exception as e:
        logger.error(f"類似チャンク検索エラー: {e}")
        return []