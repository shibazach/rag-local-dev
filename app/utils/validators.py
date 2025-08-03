"""
バリデーター
Custom validators for Pydantic models and API inputs
"""

import re
from typing import Any, Dict, List, Optional
from datetime import datetime
from pathlib import Path

from pydantic import field_validator
from app.config import config


class FileValidators:
    """ファイル関連バリデーター"""
    
    @staticmethod
    def validate_file_extension(filename: str) -> str:
        """ファイル拡張子バリデーション"""
        if not filename:
            raise ValueError("ファイル名が空です")
        
        file_path = Path(filename)
        extension = file_path.suffix.lower()
        
        if extension not in config.ALLOWED_EXTENSIONS:
            allowed = ", ".join(config.ALLOWED_EXTENSIONS)
            raise ValueError(f"サポートされていないファイル形式です。許可形式: {allowed}")
        
        return filename
    
    @staticmethod
    def validate_file_size(size: int) -> int:
        """ファイルサイズバリデーション"""
        if size <= 0:
            raise ValueError("ファイルサイズが無効です")
        
        if size > config.MAX_UPLOAD_SIZE:
            max_mb = config.MAX_UPLOAD_SIZE // (1024 * 1024)
            raise ValueError(f"ファイルサイズが上限を超えています（最大: {max_mb}MB）")
        
        return size
    
    @staticmethod
    def validate_filename_safety(filename: str) -> str:
        """ファイル名安全性バリデーション"""
        # 基本的な文字チェック
        if re.search(r'[<>:"/\\|?*\x00-\x1f]', filename):
            raise ValueError("ファイル名に使用できない文字が含まれています")
        
        # 長さチェック
        if len(filename) > 255:
            raise ValueError("ファイル名が長すぎます（最大255文字）")
        
        # 予約語チェック
        reserved = ['CON', 'PRN', 'AUX', 'NUL', 'COM1', 'COM2', 'COM3', 'COM4', 
                   'COM5', 'COM6', 'COM7', 'COM8', 'COM9', 'LPT1', 'LPT2', 'LPT3', 
                   'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9']
        
        name_without_ext = Path(filename).stem.upper()
        if name_without_ext in reserved:
            raise ValueError("予約されたファイル名は使用できません")
        
        return filename


class ProcessingValidators:
    """処理関連バリデーター"""
    
    @staticmethod
    def validate_llm_model(model: str) -> str:
        """LLMモデルバリデーション"""
        allowed_models = ['phi4-mini', 'gemma:7b', 'llama2', 'mistral']
        
        if model not in allowed_models:
            allowed_str = ", ".join(allowed_models)
            raise ValueError(f"サポートされていないLLMモデルです。許可モデル: {allowed_str}")
        
        return model
    
    @staticmethod
    def validate_ocr_engine(engine: str) -> str:
        """OCRエンジンバリデーション"""
        allowed_engines = ['ocrmypdf', 'tesseract', 'paddleocr']
        
        if engine not in allowed_engines:
            allowed_str = ", ".join(allowed_engines)
            raise ValueError(f"サポートされていないOCRエンジンです。許可エンジン: {allowed_str}")
        
        return engine
    
    @staticmethod
    def validate_embedding_option(option: str) -> str:
        """埋め込みオプションバリデーション"""
        if option not in config.EMBEDDING_OPTIONS:
            available = ", ".join(config.EMBEDDING_OPTIONS.keys())
            raise ValueError(f"無効な埋め込みオプションです。利用可能: {available}")
        
        return option
    
    @staticmethod
    def validate_quality_threshold(threshold: float) -> float:
        """品質閾値バリデーション"""
        if not 0.0 <= threshold <= 1.0:
            raise ValueError("品質閾値は0.0〜1.0の範囲で指定してください")
        
        return threshold
    
    @staticmethod
    def validate_chunk_size(size: int) -> int:
        """チャンクサイズバリデーション"""
        if not 100 <= size <= 4000:
            raise ValueError("チャンクサイズは100〜4000の範囲で指定してください")
        
        return size
    
    @staticmethod
    def validate_timeout(timeout: int) -> int:
        """タイムアウトバリデーション"""
        if timeout < 0:
            raise ValueError("タイムアウトは0以上を指定してください")
        
        if timeout > 3600:  # 1時間
            raise ValueError("タイムアウトは3600秒以下を指定してください")
        
        return timeout


class ChatValidators:
    """チャット関連バリデーター"""
    
    @staticmethod
    def validate_search_mode(mode: str) -> str:
        """検索モードバリデーション"""
        allowed_modes = ['chunk_merge', 'file_separate']
        
        if mode not in allowed_modes:
            allowed_str = ", ".join(allowed_modes)
            raise ValueError(f"無効な検索モードです。許可モード: {allowed_str}")
        
        return mode
    
    @staticmethod
    def validate_search_limit(limit: int) -> int:
        """検索結果件数バリデーション"""
        if not 1 <= limit <= 100:
            raise ValueError("検索結果件数は1〜100の範囲で指定してください")
        
        return limit
    
    @staticmethod
    def validate_min_score(score: float) -> float:
        """最小スコアバリデーション"""
        if not 0.0 <= score <= 1.0:
            raise ValueError("最小スコアは0.0〜1.0の範囲で指定してください")
        
        return score
    
    @staticmethod
    def validate_query_length(query: str) -> str:
        """クエリ長バリデーション"""
        if not query or not query.strip():
            raise ValueError("検索クエリを入力してください")
        
        if len(query) > 1000:
            raise ValueError("検索クエリが長すぎます（最大1000文字）")
        
        return query.strip()


