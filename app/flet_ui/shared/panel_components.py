#!/usr/bin/env python3
"""
Flet RAGシステム - 共通パネルコンポーネント
パネルヘッダ・パネル本体・設定クラスの統一実装
"""

import flet as ft
from dataclasses import dataclass
from typing import Optional, Callable, Any, List


@dataclass
class PanelHeaderConfig:
    """パネルヘッダ設定クラス"""
    title: str
    title_icon: Optional[str] = None
    show_status: bool = False
    show_search: bool = False
    show_file_select: bool = False
    status_callback: Optional[Callable] = None
    search_callback: Optional[Callable] = None
    file_select_callback: Optional[Callable] = None
    height: int = 54
    bgcolor: str = ft.Colors.BLUE_GREY_800
    text_color: str = ft.Colors.WHITE
    padding_horizontal: int = 8
    padding_vertical: int = 2


@dataclass
class PanelConfig:
    """パネル全体設定クラス"""
    header_config: PanelHeaderConfig
    margin: ft.Margin = ft.margin.all(4)
    padding: ft.Padding = ft.padding.all(0)
    bgcolor: str = ft.Colors.WHITE
    border_radius: int = 8
    border: ft.Border = ft.border.all(1, ft.Colors.GREY_300)
    enable_scroll: bool = True  # パネル内スクロール有効/無効


def create_panel_header(config: PanelHeaderConfig) -> ft.Container:
    """統一パネルヘッダ作成"""
    # タイトル部分
    title_controls = []
    if config.title_icon:
        # ft.Icons（Material Icons）のみをサポート
        title_controls.append(ft.Icon(config.title_icon, size=20, color=config.text_color))
    title_controls.append(ft.Text(config.title, size=16, weight=ft.FontWeight.BOLD, color=config.text_color))
    
    title_row = ft.Row(title_controls, alignment=ft.MainAxisAlignment.START)
    
    # 右側コントロール部分
    right_controls = []
    
    # ファイル選択ボタン
    if config.show_file_select:
        file_btn = ft.IconButton(
            icon=ft.Icons.FOLDER_OPEN,
            icon_size=24,
            icon_color=config.text_color,
            on_click=config.file_select_callback if config.file_select_callback else lambda e: None
        )
        right_controls.append(file_btn)
    
    # ステータスドロップダウン
    if config.show_status:
        status_dropdown = ft.Dropdown(
            options=[
                ft.dropdown.Option("全て"),
                ft.dropdown.Option("処理完了"),
                ft.dropdown.Option("処理中"),
                ft.dropdown.Option("未処理"),
                ft.dropdown.Option("エラー")
            ],
            value="全て",
            width=120,
            filled=True,
            bgcolor=ft.Colors.WHITE,
            fill_color=ft.Colors.WHITE,
            on_change=config.status_callback if config.status_callback else lambda e: None
        )
        right_controls.append(status_dropdown)
    
    # 検索テキストボックス
    if config.show_search:
        search_field = ft.TextField(
            hint_text="ファイル名で検索",
            filled=True,
            bgcolor=ft.Colors.WHITE,
            fill_color=ft.Colors.WHITE,
            expand=True,  # パネル幅にAnchor
            on_change=config.search_callback if config.search_callback else lambda e: None
        )
        right_controls.append(search_field)
    
    # ヘッダーレイアウト（タイトル+ステータス | 検索）
    # 左セクション：タイトル + ステータスドロップダウン（横付け）
    left_controls = title_controls.copy()
    status_controls = [ctrl for ctrl in right_controls if isinstance(ctrl, ft.Dropdown)]
    left_controls.extend(status_controls)
    left_section = ft.Row(left_controls, spacing=12, alignment=ft.MainAxisAlignment.START)
    
    # 右セクション：検索テキストボックス（パネル幅にAnchor）
    search_controls = [ctrl for ctrl in right_controls if isinstance(ctrl, ft.TextField)]
    right_section = ft.Container(
        content=ft.Row(search_controls, spacing=8),
        expand=True,
        alignment=ft.alignment.center_right
    ) if search_controls else ft.Container()
    
    header_content = ft.Row([
        left_section,
        right_section
    ], spacing=16, expand=True)
    
    return ft.Container(
        content=header_content,
        height=config.height,
        padding=ft.padding.symmetric(horizontal=config.padding_horizontal, vertical=config.padding_vertical),
        bgcolor=config.bgcolor
    )


def create_panel(config: PanelConfig, content: ft.Control) -> ft.Container:
    """統一パネル作成"""
    header = create_panel_header(config.header_config)
    
    # スクロール制御：テーブル系パネルでは無効、詳細設定系では有効
    if config.enable_scroll:
        # スクロール対応のColumnでラップ
        content_wrapper = ft.Column(
            controls=[content],
            expand=True,
            scroll=ft.ScrollMode.AUTO  # 縦方向にはみ出た場合にスクロールバー表示
        )
    else:
        # スクロール無効：テーブル独自スクロールを優先
        content_wrapper = content
    
    panel_content = ft.Column([
        header,
        content_wrapper
    ], spacing=0, expand=True)
    
    return ft.Container(
        content=panel_content,
        margin=config.margin,
        padding=config.padding,
        bgcolor=config.bgcolor,
        border_radius=config.border_radius,
        border=config.border,
        expand=True
    )


