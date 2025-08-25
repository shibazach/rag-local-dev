#!/usr/bin/env python3
"""
EasyOCR エンジン設定パラメータ定義とレイアウト
"""
import flet as ft
from app.flet_ui.shared.panel_components import create_styled_expansion_tile, create_parameter_row

def get_easyocr_parameters() -> list:
    """EasyOCR のパラメータ定義"""
    return [
        {"name": "languages", "label": "認識言語", "type": "select", "default": ["ja", "en"], "options": [
            {"value": ["ja"], "label": "日本語のみ"}, {"value": ["en"], "label": "英語のみ"}, 
            {"value": ["ja", "en"], "label": "日本語+英語"}, {"value": ["zh"], "label": "中国語"}, 
            {"value": ["ko"], "label": "韓国語"}], "description": "OCR認識対象言語"},
        {"name": "use_gpu", "label": "GPU使用", "type": "boolean", "default": False, "description": "GPU加速使用"},
        {"name": "zoom_factor", "label": "画像拡大倍率", "type": "number", "default": 2.0, "min": 1.0, "max": 4.0, "step": 0.5, "description": "拡大倍率（精度↑時間↑）"},
        {"name": "detail", "label": "詳細情報", "type": "select", "default": 1, "options": [{"value": 0, "label": "テキストのみ"}, {"value": 1, "label": "座標+信頼度"}], "description": "出力詳細レベル"},
        {"name": "paragraph", "label": "段落モード", "type": "boolean", "default": False, "description": "段落単位グループ化"},
        {"name": "high_quality_mode", "label": "高精度モード", "type": "boolean", "default": False, "description": "高精度処理（時間↑精度↑）"},
        {"name": "text_threshold", "label": "テキスト検出閾値", "type": "number", "default": 0.7, "min": 0.1, "max": 1.0, "step": 0.1, "description": "検出信頼度閾値"},
        {"name": "link_threshold", "label": "リンク閾値", "type": "number", "default": 0.4, "min": 0.1, "max": 1.0, "step": 0.1, "description": "文字間リンク閾値"},
        {"name": "canvas_size", "label": "キャンバスサイズ", "type": "number", "default": 2560, "min": 1280, "max": 5120, "step": 256, "description": "処理用キャンバス（精度↑メモリ↑）"},
        {"name": "mag_ratio", "label": "拡大比率", "type": "number", "default": 1.5, "min": 1.0, "max": 3.0, "step": 0.1, "description": "高精度時拡大比率"}
    ]

def create_easyocr_panel_content() -> ft.Control:
    """EasyOCR専用レイアウト表示"""
    params = get_easyocr_parameters()
    

    
    # セクション化されたレイアウト（共通スタイル使用）
    basic_section = create_styled_expansion_tile(
        "基本設定",
        [ft.Container(create_parameter_row(p), padding=ft.padding.only(left=16)) for p in params[:4]]  # 言語、GPU、拡大倍率、詳細情報
    )
    
    advanced_section = create_styled_expansion_tile(
        "高精度設定",
        [ft.Container(create_parameter_row(p), padding=ft.padding.only(left=16)) for p in params[4:]]  # 段落モード以降
    )
    
    return ft.Column([basic_section, advanced_section], spacing=8)
