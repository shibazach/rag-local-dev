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
    """Tesseract専用レイアウト表示（1行形式）"""
    params = get_tesseract_parameters()
    
    def _create_control(param: dict) -> ft.Control:
        """パラメータコントロール作成"""
        param_type = param.get("type", "text")
        param_default = param.get("default")
        
        if param_type == "select":
            options = param.get("options", [])
            dropdown_options = [ft.dropdown.Option(key=str(opt["value"]), text=opt["label"]) for opt in options]
            return ft.Container(
                ft.Dropdown(options=dropdown_options, value=str(param_default), width=200),
                margin=ft.margin.symmetric(vertical=2)
            )
        elif param_type == "number":
            return ft.TextField(value=str(param_default), width=100, height=40, keyboard_type=ft.KeyboardType.NUMBER, input_filter=ft.NumbersOnlyInputFilter(), text_align=ft.TextAlign.CENTER)
        else:
            return ft.TextField(value=str(param_default), width=150, height=40)
    
    def _create_row(param: dict) -> ft.Control:
        """1行形式でパラメータを表示"""
        return ft.Row([
            ft.Container(ft.Text(f"{param['label']}:", size=13, weight=ft.FontWeight.W_500), width=140, alignment=ft.alignment.center_left),
            _create_control(param),
            ft.Text(param.get("description", ""), size=11, color=ft.Colors.GREY_600, expand=True)
        ], spacing=8, alignment=ft.MainAxisAlignment.START, vertical_alignment=ft.CrossAxisAlignment.CENTER)
    
    # 1行形式レイアウト（リトラクタブル）
    return ft.ExpansionTile(
        title=ft.Container(ft.Text("Tesseract設定", size=14, weight=ft.FontWeight.BOLD), alignment=ft.alignment.center_left),
        controls=[ft.Container(_create_row(p), padding=ft.padding.only(left=16)) for p in params],
        initially_expanded=True
    )
