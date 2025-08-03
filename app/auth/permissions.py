"""
権限管理
Role-based access control and permissions
"""

from enum import Enum
from typing import List, Dict, Any, Optional, Set
from functools import wraps
from fastapi import HTTPException, Depends

from app.config import logger


class Role(Enum):
    """ユーザーロール"""
    GUEST = "guest"           # ゲスト（読み取り限定）
    USER = "user"             # 一般ユーザー
    ANALYST = "analyst"       # アナリスト（分析権限）
    ADMIN = "admin"           # 管理者
    SUPER_ADMIN = "super_admin"  # スーパー管理者


class Permission(Enum):
    """権限"""
    # ファイル関連
    FILE_READ = "file:read"
    FILE_UPLOAD = "file:upload"
    FILE_DELETE = "file:delete"
    FILE_ADMIN = "file:admin"
    
    # 処理関連
    PROCESSING_START = "processing:start"
    PROCESSING_MONITOR = "processing:monitor"
    PROCESSING_CANCEL = "processing:cancel"
    PROCESSING_ADMIN = "processing:admin"
    
    # チャット関連
    CHAT_USE = "chat:use"
    CHAT_HISTORY = "chat:history"
    CHAT_ADMIN = "chat:admin"
    
    # システム関連
    SYSTEM_READ = "system:read"
    SYSTEM_CONFIG = "system:config"
    SYSTEM_ADMIN = "system:admin"
    
    # ユーザー管理
    USER_READ = "user:read"
    USER_MANAGE = "user:manage"
    USER_ADMIN = "user:admin"


class RolePermissions:
    """ロール権限マッピング"""
    
    ROLE_PERMISSIONS = {
        Role.GUEST: {
            Permission.FILE_READ,
            Permission.CHAT_USE
        },
        
        Role.USER: {
            Permission.FILE_READ,
            Permission.FILE_UPLOAD,
            Permission.PROCESSING_START,
            Permission.PROCESSING_MONITOR,
            Permission.CHAT_USE,
            Permission.CHAT_HISTORY
        },
        
        Role.ANALYST: {
            Permission.FILE_READ,
            Permission.FILE_UPLOAD,
            Permission.FILE_DELETE,  # 自分のファイルのみ
            Permission.PROCESSING_START,
            Permission.PROCESSING_MONITOR,
            Permission.PROCESSING_CANCEL,
            Permission.CHAT_USE,
            Permission.CHAT_HISTORY,
            Permission.SYSTEM_READ
        },
        
        Role.ADMIN: {
            Permission.FILE_READ,
            Permission.FILE_UPLOAD,
            Permission.FILE_DELETE,
            Permission.FILE_ADMIN,
            Permission.PROCESSING_START,
            Permission.PROCESSING_MONITOR,
            Permission.PROCESSING_CANCEL,
            Permission.PROCESSING_ADMIN,
            Permission.CHAT_USE,
            Permission.CHAT_HISTORY,
            Permission.CHAT_ADMIN,
            Permission.SYSTEM_READ,
            Permission.SYSTEM_CONFIG,
            Permission.USER_READ,
            Permission.USER_MANAGE
        },
        
        Role.SUPER_ADMIN: {perm for perm in Permission}  # 全権限
    }
    
    @classmethod
    def get_permissions(cls, role: Role) -> Set[Permission]:
        """ロールの権限取得"""
        return cls.ROLE_PERMISSIONS.get(role, set())
    
    @classmethod
    def has_permission(cls, role: Role, permission: Permission) -> bool:
        """権限チェック"""
        return permission in cls.get_permissions(role)


