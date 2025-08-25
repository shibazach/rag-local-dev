#!/usr/bin/env python3
"""
PaddleOCR エンジン設定パラメータ定義とレイアウト
"""
import flet as ft
from app.flet_ui.shared.panel_components import create_styled_expansion_tile, create_parameter_row

def get_paddleocr_parameters() -> list:
    """PaddleOCR のパラメータ定義"""
    return [
        {"name": "lang", "label": "認識言語", "type": "select", "default": "japan", "options": [
            {"value": "japan", "label": "日本語"}, {"value": "ch", "label": "中国語(簡体)"}, 
            {"value": "en", "label": "英語"}, {"value": "korean", "label": "韓国語"}, 
            {"value": "french", "label": "フランス語"}, {"value": "german", "label": "ドイツ語"}], "description": "OCR認識対象言語"},
        {"name": "use_gpu", "label": "GPU使用", "type": "boolean", "default": False, "description": "GPU加速使用"},
        {"name": "zoom_factor", "label": "画像拡大倍率", "type": "number", "default": 2.0, "min": 1.0, "max": 4.0, "step": 0.5, "description": "拡大倍率（精度↑時間↑）"},
        {"name": "use_angle_cls", "label": "角度分類", "type": "boolean", "default": True, "description": "テキスト角度自動補正"},
        {"name": "use_detection", "label": "テキスト検出", "type": "boolean", "default": True, "description": "テキスト領域検出実行"},
        {"name": "use_recognition", "label": "テキスト認識", "type": "boolean", "default": True, "description": "テキスト認識実行"},
        {"name": "det_algorithm", "label": "検出アルゴリズム", "type": "select", "default": "DB", "options": [
            {"value": "DB", "label": "DB"}, {"value": "EAST", "label": "EAST"}, 
            {"value": "SAST", "label": "SAST"}, {"value": "PSE", "label": "PSE"}], "description": "テキスト検出アルゴリズム"},
        {"name": "det_limit_side_len", "label": "検出画像サイズ制限", "type": "number", "default": 960, "min": 480, "max": 2048, "step": 32, "description": "検出処理時画像サイズ制限"},
        {"name": "det_db_thresh", "label": "DB閾値", "type": "number", "default": 0.3, "min": 0.1, "max": 0.9, "step": 0.1, "description": "DB検出アルゴリズム閾値"},
        {"name": "det_db_box_thresh", "label": "DBボックス閾値", "type": "number", "default": 0.6, "min": 0.1, "max": 0.9, "step": 0.1, "description": "DBボックス検出閾値"},
        {"name": "det_db_unclip_ratio", "label": "DBアンクリップ比率", "type": "number", "default": 1.5, "min": 1.0, "max": 3.0, "step": 0.1, "description": "DBボックス拡張比率"},
        {"name": "rec_batch_num", "label": "認識バッチサイズ", "type": "number", "default": 6, "min": 1, "max": 20, "step": 1, "description": "認識バッチサイズ"}
    ]

def create_paddleocr_panel_content() -> ft.Control:
    """PaddleOCR専用レイアウト表示（セクション分け）"""
    params = get_paddleocr_parameters()
    

    
    # セクション分け：基本設定、検出設定、認識設定（共通スタイル使用）
    basic_section = create_styled_expansion_tile(
        "基本設定",
        [ft.Container(create_parameter_row(p), padding=ft.padding.only(left=16)) for p in params[:6]]  # 言語〜認識実行
    )
    
    detection_section = create_styled_expansion_tile(
        "検出設定",
        [ft.Container(create_parameter_row(p), padding=ft.padding.only(left=16)) for p in params[6:11]]  # 検出アルゴリズム〜アンクリップ比率
    )
    
    recognition_section = create_styled_expansion_tile(
        "認識設定",
        [ft.Container(create_parameter_row(params[11]), padding=ft.padding.only(left=16))]  # 認識バッチサイズ
    )
    
    return ft.Column([basic_section, detection_section, recognition_section], spacing=8)
