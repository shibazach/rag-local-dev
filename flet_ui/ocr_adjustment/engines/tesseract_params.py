#!/usr/bin/env python3
"""
Tesseract エンジン設定パラメータ定義とレイアウト
"""
import flet as ft

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

def create_tesseract_panel_content() -> ft.Control:
    """Tesseract専用レイアウト表示（2x2グリッド）"""
    params = get_tesseract_parameters()
    
    def _create_control(param: dict) -> ft.Control:
        """パラメータコントロール作成"""
        param_type = param.get("type", "text")
        param_default = param.get("default")
        
        if param_type == "select":
            options = param.get("options", [])
            dropdown_options = [ft.dropdown.Option(key=str(opt["value"]), text=opt["label"]) for opt in options]
            return ft.Dropdown(options=dropdown_options, value=str(param_default), width=200)
        elif param_type == "number":
            return ft.TextField(value=str(param_default), width=100, height=32, keyboard_type=ft.KeyboardType.NUMBER, input_filter=ft.NumbersOnlyInputFilter())
        else:
            return ft.TextField(value=str(param_default), width=150, height=32)
    
    def _create_param_box(param: dict) -> ft.Control:
        """パラメータをボックス形式で表示"""
        return ft.Container(
            content=ft.Column([
                ft.Text(param["label"], size=12, weight=ft.FontWeight.W_500),
                _create_control(param),
                ft.Text(param.get("description", ""), size=9, color=ft.Colors.GREY_600, max_lines=2)
            ], spacing=4, alignment=ft.MainAxisAlignment.START),
            padding=ft.padding.all(8),
            border=ft.border.all(1, ft.Colors.GREY_300),
            border_radius=4,
            width=280
        )
    
    # 2x2グリッドレイアウト
    return ft.Column([
        ft.Row([_create_param_box(params[0]), _create_param_box(params[1])], spacing=12),  # PSM, OEM
        ft.Row([_create_param_box(params[2]), _create_param_box(params[3])], spacing=12),  # 言語, DPI
    ], spacing=12)
