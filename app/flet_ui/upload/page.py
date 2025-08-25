#!/usr/bin/env python3
"""
Flet RAGシステム - アップロードページメイン
1:2横分割（左:右）+ 左ペイン1:1縦分割 + リアルタイムログ
"""

import flet as ft
from .components import FileUploadArea, FolderUploadArea, RealTimeLogArea
from app.flet_ui.shared.style_constants import CommonComponents, PageStyles

def show_upload_page(page: ft.Page = None):
    """アップロードページ表示関数"""
    if page:
        PageStyles.set_page_background(page)
    
    # 左ペイン（上下1:1分割）
    file_upload_area = FileUploadArea()
    folder_upload_area = FolderUploadArea()
    
    left_pane = CommonComponents.create_standard_column([
        file_upload_area,
        CommonComponents.create_spacing_container(4),  # 8px → 4px（margin削除により調整）
        folder_upload_area
    ])
    
    # 右ペイン（リアルタイムログ）
    right_pane = ft.Container(
        content=RealTimeLogArea(),
        expand=2  # 1:2の比率
    )
    
    # メインレイアウト（左右1:2分割）
    main_layout = CommonComponents.create_standard_row([
        left_pane,
        right_pane
    ])
    
    return ft.Container(
        content=main_layout,
        expand=True
    )
