#!/usr/bin/env python3
"""
OCRMyPDF エンジン設定パラメータ定義とレイアウト
"""
import flet as ft
from app.flet_ui.shared.panel_components import create_styled_expansion_tile, create_parameter_row

def get_ocrmypdf_parameters() -> list:
    """OCRMyPDF のパラメータ定義"""
    return [
        {"name": "language", "label": "認識言語", "type": "select", "default": "jpn+eng", "options": [
            {"value": "jpn", "label": "日本語のみ"}, {"value": "eng", "label": "英語のみ"}, 
            {"value": "jpn+eng", "label": "日本語+英語"}, {"value": "chi_sim", "label": "中国語(簡体)"}, 
            {"value": "chi_tra", "label": "中国語(繁体)"}, {"value": "kor", "label": "韓国語"}], "description": "OCR認識対象言語"},
        {"name": "dpi", "label": "DPI設定", "type": "number", "default": 300, "min": 150, "max": 600, "step": 50, "description": "画像解像度（精度↑時間↑）"},
        {"name": "optimize", "label": "PDF最適化レベル", "type": "select", "default": 1, "options": [
            {"value": 0, "label": "0:最適化なし"}, {"value": 1, "label": "1:軽度最適化"}, 
            {"value": 2, "label": "2:中程度最適化"}, {"value": 3, "label": "3:高度最適化"}], "description": "出力PDF最適化レベル"},
        {"name": "force_ocr", "label": "強制OCR実行", "type": "checkbox", "default": True, "description": "OCR済みPDFでも再処理実行"}
    ]

def create_ocrmypdf_panel_content() -> ft.Control:
    """OCRMyPDF専用レイアウト表示（シンプル縦並び）"""
    params = get_ocrmypdf_parameters()
    

    
    # シンプルな縦並びレイアウト（共通スタイル使用）
    return create_styled_expansion_tile(
        "PDF処理設定",
        [ft.Container(create_parameter_row(p), padding=ft.padding.only(left=16)) for p in params]
    )
