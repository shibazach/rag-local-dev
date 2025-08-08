"""
OCR誤字補正サービス - Prototype統合版
MeCabと誤字辞書を使用した日本語テキスト補正
"""

import os
import csv
import MeCab
from typing import List, Dict, Set, Optional
from pathlib import Path

from app.config import config, logger

class SpellChecker:
    """OCR誤字補正サービス"""
    
    def __init__(self, dict_dir: Optional[str] = None):
        """
        Args:
            dict_dir: 辞書ファイルディレクトリ（省略時はデフォルト）
        """
        if dict_dir is None:
            self.dict_dir = Path(__file__).parent / "dic"
        else:
            self.dict_dir = Path(dict_dir)
        
        # MeCab初期化
        self.mecab = None
        self._init_mecab()
        
        # 辞書キャッシュ
        self._known_words_cache = None
        self._kanji_mistakes_cache = None
    
    def _init_mecab(self):
        """MeCab初期化"""
        try:
            # システムのMeCab辞書を使用
            self.mecab = MeCab.Tagger("-Owakati")
            logger.info("MeCab初期化成功")
        except Exception as e:
            logger.warning(f"MeCab初期化失敗（デフォルト設定）: {e}")
            try:
                # 代替パスを試行
                self.mecab = MeCab.Tagger("-d /usr/lib/x86_64-linux-gnu/mecab/dic/mecab-ipadic-neologd -Owakati")
                logger.info("MeCab初期化成功（NEologd辞書）")
            except Exception as e2:
                logger.error(f"MeCab初期化に失敗しました: {e2}")
                self.mecab = None
    
    def load_known_words(self, csv_paths: List[str]) -> Set[str]:
        """
        既知単語を複数CSVから読み込み
        
        Args:
            csv_paths: CSVファイルパスのリスト（相対パス）
            
        Returns:
            既知単語のセット
        """
        if self._known_words_cache is not None:
            return self._known_words_cache
            
        words = set()
        
        for path in csv_paths:
            abs_path = self.dict_dir / path
            if not abs_path.exists():
                logger.warning(f"辞書ファイルが見つかりません: {abs_path}")
                continue
                
            try:
                with open(abs_path, encoding="utf-8") as f:
                    reader = csv.reader(f)
                    for row in reader:
                        if row and row[0].strip():
                            words.add(row[0].strip())
                logger.info(f"既知単語辞書読み込み: {abs_path} ({len(words)}語)")
                
            except Exception as e:
                logger.error(f"辞書読み込みエラー: {abs_path} - {e}")
        
        self._known_words_cache = words
        return words
    
    def load_kanji_mistakes(self, csv_path: str) -> Dict[str, str]:
        """
        誤字辞書をCSVから読み込み
        
        Args:
            csv_path: CSVファイルパス（相対パス）
            
        Returns:
            誤字→正字の辞書
        """
        if self._kanji_mistakes_cache is not None:
            return self._kanji_mistakes_cache
            
        mapping = {}
        abs_path = self.dict_dir / csv_path
        
        if not abs_path.exists():
            logger.warning(f"誤字辞書ファイルが見つかりません: {abs_path}")
            return mapping
        
        try:
            with open(abs_path, encoding="utf-8") as f:
                reader = csv.reader(f)
                next(reader, None)  # ヘッダースキップ
                
                for row in reader:
                    if len(row) >= 2:
                        wrong, correct = row[0].strip(), row[1].strip()
                        if wrong and correct:
                            mapping[wrong] = correct
                            
            logger.info(f"誤字辞書読み込み: {abs_path} ({len(mapping)}パターン)")
            
        except Exception as e:
            logger.error(f"誤字辞書読み込みエラー: {abs_path} - {e}")
        
        self._kanji_mistakes_cache = mapping
        return mapping
    
    def tokenize(self, text: str) -> List[str]:
        """
        MeCab分かち書き
        
        Args:
            text: 入力テキスト
            
        Returns:
            トークンリスト
        """
        if self.mecab is None:
            logger.warning("MeCabが初期化されていません")
            return text.split()  # フォールバック：空白で分割
        
        try:
            return self.mecab.parse(text).strip().split()
        except Exception as e:
            logger.error(f"MeCab分かち書きエラー: {e}")
            return text.split()  # フォールバック
    
    def correct_text(
        self,
        text: str,
        known_word_paths: Optional[List[str]] = None,
        kanji_mistakes_path: Optional[str] = None
    ) -> str:
        """
        メイン補正関数
        
        Args:
            text: 入力テキスト
            known_word_paths: 既知単語辞書パス（省略時はデフォルト）
            kanji_mistakes_path: 誤字辞書パス（省略時はデフォルト）
            
        Returns:
            補正後テキスト
        """
        # デフォルト辞書パス
        if known_word_paths is None:
            known_word_paths = [
                "known_words_common.csv",
                "known_words_custom.csv"
            ]
        if kanji_mistakes_path is None:
            kanji_mistakes_path = "ocr_word_mistakes.csv"
        
        # 辞書読み込み
        known_words = self.load_known_words(known_word_paths)
        kanji_mistakes = self.load_kanji_mistakes(kanji_mistakes_path)
        
        # 誤字補正
        corrected_text = text
        correction_count = 0
        
        for wrong, correct in kanji_mistakes.items():
            if wrong not in known_words:
                # 置換実行
                if wrong in corrected_text:
                    corrected_text = corrected_text.replace(wrong, correct)
                    correction_count += 1
                    logger.debug(f"誤字補正: {wrong} → {correct}")
        
        if correction_count > 0:
            logger.info(f"✅ {correction_count}箇所の誤字を補正しました")
        
        return corrected_text
    
    def create_default_dictionaries(self):
        """デフォルト辞書ファイルを作成（初期セットアップ用）"""
        self.dict_dir.mkdir(parents=True, exist_ok=True)
        
        # 一般的な既知単語辞書
        common_words_path = self.dict_dir / "known_words_common.csv"
        if not common_words_path.exists():
            with open(common_words_path, "w", encoding="utf-8") as f:
                writer = csv.writer(f)
                # サンプルデータ
                for word in ["株式会社", "有限会社", "合同会社", "一般社団法人"]:
                    writer.writerow([word])
            logger.info(f"デフォルト既知単語辞書を作成: {common_words_path}")
        
        # カスタム既知単語辞書
        custom_words_path = self.dict_dir / "known_words_custom.csv"
        if not custom_words_path.exists():
            with open(custom_words_path, "w", encoding="utf-8") as f:
                writer = csv.writer(f)
                # 空ファイルとして作成
            logger.info(f"カスタム既知単語辞書を作成: {custom_words_path}")
        
        # OCR誤字辞書
        mistakes_path = self.dict_dir / "ocr_word_mistakes.csv"
        if not mistakes_path.exists():
            with open(mistakes_path, "w", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["誤字", "正字"])
                # サンプルデータ
                mistakes = [
                    ("巾", "中"),
                    ("カ", "力"),
                    ("エ", "工"),
                    ("夕", "タ"),
                    ("口", "ロ"),
                ]
                for wrong, correct in mistakes:
                    writer.writerow([wrong, correct])
            logger.info(f"OCR誤字辞書を作成: {mistakes_path}")

# サービスインスタンス作成ヘルパー
def get_spell_checker(dict_dir: Optional[str] = None) -> SpellChecker:
    """スペルチェッカーインスタンス取得"""
    return SpellChecker(dict_dir)