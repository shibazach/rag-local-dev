"""
共通スタイル定義 - new/系統一デザインシステム
"""

class CommonStyles:
    """共通スタイル定数"""
    
    # === フォント設定 ===
    FONT_FAMILY = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif"
    
    # フォントサイズ
    FONT_SIZE_XS = "text-xs"      # 10px
    FONT_SIZE_SM = "text-sm"      # 14px
    FONT_SIZE_BASE = "text-base"  # 16px
    FONT_SIZE_LG = "text-lg"      # 18px
    FONT_SIZE_XL = "text-xl"      # 20px
    FONT_SIZE_2XL = "text-2xl"    # 24px
    FONT_SIZE_3XL = "text-3xl"    # 30px
    FONT_SIZE_4XL = "text-4xl"    # 36px
    
    # === 色設定 ===
    # メイン色（new/統一）
    COLOR_PRIMARY = "#334155"     # slate-800
    COLOR_PRIMARY_LIGHT = "#475569"
    COLOR_SECONDARY = "#3b82f6"   # blue-600
    COLOR_SUCCESS = "#10b981"     # green-500
    COLOR_WARNING = "#f59e0b"     # amber-500
    COLOR_DANGER = "#ef4444"      # red-500
    
    # テキスト色
    COLOR_TEXT_PRIMARY = "#1f2937"    # gray-800
    COLOR_TEXT_SECONDARY = "#6b7280"  # gray-500
    COLOR_TEXT_WHITE = "#ffffff"
    COLOR_TEXT_MUTED = "#9ca3af"      # gray-400
    
    # 背景色
    COLOR_BG_PRIMARY = "#f8fafc"      # slate-50
    COLOR_BG_SECONDARY = "#f1f5f9"    # slate-100
    COLOR_BG_DARK = "#1e293b"         # slate-800
    
    # === スペーシング設定 ===
    # パディング（統一）
    PADDING_NONE = "p-0"
    PADDING_XS = "p-1"      # 4px
    PADDING_SM = "p-2"      # 8px
    PADDING_BASE = "p-4"    # 16px
    PADDING_LG = "p-6"      # 24px
    PADDING_XL = "p-8"      # 32px
    
    # マージン（統一）
    MARGIN_NONE = "m-0"
    MARGIN_XS = "m-1"       # 4px
    MARGIN_SM = "m-2"       # 8px
    MARGIN_BASE = "m-4"     # 16px
    MARGIN_LG = "m-6"       # 24px
    MARGIN_XL = "m-8"       # 32px
    
    # === レイアウト設定 ===
    # コンテナ幅
    CONTAINER_SM = "max-w-sm"     # 384px
    CONTAINER_MD = "max-w-md"     # 448px
    CONTAINER_LG = "max-w-lg"     # 512px
    CONTAINER_XL = "max-w-xl"     # 576px
    CONTAINER_2XL = "max-w-2xl"   # 672px
    CONTAINER_4XL = "max-w-4xl"   # 896px
    CONTAINER_6XL = "max-w-6xl"   # 1152px
    
    # === コンポーネント共通クラス ===
    # ボタン
    BTN_PRIMARY = f"bg-blue-600 hover:bg-blue-700 text-white font-medium {PADDING_SM} px-4 rounded transition-colors"
    BTN_SECONDARY = f"bg-gray-600 hover:bg-gray-700 text-white font-medium {PADDING_SM} px-4 rounded transition-colors"
    BTN_OUTLINE = f"border border-gray-300 hover:bg-gray-50 text-gray-700 font-medium {PADDING_SM} px-4 rounded transition-colors"
    BTN_TRANSPARENT = f"bg-transparent hover:bg-slate-700 text-white {PADDING_SM} px-3 rounded transition-colors"
    
    # カード
    CARD_BASE = f"bg-white rounded-lg shadow-md {PADDING_BASE}"
    CARD_COMPACT = f"bg-white rounded-md shadow-sm {PADDING_SM}"
    
    # ヘッダー
    HEADER_HEIGHT = "h-12"        # 48px
    HEADER_BG = f"bg-slate-800 text-white"
    
    # フッター
    FOOTER_HEIGHT = "h-6"         # 24px
    FOOTER_BG = "bg-gray-800 text-white"
    
    # === セクション設定 ===
    SECTION_PADDING_Y = "py-8"    # 上下32px
    SECTION_PADDING_Y_SM = "py-4" # 上下16px
    SECTION_MARGIN_B = "mb-6"     # 下24px
    SECTION_MARGIN_B_SM = "mb-4"  # 下16px

class PageLayouts:
    """ページレイアウト共通設定"""
    
    @staticmethod
    def get_page_container():
        """ページ全体コンテナ"""
        return "w-full min-h-screen m-0 p-0"
    
    @staticmethod
    def get_content_container():
        """メインコンテンツエリア"""
        return f"w-full {CommonStyles.CONTAINER_6XL} mx-auto"
    
    @staticmethod
    def get_section_container():
        """セクションコンテナ"""
        return f"w-full text-center {CommonStyles.SECTION_PADDING_Y_SM}"
    
    @staticmethod
    def get_feature_list_container():
        """機能リストコンテナ"""
        return f"w-full {CommonStyles.CONTAINER_4XL} mx-auto"

class ComponentStyles:
    """コンポーネント別スタイル"""
    
    # タイトル
    TITLE_MAIN = f"{CommonStyles.FONT_SIZE_3XL} font-bold {CommonStyles.COLOR_TEXT_PRIMARY}"
    TITLE_SECTION = f"{CommonStyles.FONT_SIZE_2XL} font-bold {CommonStyles.COLOR_TEXT_PRIMARY}"
    TITLE_SUBTITLE = f"{CommonStyles.FONT_SIZE_BASE} {CommonStyles.COLOR_TEXT_SECONDARY}"
    
    # 機能リスト
    FEATURE_ICON = f"{CommonStyles.FONT_SIZE_BASE}"
    FEATURE_NAME = f"font-bold {CommonStyles.COLOR_TEXT_PRIMARY} {CommonStyles.FONT_SIZE_XS}"
    FEATURE_DESC = f"{CommonStyles.COLOR_TEXT_SECONDARY} {CommonStyles.FONT_SIZE_XS}"
    
    # 統計カード
    STAT_CARD = f"{CommonStyles.CARD_COMPACT} text-center min-w-32"
    STAT_ICON = f"{CommonStyles.FONT_SIZE_XL}"
    STAT_VALUE = f"{CommonStyles.FONT_SIZE_2XL} font-bold text-blue-600"
    STAT_LABEL = f"{CommonStyles.FONT_SIZE_XS} {CommonStyles.COLOR_TEXT_SECONDARY}"