"""
認証管理 - 簡易実装
循環インポートを避けるため独立モジュール化
"""

class SimpleAuth:
    """簡易認証クラス"""
    _authenticated = False
    
    @classmethod
    def login(cls, username: str, password: str) -> bool:
        """ログイン処理"""
        if username == "admin" and password == "password":
            cls._authenticated = True
            return True
        return False
    
    @classmethod
    def logout(cls):
        """ログアウト処理"""
        cls._authenticated = False
    
    @classmethod
    def is_authenticated(cls) -> bool:
        """認証状態確認"""
        return cls._authenticated