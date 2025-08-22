#!/usr/bin/env python3
"""
Flet RAGシステム - ホームページ
ホームページのメインコンポーネント
"""

import flet as ft
from .components import create_hero_section, create_features_section, create_stats_section
from ..shared.style_constants import CommonComponents


def show_home_page():
    """
    ホームページのコンテンツを作成
    
    Returns:
        ft.Container: ホームページコンテナ
    """
    return CommonComponents.create_standard_container(
        CommonComponents.create_standard_column([
            # ヒーローセクション
            create_hero_section(),
            
            # 主な機能セクション
            create_features_section(),
            
            # システム状況セクション
            create_stats_section(),
        ])
    )
