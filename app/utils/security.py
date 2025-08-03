"""
セキュリティユーティリティ
Security utilities for input validation, sanitization, and protection
"""

import re
import html
import hashlib
import secrets
import ipaddress
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union
from urllib.parse import urlparse
import jwt
from passlib.context import CryptContext

from app.config import config, logger
from app.utils.logging import security_log


# パスワードハッシュ化
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class InputValidator:
    """入力値バリデーション"""
    
    # 危険なパターン
    DANGEROUS_PATTERNS = [
        r'<script[^>]*>.*?</script>',  # XSS
        r'javascript:',               # JavaScript URL
        r'on\w+\s*=',                # イベントハンドラー
        r'expression\s*\(',          # CSS expression
        r'@import',                  # CSS import
        r'<iframe[^>]*>',            # iframe
        r'<object[^>]*>',            # object
        r'<embed[^>]*>',             # embed
        r'<link[^>]*>',              # link
        r'<meta[^>]*>',              # meta
    ]
    
    # SQLインジェクションパターン
    SQL_INJECTION_PATTERNS = [
        r'(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION)\b)',
        r'(\b(OR|AND)\s+\d+\s*=\s*\d+)',
        r'[;\'"\\]',
        r'(-{2}|/\*|\*/)',
    ]
    
    @classmethod
    def validate_string(
        cls,
        value: str,
        max_length: int = 1000,
        allow_html: bool = False,
        field_name: str = "入力値"
    ) -> str:
        """文字列バリデーション"""
        if not isinstance(value, str):
            raise ValueError(f"{field_name}は文字列である必要があります")
        
        if len(value) > max_length:
            raise ValueError(f"{field_name}が長すぎます（最大{max_length}文字）")
        
        # XSSチェック
        if not allow_html:
            for pattern in cls.DANGEROUS_PATTERNS:
                if re.search(pattern, value, re.IGNORECASE):
                    security_log.suspicious_activity(
                        f"危険なパターン検出: {pattern} in {field_name}",
                        description=f"入力値: {value[:100]}..."
                    )
                    raise ValueError(f"{field_name}に危険な文字列が含まれています")
        
        return value
    
    @classmethod
    def validate_email(cls, email: str) -> str:
        """メールアドレスバリデーション"""
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            raise ValueError("有効なメールアドレスを入力してください")
        
        if len(email) > 255:
            raise ValueError("メールアドレスが長すぎます")
        
        return email.lower()
    
    @classmethod
    def validate_filename(cls, filename: str) -> str:
        """ファイル名バリデーション"""
        # 危険な文字チェック
        dangerous_chars = r'[<>:"/\\|?*\x00-\x1f]'
        if re.search(dangerous_chars, filename):
            raise ValueError("ファイル名に使用できない文字が含まれています")
        
        # 予約語チェック（Windows）
        reserved_names = [
            'CON', 'PRN', 'AUX', 'NUL',
            'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
            'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
        ]
        
        base_name = filename.split('.')[0].upper()
        if base_name in reserved_names:
            raise ValueError("予約されたファイル名は使用できません")
        
        if len(filename) > 255:
            raise ValueError("ファイル名が長すぎます")
        
        return filename
    
    @classmethod
    def validate_sql_safety(cls, value: str, field_name: str = "値") -> str:
        """SQLインジェクション対策"""
        for pattern in cls.SQL_INJECTION_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                security_log.suspicious_activity(
                    f"SQLインジェクション疑いの入力: {field_name}",
                    description=f"入力値: {value[:100]}..."
                )
                raise ValueError(f"{field_name}に不正な文字列が含まれています")
        
        return value
    
    @classmethod
    def validate_url(cls, url: str) -> str:
        """URL バリデーション"""
        try:
            parsed = urlparse(url)
            
            # スキームチェック
            if parsed.scheme not in ['http', 'https']:
                raise ValueError("HTTPまたはHTTPSのURLのみ許可されています")
            
            # ホスト名チェック
            if not parsed.netloc:
                raise ValueError("有効なホスト名が必要です")
            
            # ローカルアドレスチェック（本番環境）
            if not config.DEBUG:
                try:
                    ip = ipaddress.ip_address(parsed.hostname)
                    if ip.is_private or ip.is_loopback:
                        raise ValueError("プライベートアドレスへのアクセスは許可されていません")
                except ValueError:
                    pass  # IPアドレスではない場合はスルー
            
            return url
            
        except Exception as e:
            raise ValueError(f"無効なURL: {e}")


class InputSanitizer:
    """入力値サニタイゼーション"""
    
    @staticmethod
    def sanitize_html(value: str) -> str:
        """HTMLサニタイゼーション"""
        return html.escape(value, quote=True)
    
    @staticmethod
    def sanitize_sql(value: str) -> str:
        """SQL文字列エスケープ"""
        # SQLAlchemyのパラメータ化クエリを使用することを推奨
        # ここでは基本的なエスケープのみ
        return value.replace("'", "''").replace('"', '""')
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """ファイル名サニタイゼーション"""
        # 危険な文字を削除
        safe_filename = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '', filename)
        
        # 連続するドットを単一に
        safe_filename = re.sub(r'\.{2,}', '.', safe_filename)
        
        # 先頭末尾の空白・ドット削除
        safe_filename = safe_filename.strip(' .')
        
        # 空の場合のフォールバック
        if not safe_filename:
            safe_filename = f"file_{secrets.token_hex(4)}"
        
        return safe_filename
    
    @staticmethod
    def sanitize_search_query(query: str) -> str:
        """検索クエリサニタイゼーション"""
        # 特殊文字エスケープ
        escaped = re.escape(query)
        
        # 長すぎるクエリを切り詰め
        if len(escaped) > 500:
            escaped = escaped[:500]
        
        return escaped


