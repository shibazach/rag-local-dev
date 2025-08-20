#!/usr/bin/env python3
"""
Flet RAGシステム - ホームページ用コンポーネント
機能テーブル、統計カードなどの再利用可能なコンポーネント
"""

import flet as ft


def create_feature_table():
    """
    機能一覧表を作成（アイコン・項目名・説明の3列、6行）
    
    Returns:
        ft.Container: 機能テーブルコンテナ
    """
    features = [
        {"icon": "📄", "name": "多形式文書対応", "desc": "PDF、Word、テキスト、CSV、JSON、EMLファイルの処理に対応"},
        {"icon": "🔍", "name": "高精度OCR", "desc": "複数のOCRエンジンによる高精度なテキスト抽出"},
        {"icon": "🎭", "name": "LLM整形", "desc": "Ollamaを使用した日本語テキストの品質向上"},
        {"icon": "🔍", "name": "ベクトル検索", "desc": "複数の埋め込みモデルによる高精度検索"},
        {"icon": "⚡", "name": "リアルタイム処理", "desc": "SSEによる進捗表示とリアルタイム処理"},
        {"icon": "🔐", "name": "セキュリティ設計", "desc": "HTTPS対応、認証、API分離によるセキュアな設計"},
    ]
    
    # 6行×3列（アイコン・項目名・説明）のテーブル
    table_rows = []
    for feature in features:
        row = ft.Row([
            # 1列目：アイコン
            ft.Container(
                content=ft.Text(feature["icon"], size=20),
                width=50,
                alignment=ft.alignment.center
            ),
            # 2列目：項目名
            ft.Container(
                content=ft.Text(feature["name"] + "：", size=14, weight=ft.FontWeight.BOLD),
                width=150,
                alignment=ft.alignment.center_left
            ),
            # 3列目：説明
            ft.Container(
                content=ft.Text(feature["desc"], size=12, color=ft.Colors.GREY_700),
                width=400,
                alignment=ft.alignment.center_left
            )
        ], spacing=10, alignment=ft.MainAxisAlignment.CENTER)
        table_rows.append(row)
    
    return ft.Container(
        content=ft.Column(
            table_rows, 
            spacing=8,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER  # 表全体をセンター配置
        ),
        alignment=ft.alignment.center,
        width=float("inf")
    )


def create_stat_card(value, label, color):
    """
    統計カードを作成
    
    Args:
        value (str): 表示する値
        label (str): ラベル
        color (ft.Colors): カードのメイン色
        
    Returns:
        ft.Container: 統計カードコンテナ
    """
    return ft.Container(
        content=ft.Column([
            ft.Text(
                value,
                size=48,
                weight=ft.FontWeight.BOLD,
                color=color,
                text_align=ft.TextAlign.CENTER
            ),
            ft.Text(
                label,
                size=14,
                color=ft.Colors.GREY_600,
                text_align=ft.TextAlign.CENTER
            )
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=5),
        width=200,
        padding=ft.padding.all(20),
        bgcolor=ft.Colors.WHITE,
        border_radius=10,
        shadow=ft.BoxShadow(
            spread_radius=1,
            blur_radius=5,
            color=ft.Colors.with_opacity(0.1, ft.Colors.BLACK),
            offset=ft.Offset(0, 2)
        )
    )
    

def create_hero_section():
    """
    ヒーローセクションを作成
    
    Returns:
        ft.Container: ヒーローセクションコンテナ
    """
    return ft.Container(
        content=ft.Column([
            ft.Text(
                "R&D RAGシステム",
                size=42,  # 36→42に1段階UP
                weight=ft.FontWeight.BOLD,
                color=ft.Colors.WHITE,
                text_align=ft.TextAlign.CENTER
            ),
            ft.Container(height=5),  # タイトルとサブタイトル間を更に詰める
            ft.Text(
                "AIブーストされた新世代ドキュメント検索プラットフォーム✨",
                size=16,
                color=ft.Colors.with_opacity(0.8, ft.Colors.WHITE),
                text_align=ft.TextAlign.CENTER
            )
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=0),
        bgcolor="#334155",
        padding=ft.padding.only(top=15, bottom=25, left=25, right=25),  # 上部余白を更に小さく
        margin=ft.margin.all(0),
        width=float("inf")
    )


def create_features_section():
    """
    主な機能セクションを作成
    
    Returns:
        ft.Container: 機能セクションコンテナ
    """
    return ft.Container(
        content=ft.Column([
            ft.Text(
                "主な機能",
                size=24,
                weight=ft.FontWeight.BOLD,
                text_align=ft.TextAlign.CENTER,
                color=ft.Colors.BLUE_GREY_800
            ),
            ft.Container(height=20),
            
            # 機能一覧表
            create_feature_table(),
            
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        padding=ft.padding.all(30)
    )


def create_stats_section():
    """
    システム状況セクションを作成
    
    Returns:
        ft.Container: 統計セクションコンテナ
    """
    return ft.Container(
        content=ft.Column([
            ft.Text(
                "システム状況",
                size=24,
                weight=ft.FontWeight.BOLD,
                text_align=ft.TextAlign.CENTER,
                color=ft.Colors.BLUE_GREY_800
            ),
            ft.Container(height=20),
            
            # 統計カード
            ft.Row([
                create_stat_card("31", "登録ファイル数", ft.Colors.BLUE_600),
                create_stat_card("1", "チャットセッション数", ft.Colors.GREEN_600),
                create_stat_card("0", "埋め込みベクトル数", ft.Colors.ORANGE_600),
            ], alignment=ft.MainAxisAlignment.CENTER, spacing=20)
            
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        padding=ft.padding.all(30)
    )
