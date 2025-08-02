#!/usr/bin/env python3
# new/services/search_service.py
# 検索サービス

import logging
import json
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from ..models import File, FileText, Embedding, FileImage
from ..config import LOGGER
from .embedding_service import EmbeddingService

class SearchService:
    """検索サービス"""
    
    def __init__(self):
        self.embedding_service = EmbeddingService()
    
    def search_text(self, db: Session, query: str, top_k: int = 5, file_ids: List[str] = None) -> List[Dict[str, Any]]:
        """テキスト検索"""
        try:
            LOGGER.info(f"🔍 テキスト検索開始: クエリ='{query}', top_k={top_k}")
            
            # クエリをベクトル化
            query_embedding = self.embedding_service.create_embeddings([query])[0]
            
            # 検索対象のファイルを取得
            query_conditions = [Embedding.embedding_vector.isnot(None)]
            if file_ids:
                query_conditions.append(Embedding.file_id.in_(file_ids))
            
            embeddings = db.query(Embedding).filter(and_(*query_conditions)).all()
            
            if not embeddings:
                LOGGER.warning("検索対象のベクトルが見つかりません")
                return []
            
            # 類似度計算
            similarities = []
            for embedding in embeddings:
                try:
                    embedding_vector = json.loads(embedding.embedding_vector)
                    similarity = self.embedding_service.calculate_similarity(query_embedding, embedding_vector)
                    
                    similarities.append({
                        "file_id": str(embedding.file_id),
                        "chunk_id": embedding.chunk_id,
                        "text_chunk": embedding.text_chunk,
                        "similarity": similarity,
                        "embedding_model": embedding.embedding_model
                    })
                except Exception as e:
                    LOGGER.warning(f"類似度計算エラー: {e}")
                    continue
            
            # 類似度でソート
            similarities.sort(key=lambda x: x["similarity"], reverse=True)
            
            # top_kを返す
            results = similarities[:top_k]
            
            LOGGER.info(f"🎉 テキスト検索完了: {len(results)}件")
            return results
            
        except Exception as e:
            LOGGER.error(f"テキスト検索エラー: {e}")
            return []
    
    def search_images(self, db: Session, query: str, top_k: int = 5, file_ids: List[str] = None) -> List[Dict[str, Any]]:
        """画像検索"""
        try:
            LOGGER.info(f"🖼️ 画像検索開始: クエリ='{query}', top_k={top_k}")
            
            # クエリをベクトル化
            query_embedding = self.embedding_service.create_embeddings([query])[0]
            
            # 検索対象の画像を取得
            query_conditions = [FileImage.embedding_vector.isnot(None)]
            if file_ids:
                query_conditions.append(FileImage.file_id.in_(file_ids))
            
            images = db.query(FileImage).filter(and_(*query_conditions)).all()
            
            if not images:
                LOGGER.warning("検索対象の画像ベクトルが見つかりません")
                return []
            
            # 類似度計算
            similarities = []
            for image in images:
                try:
                    embedding_vector = json.loads(image.embedding_vector)
                    similarity = self.embedding_service.calculate_similarity(query_embedding, embedding_vector)
                    
                    similarities.append({
                        "file_id": str(image.file_id),
                        "page_number": image.page_number,
                        "image_number": image.image_number,
                        "ocr_text": image.ocr_text,
                        "llm_description": image.llm_description,
                        "similarity": similarity,
                        "embedding_model": image.embedding_model
                    })
                except Exception as e:
                    LOGGER.warning(f"画像類似度計算エラー: {e}")
                    continue
            
            # 類似度でソート
            similarities.sort(key=lambda x: x["similarity"], reverse=True)
            
            # top_kを返す
            results = similarities[:top_k]
            
            LOGGER.info(f"🎉 画像検索完了: {len(results)}件")
            return results
            
        except Exception as e:
            LOGGER.error(f"画像検索エラー: {e}")
            return []
    
    def hybrid_search(self, db: Session, query: str, top_k: int = 10, file_ids: List[str] = None) -> Dict[str, Any]:
        """ハイブリッド検索（テキスト + 画像）"""
        try:
            LOGGER.info(f"🔍 ハイブリッド検索開始: クエリ='{query}', top_k={top_k}")
            
            # テキスト検索
            text_results = self.search_text(db, query, top_k // 2, file_ids)
            
            # 画像検索
            image_results = self.search_images(db, query, top_k // 2, file_ids)
            
            # 結果を統合
            all_results = []
            
            # テキスト結果を追加
            for result in text_results:
                result["type"] = "text"
                all_results.append(result)
            
            # 画像結果を追加
            for result in image_results:
                result["type"] = "image"
                all_results.append(result)
            
            # 類似度でソート
            all_results.sort(key=lambda x: x["similarity"], reverse=True)
            
            # top_kを返す
            final_results = all_results[:top_k]
            
            # 統計情報
            text_count = len([r for r in final_results if r["type"] == "text"])
            image_count = len([r for r in final_results if r["type"] == "image"])
            
            stats = {
                "total_results": len(final_results),
                "text_results": text_count,
                "image_results": image_count,
                "avg_similarity": sum(r["similarity"] for r in final_results) / len(final_results) if final_results else 0.0
            }
            
            LOGGER.info(f"🎉 ハイブリッド検索完了: {len(final_results)}件 (テキスト:{text_count}, 画像:{image_count})")
            
            return {
                "results": final_results,
                "stats": stats
            }
            
        except Exception as e:
            LOGGER.error(f"ハイブリッド検索エラー: {e}")
            return {"results": [], "stats": {}}
    
    def get_file_summary(self, db: Session, file_id: str) -> Dict[str, Any]:
        """ファイルの検索サマリーを取得"""
        try:
            # ファイル情報
            file = db.query(File).filter(File.id == file_id).first()
            if not file:
                return {}
            
            # テキスト情報
            file_text = db.query(FileText).filter(FileText.file_id == file_id).first()
            
            # 埋め込みベクトル数
            embedding_count = db.query(Embedding).filter(Embedding.file_id == file_id).count()
            
            # 画像数
            image_count = db.query(FileImage).filter(FileImage.file_id == file_id).count()
            
            return {
                "file_id": str(file.id),
                "file_name": file.file_name,
                "file_size": file.file_size,
                "status": file.status,
                "processing_stage": file.processing_stage,
                "text_chunks": len(file_text.text_chunks) if file_text and file_text.text_chunks else 0,
                "embeddings": embedding_count,
                "images": image_count,
                "created_at": file.created_at.isoformat() if file.created_at else None
            }
            
        except Exception as e:
            LOGGER.error(f"ファイルサマリー取得エラー: {e}")
            return {}
    
    def get_search_statistics(self, db: Session) -> Dict[str, Any]:
        """検索統計情報を取得（新DB設計対応）"""
        try:
            from sqlalchemy import text as sql_text
            from ..db_handler import get_all_files
            
            # 新しいDBハンドラーからファイル一覧を取得
            files = get_all_files()
            
            # ファイル数
            total_files = len(files)
            
            # 処理済みファイル数（files_textテーブルにデータがあるもの）
            processed_files = len([f for f in files if f["status"] == "processed"])
            
            # テキストチャンク数（embeddingsテーブルから取得）
            total_chunks_query = db.execute(sql_text("SELECT COUNT(*) FROM embeddings"))
            total_chunks = total_chunks_query.scalar() or 0
            
            # 画像数（処理済みファイルから推定 - 実際の画像テーブルは別途実装予定）
            total_images = 0  # 一時的に0とする
            
            # ベクトル化済みファイル数（embeddingsテーブルにデータがあるファイル）
            vectorized_files_query = db.execute(sql_text("""
                SELECT COUNT(DISTINCT blob_id) FROM embeddings WHERE blob_id IS NOT NULL
            """))
            vectorized_files = vectorized_files_query.scalar() or 0
            
            # 処理率計算
            processing_rate = (processed_files / total_files * 100) if total_files > 0 else 0.0
            
            LOGGER.debug(f"📊 統計情報: ファイル={total_files}, 処理済み={processed_files}, チャンク={total_chunks}, 画像={total_images}")
            
            return {
                "total_files": total_files,
                "processed_files": processed_files,
                "total_chunks": total_chunks,
                "total_images": total_images,
                "vectorized_files": vectorized_files,
                "processing_rate": processing_rate
            }
            
        except Exception as e:
            LOGGER.error(f"検索統計取得エラー: {e}")
            return {
                "total_files": 0,
                "processed_files": 0,
                "total_chunks": 0,
                "total_images": 0,
                "vectorized_files": 0,
                "processing_rate": 0.0
            } 