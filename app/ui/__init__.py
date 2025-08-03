"""
NiceGUI統一UIモジュール
Unified UI module with theme and components
"""

from .themes.base import RAGTheme
from .components import (
    RAGHeader,
    RAGSidebar,
    RAGFooter,
    RAGBreadcrumb,
    RAGContainer,
    RAGPageLayout,
    RAGInput,
    RAGSelect,
    RAGTextArea,
    RAGButton,
    RAGFileUpload,
    RAGForm,
    RAGTable,
    RAGDataTable,
    RAGStatusTable
)

# NiceGUIアプリケーション初期化
def init_nicegui_app(fastapi_app):
    """NiceGUI統合アプリケーション初期化"""
    try:
        from nicegui import ui
        from .app import create_nicegui_pages
        
        # ⭐ 正しい順序: 先にページ定義
        create_nicegui_pages()
        
        # その後でFastAPIと統合
        ui.run_with(
            fastapi_app,
            mount_path="/ui",
            title="R&D RAGシステム"
        )
        
        return True
        
    except ImportError as e:
        raise ImportError(f"NiceGUI統合エラー: {e}")
    except Exception as e:
        raise Exception(f"NiceGUI初期化エラー: {e}")

__all__ = [
    "RAGTheme",
    "RAGHeader",
    "RAGSidebar",
    "RAGFooter", 
    "RAGBreadcrumb",
    "RAGContainer",
    "RAGPageLayout",
    "RAGInput",
    "RAGSelect",
    "RAGTextArea",
    "RAGButton", 
    "RAGFileUpload",
    "RAGForm",
    "RAGTable",
    "RAGDataTable",
    "RAGStatusTable",
    "init_nicegui_app"
]
