#!/usr/bin/env python3
"""
OCRMyPDF エンジン設定パラメータ定義とレイアウト
"""
import flet as ft
from app.flet_ui.shared.panel_components import create_indented_parameter_row
from app.flet_ui.shared.custom_accordion import create_ocr_detail_accordion

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

def create_ocrmypdf_panel_content(page: ft.Page = None) -> ft.Control:
    """OCRMyPDF専用レイアウト表示（関数型アコーディオン版）"""
    params = get_ocrmypdf_parameters()
    
    # PDF処理設定パラメータ
    controls = [create_indented_parameter_row(p) for p in params]
    content = ft.Column(controls, spacing=4, tight=True)
    
    # 単一アコーディオン項目定義（title, content, initially_expanded）
    accordion_items = [
        ("PDF処理設定", content, True)  # デフォルト展開
    ]
    
    # 関数型アコーディオン適用（詳細設定風スタイル）
    if page:
        return create_ocr_detail_accordion(page, accordion_items)
    else:
        # page未指定時のフォールバック（後方互換性）
        return content
