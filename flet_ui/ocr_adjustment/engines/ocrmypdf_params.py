#!/usr/bin/env python3
"""
OCRMyPDF エンジン設定パラメータ定義とレイアウト
"""
import flet as ft

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
    
    def _create_control(param: dict) -> ft.Control:
        """パラメータコントロール作成"""
        param_type = param.get("type", "text")
        param_default = param.get("default")
        
        if param_type == "select":
            options = param.get("options", [])
            dropdown_options = [ft.dropdown.Option(key=str(opt["value"]), text=opt["label"]) for opt in options]
            return ft.Dropdown(options=dropdown_options, value=str(param_default), width=200)
        elif param_type == "number":
            return ft.TextField(value=str(param_default), width=80, height=32, keyboard_type=ft.KeyboardType.NUMBER, input_filter=ft.NumbersOnlyInputFilter())
        elif param_type in ["boolean", "checkbox"]:
            return ft.Switch(value=bool(param_default))
        else:
            return ft.TextField(value=str(param_default), width=150, height=32)
    
    def _create_row(param: dict) -> ft.Control:
        """1行形式でパラメータを表示"""
        return ft.Row([
            ft.Container(ft.Text(f"{param['label']}:", size=12, weight=ft.FontWeight.W_500), width=120, alignment=ft.alignment.center_left),
            _create_control(param),
            ft.Text(param.get("description", ""), size=10, color=ft.Colors.GREY_600, expand=True)
        ], spacing=8)
    
    # シンプルな縦並びレイアウト
    return ft.Container(
        content=ft.Column([
            ft.Text("PDF処理設定", size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.INDIGO_800),
            ft.Divider(height=1, color=ft.Colors.INDIGO_200),
            *[_create_row(p) for p in params]
        ], spacing=6),
        padding=ft.padding.all(12),
        border=ft.border.all(1, ft.Colors.INDIGO_100),
        border_radius=6
    )
