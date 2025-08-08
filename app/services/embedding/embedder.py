"""
Embeddingサービス - Prototype統合版
文書の埋め込みベクトル生成・管理
"""

import torch
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from sentence_transformers import SentenceTransformer
from langchain_community.embeddings import OllamaEmbeddings

from app.config import config, logger
from app.services.llm import get_text_chunker

class EmbeddingService:
    """埋め込みベクトル生成サービス"""
    
    def __init__(self):
        self.embedding_options = config.EMBEDDING_OPTIONS
        self.default_option = config.DEFAULT_EMBEDDING_OPTION
        self.chunker = get_text_chunker()
        self._model_cache = {}
    
    def pick_embed_device(self, min_free_vram_mb: int = 1024) -> str:
        """
        GPU 空き VRAM をチェックしてエンベッド用デバイスを返す
        
        Args:
            min_free_vram_mb: 最小必要VRAM（MB）
            
        Returns:
            デバイス名（"cuda" or "cpu"）
        """
        if config.CUDA_AVAILABLE and torch.cuda.is_available():
            try:
                free, _ = torch.cuda.mem_get_info()
                free_mb = free // (1024 * 1024)
                
                if free_mb >= min_free_vram_mb:
                    logger.info(f"GPU使用可能（空きVRAM: {free_mb}MB）")
                    return "cuda"
                else:
                    logger.warning(
                        f"GPU空きVRAM不足（{free_mb}MB < {min_free_vram_mb}MB）"
                    )
            except Exception as e:
                logger.warning(f"GPU情報取得エラー: {e}")
                try:
                    # pynvmlを使用した代替方法
                    from pynvml import nvmlInit, nvmlDeviceGetHandleByIndex, nvmlDeviceGetMemoryInfo
                    nvmlInit()
                    handle = nvmlDeviceGetHandleByIndex(0)
                    info = nvmlDeviceGetMemoryInfo(handle)
                    free_mb = info.free // (1024 * 1024)
                    
                    if free_mb >= min_free_vram_mb:
                        return "cuda"
                except Exception:
                    pass
        
        logger.info("CPU使用")
        return "cpu"
    
    def get_embedding_model(self, model_key: Optional[str] = None):
        """
        指定されたモデルキーに対応する埋め込みモデルを取得
        
        Args:
            model_key: モデルキー（省略時はデフォルト）
            
        Returns:
            埋め込みモデルインスタンス
        """
        if model_key is None:
            model_key = self.default_option
        
        # キャッシュチェック
        if model_key in self._model_cache:
            return self._model_cache[model_key]
        
        if model_key not in self.embedding_options:
            logger.warning(f"未対応のモデルキー: {model_key}, デフォルトを使用")
            model_key = self.default_option
        
        config_data = self.embedding_options[model_key]
        
        try:
            if config_data["embedder"] == "SentenceTransformer":
                device = self.pick_embed_device()
                logger.info(
                    f"SentenceTransformerモデルをロード: "
                    f"{config_data['model_name']} on {device}"
                )
                model = SentenceTransformer(
                    config_data["model_name"],
                    device=device
                )
            elif config_data["embedder"] == "OllamaEmbeddings":
                logger.info(
                    f"OllamaEmbeddingsモデルをロード: {config_data['model_name']}"
                )
                model = OllamaEmbeddings(
                    model=config_data["model_name"],
                    base_url=config.OLLAMA_BASE_URL
                )
            else:
                raise ValueError(f"未対応の埋め込みモデル: {config_data['embedder']}")
            
            # キャッシュに保存
            self._model_cache[model_key] = model
            
            return model
            
        except Exception as e:
            logger.error(f"モデルロードエラー: {e}")
            raise
    
    def generate_embedding(
        self,
        text: str,
        model_key: Optional[str] = None
    ) -> np.ndarray:
        """
        単一テキストの埋め込みベクトルを生成
        
        Args:
            text: 入力テキスト
            model_key: モデルキー
            
        Returns:
            埋め込みベクトル（numpy配列）
        """
        model = self.get_embedding_model(model_key)
        
        try:
            if hasattr(model, 'encode'):
                # SentenceTransformer
                embedding = model.encode(
                    [text],
                    convert_to_numpy=True,
                    show_progress_bar=False
                )[0]
            else:
                # OllamaEmbeddings
                embedding = model.embed_query(text)
                embedding = np.array(embedding)
            
            return embedding
            
        except Exception as e:
            logger.error(f"埋め込み生成エラー: {e}")
            raise
    
    def generate_embeddings(
        self,
        texts: List[str],
        model_key: Optional[str] = None,
        batch_size: Optional[int] = None
    ) -> np.ndarray:
        """
        複数テキストの埋め込みベクトルを生成
        
        Args:
            texts: 入力テキストのリスト
            model_key: モデルキー
            batch_size: バッチサイズ
            
        Returns:
            埋め込みベクトルの配列
        """
        if not texts:
            return np.array([])
        
        model = self.get_embedding_model(model_key)
        
        try:
            if hasattr(model, 'encode'):
                # SentenceTransformer
                device = getattr(model, 'device', 'cpu')
                if batch_size is None:
                    batch_size = 16 if str(device) == 'cuda' else 8
                
                embeddings = model.encode(
                    texts,
                    batch_size=batch_size,
                    convert_to_numpy=True,
                    show_progress_bar=len(texts) > 100
                )
            else:
                # OllamaEmbeddings
                embeddings = model.embed_documents(texts)
                embeddings = np.array(embeddings)
            
            logger.info(
                f"✅ {len(texts)}個のテキストの埋め込みを生成 "
                f"(shape: {embeddings.shape})"
            )
            
            return embeddings
            
        except torch.cuda.OutOfMemoryError:
            logger.warning("GPU OOM発生、CPUにフォールバック")
            torch.cuda.empty_cache()
            
            # CPUで再試行
            if hasattr(model, 'to'):
                model = model.to('cpu')
            
            return self.generate_embeddings(
                texts,
                model_key=model_key,
                batch_size=2  # CPU用の小さいバッチサイズ
            )
        except Exception as e:
            logger.error(f"埋め込み生成エラー: {e}")
            raise
    
    def embed_and_chunk_text(
        self,
        text: str,
        model_key: Optional[str] = None,
        chunk_size: Optional[int] = None,
        overlap: Optional[int] = None
    ) -> Tuple[List[str], np.ndarray]:
        """
        テキストをチャンク分割して埋め込みベクトルを生成
        
        Args:
            text: 入力テキスト
            model_key: モデルキー
            chunk_size: チャンクサイズ
            overlap: オーバーラップサイズ
            
        Returns:
            (チャンクリスト, 埋め込みベクトル配列)のタプル
        """
        # チャンク分割
        chunks = self.chunker.split_into_chunks(
            text,
            chunk_size=chunk_size,
            overlap=overlap
        )
        
        if not chunks:
            return [], np.array([])
        
        # 埋め込み生成
        embeddings = self.generate_embeddings(chunks, model_key)
        
        return chunks, embeddings
    
    def get_model_info(self, model_key: Optional[str] = None) -> Dict[str, Any]:
        """
        モデル情報を取得
        
        Args:
            model_key: モデルキー
            
        Returns:
            モデル情報の辞書
        """
        if model_key is None:
            model_key = self.default_option
        
        if model_key not in self.embedding_options:
            return {
                "error": f"未対応のモデルキー: {model_key}"
            }
        
        config_data = self.embedding_options[model_key]
        
        info = {
            "model_key": model_key,
            "embedder": config_data["embedder"],
            "model_name": config_data["model_name"],
            "dimension": config_data["dimension"]
        }
        
        # モデルがロード済みの場合は追加情報
        if model_key in self._model_cache:
            model = self._model_cache[model_key]
            if hasattr(model, 'device'):
                info["device"] = str(model.device)
            info["loaded"] = True
        else:
            info["loaded"] = False
        
        return info
    
    def to_pgvector_literal(self, vector: np.ndarray) -> str:
        """
        numpy配列をPostgreSQL pgvector形式の文字列に変換
        
        Args:
            vector: numpy配列
            
        Returns:
            pgvector形式の文字列
        """
        if isinstance(vector, np.ndarray):
            vector_list = vector.tolist()
        else:
            vector_list = list(vector)
        
        return "[" + ",".join(map(str, vector_list)) + "]"

# サービスインスタンス作成ヘルパー
def get_embedding_service() -> EmbeddingService:
    """埋め込みサービスインスタンス取得"""
    return EmbeddingService()