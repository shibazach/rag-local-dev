#!/usr/bin/env python3
"""
Flet RAGシステム - 共通パネルコンポーネント
パネルヘッダ・パネル本体・設定クラスの統一実装
"""

import flet as ft
from dataclasses import dataclass
from typing import Optional, Callable, Any, List


# OCR詳細設定パネル統一スタイル定数
class OCRPanelStyles:
    """OCR詳細設定パネル用統一スタイル定義"""
    
    # フォント・文字設定
    SECTION_TITLE_SIZE = 15           # セクションタイトル（「基本設定」等）
    SECTION_TITLE_WEIGHT = ft.FontWeight.BOLD
    SECTION_TITLE_COLOR = ft.Colors.GREY_700
    
    ITEM_LABEL_SIZE = 14              # 項目名（「認識言語」等）
    ITEM_LABEL_WEIGHT = ft.FontWeight.W_500  
    ITEM_LABEL_COLOR = ft.Colors.BLACK87
    ITEM_LABEL_WIDTH = 140            # 項目名ラベル固定幅
    
    DESCRIPTION_SIZE = 11             # 簡易説明文字サイズ
    DESCRIPTION_COLOR = ft.Colors.GREY_600
    
    # コントロール設定
    CONTROL_HEIGHT = 40               # TextField、Dropdown等の高さ統一
    SWITCH_HEIGHT = 32                # Switch高さ
    
    # レイアウト・間隔設定
    SECTION_HEADER_LEFT_PADDING = 0   # セクションヘッド左padding（左寄せ強化）
    SECTION_CONTENT_LEFT_INDENT = 20  # セクション内容の字下げ
    ITEM_ROW_SPACING = 8              # 項目間の縦間隔
    CONTROL_MARGIN_VERTICAL = 2       # コントロール上下margin（小さめ）
    
    # 色・背景設定
    SECTION_HEADER_BG_COLOR = ft.Colors.WHITE  # セクションヘッド背景（線隠し）
    PANEL_BG_COLOR = ft.Colors.WHITE           # パネル全体背景


def create_ocr_divider_theme() -> ft.Theme:
    """OCR詳細設定用テーマ（参考情報完全適用版）"""
    return ft.Theme(
        use_material3=True,
        divider_theme=ft.DividerThemeData(
            color=ft.Colors.TRANSPARENT,   # 区切り線の色を透明に
            thickness=0,                   # 太さを0に
            space=0,                       # 上下の余白も0に
        ),
        # 📋 参考情報：リスト系の区切り線も完全制御
        list_tile_theme=ft.ListTileThemeData(
            shape=ft.RoundedRectangleBorder(
                side=ft.BorderSide(0, ft.Colors.TRANSPARENT)
            )
        )
    )


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
    initially_expanded: bool = True,
    page: ft.Page = None
) -> ft.Control:
    """OCR詳細設定用の統一スタイル アコーディオン作成（暫定: 元のContainer実装）"""
    
    # 🚧 暫定措置: 元の静的Container実装に戻す（tab_aテスト成功後に関数型適用）
    
    # ヘッダー部分
    header = ft.Container(
        content=ft.Row([
            ft.Icon(
                ft.Icons.EXPAND_MORE if initially_expanded else ft.Icons.CHEVRON_RIGHT,
                size=16,
                color=ft.Colors.GREY_600
            ),
            ft.Text(
                title, 
                size=14, 
                weight=ft.FontWeight.W_500, 
                color=ft.Colors.BLACK87
            )
        ], spacing=8, alignment=ft.MainAxisAlignment.START),
        bgcolor=ft.Colors.BLUE_50,
        padding=ft.padding.all(8),
        border_radius=ft.border_radius.only(top_left=4, top_right=4)
    )
    
    # コンテンツ部分
    content = ft.Container(
        content=ft.Column(controls, spacing=4, tight=True),
        padding=ft.padding.all(8),
        bgcolor=ft.Colors.WHITE,
        visible=initially_expanded
    )
    
    # 全体コンテナ（線なし）
    return ft.Container(
        content=ft.Column([header, content], spacing=0, tight=True),
        margin=ft.margin.symmetric(vertical=2),
        border_radius=4,
        border=ft.border.all(1, ft.Colors.GREY_200),  # 薄いボーダーのみ
        bgcolor=ft.Colors.WHITE
    )


def create_parameter_control(param: dict) -> ft.Control:
    """OCRパラメータ用コントロール作成（統一スタイル適用）"""
    param_type = param.get("type", "text")
    param_default = param.get("default")
    
    if param_type == "select":
        options = param.get("options", [])
        dropdown_options = [ft.dropdown.Option(key=str(opt["value"]), text=opt["label"]) for opt in options]
        return ft.Container(
            ft.Dropdown(
                options=dropdown_options, 
                value=str(param_default), 
                width=180
                # height パラメータは ft.Dropdown に存在しないため削除
            ),
            margin=ft.margin.symmetric(vertical=OCRPanelStyles.CONTROL_MARGIN_VERTICAL)  # 統一margin
        )
    elif param_type == "number":
        return ft.TextField(
            value=str(param_default), 
            width=80, 
            height=OCRPanelStyles.CONTROL_HEIGHT,  # 統一高さ
            keyboard_type=ft.KeyboardType.NUMBER, 
            input_filter=ft.NumbersOnlyInputFilter(), 
            text_align=ft.TextAlign.CENTER
        )
    elif param_type == "boolean":
        return ft.Container(
            ft.Switch(
                value=bool(param_default),
                height=OCRPanelStyles.SWITCH_HEIGHT  # 統一Switch高さ
            ),
            height=OCRPanelStyles.SWITCH_HEIGHT,
            alignment=ft.alignment.center_left
        )
    else:
        return ft.TextField(
            value=str(param_default), 
            width=150, 
            height=OCRPanelStyles.CONTROL_HEIGHT  # 統一高さ
        )


def create_parameter_row(param: dict) -> ft.Control:
    """OCRパラメータ1行表示（統一スタイル適用）"""
    return ft.Row([
        ft.Container(
            ft.Text(
                f"{param['label']}:", 
                size=OCRPanelStyles.ITEM_LABEL_SIZE, 
                weight=OCRPanelStyles.ITEM_LABEL_WEIGHT, 
                color=OCRPanelStyles.ITEM_LABEL_COLOR
            ), 
            width=OCRPanelStyles.ITEM_LABEL_WIDTH,  # 統一ラベル幅
            alignment=ft.alignment.center_left
        ),
        create_parameter_control(param),
        ft.Text(
            param.get("description", ""), 
            size=OCRPanelStyles.DESCRIPTION_SIZE, 
            color=OCRPanelStyles.DESCRIPTION_COLOR, 
            expand=True
        )
    ], spacing=OCRPanelStyles.ITEM_ROW_SPACING, alignment=ft.MainAxisAlignment.START, vertical_alignment=ft.CrossAxisAlignment.CENTER)


def create_indented_parameter_row(param: dict) -> ft.Control:
    """セクション内字下げされたパラメータ行（統一スタイル）"""
    return ft.Container(
        create_parameter_row(param), 
        padding=ft.padding.only(left=OCRPanelStyles.SECTION_CONTENT_LEFT_INDENT)
    )