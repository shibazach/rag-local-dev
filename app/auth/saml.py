"""
SAML認証
SAML authentication with enterprise SSO support
"""

import base64
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from urllib.parse import urlparse, quote_plus
import hashlib
import hmac

from app.config import config, logger


class SAMLConfig:
    """SAML設定"""
    
    def __init__(self):
        # SAML基本設定
        self.entity_id = config.SAML_ENTITY_ID if hasattr(config, 'SAML_ENTITY_ID') else f"{config.APP_NAME}"
        self.sso_url = config.SAML_SSO_URL if hasattr(config, 'SAML_SSO_URL') else None
        self.x509_cert = config.SAML_X509_CERT if hasattr(config, 'SAML_X509_CERT') else None
        self.private_key = config.SAML_PRIVATE_KEY if hasattr(config, 'SAML_PRIVATE_KEY') else None
        
        # メタデータ設定
        self.acs_url = f"{config.BASE_URL}/auth/saml/acs" if hasattr(config, 'BASE_URL') else None
        self.sls_url = f"{config.BASE_URL}/auth/saml/sls" if hasattr(config, 'BASE_URL') else None
        
        # 属性マッピング
        self.attribute_mapping = {
            "email": "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress",
            "name": "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/name",
            "groups": "http://schemas.microsoft.com/ws/2008/06/identity/claims/groups",
            "employee_id": "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/nameidentifier"
        }