class PermissionChecker:
    """権限チェッカー"""
    
    def __init__(self, user: Dict[str, Any]):
        self.user = user
        self.role = Role(user.get("role", Role.GUEST.value))
        self.permissions = RolePermissions.get_permissions(self.role)
        self.groups = user.get("groups", [])
        self.user_id = user.get("id")
    
    def has_permission(self, permission: Permission) -> bool:
        """基本権限チェック"""
        return permission in self.permissions
    
    def has_any_permission(self, permissions: List[Permission]) -> bool:
        """いずれかの権限を持っているかチェック"""
        return any(perm in self.permissions for perm in permissions)
    
    def has_all_permissions(self, permissions: List[Permission]) -> bool:
        """すべての権限を持っているかチェック"""
        return all(perm in self.permissions for perm in permissions)
    
    def can_access_file(self, file_owner_id: str, permission: Permission) -> bool:
        """ファイルアクセス権限チェック"""
        # 基本権限チェック
        if not self.has_permission(permission):
            return False
        
        # 管理者は全ファイルアクセス可能
        if self.role in [Role.ADMIN, Role.SUPER_ADMIN]:
            return True
        
        # ファイル管理権限があれば全ファイルアクセス可能
        if self.has_permission(Permission.FILE_ADMIN):
            return True
        
        # 自分のファイルのみアクセス可能
        return self.user_id == file_owner_id
    
    def can_manage_user(self, target_user: Dict[str, Any]) -> bool:
        """ユーザー管理権限チェック"""
        if not self.has_permission(Permission.USER_MANAGE):
            return False
        
        target_role = Role(target_user.get("role", Role.GUEST.value))
        
        # スーパー管理者は全ユーザー管理可能
        if self.role == Role.SUPER_ADMIN:
            return True
        
        # 管理者は自分より低い権限のユーザーのみ管理可能
        if self.role == Role.ADMIN:
            return target_role in [Role.GUEST, Role.USER, Role.ANALYST]
        
        return False
    
    def can_access_processing_job(self, job_owner_id: str) -> bool:
        """処理ジョブアクセス権限チェック"""
        # 管理者は全ジョブアクセス可能
        if self.role in [Role.ADMIN, Role.SUPER_ADMIN]:
            return True
        
        # 処理管理権限があれば全ジョブアクセス可能
        if self.has_permission(Permission.PROCESSING_ADMIN):
            return True
        
        # 自分のジョブのみアクセス可能
        return self.user_id == job_owner_id
    
    def get_accessible_resources(self, resource_type: str) -> List[str]:
        """アクセス可能リソース取得"""
        # TODO: リソース別のアクセス制御実装
        if resource_type == "files":
            if self.has_permission(Permission.FILE_ADMIN):
                return ["*"]  # 全ファイル
            else:
                return [self.user_id]  # 自分のファイルのみ
        
        return []


def require_permission(permission: Permission):
    """権限必須デコレータ"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # current_userを取得（FastAPI Dependsから）
            current_user = kwargs.get('current_user')
            if not current_user:
                raise HTTPException(status_code=401, detail="認証が必要です")
            
            checker = PermissionChecker(current_user)
            if not checker.has_permission(permission):
                raise HTTPException(
                    status_code=403,
                    detail=f"権限が不足しています: {permission.value}"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def require_any_permission(permissions: List[Permission]):
    """いずれかの権限必須デコレータ"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_user = kwargs.get('current_user')
            if not current_user:
                raise HTTPException(status_code=401, detail="認証が必要です")
            
            checker = PermissionChecker(current_user)
            if not checker.has_any_permission(permissions):
                perm_names = [p.value for p in permissions]
                raise HTTPException(
                    status_code=403,
                    detail=f"いずれかの権限が必要です: {', '.join(perm_names)}"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def require_role(required_role: Role):
    """ロール必須デコレータ"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_user = kwargs.get('current_user')
            if not current_user:
                raise HTTPException(status_code=401, detail="認証が必要です")
            
            user_role = Role(current_user.get("role", Role.GUEST.value))
            
            # ロール階層チェック
            role_hierarchy = [Role.GUEST, Role.USER, Role.ANALYST, Role.ADMIN, Role.SUPER_ADMIN]
            required_level = role_hierarchy.index(required_role)
            user_level = role_hierarchy.index(user_role)
            
            if user_level < required_level:
                raise HTTPException(
                    status_code=403,
                    detail=f"ロール権限が不足しています: {required_role.value}以上が必要"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


class ResourcePermission:
    """リソース固有権限チェック"""
    
    @staticmethod
    def check_file_access(
        user: Dict[str, Any],
        file_owner_id: str,
        action: Permission
    ) -> bool:
        """ファイルアクセス権限チェック"""
        checker = PermissionChecker(user)
        return checker.can_access_file(file_owner_id, action)
    
    @staticmethod
    def check_processing_access(
        user: Dict[str, Any],
        job_owner_id: str
    ) -> bool:
        """処理ジョブアクセス権限チェック"""
        checker = PermissionChecker(user)
        return checker.can_access_processing_job(job_owner_id)
    
    @staticmethod
    def filter_accessible_files(
        user: Dict[str, Any],
        files: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """アクセス可能ファイルフィルタリング"""
        checker = PermissionChecker(user)
        
        if checker.has_permission(Permission.FILE_ADMIN):
            return files  # 管理者は全ファイル表示
        
        # 自分のファイルのみ表示
        return [f for f in files if f.get("created_by") == checker.user_id]


# グループベース権限（将来拡張用）
class GroupPermissions:
    """グループベース権限管理"""
    
    # 部署別権限設定例
    DEPARTMENT_PERMISSIONS = {
        "research": {
            Permission.FILE_READ,
            Permission.FILE_UPLOAD,
            Permission.PROCESSING_START,
            Permission.CHAT_USE,
            Permission.SYSTEM_READ
        },
        "admin": {
            Permission.FILE_ADMIN,
            Permission.PROCESSING_ADMIN,
            Permission.SYSTEM_ADMIN,
            Permission.USER_ADMIN
        }
    }
    
    @classmethod
    def get_group_permissions(cls, groups: List[str]) -> Set[Permission]:
        """グループ権限取得"""
        permissions = set()
        for group in groups:
            permissions.update(cls.DEPARTMENT_PERMISSIONS.get(group, set()))
        return permissions