def create_files_panel_config(
    title: str,
    title_icon: Optional[str] = None,
    show_status: bool = False,
    show_search: bool = False,
    show_file_select: bool = False,
    status_callback: Optional[Callable] = None,
    search_callback: Optional[Callable] = None,
    file_select_callback: Optional[Callable] = None
) -> PanelConfig:
    """ファイル系パネル設定作成"""
    header_config = PanelHeaderConfig(
        title=title,
        title_icon=title_icon,
        show_status=show_status,
        show_search=show_search,
        show_file_select=show_file_select,
        status_callback=status_callback,
        search_callback=search_callback,
        file_select_callback=file_select_callback
    )
    
    return PanelConfig(
        header_config=header_config
        # その他はPanelConfigのデフォルト値を使用
    )


def create_upload_panel_config(
    title: str,
    title_icon: Optional[str] = None,
    show_status: bool = False,
    show_search: bool = False,
    show_file_select: bool = False,
    status_callback: Optional[Callable] = None,
    search_callback: Optional[Callable] = None,
    file_select_callback: Optional[Callable] = None
) -> PanelConfig:
    """アップロード系パネル設定作成"""
    header_config = PanelHeaderConfig(
        title=title,
        title_icon=title_icon,
        show_status=show_status,
        show_search=show_search,
        show_file_select=show_file_select,
        status_callback=status_callback,
        search_callback=search_callback,
        file_select_callback=file_select_callback
    )
    
    return PanelConfig(
        header_config=header_config
        # その他はPanelConfigのデフォルト値を使用
    )


def create_status_badge(status: str) -> ft.Container:
    """ステータスバッジ作成"""
    status_colors = {
        "処理完了": ft.Colors.GREEN,
        "処理中": ft.Colors.ORANGE,
        "未処理": ft.Colors.GREY_600,
        "未整形": ft.Colors.BLUE,
        "未ベクトル化": ft.Colors.PURPLE,
        "エラー": ft.Colors.RED
    }
    
    color = status_colors.get(status, ft.Colors.GREY)
    
    return ft.Container(
        content=ft.Text(status, color=ft.Colors.WHITE, size=12, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER),
        padding=ft.padding.symmetric(horizontal=8, vertical=4),
        bgcolor=color,
        border_radius=12,
        alignment=ft.alignment.center  # センタリング追加
    )


def create_styled_expansion_tile(
    title: str, 
    controls: List[ft.Control], 
    initially_expanded: bool = True
) -> ft.ExpansionTile:
    """OCR詳細設定用の統一スタイル ExpansionTile 作成"""
    return ft.ExpansionTile(
        title=ft.Container(
            ft.Text(
                title, 
                size=14, 
                weight=ft.FontWeight.BOLD, 
                color=ft.Colors.GREY_700
            ), 
            alignment=ft.alignment.center_left,
            bgcolor=ft.Colors.WHITE,  # 白背景で線を隠す
            padding=ft.padding.only(left=4, top=8, right=8, bottom=8),
            border_radius=4
        ),
        controls=controls,
        initially_expanded=initially_expanded,
        collapsed_icon_color=ft.Colors.GREY_400,
        icon_color=ft.Colors.GREY_400
    )


def create_parameter_control(param: dict) -> ft.Control:
    """OCRパラメータ用コントロール作成（共通）"""
    param_type = param.get("type", "text")
    param_default = param.get("default")
    
    if param_type == "select":
        options = param.get("options", [])
        dropdown_options = [ft.dropdown.Option(key=str(opt["value"]), text=opt["label"]) for opt in options]
        return ft.Container(
            ft.Dropdown(options=dropdown_options, value=str(param_default), width=180),
            margin=ft.margin.symmetric(vertical=2)
        )
    elif param_type == "number":
        return ft.TextField(
            value=str(param_default), 
            width=80, 
            height=40, 
            keyboard_type=ft.KeyboardType.NUMBER, 
            input_filter=ft.NumbersOnlyInputFilter(), 
            text_align=ft.TextAlign.CENTER
        )
    elif param_type == "boolean":
        return ft.Switch(value=bool(param_default))
    else:
        return ft.TextField(value=str(param_default), width=150, height=40)


def create_parameter_row(param: dict) -> ft.Control:
    """OCRパラメータ1行表示（共通）"""
    return ft.Row([
        ft.Container(
            ft.Text(f"{param['label']}:", size=13, weight=ft.FontWeight.W_500), 
            width=140, 
            alignment=ft.alignment.center_left
        ),
        create_parameter_control(param),
        ft.Text(param.get("description", ""), size=11, color=ft.Colors.GREY_600, expand=True)
    ], spacing=8, alignment=ft.MainAxisAlignment.START, vertical_alignment=ft.CrossAxisAlignment.CENTER)