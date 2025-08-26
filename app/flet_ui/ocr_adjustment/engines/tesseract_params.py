#!/usr/bin/env python3
"""
Tesseract エンジン設定パラメータ定義とレイアウト
"""
import flet as ft
from app.flet_ui.shared.panel_components import create_indented_parameter_row
from app.flet_ui.shared.custom_accordion import create_ocr_detail_accordion

def get_tesseract_parameters() -> list:
    """Tesseract のパラメータ定義"""
    return [
        {"name": "psm", "label": "ページセグメンテーションモード", "type": "select", "default": 6, "options": [
            {"value": 0, "label": "0:向き・スクリプト検出のみ"}, {"value": 1, "label": "1:自動セグメンテーション(OSD付)"}, 
            {"value": 3, "label": "3:完全自動セグメンテーション"}, {"value": 6, "label": "6:単一テキストブロック"}, 
            {"value": 7, "label": "7:単一テキスト行"}, {"value": 8, "label": "8:単一単語"}, 
            {"value": 13, "label": "13:生の行"}], "description": "テキスト認識セグメンテーション方法"},
        {"name": "oem", "label": "OCRエンジンモード", "type": "select", "default": 3, "options": [
            {"value": 0, "label": "0:レガシーエンジンのみ"}, {"value": 1, "label": "1:LSTMエンジンのみ"}, 
            {"value": 2, "label": "2:レガシー+LSTM"}, {"value": 3, "label": "3:デフォルト"}], "description": "使用するOCRエンジン種類"},
        {"name": "language", "label": "認識言語", "type": "select", "default": "jpn+eng", "options": [
            {"value": "jpn", "label": "日本語のみ"}, {"value": "eng", "label": "英語のみ"}, 
            {"value": "jpn+eng", "label": "日本語+英語"}, {"value": "chi_sim", "label": "中国語(簡体)"}, 
            {"value": "chi_tra", "label": "中国語(繁体)"}, {"value": "kor", "label": "韓国語"}], "description": "OCR認識対象言語"},
        {"name": "dpi", "label": "DPI設定", "type": "number", "default": 300, "min": 150, "max": 600, "step": 50, "description": "画像解像度（精度↑時間↑）"}
    ]

def create_tesseract_panel_content(page: ft.Page = None) -> ft.Control:
    """Tesseract専用レイアウト表示（関数型アコーディオン版）"""
    params = get_tesseract_parameters()
    
    # Tesseract設定パラメータ
    controls = [create_indented_parameter_row(p) for p in params]
    content = ft.Column(controls, spacing=4, tight=True)
    
    # 単一アコーディオン項目定義（title, content, initially_expanded）
    accordion_items = [
        ("Tesseract設定", content, True)  # デフォルト展開
    ]
    
    # 関数型アコーディオン適用（詳細設定風スタイル）
    if page:
        return create_ocr_detail_accordion(page, accordion_items)
    else:
        # page未指定時のフォールバック（後方互換性）
        return content
