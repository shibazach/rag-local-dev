"""
LLMユーティリティ - Prototype統合版
言語判定などの共通ユーティリティ関数
"""

import re
from typing import Optional

from app.config import logger

def detect_language(text: str, force_lang: Optional[str] = None) -> str:
    """
    テキストの言語を判定
    
    Args:
        text: 判定対象テキスト
        force_lang: 強制言語指定
        
    Returns:
        言語コード（ja, en等）
    """
    if force_lang:
        return force_lang
    
    if not text:
        return "ja"  # デフォルト
    
    # 日本語文字のパターン
    japanese_pattern = re.compile(r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]')
    # 英字のパターン
    english_pattern = re.compile(r'[a-zA-Z]')
    
    # 各言語の文字数をカウント
    ja_count = len(japanese_pattern.findall(text))
    en_count = len(english_pattern.findall(text))
    
    # テキスト全体に対する割合で判定
    text_len = len(text)
    ja_ratio = ja_count / text_len if text_len > 0 else 0
    en_ratio = en_count / text_len if text_len > 0 else 0
    
    # 日本語が10%以上含まれていれば日本語と判定
    if ja_ratio > 0.1:
        lang = "ja"
    # 英語が50%以上含まれていれば英語と判定
    elif en_ratio > 0.5:
        lang = "en"
    else:
        # デフォルトは日本語
        lang = "ja"
    
    logger.debug(
        f"言語判定: {lang} "
        f"(日本語: {ja_ratio:.1%}, 英語: {en_ratio:.1%})"
    )
    
    return lang

def estimate_tokens(text: str, lang: Optional[str] = None) -> int:
    """
    テキストのトークン数を推定
    
    Args:
        text: 対象テキスト
        lang: 言語コード（省略時は自動判定）
        
    Returns:
        推定トークン数
    """
    if not text:
        return 0
    
    if lang is None:
        lang = detect_language(text)
    
    # 言語別の推定係数
    if lang == "ja":
        # 日本語: 1文字 ≈ 1.6トークン
        return int(len(text) * 1.6)
    elif lang == "en":
        # 英語: 1単語 ≈ 1.3トークン
        words = text.split()
        return int(len(words) * 1.3)
    else:
        # その他: 文字数ベース
        return int(len(text) * 1.5)

def truncate_text(
    text: str,
    max_length: int,
    suffix: str = "..."
) -> str:
    """
    テキストを指定長で切り詰め
    
    Args:
        text: 対象テキスト
        max_length: 最大長
        suffix: 末尾に付ける文字列
        
    Returns:
        切り詰められたテキスト
    """
    if len(text) <= max_length:
        return text
    
    # suffixの長さを考慮して切り詰め
    truncate_length = max_length - len(suffix)
    if truncate_length <= 0:
        return suffix
    
    return text[:truncate_length] + suffix

def normalize_whitespace(text: str) -> str:
    """
    空白文字を正規化
    
    Args:
        text: 対象テキスト
        
    Returns:
        正規化されたテキスト
    """
    # 全角スペースを半角に統一
    text = text.replace('　', ' ')
    
    # タブを空白に変換
    text = text.replace('\t', ' ')
    
    # 連続する空白を1つに圧縮
    text = re.sub(r' {2,}', ' ', text)
    
    # 連続する改行を最大2つに圧縮
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # 行頭行末の空白を削除
    lines = text.split('\n')
    lines = [line.strip() for line in lines]
    text = '\n'.join(lines)
    
    return text.strip()

def extract_keywords(
    text: str,
    lang: Optional[str] = None,
    max_keywords: int = 10
) -> list[str]:
    """
    テキストからキーワードを抽出（簡易版）
    
    Args:
        text: 対象テキスト
        lang: 言語コード
        max_keywords: 最大キーワード数
        
    Returns:
        キーワードのリスト
    """
    if not text:
        return []
    
    if lang is None:
        lang = detect_language(text)
    
    # 簡易的な実装（頻出単語の抽出）
    # TODO: より高度な実装（TF-IDF, TextRank等）に置き換え
    
    # ストップワード（簡易版）
    if lang == "ja":
        stopwords = {
            'の', 'に', 'は', 'を', 'た', 'が', 'で', 'て', 'と', 'し',
            'れ', 'さ', 'ある', 'いる', 'も', 'する', 'から', 'な',
            'こと', 'として', 'い', 'や', 'など', 'なっ', 'ない',
            'この', 'ため', 'その', 'あっ', 'よう', 'また', 'もの'
        }
    else:
        stopwords = {
            'the', 'be', 'to', 'of', 'and', 'a', 'in', 'that', 'have',
            'i', 'it', 'for', 'not', 'on', 'with', 'he', 'as', 'you',
            'do', 'at', 'this', 'but', 'his', 'by', 'from'
        }
    
    # 単語分割（簡易版）
    if lang == "ja":
        # 日本語は文字種で分割（簡易的）
        words = re.findall(r'[\u4E00-\u9FAF]+|[\u30A0-\u30FF]+|[a-zA-Z]+', text)
    else:
        # 英語は空白で分割
        words = re.findall(r'\b\w+\b', text.lower())
    
    # 単語の出現回数をカウント
    word_count = {}
    for word in words:
        if len(word) >= 2 and word not in stopwords:
            word_count[word] = word_count.get(word, 0) + 1
    
    # 頻度順にソート
    sorted_words = sorted(word_count.items(), key=lambda x: x[1], reverse=True)
    
    # 上位N個を返す
    keywords = [word for word, count in sorted_words[:max_keywords]]
    
    return keywords

# サービスインスタンス作成は不要（関数のみのモジュール）