#!/usr/bin/env python3
"""
PaddleOCR エンジン設定パラメータ定義とレイアウト
"""
import flet as ft

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
    
    def _create_control(param: dict) -> ft.Control:
        """パラメータコントロール作成"""
        param_type = param.get("type", "text")
        param_default = param.get("default")
        
        if param_type == "select":
            options = param.get("options", [])
            dropdown_options = [ft.dropdown.Option(key=str(opt["value"]), text=opt["label"]) for opt in options]
            return ft.Dropdown(options=dropdown_options, value=str(param_default), width=160)
        elif param_type == "number":
            return ft.TextField(value=str(param_default), width=80, height=32, keyboard_type=ft.KeyboardType.NUMBER, input_filter=ft.NumbersOnlyInputFilter())
        elif param_type == "boolean":
            return ft.Switch(value=bool(param_default))
        else:
            return ft.TextField(value=str(param_default), width=150, height=32)
    
    def _create_row(param: dict) -> ft.Control:
        """1行形式でパラメータを表示"""
        return ft.Row([
            ft.Container(ft.Text(f"{param['label']}:", size=12, weight=ft.FontWeight.W_500), width=140, alignment=ft.alignment.center_left),
            _create_control(param),
            ft.Text(param.get("description", ""), size=10, color=ft.Colors.GREY_600, expand=True)
        ], spacing=8)
    
    # セクション分け：基本設定、検出設定、認識設定
    basic_section = ft.Container(
        content=ft.Column([
            ft.Text("基本設定", size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_800),
            ft.Divider(height=1, color=ft.Colors.GREEN_200),
            *[_create_row(p) for p in params[:6]]  # 言語〜認識実行
        ], spacing=4),
        padding=ft.padding.all(12),
        border=ft.border.all(1, ft.Colors.GREEN_100),
        border_radius=6,
        margin=ft.margin.only(bottom=8)
    )
    
    detection_section = ft.Container(
        content=ft.Column([
            ft.Text("検出設定", size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.PURPLE_800),
            ft.Divider(height=1, color=ft.Colors.PURPLE_200),
            *[_create_row(p) for p in params[6:11]]  # 検出アルゴリズム〜アンクリップ比率
        ], spacing=4),
        padding=ft.padding.all(12),
        border=ft.border.all(1, ft.Colors.PURPLE_100),
        border_radius=6,
        margin=ft.margin.only(bottom=8)
    )
    
    recognition_section = ft.Container(
        content=ft.Column([
            ft.Text("認識設定", size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.TEAL_800),
            ft.Divider(height=1, color=ft.Colors.TEAL_200),
            _create_row(params[11])  # 認識バッチサイズ
        ], spacing=4),
        padding=ft.padding.all(12),
        border=ft.border.all(1, ft.Colors.TEAL_100),
        border_radius=6
    )
    
    return ft.Column([basic_section, detection_section, recognition_section], spacing=8)
