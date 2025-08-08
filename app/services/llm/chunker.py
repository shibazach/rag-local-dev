"""
テキストチャンク分割サービス - Prototype統合版
オーバーラップ付きテキスト分割・結合ユーティリティ
"""

import textwrap
from typing import List, Optional, Dict, Any

from app.config import config, logger

class TextChunker:
    """テキストチャンク分割サービス"""
    
    def __init__(
        self,
        default_chunk_size: int = None,
        default_overlap: int = None
    ):
        """
        Args:
            default_chunk_size: デフォルトチャンクサイズ（省略時は設定値）
            default_overlap: デフォルトオーバーラップ（省略時は設定値）
        """
        self.default_chunk_size = default_chunk_size or config.CHUNK_SIZE
        self.default_overlap = default_overlap or config.CHUNK_OVERLAP
    
    def _normalize(self, text: str) -> str:
        """前後の空白を削除し、改行を \n に統一"""
        return text.replace("\r\n", "\n").replace("\r", "\n").strip()
    
    def split_into_chunks(
        self,
        text: str,
        chunk_size: Optional[int] = None,
        overlap: Optional[int] = None
    ) -> List[str]:
        """
        文字数ベースで chunk_size ごとに切り出し、隣接チャンクと overlap
        文字ぶん重なりを持たせる。
        
        Args:
            text: 入力テキスト
            chunk_size: チャンクサイズ（省略時はデフォルト）
            overlap: オーバーラップサイズ（省略時はデフォルト）
            
        Returns:
            チャンクのリスト
        """
        if chunk_size is None:
            chunk_size = self.default_chunk_size
        if overlap is None:
            overlap = self.default_overlap
        
        if chunk_size <= overlap:
            raise ValueError("chunk_size は overlap より大きい必要があります")
        
        text = self._normalize(text)
        if not text:
            return []
        
        # textwrap.wrap は単語境界優先だが、日本語でも句点・改行でほぼ問題ない
        wrapped = textwrap.wrap(
            text,
            width=chunk_size - overlap,
            break_long_words=False,
            break_on_hyphens=False
        )
        
        chunks: List[str] = []
        for idx, segment in enumerate(wrapped):
            # 先頭チャンクはそのまま、以降は直前チャンクの末尾 overlap 文字を付与
            if idx == 0:
                chunks.append(segment)
            else:
                prev_tail = chunks[-1][-overlap:] if len(chunks[-1]) >= overlap else chunks[-1]
                chunks.append(prev_tail + segment)
        
        logger.info(
            f"✅ テキストを{len(chunks)}個のチャンクに分割 "
            f"(chunk_size={chunk_size}, overlap={overlap})"
        )
        
        return chunks
    
    def merge_chunks(self, chunks: List[str]) -> str:
        """
        split_into_chunks で分割したチャンク列をほぼロスレスで復元する。
        オーバーラップ部分が重複しているので、後方チャンクから
        前方チャンクと重なる先頭 overlap 文字を削ったものを結合する。
        
        Args:
            chunks: チャンクのリスト
            
        Returns:
            結合されたテキスト
        """
        if not chunks:
            return ""
        
        merged = chunks[0]
        for prev, cur in zip(chunks[:-1], chunks[1:]):
            # 現在チャンクの前方が直前チャンク末尾と重なっているはずなので削る
            overlap_len = min(len(prev), len(cur))
            overlap = prev[-overlap_len:]
            if cur.startswith(overlap):
                merged += cur[overlap_len:]
            else:
                # 想定外（手動改変など）の場合はそのまま連結
                merged += cur
        
        logger.info(f"✅ {len(chunks)}個のチャンクを結合")
        
        return merged
    
    def split_by_tokens(
        self,
        text: str,
        max_tokens: int = 512,
        tokenizer=None
    ) -> List[str]:
        """
        トークン数ベースでテキストを分割（高度な分割）
        
        Args:
            text: 入力テキスト
            max_tokens: 最大トークン数
            tokenizer: トークナイザー（省略時は文字数ベースで推定）
            
        Returns:
            チャンクのリスト
        """
        text = self._normalize(text)
        if not text:
            return []
        
        if tokenizer is None:
            # トークナイザーがない場合は文字数ベースで推定
            # 日本語の場合、平均的に1文字≒1.6トークン
            estimated_chunk_size = int(max_tokens / 1.6)
            return self.split_into_chunks(
                text,
                chunk_size=estimated_chunk_size,
                overlap=int(estimated_chunk_size * 0.1)
            )
        
        # トークナイザーがある場合の実装
        chunks = []
        current_chunk = []
        current_tokens = 0
        
        sentences = text.split('。')  # 簡易的な文分割
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            # トークン数計算
            tokens = tokenizer.tokenize(sentence + '。')
            token_count = len(tokens)
            
            if current_tokens + token_count > max_tokens and current_chunk:
                # 現在のチャンクを保存して新しいチャンクを開始
                chunks.append('。'.join(current_chunk) + '。')
                current_chunk = [sentence]
                current_tokens = token_count
            else:
                current_chunk.append(sentence)
                current_tokens += token_count
        
        # 最後のチャンクを追加
        if current_chunk:
            chunks.append('。'.join(current_chunk) + '。')
        
        logger.info(
            f"✅ テキストを{len(chunks)}個のチャンクに分割 "
            f"(max_tokens={max_tokens})"
        )
        
        return chunks
    
    def get_chunk_info(self, chunks: List[str]) -> Dict[str, Any]:
        """
        チャンク情報を取得
        
        Args:
            chunks: チャンクのリスト
            
        Returns:
            チャンク情報の辞書
        """
        if not chunks:
            return {
                "total_chunks": 0,
                "total_chars": 0,
                "avg_chunk_size": 0,
                "min_chunk_size": 0,
                "max_chunk_size": 0
            }
        
        chunk_sizes = [len(chunk) for chunk in chunks]
        
        return {
            "total_chunks": len(chunks),
            "total_chars": sum(chunk_sizes),
            "avg_chunk_size": sum(chunk_sizes) / len(chunks),
            "min_chunk_size": min(chunk_sizes),
            "max_chunk_size": max(chunk_sizes)
        }

# サービスインスタンス作成ヘルパー
def get_text_chunker(
    default_chunk_size: Optional[int] = None,
    default_overlap: Optional[int] = None
) -> TextChunker:
    """テキストチャンカーインスタンス取得"""
    return TextChunker(default_chunk_size, default_overlap)