class SAMLAuth:
    """SAML認証ハンドラー"""
    
    def __init__(self, config: SAMLConfig):
        self.config = config
        self.enabled = self._check_saml_enabled()
    
    def _check_saml_enabled(self) -> bool:
        """SAML有効性チェック"""
        required_configs = [
            self.config.sso_url,
            self.config.x509_cert,
            self.config.acs_url
        ]
        return all(required_configs)
    
    def generate_auth_request(self, relay_state: Optional[str] = None) -> Dict[str, str]:
        """SAML認証リクエスト生成"""
        if not self.enabled:
            raise ValueError("SAML認証が有効化されていません")
        
        try:
            # AuthnRequest生成
            request_id = self._generate_id()
            issue_instant = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
            
            authn_request = f"""
            <samlp:AuthnRequest
                xmlns:samlp="urn:oasis:names:tc:SAML:2.0:protocol"
                xmlns:saml="urn:oasis:names:tc:SAML:2.0:assertion"
                ID="{request_id}"
                Version="2.0"
                IssueInstant="{issue_instant}"
                Destination="{self.config.sso_url}"
                AssertionConsumerServiceURL="{self.config.acs_url}"
                ProtocolBinding="urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST">
                <saml:Issuer>{self.config.entity_id}</saml:Issuer>
                <samlp:NameIDPolicy
                    Format="urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress"
                    AllowCreate="true"/>
            </samlp:AuthnRequest>
            """.strip()
            
            # Base64エンコード
            encoded_request = base64.b64encode(authn_request.encode()).decode()
            
            # パラメータ構築
            params = {
                "SAMLRequest": encoded_request,
                "RelayState": relay_state or ""
            }
            
            # 署名生成（必要に応じて）
            if self.config.private_key:
                signature = self._sign_request(params)
                params["Signature"] = signature
            
            return {
                "sso_url": self.config.sso_url,
                "params": params,
                "method": "POST"
            }
            
        except Exception as e:
            logger.error(f"SAML認証リクエスト生成エラー: {e}")
            raise
    
    def parse_saml_response(self, saml_response: str) -> Dict[str, Any]:
        """SAMLレスポンス解析"""
        if not self.enabled:
            raise ValueError("SAML認証が有効化されていません")
        
        try:
            # Base64デコード
            decoded_response = base64.b64decode(saml_response).decode()
            
            # XML解析
            root = ET.fromstring(decoded_response)
            
            # 名前空間
            namespaces = {
                'samlp': 'urn:oasis:names:tc:SAML:2.0:protocol',
                'saml': 'urn:oasis:names:tc:SAML:2.0:assertion'
            }
            
            # ステータス確認
            status = root.find('.//samlp:Status/samlp:StatusCode', namespaces)
            if status is None or status.get('Value') != 'urn:oasis:names:tc:SAML:2.0:status:Success':
                raise ValueError("SAML認証が失敗しました")
            
            # アサーション取得
            assertion = root.find('.//saml:Assertion', namespaces)
            if assertion is None:
                raise ValueError("SAMLアサーションが見つかりません")
            
            # ユーザー情報抽出
            user_info = self._extract_user_info(assertion, namespaces)
            
            # 有効期限確認
            self._validate_assertion(assertion, namespaces)
            
            logger.info(f"SAML認証成功: {user_info.get('email')}")
            return user_info
            
        except Exception as e:
            logger.error(f"SAMLレスポンス解析エラー: {e}")
            raise
    
    def generate_logout_request(self, name_id: str, session_index: str = None) -> Dict[str, str]:
        """SAMLログアウトリクエスト生成"""
        if not self.enabled:
            raise ValueError("SAML認証が有効化されていません")
        
        try:
            request_id = self._generate_id()
            issue_instant = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
            
            logout_request = f"""
            <samlp:LogoutRequest
                xmlns:samlp="urn:oasis:names:tc:SAML:2.0:protocol"
                xmlns:saml="urn:oasis:names:tc:SAML:2.0:assertion"
                ID="{request_id}"
                Version="2.0"
                IssueInstant="{issue_instant}"
                Destination="{self.config.sso_url}">
                <saml:Issuer>{self.config.entity_id}</saml:Issuer>
                <saml:NameID Format="urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress">{name_id}</saml:NameID>
                {f'<samlp:SessionIndex>{session_index}</samlp:SessionIndex>' if session_index else ''}
            </samlp:LogoutRequest>
            """.strip()
            
            encoded_request = base64.b64encode(logout_request.encode()).decode()
            
            return {
                "sso_url": self.config.sls_url or self.config.sso_url,
                "params": {"SAMLRequest": encoded_request},
                "method": "GET"
            }
            
        except Exception as e:
            logger.error(f"SAMLログアウトリクエスト生成エラー: {e}")
            raise
    
    def get_metadata(self) -> str:
        """SAMLメタデータ生成"""
        try:
            metadata = f"""
            <md:EntityDescriptor
                xmlns:md="urn:oasis:names:tc:SAML:2.0:metadata"
                entityID="{self.config.entity_id}">
                <md:SPSSODescriptor
                    AuthnRequestsSigned="false"
                    protocolSupportEnumeration="urn:oasis:names:tc:SAML:2.0:protocol">
                    <md:AssertionConsumerService
                        Binding="urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST"
                        Location="{self.config.acs_url}"
                        index="0"/>
                    <md:SingleLogoutService
                        Binding="urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect"
                        Location="{self.config.sls_url}"/>
                </md:SPSSODescriptor>
            </md:EntityDescriptor>
            """.strip()
            
            return metadata
            
        except Exception as e:
            logger.error(f"SAMLメタデータ生成エラー: {e}")
            raise
    
    # プライベートメソッド
    
    def _generate_id(self) -> str:
        """一意ID生成"""
        return f"_{hashlib.sha1(str(datetime.utcnow()).encode()).hexdigest()}"
    
    def _sign_request(self, params: Dict[str, str]) -> str:
        """リクエスト署名生成"""
        # TODO: 実際の署名実装
        # RSA秘密鍵を使用したXML署名
        return "dummy_signature"
    
    def _extract_user_info(self, assertion: ET.Element, namespaces: Dict[str, str]) -> Dict[str, Any]:
        """ユーザー情報抽出"""
        user_info = {}
        
        # NameID取得
        name_id = assertion.find('.//saml:Subject/saml:NameID', namespaces)
        if name_id is not None:
            user_info['name_id'] = name_id.text
            user_info['email'] = name_id.text  # emailAddressフォーマットの場合
        
        # 属性取得
        attributes = assertion.findall('.//saml:AttributeStatement/saml:Attribute', namespaces)
        for attr in attributes:
            attr_name = attr.get('Name')
            attr_values = [val.text for val in attr.findall('saml:AttributeValue', namespaces)]
            
            # 属性マッピング
            for key, mapped_name in self.config.attribute_mapping.items():
                if attr_name == mapped_name:
                    user_info[key] = attr_values[0] if len(attr_values) == 1 else attr_values
                    break
        
        # セッション情報
        authn_statement = assertion.find('.//saml:AuthnStatement', namespaces)
        if authn_statement is not None:
            user_info['session_index'] = authn_statement.get('SessionIndex')
            user_info['authn_instant'] = authn_statement.get('AuthnInstant')
        
        return user_info
    
    def _validate_assertion(self, assertion: ET.Element, namespaces: Dict[str, str]) -> None:
        """アサーション有効性検証"""
        # 有効期限確認
        conditions = assertion.find('.//saml:Conditions', namespaces)
        if conditions is not None:
            not_before = conditions.get('NotBefore')
            not_on_or_after = conditions.get('NotOnOrAfter')
            
            now = datetime.utcnow()
            
            if not_before:
                not_before_time = datetime.fromisoformat(not_before.replace('Z', '+00:00'))
                if now < not_before_time:
                    raise ValueError("SAMLアサーションがまだ有効ではありません")
            
            if not_on_or_after:
                not_on_or_after_time = datetime.fromisoformat(not_on_or_after.replace('Z', '+00:00'))
                if now >= not_on_or_after_time:
                    raise ValueError("SAMLアサーションの有効期限が切れています")
        
        # TODO: 署名検証
        # X.509証明書を使用したXML署名検証


# グローバルインスタンス
saml_config = SAMLConfig()
saml_auth = SAMLAuth(saml_config)