#!/usr/bin/env python3
"""
EasyOCR エンジン設定パラメータ定義とレイアウト
"""
import flet as ft

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
    
    def _create_control(param: dict) -> ft.Control:
        """パラメータコントロール作成"""
        param_type = param.get("type", "text")
        param_default = param.get("default")
        
        if param_type == "select":
            options = param.get("options", [])
            dropdown_options = [ft.dropdown.Option(key=str(opt["value"]), text=opt["label"]) for opt in options]
            return ft.Dropdown(options=dropdown_options, value=str(param_default), width=180)
        elif param_type == "number":
            return ft.TextField(value=str(param_default), width=80, height=32, keyboard_type=ft.KeyboardType.NUMBER, input_filter=ft.NumbersOnlyInputFilter())
        elif param_type == "boolean":
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
    
    # セクション化されたレイアウト
    basic_section = ft.Container(
        content=ft.Column([
            ft.Text("基本設定", size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_800),
            ft.Divider(height=1, color=ft.Colors.BLUE_200),
            *[_create_row(p) for p in params[:4]]  # 言語、GPU、拡大倍率、詳細情報
        ], spacing=4),
        padding=ft.padding.all(12),
        border=ft.border.all(1, ft.Colors.BLUE_100),
        border_radius=6,
        margin=ft.margin.only(bottom=8)
    )
    
    advanced_section = ft.Container(
        content=ft.Column([
            ft.Text("高精度設定", size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.ORANGE_800),
            ft.Divider(height=1, color=ft.Colors.ORANGE_200),
            *[_create_row(p) for p in params[4:]]  # 段落モード以降
        ], spacing=4),
        padding=ft.padding.all(12),
        border=ft.border.all(1, ft.Colors.ORANGE_100),
        border_radius=6
    )
    
    return ft.Column([basic_section, advanced_section], spacing=8)
