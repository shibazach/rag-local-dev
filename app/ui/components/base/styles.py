"""
基本スタイル管理システム
継承可能なスタイルビルダーと共通スタイル定義
"""
from typing import Dict, Optional, Union


class StyleBuilder:
    """
    スタイル継承とマージ機能を提供
    
    Usage:
        base_style = {'margin': '0', 'padding': '8px'}
        additional = {'padding': '16px', 'border': '1px solid #ccc'}
        final_style = StyleBuilder.merge_styles(base_style, additional)
        # Result: {'margin': '0', 'padding': '16px', 'border': '1px solid #ccc'}
    """
    
    @staticmethod
    def merge_styles(
        base_styles: Dict[str, str], 
        additional_styles: Optional[Dict[str, str]] = None
    ) -> Dict[str, str]:
        """スタイル辞書をマージ（additionalが優先）"""
        result = base_styles.copy()
        if additional_styles:
            result.update(additional_styles)
        return result
    
    @staticmethod
    def to_string(styles: Dict[str, str]) -> str:
        """スタイル辞書をCSS文字列に変換"""
        if not styles:
            return ""
        return "; ".join([f"{k}: {v}" for k, v in styles.items()]) + ";"
    
    @classmethod
    def build(
        cls,
        base_styles: Dict[str, str],
        additional_styles: Optional[Dict[str, str]] = None
    ) -> str:
        """ベーススタイルと追加スタイルをマージしてCSS文字列を生成"""
        merged = cls.merge_styles(base_styles, additional_styles)
        return cls.to_string(merged)


class CommonStyles:
    """
    プロジェクト全体で使用する共通スタイル定義
    """
    
    # === 基本色定義 ===
    # プライマリカラー（NiceGUI標準のブルー）
    COLOR_PRIMARY = '#2563eb'
    COLOR_PRIMARY_HOVER = '#1d4ed8'
    COLOR_PRIMARY_LIGHT = '#dbeafe'
    
    # グレースケール
    COLOR_GRAY_50 = '#f9fafb'
    COLOR_GRAY_100 = '#f3f4f6'
    COLOR_GRAY_200 = '#e5e7eb'
    COLOR_GRAY_300 = '#d1d5db'
    COLOR_GRAY_400 = '#9ca3af'
    COLOR_GRAY_500 = '#6b7280'
    COLOR_GRAY_600 = '#4b5563'
    COLOR_GRAY_700 = '#374151'
    COLOR_GRAY_800 = '#1f2937'
    COLOR_GRAY_900 = '#111827'
    
    # セマンティックカラー
    COLOR_SUCCESS = '#10b981'
    COLOR_WARNING = '#f59e0b'
    COLOR_ERROR = '#ef4444'
    COLOR_INFO = '#3b82f6'
    
    # === 統一ヘッダー色 ===
    HEADER_BACKGROUND = COLOR_GRAY_100  # シンプルグレー
    HEADER_COLOR = COLOR_GRAY_800
    HEADER_BORDER = COLOR_GRAY_200
    
    # === 基本レイアウト ===
    BASE_LAYOUT = {
        'margin': '0',
        'padding': '0',
        'box-sizing': 'border-box'
    }
    
    # === フレックスボックス ===
    FLEX_COLUMN = {
        'display': 'flex',
        'flex-direction': 'column'
    }
    
    FLEX_ROW = {
        'display': 'flex',
        'flex-direction': 'row'
    }
    
    FLEX_CENTER = {
        'display': 'flex',
        'justify-content': 'center',
        'align-items': 'center'
    }
    
    FLEX_BETWEEN = {
        'display': 'flex',
        'justify-content': 'space-between',
        'align-items': 'center'
    }
    
    # === パネル基本 ===
    PANEL_BASE = {
        **BASE_LAYOUT,
        'background': 'white',
        'border-radius': '8px',
        'box-shadow': '0 1px 3px rgba(0, 0, 0, 0.1)',
        'border': f'1px solid {COLOR_GRAY_200}',
        'overflow': 'hidden'
    }
    
    # === ヘッダー基本（統一グレー） ===
    HEADER_BASE = {
        'padding': '8px 12px',
        'height': '32px',
        'background': HEADER_BACKGROUND,
        'color': HEADER_COLOR,
        'border-bottom': f'1px solid {HEADER_BORDER}',
        **FLEX_BETWEEN,
        'box-sizing': 'border-box',
        'flex-shrink': '0'
    }
    
    # === コンテンツエリア基本 ===
    CONTENT_BASE = {
        'flex': '1',
        'overflow': 'auto',
        'padding': '12px'
    }
    
    # === フッター基本 ===
    FOOTER_BASE = {
        'padding': '8px 12px',
        'height': '32px',
        'background': COLOR_GRAY_50,
        'border-top': f'1px solid {COLOR_GRAY_200}',
        **FLEX_BETWEEN,
        'box-sizing': 'border-box',
        'flex-shrink': '0',
        'font-size': '11px',
        'color': COLOR_GRAY_600
    }
    
    # === 基本サイズ ===
    SPACING_XS = '4px'
    SPACING_SM = '8px'
    SPACING_MD = '12px'
    SPACING_LG = '16px'
    SPACING_XL = '24px'
    
    FONT_SIZE_XS = '11px'
    FONT_SIZE_SM = '12px'
    FONT_SIZE_BASE = '13px'
    FONT_SIZE_MD = '14px'
    FONT_SIZE_LG = '16px'
    
    HEADER_HEIGHT = '32px'
    FOOTER_HEIGHT = '32px'
    
    # === フォーム要素 ===
    FORM_ROW = {
        'display': 'flex',
        'align-items': 'center',
        'margin-bottom': SPACING_SM,
        'gap': SPACING_SM
    }
    
    FORM_LABEL = {
        'font-size': FONT_SIZE_BASE,
        'color': COLOR_GRAY_700,
        'font-weight': '500',
        'flex-shrink': '0'
    }
    
    FORM_CONTROL = {
        'flex': '1',
        'font-size': FONT_SIZE_BASE
    }