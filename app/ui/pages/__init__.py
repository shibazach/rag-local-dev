"""
UI Pages - NiceGUIページ定義
"""

from .auth import LoginPage
from .index import IndexPage
from .chat import ChatPage
from .files import FilesPage
from .upload import UploadPage
from .ocr_adjustment import OCRAdjustmentPage
from .data_registration import DataRegistrationPage
from .arrangement_test import ArrangementTestPage
from .admin import AdminPage

__all__ = [
    'LoginPage',
    'IndexPage', 
    'ChatPage',
    'FilesPage',
    'UploadPage',
    'OCRAdjustmentPage',
    'DataRegistrationPage',
    'ArrangementTestPage',
    'AdminPage'
]