class UserValidators:
    """ユーザー関連バリデーター"""
    
    @staticmethod
    def validate_email(email: str) -> str:
        """メールアドレスバリデーション"""
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        
        if not re.match(email_pattern, email):
            raise ValueError("有効なメールアドレスを入力してください")
        
        if len(email) > 254:
            raise ValueError("メールアドレスが長すぎます")
        
        return email.lower()
    
    @staticmethod
    def validate_username(username: str) -> str:
        """ユーザー名バリデーション"""
        if not username or len(username.strip()) < 2:
            raise ValueError("ユーザー名は2文字以上入力してください")
        
        if len(username) > 50:
            raise ValueError("ユーザー名が長すぎます（最大50文字）")
        
        # 英数字とアンダースコア、ハイフンのみ許可
        if not re.match(r'^[a-zA-Z0-9_-]+$', username):
            raise ValueError("ユーザー名は英数字、アンダースコア、ハイフンのみ使用できます")
        
        return username.strip()
    
    @staticmethod
    def validate_password(password: str) -> str:
        """パスワードバリデーション"""
        if len(password) < 8:
            raise ValueError("パスワードは8文字以上入力してください")
        
        if len(password) > 128:
            raise ValueError("パスワードが長すぎます（最大128文字）")
        
        # 複雑性チェック
        if not re.search(r'[A-Za-z]', password):
            raise ValueError("パスワードには英字を含めてください")
        
        if not re.search(r'\d', password):
            raise ValueError("パスワードには数字を含めてください")
        
        return password
    
    @staticmethod
    def validate_role(role: str) -> str:
        """ロールバリデーション"""
        allowed_roles = ['guest', 'user', 'analyst', 'admin', 'super_admin']
        
        if role not in allowed_roles:
            allowed_str = ", ".join(allowed_roles)
            raise ValueError(f"無効なロールです。許可ロール: {allowed_str}")
        
        return role


class SystemValidators:
    """システム関連バリデーター"""
    
    @staticmethod
    def validate_log_level(level: str) -> str:
        """ログレベルバリデーション"""
        allowed_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        
        level_upper = level.upper()
        if level_upper not in allowed_levels:
            allowed_str = ", ".join(allowed_levels)
            raise ValueError(f"無効なログレベルです。許可レベル: {allowed_str}")
        
        return level_upper
    
    @staticmethod
    def validate_ip_address(ip: str) -> str:
        """IPアドレスバリデーション"""
        import ipaddress
        
        try:
            ipaddress.ip_address(ip)
            return ip
        except ValueError:
            raise ValueError("有効なIPアドレスを入力してください")
    
    @staticmethod
    def validate_url(url: str) -> str:
        """URLバリデーション"""
        from urllib.parse import urlparse
        
        try:
            result = urlparse(url)
            if not all([result.scheme, result.netloc]):
                raise ValueError("有効なURLを入力してください")
            
            if result.scheme not in ['http', 'https']:
                raise ValueError("HTTPまたはHTTPSのURLを入力してください")
            
            return url
            
        except Exception:
            raise ValueError("有効なURLを入力してください")
    
    @staticmethod
    def validate_port(port: int) -> int:
        """ポート番号バリデーション"""
        if not 1 <= port <= 65535:
            raise ValueError("ポート番号は1〜65535の範囲で指定してください")
        
        return port


class DateTimeValidators:
    """日時関連バリデーター"""
    
    @staticmethod
    def validate_future_datetime(dt: datetime) -> datetime:
        """未来日時バリデーション"""
        if dt <= datetime.utcnow():
            raise ValueError("未来の日時を指定してください")
        
        return dt
    
    @staticmethod
    def validate_past_datetime(dt: datetime) -> datetime:
        """過去日時バリデーション"""
        if dt >= datetime.utcnow():
            raise ValueError("過去の日時を指定してください")
        
        return dt
    
    @staticmethod
    def validate_datetime_range(start: datetime, end: datetime) -> tuple:
        """日時範囲バリデーション"""
        if start >= end:
            raise ValueError("開始日時は終了日時より前である必要があります")
        
        # 範囲制限（例：1年以内）
        from datetime import timedelta
        max_range = timedelta(days=365)
        
        if end - start > max_range:
            raise ValueError("日時範囲が大きすぎます（最大1年）")
        
        return start, end


# Pydantic用カスタムバリデーター関数
def file_extension_validator(cls, v):
    """Pydantic用ファイル拡張子バリデーター"""
    return FileValidators.validate_file_extension(v)

def email_validator(cls, v):
    """Pydantic用メールバリデーター"""
    return UserValidators.validate_email(v)

def password_validator(cls, v):
    """Pydantic用パスワードバリデーター"""
    return UserValidators.validate_password(v)

def quality_threshold_validator(cls, v):
    """Pydantic用品質閾値バリデーター"""
    return ProcessingValidators.validate_quality_threshold(v)

def search_limit_validator(cls, v):
    """Pydantic用検索件数バリデーター"""
    return ChatValidators.validate_search_limit(v)