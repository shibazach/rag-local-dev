"""
テキスト品質スコアリングサービス - Prototype統合版
OCR前後のテキスト品質を評価
"""

import re
from typing import Optional

from app.config import logger

class TextScorer:
    """テキスト品質スコアリングサービス"""
    
    def __init__(self):
        # 日本語文字パターン
        self.japanese_pattern = re.compile(r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]')
        # 英数字パターン
        self.alphanumeric_pattern = re.compile(r'[a-zA-Z0-9]')
        # 記号・特殊文字パターン
        self.special_char_pattern = re.compile(r'[^\w\s\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]')
    
    def score_text_quality(
        self,
        original_text: str,
        refined_text: str,
        lang: str = "ja"
    ) -> float:
        """
        テキスト品質スコアを算出（0.0-1.0）
        
        Args:
            original_text: 元のテキスト（OCR後）
            refined_text: 整形後のテキスト（LLM後）
            lang: 言語コード
            
        Returns:
            品質スコア（0.0-1.0）
        """
        if not original_text or not refined_text:
            return 0.0
        
        scores = []
        
        # 1. 文字数の変化率（大幅な削除・追加はペナルティ）
        len_ratio = len(refined_text) / len(original_text)
        if 0.8 <= len_ratio <= 1.2:
            len_score = 1.0
        elif 0.5 <= len_ratio <= 1.5:
            len_score = 0.7
        else:
            len_score = 0.3
        scores.append(len_score)
        
        # 2. 言語の一貫性
        if lang == "ja":
            # 日本語の含有率
            ja_chars_orig = len(self.japanese_pattern.findall(original_text))
            ja_chars_refined = len(self.japanese_pattern.findall(refined_text))
            
            if ja_chars_refined > 0:
                ja_ratio = ja_chars_refined / len(refined_text)
                lang_score = min(ja_ratio * 1.5, 1.0)  # 日本語が多いほど高スコア
            else:
                lang_score = 0.3
        else:
            # 英語の場合は英数字の含有率
            alnum_chars = len(self.alphanumeric_pattern.findall(refined_text))
            if alnum_chars > 0:
                alnum_ratio = alnum_chars / len(refined_text)
                lang_score = min(alnum_ratio * 1.5, 1.0)
            else:
                lang_score = 0.3
        scores.append(lang_score)
        
        # 3. 特殊文字・記号の削減率
        special_orig = len(self.special_char_pattern.findall(original_text))
        special_refined = len(self.special_char_pattern.findall(refined_text))
        
        if special_orig > 0:
            reduction_rate = 1 - (special_refined / special_orig)
            special_score = min(reduction_rate * 1.2, 1.0)
        else:
            special_score = 0.8
        scores.append(special_score)
        
        # 4. 改行・空白の正規化
        # 連続する空白・改行の削減
        whitespace_orig = len(re.findall(r'\s{2,}', original_text))
        whitespace_refined = len(re.findall(r'\s{2,}', refined_text))
        
        if whitespace_orig > 0:
            whitespace_reduction = 1 - (whitespace_refined / whitespace_orig)
            whitespace_score = min(whitespace_reduction * 1.5, 1.0)
        else:
            whitespace_score = 0.9
        scores.append(whitespace_score)
        
        # 5. 文の完全性（句読点の存在）
        if lang == "ja":
            # 日本語の句読点
            punctuation_count = refined_text.count('。') + refined_text.count('、')
            if punctuation_count > 0:
                # 100文字あたりの句読点数で評価
                punct_ratio = punctuation_count / (len(refined_text) / 100)
                punct_score = min(punct_ratio / 10, 1.0)  # 10個/100文字で満点
            else:
                punct_score = 0.3
        else:
            # 英語のピリオド・カンマ
            punctuation_count = refined_text.count('.') + refined_text.count(',')
            if punctuation_count > 0:
                punct_ratio = punctuation_count / (len(refined_text) / 100)
                punct_score = min(punct_ratio / 5, 1.0)  # 5個/100文字で満点
            else:
                punct_score = 0.3
        scores.append(punct_score)
        
        # 総合スコア（重み付き平均）
        weights = [0.2, 0.3, 0.2, 0.15, 0.15]  # 各スコアの重み
        total_score = sum(s * w for s, w in zip(scores, weights))
        
        logger.debug(
            f"品質スコア詳細: "
            f"文字数={len_score:.2f}, "
            f"言語一貫性={lang_score:.2f}, "
            f"特殊文字削減={special_score:.2f}, "
            f"空白正規化={whitespace_score:.2f}, "
            f"文完全性={punct_score:.2f}, "
            f"総合={total_score:.2f}"
        )
        
        return total_score
    
    def analyze_text_quality(
        self,
        text: str,
        lang: Optional[str] = None
    ) -> dict:
        """
        単一テキストの品質分析
        
        Args:
            text: 分析対象テキスト
            lang: 言語コード（省略時は自動判定）
            
        Returns:
            品質分析結果の辞書
        """
        if not text:
            return {
                "quality": "empty",
                "score": 0.0,
                "issues": ["テキストが空です"]
            }
        
        # 言語自動判定
        if lang is None:
            ja_chars = len(self.japanese_pattern.findall(text))
            en_chars = len(self.alphanumeric_pattern.findall(text))
            lang = "ja" if ja_chars > en_chars else "en"
        
        issues = []
        
        # 文字数チェック
        if len(text) < 10:
            issues.append("テキストが短すぎます")
        
        # 特殊文字の割合チェック
        special_chars = len(self.special_char_pattern.findall(text))
        special_ratio = special_chars / len(text)
        if special_ratio > 0.3:
            issues.append(f"特殊文字が多すぎます（{special_ratio:.1%}）")
        
        # 連続空白・改行チェック
        whitespace_issues = len(re.findall(r'\s{5,}', text))
        if whitespace_issues > 0:
            issues.append(f"過剰な空白・改行が{whitespace_issues}箇所あります")
        
        # 言語の一貫性チェック
        if lang == "ja":
            ja_ratio = len(self.japanese_pattern.findall(text)) / len(text)
            if ja_ratio < 0.3:
                issues.append("日本語の含有率が低いです")
        
        # 総合評価
        if not issues:
            quality = "good"
            score = 0.9
        elif len(issues) <= 1:
            quality = "fair"
            score = 0.7
        elif len(issues) <= 2:
            quality = "poor"
            score = 0.5
        else:
            quality = "bad"
            score = 0.3
        
        return {
            "quality": quality,
            "score": score,
            "language": lang,
            "length": len(text),
            "issues": issues,
            "stats": {
                "special_char_ratio": special_ratio,
                "whitespace_issues": whitespace_issues,
                "japanese_ratio": ja_ratio if lang == "ja" else None
            }
        }

# サービスインスタンス作成ヘルパー
def get_text_scorer() -> TextScorer:
    """テキストスコアラーインスタンス取得"""
    return TextScorer()