class RateLimiter:
    """レート制限"""
    
    def __init__(self):
        self.requests = {}  # IP -> [timestamp, ...]
        self.blocked_ips = {}  # IP -> blocked_until
    
    def is_allowed(
        self,
        ip_address: str,
        limit: int = 100,
        window: int = 3600,  # 1時間
        block_duration: int = 1800  # 30分
    ) -> bool:
        """レート制限チェック"""
        now = datetime.utcnow()
        
        # ブロック中かチェック
        if ip_address in self.blocked_ips:
            blocked_until = self.blocked_ips[ip_address]
            if now < blocked_until:
                return False
            else:
                del self.blocked_ips[ip_address]
        
        # リクエスト履歴取得
        if ip_address not in self.requests:
            self.requests[ip_address] = []
        
        request_times = self.requests[ip_address]
        
        # 古いリクエストを削除
        cutoff_time = now - timedelta(seconds=window)
        request_times[:] = [t for t in request_times if t > cutoff_time]
        
        # 制限チェック
        if len(request_times) >= limit:
            # ブロック実行
            self.blocked_ips[ip_address] = now + timedelta(seconds=block_duration)
            security_log.suspicious_activity(
                f"レート制限超過: {ip_address}",
                ip_address=ip_address,
                description=f"{window}秒間に{len(request_times)}リクエスト"
            )
            return False
        
        # リクエスト記録
        request_times.append(now)
        return True
    
    def cleanup(self):
        """古いデータクリーンアップ"""
        now = datetime.utcnow()
        cutoff_time = now - timedelta(hours=24)
        
        # 古いリクエスト履歴削除
        for ip in list(self.requests.keys()):
            self.requests[ip] = [t for t in self.requests[ip] if t > cutoff_time]
            if not self.requests[ip]:
                del self.requests[ip]
        
        # 期限切れブロック削除
        expired_blocks = [ip for ip, until in self.blocked_ips.items() if now >= until]
        for ip in expired_blocks:
            del self.blocked_ips[ip]


class TokenManager:
    """トークン管理"""
    
    @staticmethod
    def generate_secure_token(length: int = 32) -> str:
        """セキュアトークン生成"""
        return secrets.token_urlsafe(length)
    
    @staticmethod
    def create_jwt_token(
        payload: Dict[str, Any],
        expires_in: int = 3600,  # 1時間
        secret_key: str = None
    ) -> str:
        """JWTトークン作成"""
        if not secret_key:
            secret_key = config.SESSION_SECRET_KEY
        
        payload_copy = payload.copy()
        payload_copy["exp"] = datetime.utcnow() + timedelta(seconds=expires_in)
        payload_copy["iat"] = datetime.utcnow()
        
        return jwt.encode(payload_copy, secret_key, algorithm="HS256")
    
    @staticmethod
    def verify_jwt_token(token: str, secret_key: str = None) -> Dict[str, Any]:
        """JWTトークン検証"""
        if not secret_key:
            secret_key = config.SESSION_SECRET_KEY
        
        try:
            payload = jwt.decode(token, secret_key, algorithms=["HS256"])
            return payload
        except jwt.ExpiredSignatureError:
            raise ValueError("トークンの有効期限が切れています")
        except jwt.InvalidTokenError:
            raise ValueError("無効なトークンです")
    
    @staticmethod
    def hash_password(password: str) -> str:
        """パスワードハッシュ化"""
        return pwd_context.hash(password)
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """パスワード検証"""
        return pwd_context.verify(plain_password, hashed_password)


class IPWhitelist:
    """IP許可リスト管理"""
    
    def __init__(self, whitelist: List[str] = None):
        self.whitelist = whitelist or []
        self.compiled_networks = []
        self._compile_networks()
    
    def _compile_networks(self):
        """ネットワークアドレス事前コンパイル"""
        self.compiled_networks = []
        for addr in self.whitelist:
            try:
                network = ipaddress.ip_network(addr, strict=False)
                self.compiled_networks.append(network)
            except ValueError:
                logger.warning(f"無効なIPアドレス/ネットワーク: {addr}")
    
    def is_allowed(self, ip_address: str) -> bool:
        """IP許可チェック"""
        if not self.compiled_networks:
            return True  # 制限なし
        
        try:
            ip = ipaddress.ip_address(ip_address)
            return any(ip in network for network in self.compiled_networks)
        except ValueError:
            return False
    
    def add_ip(self, ip_address: str):
        """IP追加"""
        self.whitelist.append(ip_address)
        self._compile_networks()
    
    def remove_ip(self, ip_address: str):
        """IP削除"""
        if ip_address in self.whitelist:
            self.whitelist.remove(ip_address)
            self._compile_networks()


# グローバルインスタンス
rate_limiter = RateLimiter()
admin_ip_whitelist = IPWhitelist(
    getattr(config, 'ADMIN_IP_WHITELIST', [])
)