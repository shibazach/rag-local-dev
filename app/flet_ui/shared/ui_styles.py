#!/usr/bin/env python3
"""
汎用UI統一スタイルシステム
OCRページベース設計 → 全アプリ展開用
"""

import flet as ft
from typing import Optional


class CommonUIStyles:
    """全アプリ共通UIスタイル定数"""
    
    # == 基本レイアウトサイズ ==
    LABEL_WIDTH_STANDARD = 120      # ラベルコンテナ標準幅
    CONTROL_HEIGHT_STANDARD = 40    # TextField, Dropdown等標準高さ
    CONTROL_WIDTH_NUMBER = 80       # 数値入力欄標準幅  
    CONTROL_WIDTH_DROPDOWN = 200    # ドロップダウン標準幅
    ICON_SIZE_STANDARD = 20         # アイコン標準サイズ
    
    # == フォント系統一 ==
    # パネルヘッダー（白背景ヘッダー）
    PANEL_HEADER_SIZE = 16
    PANEL_HEADER_WEIGHT = ft.FontWeight.BOLD
    PANEL_HEADER_COLOR = ft.Colors.WHITE
    
    # ラベル（項目名）
    LABEL_SIZE = 12
    LABEL_WEIGHT = ft.FontWeight.BOLD
    LABEL_COLOR = ft.Colors.BLACK
    
    # 説明文（小）
    DESCRIPTION_SIZE = 10
    DESCRIPTION_COLOR = ft.Colors.GREY_600
    
    # セクション内項目ラベル（詳細設定内）
    SECTION_ITEM_SIZE = 14
    SECTION_ITEM_WEIGHT = ft.FontWeight.W_500
    SECTION_ITEM_COLOR = ft.Colors.BLACK87
    
    # == レイアウト・間隔統一 ==
    ROW_SPACING_STANDARD = 8        # Row内要素間spacing
    COLUMN_SPACING_STANDARD = 10    # Column内要素間spacing
    SECTION_INDENT = 20             # セクション内容字下げ
    CONTAINER_PADDING_STANDARD = 8  # Container内側padding
    MARGIN_SMALL = 4               # 小margin
    
    # == ダイアログサイズ ==
    DIALOG_WIDTH_STANDARD = 900
    DIALOG_HEIGHT_STANDARD = 700
    DIALOG_WIDTH_LARGE = 1400      # ユーザー辞書用大サイズ
    DIALOG_HEIGHT_LARGE = 900
    
    # == 線・境界線 ==
    DIVIDER_HEIGHT = 1
    DIVIDER_THICKNESS = 1
    DIVIDER_COLOR = ft.Colors.GREY_400


class UIComponentFactory:
    """汎用UIコンポーネント作成ファクトリー"""
    
    @staticmethod
    def create_standard_label_container(label_text: str, width: Optional[int] = None) -> ft.Container:
        """標準ラベルコンテナ作成（OCRページ4回重複パターン対応）"""
        return ft.Container(
            content=ft.Text(
                label_text, 
                weight=CommonUIStyles.LABEL_WEIGHT, 
                size=CommonUIStyles.LABEL_SIZE,
                color=CommonUIStyles.LABEL_COLOR
            ),
            width=width or CommonUIStyles.LABEL_WIDTH_STANDARD,
            alignment=ft.alignment.center_left
        )
    
    @staticmethod
    def create_standard_textfield(
        value: str = "", 
        hint_text: str = "",
        width: Optional[int] = None,
        height: Optional[int] = None,
        read_only: bool = False,
        **kwargs
    ) -> ft.TextField:
        """標準TextFieldコンポーネント"""
        return ft.TextField(
            value=value,
            hint_text=hint_text,
            width=width,
            height=height or CommonUIStyles.CONTROL_HEIGHT_STANDARD,
            read_only=read_only,
            **kwargs
        )
    
    @staticmethod
    def create_standard_row_layout(
        label_text: str, 
        control: ft.Control, 
        description: str = "",
        spacing: Optional[int] = None
    ) -> ft.Row:
        """標準 ラベル:コントロール 行レイアウト"""
        controls = [
            UIComponentFactory.create_standard_label_container(label_text),
            control
        ]
        
        # 説明文追加
        if description:
            controls.append(
                ft.Text(
                    description, 
                    size=CommonUIStyles.DESCRIPTION_SIZE, 
                    color=CommonUIStyles.DESCRIPTION_COLOR
                )
            )
            
        return ft.Row(
            controls,
            spacing=spacing or CommonUIStyles.ROW_SPACING_STANDARD,
            alignment=ft.MainAxisAlignment.START
        )
    
    @staticmethod
    def create_number_input_field(
        value: str = "1",
        width: Optional[int] = None,
        **kwargs
    ) -> ft.TextField:
        """数値入力専用TextField"""
        return UIComponentFactory.create_standard_textfield(
            value=value,
            width=width or CommonUIStyles.CONTROL_WIDTH_NUMBER,
            text_align=ft.TextAlign.CENTER,
            keyboard_type=ft.KeyboardType.NUMBER,
            input_filter=ft.NumbersOnlyInputFilter(),
            **kwargs
        )
    
    @staticmethod
    def create_panel_header_row(icon: ft.Icons, title: str) -> ft.Row:
        """パネルヘッダー行（白アイコン+白テキスト）"""
        return ft.Row([
            ft.Icon(
                icon, 
                size=CommonUIStyles.ICON_SIZE_STANDARD, 
                color=CommonUIStyles.PANEL_HEADER_COLOR
            ),
            ft.Text(
                title, 
                size=CommonUIStyles.PANEL_HEADER_SIZE, 
                weight=CommonUIStyles.PANEL_HEADER_WEIGHT, 
                color=CommonUIStyles.PANEL_HEADER_COLOR
            )
        ])
    
    @staticmethod
    def create_standard_divider() -> ft.Divider:
        """標準区切り線"""
        return ft.Divider(
            height=CommonUIStyles.DIVIDER_HEIGHT,
            thickness=CommonUIStyles.DIVIDER_THICKNESS,
            color=CommonUIStyles.DIVIDER_COLOR
        )
    
    @staticmethod
    def create_vertical_divider() -> ft.VerticalDivider:
        """標準縦区切り線"""
        return ft.VerticalDivider(
            width=CommonUIStyles.DIVIDER_HEIGHT,
            thickness=CommonUIStyles.DIVIDER_THICKNESS,
            color=CommonUIStyles.DIVIDER_COLOR
        )
