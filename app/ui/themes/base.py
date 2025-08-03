"""
NiceGUI基本テーマ
Unified theme system for consistent UI/UX
"""

from nicegui import ui
from typing import Dict, Any, Optional

class RAGTheme:
    """R&D RAGシステム統一テーマ"""
    
    # ========== カラーパレット ==========
    COLORS = {
        # プライマリ（青系）
        "primary": "#2563eb",
        "primary_dark": "#1d4ed8", 
        "primary_light": "#3b82f6",
        
        # セカンダリ（緑系）
        "secondary": "#16a34a",
        "secondary_dark": "#15803d",
        "secondary_light": "#22c55e",
        
        # アクセント（オレンジ系）
        "accent": "#ea580c",
        "accent_dark": "#c2410c",
        "accent_light": "#f97316",
        
        # ニュートラル（グレー系）
        "neutral": "#64748b",
        "neutral_dark": "#475569",
        "neutral_light": "#94a3b8",
        
        # 状態色
        "success": "#16a34a",
        "warning": "#ca8a04", 
        "error": "#dc2626",
        "info": "#0ea5e9",
        
        # 背景色
        "bg_primary": "#ffffff",
        "bg_secondary": "#f8fafc",
        "bg_tertiary": "#f1f5f9",
        "bg_dark": "#0f172a",
        
        # テキスト色
        "text_primary": "#0f172a",
        "text_secondary": "#475569",
        "text_muted": "#94a3b8",
        "text_white": "#ffffff"
    }
    
    # ========== タイポグラフィ（new/系準拠）==========
    TYPOGRAPHY = {
        "font_family": "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
        "font_size_xs": "12px",      # new/系統一
        "font_size_sm": "13px",      # new/系統一
        "font_size_base": "14px",    # new/系統一（メイン）
        "font_size_lg": "16px",      # パネルヘッダー
        "font_size_xl": "18px",      # ページタイトル
        "font_size_2xl": "20px",     # セクションタイトル
        
        "line_height_tight": "1.1",   # new/系準拠
        "line_height_normal": "1.2",  # new/系準拠  
        "line_height_relaxed": "1.4"  # new/系準拠
    }
    
    # ========== スペーシング（new/系準拠）==========
    SPACING = {
        "xs": "4px",       # new/系統一
        "sm": "8px",       # new/系統一（メインパディング）
        "md": "12px",      # new/系統一
        "lg": "16px",      # new/系統一
        "xl": "24px",      # new/系統一
        "gap": "6px",      # new/系グリッドギャップ統一
        "resizer": "5px",  # new/系リサイザー幅統一
    }
    
    # ========== 角丸 ==========
    RADIUS = {
        "none": "0",
        "sm": "0.25rem",   # 4px
        "md": "0.375rem",  # 6px
        "lg": "0.5rem",    # 8px
        "xl": "0.75rem",   # 12px
        "2xl": "1rem",     # 16px
        "full": "9999px"
    }
    
    # ========== 影 ==========
    SHADOWS = {
        "sm": "0 1px 2px 0 rgb(0 0 0 / 0.05)",
        "md": "0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)",
        "lg": "0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1)",
        "xl": "0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1)",
        "2xl": "0 25px 50px -12px rgb(0 0 0 / 0.25)"
    }
    
    @classmethod
    def apply_global_styles(cls):
        """グローバルスタイル適用"""
        ui.add_head_html(f"""
        <style>
        :root {{
            --rag-primary: {cls.COLORS['primary']};
            --rag-secondary: {cls.COLORS['secondary']};
            --rag-accent: {cls.COLORS['accent']};
            --rag-success: {cls.COLORS['success']};
            --rag-warning: {cls.COLORS['warning']};
            --rag-error: {cls.COLORS['error']};
            --rag-info: {cls.COLORS['info']};
            
            --rag-bg-primary: {cls.COLORS['bg_primary']};
            --rag-bg-secondary: {cls.COLORS['bg_secondary']};
            --rag-text-primary: {cls.COLORS['text_primary']};
            --rag-text-secondary: {cls.COLORS['text_secondary']};
            
            --rag-font-family: {cls.TYPOGRAPHY['font_family']};
            --rag-shadow-md: {cls.SHADOWS['md']};
            --rag-radius-lg: {cls.RADIUS['lg']};
        }}
        
        body {{
            font-family: var(--rag-font-family);
            font-size: {cls.TYPOGRAPHY['font_size_base']};
            line-height: {cls.TYPOGRAPHY['line_height_normal']};
            background-color: var(--rag-bg-secondary);
            color: var(--rag-text-primary);
            margin: 0;
            padding: 0;
        }}
        
        /* 統一コンテナ（new/系準拠）*/
        .rag-container {{
            height: calc(100vh - 95px);
            padding: {cls.SPACING['sm']};
            overflow: hidden;
            background: transparent;
        }}
        
        /* 統一パネルスタイル（new/系準拠）*/
        .rag-panel {{
            background: white;
            border: 1px solid #ddd;
            border-radius: 8px;
            display: flex;
            flex-direction: column;
            overflow: hidden;
            height: 100%;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        }}
        
        /* 統一パネルヘッダー（new/系準拠）*/
        .rag-panel-header {{
            background: #f8f9fa;
            padding: {cls.SPACING['sm']} {cls.SPACING['md']};
            border-bottom: 1px solid #ddd;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        
        .rag-panel-header h3 {{
            margin: 0;
            font-size: {cls.TYPOGRAPHY['font_size_lg']};
            font-weight: 600;
            color: var(--rag-text-primary);
        }}
        
        /* 統一パネルコンテンツ（new/系準拠）*/
        .rag-panel-content {{
            flex: 1;
            padding: {cls.SPACING['sm']};
            overflow-y: auto;
            overflow-x: hidden;
            min-height: 0;
        }}
        
        /* 統一ボタンスタイル */
        .rag-button {{
            background: var(--rag-primary);
            color: var(--rag-text-white);
            border: none;
            border-radius: var(--rag-radius-lg);
            padding: {cls.SPACING['sm']} {cls.SPACING['lg']};
            font-weight: 500;
            transition: all 0.2s ease;
            cursor: pointer;
        }}
        
        .rag-button:hover {{
            background: var(--rag-primary);
            transform: translateY(-1px);
            box-shadow: var(--rag-shadow-lg);
        }}
        
        .rag-button-secondary {{
            background: var(--rag-secondary);
        }}
        
        .rag-button-outline {{
            background: transparent;
            color: var(--rag-primary);
            border: 2px solid var(--rag-primary);
        }}
        
        .rag-button-outline:hover {{
            background: var(--rag-primary);
            color: var(--rag-text-white);
        }}
        
        /* 統一入力フィールドスタイル（new/系準拠）*/
        .rag-input {{
            border: 1px solid #ddd;
            border-radius: 4px;
            padding: {cls.SPACING['xs']} {cls.SPACING['sm']};
            font-size: {cls.TYPOGRAPHY['font_size_sm']};
            width: 100%;
            transition: border-color 0.2s ease;
        }}
        
        .rag-input:focus {{
            border-color: var(--rag-primary);
            outline: none;
            box-shadow: none;
        }}
        
        /* new/系コンパクト入力フィールド */
        .rag-input-compact {{
            height: 32px;
            font-size: {cls.TYPOGRAPHY['font_size_xs']};
            padding: {cls.SPACING['xs']} {cls.SPACING['sm']};
        }}
        
        /* new/系セレクトボックス */
        .rag-select {{
            border: 1px solid #ddd;
            border-radius: 4px;
            padding: {cls.SPACING['xs']} {cls.SPACING['sm']};
            font-size: {cls.TYPOGRAPHY['font_size_sm']};
            height: 32px;
        }}
        
        /* 統一テーブルスタイル */
        .rag-table {{
            background: var(--rag-bg-primary);
            border-radius: var(--rag-radius-lg);
            overflow: hidden;
            box-shadow: var(--rag-shadow-md);
        }}
        
        .rag-table th {{
            background: var(--rag-bg-tertiary);
            color: var(--rag-text-primary);
            font-weight: 600;
            padding: {cls.SPACING['md']};
            border-bottom: 2px solid #e2e8f0;
        }}
        
        .rag-table td {{
            padding: {cls.SPACING['md']};
            border-bottom: 1px solid #e2e8f0;
        }}
        
        .rag-table tr:hover {{
            background: var(--rag-bg-secondary);
        }}
        
        /* 統一ヘッダースタイル */
        .rag-header {{
            background: linear-gradient(135deg, var(--rag-primary), var(--rag-secondary));
            color: var(--rag-text-white);
            padding: {cls.SPACING['lg']} {cls.SPACING['xl']};
            box-shadow: var(--rag-shadow-lg);
        }}
        
        /* 統一コンテンツエリア */
        .rag-content {{
            max-width: 1200px;
            margin: 0 auto;
            padding: {cls.SPACING['xl']};
        }}
        
        /* 統一グリッドレイアウト */
        .rag-grid {{
            display: grid;
            gap: {cls.SPACING['lg']};
        }}
        
        .rag-grid-2 {{
            grid-template-columns: repeat(2, 1fr);
        }}
        
        .rag-grid-3 {{
            grid-template-columns: repeat(3, 1fr);
        }}
        
        .rag-grid-4 {{
            grid-template-columns: repeat(4, 1fr);
        }}
        
        /* レスポンシブ対応 */
        @media (max-width: 768px) {{
            .rag-grid-2, .rag-grid-3, .rag-grid-4 {{
                grid-template-columns: 1fr;
            }}
            
            .rag-content {{
                padding: {cls.SPACING['md']};
            }}
        }}
        
        /* 統一ステータスバッジ */
        .rag-badge {{
            display: inline-flex;
            align-items: center;
            padding: {cls.SPACING['xs']} {cls.SPACING['sm']};
            border-radius: {cls.RADIUS['full']};
            font-size: {cls.TYPOGRAPHY['font_size_sm']};
            font-weight: 500;
        }}
        
        .rag-badge-success {{
            background: #dcfce7;
            color: #166534;
        }}
        
        .rag-badge-warning {{
            background: #fef3c7;
            color: #92400e;
        }}
        
        .rag-badge-error {{
            background: #fee2e2;
            color: #991b1b;
        }}
        
        .rag-badge-info {{
            background: #dbeafe;
            color: #1e40af;
        }}
        
        /* アニメーション */
        .rag-fade-in {{
            animation: fadeIn 0.3s ease-in-out;
        }}
        
        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(10px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
        
        .rag-slide-in {{
            animation: slideIn 0.3s ease-out;
        }}
        
        @keyframes slideIn {{
            from {{ transform: translateX(-100%); }}
            to {{ transform: translateX(0); }}
        }}
        </style>
        """)
    
    @classmethod 
    def get_status_color(cls, status: str) -> str:
        """ステータス別カラー取得"""
        status_colors = {
            "success": cls.COLORS["success"],
            "completed": cls.COLORS["success"],
            "processing": cls.COLORS["info"],
            "pending": cls.COLORS["warning"],
            "failed": cls.COLORS["error"],
            "error": cls.COLORS["error"],
            "warning": cls.COLORS["warning"],
            "info": cls.COLORS["info"]
        }
        return status_colors.get(status.lower(), cls.COLORS["neutral"])
    
    @classmethod
    def create_status_badge(cls, status: str, text: str = None) -> dict:
        """ステータスバッジ作成"""
        display_text = text or status.title()
        color = cls.get_status_color(status)
        
        return {
            "text": display_text,
            "color": "positive" if status in ["success", "completed"] else
                    "warning" if status in ["pending", "processing"] else
                    "negative" if status in ["failed", "error"] else "info"
        }