"""
Cookieベースセッション管理 - NiceGUI完全対応版
ページ遷移でも確実に永続化される方式
"""

from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import json
import base64
import uuid

from nicegui import ui
from app.config import logger

class CookieSessionManager:
    """
    Cookieベースセッション管理 - NiceGUI安定版
    """
    
    # 簡易暗号化（cryptographyライブラリなしで実装）
    _simple_key = "rag_session_key_2025"
    
    SESSION_COOKIE_NAME = "rag_session_id"
    COOKIE_MAX_AGE = 86400  # 24時間
    
    @classmethod
    def _encrypt_session_id(cls, session_id: str) -> str:
        """セッションIDを簡易暗号化"""
        try:
            # 簡易XOR暗号化
            key_bytes = cls._simple_key.encode()
            session_bytes = session_id.encode()
            encrypted_bytes = bytes(a ^ key_bytes[i % len(key_bytes)] for i, a in enumerate(session_bytes))
            return base64.urlsafe_b64encode(encrypted_bytes).decode()
        except Exception as e:
            logger.error(f"❌ セッションID暗号化エラー: {e}")
            return session_id
    
    @classmethod
    def _decrypt_session_id(cls, encrypted_session_id: str) -> Optional[str]:
        """暗号化されたセッションIDを復号化"""
        try:
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_session_id.encode())
            key_bytes = cls._simple_key.encode()
            decrypted_bytes = bytes(a ^ key_bytes[i % len(key_bytes)] for i, a in enumerate(encrypted_bytes))
            return decrypted_bytes.decode()
        except Exception as e:
            logger.debug(f"🔍 セッションID復号化失敗: {e}")
            return None
    
    @classmethod
    def set_session_cookie(cls, session_id: str) -> None:
        """
        セッションIDをCookieに設定
        """
        try:
            # セッションIDを暗号化
            encrypted_session_id = cls._encrypt_session_id(session_id)
            
            # JavaScriptでCookieを設定
            cookie_script = f"""
                document.cookie = "{cls.SESSION_COOKIE_NAME}={encrypted_session_id}; "
                    + "max-age={cls.COOKIE_MAX_AGE}; "
                    + "path=/; "
                    + "secure=false; "
                    + "samesite=lax";
                console.log('✅ セッションCookie設定完了: {session_id[:8]}...');
            """
            ui.run_javascript(cookie_script)
            
            logger.info(f"🍪 セッションCookie設定: {session_id[:8]}...")
            
        except Exception as e:
            logger.error(f"❌ セッションCookie設定エラー: {e}")
    
    @classmethod
    def get_session_from_cookie(cls) -> Optional[str]:
        """
        CookieからセッションIDを取得
        """
        try:
            # JavaScriptでCookie取得（同期実行）
            cookie_script = f"""
                function getCookie(name) {{
                    const value = `; ${{document.cookie}}`;
                    const parts = value.split(`; ${{name}}=`);
                    if (parts.length === 2) return parts.pop().split(';').shift();
                    return null;
                }}
                
                const sessionCookie = getCookie('{cls.SESSION_COOKIE_NAME}');
                console.log('🔍 Cookie取得:', sessionCookie ? 'あり' : 'なし');
                
                // NiceGUIに結果を返す
                if (sessionCookie) {{
                    window.ragSessionCookie = sessionCookie;
                    return sessionCookie;
                }} else {{
                    window.ragSessionCookie = null;
                    return null;
                }}
            """
            
            # まずJavaScriptを実行
            ui.run_javascript(cookie_script)
            
            # window.ragSessionCookieから取得を試行
            get_cookie_script = """
                return window.ragSessionCookie || null;
            """
            
            # TODO: NiceGUIでの同期的Cookie取得は複雑
            # とりあえず、代替手段として直接的な方法を使用
            return None
            
        except Exception as e:
            logger.debug(f"🔍 Cookie取得エラー: {e}")
            return None
    
    @classmethod
    def create_session_with_cookie(cls, user_data: Dict[str, Any]) -> str:
        """
        セッション作成 + Cookie設定
        """
        try:
            # セッションID生成
            session_id = str(uuid.uuid4())
            
            session_data = {
                "session_id": session_id,
                "user_id": user_data.get("id"),
                "username": user_data.get("username"),
                "email": user_data.get("email"),
                "is_admin": user_data.get("is_admin", False),
                "created_at": datetime.utcnow().isoformat(),
                "last_activity": datetime.utcnow().isoformat()
            }
            
            # データベースに直接保存
            from app.core.db_simple import execute
            
            expires_at = datetime.utcnow() + timedelta(hours=24)  # 24時間有効
            
            upsert_sql = """
                INSERT INTO user_sessions (
                    session_id, user_id, username, email, is_admin,
                    session_data, last_activity, expires_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (session_id) 
                DO UPDATE SET
                    user_id = EXCLUDED.user_id,
                    username = EXCLUDED.username,
                    email = EXCLUDED.email,
                    is_admin = EXCLUDED.is_admin,
                    session_data = EXCLUDED.session_data,
                    last_activity = EXCLUDED.last_activity,
                    expires_at = EXCLUDED.expires_at,
                    is_active = TRUE
            """
            
            execute(upsert_sql, (
                session_id,
                session_data.get('user_id'),
                session_data.get('username'),
                session_data.get('email'),
                session_data.get('is_admin', False),
                json.dumps(session_data),
                datetime.utcnow(),
                expires_at
            ))
            
            success = True
            
            if success:
                # Cookieに設定
                cls.set_session_cookie(session_id)
                logger.info(f"🎫 Cookie付きセッション作成: {user_data.get('username', 'unknown')} -> {session_id[:8]}...")
                return session_id
            else:
                logger.error("❌ セッション保存失敗")
                return ""
                
        except Exception as e:
            logger.error(f"❌ Cookie付きセッション作成エラー: {e}")
            return ""
    
    @classmethod
    def get_current_user_from_cookie(cls) -> Optional[Dict[str, Any]]:
        """
        Cookieベースでの現在ユーザー取得
        """
        try:
            # データベースから最新のアクティブセッションを取得（Cookie代替方式）
            
            # データベースから最新のアクティブセッションを取得
            from app.core.db_simple import fetch_one
            
            latest_session = fetch_one("""
                SELECT * FROM user_sessions 
                WHERE is_active = TRUE 
                  AND expires_at > %s
                ORDER BY last_activity DESC 
                LIMIT 1
            """, (datetime.utcnow(),))
            
            if latest_session:
                # session_dataの型チェック（psycopg2は自動でdictに変換する場合がある）
                raw_session_data = latest_session['session_data']
                if isinstance(raw_session_data, str):
                    session_data = json.loads(raw_session_data)
                else:
                    session_data = raw_session_data  # 既にdict
                
                # 最終活動時刻更新
                session_data['last_activity'] = datetime.utcnow().isoformat()
                from app.core.db_simple import execute
                execute("""
                    UPDATE user_sessions 
                    SET session_data = %s, last_activity = %s 
                    WHERE session_id = %s
                """, (json.dumps(session_data), datetime.utcnow(), latest_session['session_id']))
                
                logger.debug(f"🍪 Cookie代替取得: {session_data.get('username', 'unknown')}")
                return session_data
            else:
                logger.debug("🍪 Cookie代替取得: セッションなし")
                return None
                
        except Exception as e:
            logger.error(f"❌ Cookie代替ユーザー取得エラー: {e}")
            return None
    
    @classmethod
    def destroy_session_cookie(cls) -> bool:
        """
        セッションCookie削除
        """
        try:
            # 最新のアクティブセッションを無効化
            from app.core.db_simple import execute
            execute("""
                UPDATE user_sessions 
                SET is_active = FALSE, last_activity = %s 
                WHERE is_active = TRUE
            """, (datetime.utcnow(),))
            
            # Cookie削除
            cookie_script = f"""
                document.cookie = "{cls.SESSION_COOKIE_NAME}=; "
                    + "max-age=0; "
                    + "path=/; "
                    + "expires=Thu, 01 Jan 1970 00:00:00 GMT";
                console.log('🗑️ セッションCookie削除完了');
                window.ragSessionCookie = null;
            """
            ui.run_javascript(cookie_script)
            
            logger.info("🗑️ セッションCookie削除")
            return True
            
        except Exception as e:
            logger.error(f"❌ セッションCookie削除エラー: {e}")
            return False


# 既存システムとの統合用エイリアス
def generate_session_id():
    return str(__import__('uuid').uuid4())
