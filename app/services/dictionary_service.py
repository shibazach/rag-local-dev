#!/usr/bin/env python3
"""
辞書管理サービス - 各種辞書ファイルの読み書きを管理
"""

import csv
import os
from typing import List, Dict, Optional
from pathlib import Path


class DictionaryService:
    """辞書ファイルの操作を管理するサービス"""
    
    def __init__(self, dict_base_path: str = "app/config/ocr/dic"):
        """
        辞書サービスを初期化
        
        Args:
            dict_base_path (str): 辞書ファイルのベースパス
        """
        self.dict_base_path = Path(dict_base_path)
        
        # 辞書ファイルのマッピング
        self.dict_files = {
            "一般用語": "known_words_common.csv",
            "専門用語": "known_words_custom.csv", 
            "誤字修正": "ocr_word_mistakes.csv",
            "ユーザー辞書": "user_dict.csv"
        }
    
    def get_dictionary_content(self, dict_type: str) -> str:
        """
        指定した辞書の内容を取得
        
        Args:
            dict_type (str): 辞書タイプ（一般用語、専門用語、誤字修正、ユーザー辞書）
            
        Returns:
            str: 辞書の内容（テキスト形式）
        """
        if dict_type not in self.dict_files:
            raise ValueError(f"未知の辞書タイプ: {dict_type}")
        
        file_path = self.dict_base_path / self.dict_files[dict_type]
        
        try:
            if not file_path.exists():
                return ""
            
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            raise Exception(f"辞書ファイル読み込みエラー: {e}")
    
    def save_dictionary_content(self, dict_type: str, content: str) -> None:
        """
        指定した辞書に内容を保存
        
        Args:
            dict_type (str): 辞書タイプ（一般用語、専門用語、誤字修正、ユーザー辞書）
            content (str): 保存する内容
        """
        if dict_type not in self.dict_files:
            raise ValueError(f"未知の辞書タイプ: {dict_type}")
        
        file_path = self.dict_base_path / self.dict_files[dict_type]
        
        try:
            # ディレクトリが存在しない場合は作成
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
        except Exception as e:
            raise Exception(f"辞書ファイル保存エラー: {e}")
    
    def get_dictionary_title(self, dict_type: str) -> str:
        """
        辞書タイプに対応するタイトルを取得
        
        Args:
            dict_type (str): 辞書タイプ
            
        Returns:
            str: 表示用タイトル
        """
        titles = {
            "一般用語": "一般用語辞書の編集",
            "専門用語": "専門用語辞書の編集", 
            "誤字修正": "誤字修正辞書の編集",
            "ユーザー辞書": "ユーザー辞書の編集"
        }
        return titles.get(dict_type, f"{dict_type}辞書の編集")
    
    def validate_dictionary_content(self, dict_type: str, content: str) -> bool:
        """
        辞書の内容を検証
        
        Args:
            dict_type (str): 辞書タイプ
            content (str): 検証する内容
            
        Returns:
            bool: 内容が有効かどうか
        """
        # 基本的な検証（空でも有効とする）
        if content is None:
            return False
        
        # ユーザー辞書の場合はMeCab形式の簡単な検証
        if dict_type == "ユーザー辞書" and content.strip():
            lines = content.strip().split('\n')
            for line in lines:
                if line.strip() and len(line.split(',')) < 13:
                    return False
        
        return True
    
    def backup_dictionary(self, dict_type: str) -> None:
        """
        辞書ファイルのバックアップを作成
        
        Args:
            dict_type (str): 辞書タイプ
        """
        if dict_type not in self.dict_files:
            raise ValueError(f"未知の辞書タイプ: {dict_type}")
        
        file_path = self.dict_base_path / self.dict_files[dict_type]
        backup_dir = self.dict_base_path / "back"
        
        if file_path.exists():
            backup_dir.mkdir(exist_ok=True)
            backup_path = backup_dir / f"{self.dict_files[dict_type]}.backup"
            
            try:
                with open(file_path, 'r', encoding='utf-8') as src:
                    content = src.read()
                with open(backup_path, 'w', encoding='utf-8') as dst:
                    dst.write(content)
            except Exception as e:
                raise Exception(f"バックアップ作成エラー: {e}")


# グローバルインスタンス
dictionary_service = DictionaryService()
