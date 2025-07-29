#!/usr/bin/env python3
# new/services/text_processor.py
# テキスト処理サービス

import re
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
import json
import hashlib

from ..config import LOGGER

class TextProcessor:
    """テキスト処理クラス"""
    
    def __init__(self):
        self.chunk_size = 1000  # デフォルトチャンクサイズ
        self.overlap_size = 200  # オーバーラップサイズ
    
    def clean_text(self, text: str) -> str:
        """テキストのクリーニング"""
        if not text:
            return ""
        
        # 基本的なクリーニング
        text = re.sub(r'\s+', ' ', text)  # 複数の空白を単一に
        text = re.sub(r'\n\s*\n', '\n', text)  # 空行の削除
        text = text.strip()
        
        return text
    
    def detect_language(self, text: str) -> str:
        """言語検出（簡易版）"""
        if not text:
            return "unknown"
        
        # 日本語文字の検出
        japanese_chars = len(re.findall(r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]', text))
        total_chars = len(text)
        
        if japanese_chars / total_chars > 0.1:
            return "ja"
        else:
            return "en"
    
    def split_into_chunks(self, text: str, chunk_size: int = None, overlap: int = None) -> List[Dict[str, Any]]:
        """テキストをチャンクに分割"""
        if not text:
            return []
        
        chunk_size = chunk_size or self.chunk_size
        overlap = overlap or self.overlap_size
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            
            # 文の境界で分割
            if end < len(text):
                # 句読点で分割を試行
                for punct in ['。', '！', '？', '.', '!', '?', '\n']:
                    last_punct = text.rfind(punct, start, end)
                    if last_punct > start + chunk_size // 2:  # 半分以上進んでいれば分割
                        end = last_punct + 1
                        break
            
            chunk_text = text[start:end].strip()
            if chunk_text:
                chunk_id = self._generate_chunk_id(chunk_text, start)
                chunks.append({
                    "chunk_id": chunk_id,
                    "text": chunk_text,
                    "start_pos": start,
                    "end_pos": end,
                    "size": len(chunk_text)
                })
            
            start = end - overlap
            if start >= len(text):
                break
        
        return chunks
    
    def _generate_chunk_id(self, text: str, position: int) -> str:
        """チャンクIDを生成"""
        content_hash = hashlib.md5(text.encode('utf-8')).hexdigest()[:8]
        return f"chunk_{position}_{content_hash}"
    
    def extract_metadata(self, text: str) -> Dict[str, Any]:
        """テキストからメタデータを抽出"""
        metadata = {
            "total_length": len(text),
            "word_count": len(text.split()),
            "line_count": len(text.split('\n')),
            "language": self.detect_language(text),
            "has_japanese": bool(re.search(r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]', text)),
            "has_english": bool(re.search(r'[a-zA-Z]', text)),
            "has_numbers": bool(re.search(r'\d', text))
        }
        
        # 段落数
        paragraphs = [p for p in text.split('\n\n') if p.strip()]
        metadata["paragraph_count"] = len(paragraphs)
        
        return metadata
    
    def process_text(self, text: str, file_id: str) -> Dict[str, Any]:
        """テキストの完全処理"""
        try:
            LOGGER.info(f"📝 テキスト処理開始: ファイルID={file_id}")
            
            # テキストクリーニング
            cleaned_text = self.clean_text(text)
            LOGGER.info(f"✅ テキストクリーニング完了: {len(cleaned_text)}文字")
            
            # メタデータ抽出
            metadata = self.extract_metadata(cleaned_text)
            LOGGER.info(f"✅ メタデータ抽出完了: {metadata}")
            
            # チャンク分割
            chunks = self.split_into_chunks(cleaned_text)
            LOGGER.info(f"✅ チャンク分割完了: {len(chunks)}個のチャンク")
            
            # 結果を構築
            result = {
                "file_id": file_id,
                "raw_text": text,
                "cleaned_text": cleaned_text,
                "chunks": chunks,
                "metadata": metadata,
                "total_chunks": len(chunks),
                "processing_info": {
                    "chunk_size": self.chunk_size,
                    "overlap_size": self.overlap_size,
                    "language": metadata["language"]
                }
            }
            
            LOGGER.info(f"🎉 テキスト処理完了: ファイルID={file_id}")
            return result
            
        except Exception as e:
            LOGGER.error(f"テキスト処理エラー: {e}")
            raise 