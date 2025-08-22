#!/usr/bin/env python3
"""
Flet RAGシステム - 配置テスト タブD (縦スライダーレイヤー検討)
OCR調整ページの4分割+3スライダー構造の動作検証
真のオーバーレイ縦スライダー実装（定数なし・自動レイアウト対応）
"""

import flet as ft
import math

# スライダー定数（縦操作領域確保版）
SL_LEN = 320      # 縦スライダーの"横幅"（= Container.width）
SL_HEIGHT = 300   # 縦スライダーの"縦操作領域"（= Container.height）
SL_THICK = 22     # スライダーの"太さ"（参考値）
GUIDE_WIDTH = 36  # 青枠（ガイドライン）の幅
GUIDE_CENTER = 18 # 青枠の中央位置（36px / 2）


class TabD:
    """タブD: 縦スライダーレイヤー検討（真のオーバーレイ実装）"""
    
    def __init__(self):
        # 動的比率制御（OCR調整ページと同様）
        self.left_split_level = 3   # 左側の上下比率
        self.right_split_level = 3  # 右側の上下比率
        self.horizontal_level = 3   # 左右比率
        
        # 比率テーブル（1:5 ～ 5:1）
        self.ratios = {1: (1, 5), 2: (2, 4), 3: (3, 3), 4: (4, 2), 5: (5, 1)}
    
    def create_content(self) -> ft.Control:
        """真のオーバーレイ縦スライダー実装（定数なし・自動レイアウト対応）"""
        
        # 説明エリア
        explanation = ft.Container(
            content=ft.Column([
                ft.Text("⚡ 縦操作確保版 - 320px×300px操作領域", 
                       size=16, weight=ft.FontWeight.BOLD),
                ft.Container(height=4),
                ft.Row([
                    ft.Text("🔴 赤枠: 320px×300px（縦操作確保）", size=12, color=ft.Colors.RED_700),
                    ft.Container(width=16),
                    ft.Text("🔵 青枠: 36px純粋幅", size=12, color=ft.Colors.BLUE_700),
                    ft.Container(width=16),
                    ft.Text("📐 配置: -176px", size=12, color=ft.Colors.GREEN_700),
                ], alignment=ft.MainAxisAlignment.CENTER)
            ]),
            padding=ft.padding.all(12),
            bgcolor=ft.Colors.BLUE_GREY_50,
            border_radius=8
        )
        
        # ===== 下層: 本体レイアウト =====
        base_layer = self._create_base_layout()
        
        # ===== 上層: オーバーレイレイヤー（縦スライダー配置） =====
        overlay_layer = self._create_overlay_layer()
        
        # 初期レイアウト適用（コンテナ作成後）
        self._update_layout()
        
        # ===== ルート: 2層をStackで重ね =====
        main_content = ft.Stack(
            expand=True,
            clip_behavior=ft.ClipBehavior.NONE,  # 画面端からのはみ出し許可
            controls=[base_layer, overlay_layer],
        )
        
        return ft.Container(
            content=ft.Column([
                explanation,
                ft.Container(height=8),
                main_content
            ], spacing=0, expand=True),
            expand=True
        )
    
    def _create_base_layout(self) -> ft.Container:
        """本体レイアウト: 左右ガイド + 中央1パネル + 下部横スライダー（余白なし）"""
        
        # 中央パネル（シンプル化）
        self.main_panel = ft.Container(
            content=ft.Text("メインパネル（テスト用）", size=20, weight=ft.FontWeight.BOLD),
            expand=True,
            alignment=ft.alignment.center,
            bgcolor=ft.Colors.GREY_100
        )
        
        # 横スライダー作成
        horizontal_slider = self._create_h_slider("左右分割", self.horizontal_level, self.on_horizontal_change)
        
        return ft.Container(
            expand=True,
            # padding完全削除
            content=ft.Column([
                # メイン行: 左ガイド + 中央1パネル + 右ガイド（余白なし）
                ft.Row([
                    # 左ガイド（青枠）純粋36px
                    ft.Container(width=36, bgcolor=ft.Colors.BLUE_50,
                                border=ft.border.all(1, ft.Colors.BLUE_300)),
                    # 中央領域（1パネル）
                    self.main_panel,
                    # 右ガイド（青枠）純粋36px
                    ft.Container(width=36, bgcolor=ft.Colors.BLUE_50,
                                border=ft.border.all(1, ft.Colors.BLUE_300)),
                ], expand=True, spacing=0, vertical_alignment=ft.CrossAxisAlignment.STRETCH),
                
                # 下部横スライダーエリア
                ft.Container(
                    content=ft.Row([horizontal_slider], alignment=ft.MainAxisAlignment.CENTER),
                    height=32, bgcolor=ft.Colors.RED_50,
                    border=ft.border.all(2, ft.Colors.RED_400)
                )
            ], expand=True, spacing=0),
        )
    
    def _create_overlay_layer(self) -> ft.Container:
        """オーバーレイレイヤー: 余白なし純粋配置で縦スライダー中央配置"""
        
        # 縦スライダー作成（縦操作領域確保版）
        def create_vslider(value=50, on_change=None):
            return ft.Container(
                width=SL_LEN,      # 320px（横幅）
                height=SL_HEIGHT,  # 300px（縦操作領域）
                content=ft.Slider(
                    min=1, max=5, value=value, divisions=4,
                    rotate=math.pi / 2, on_change=on_change, width=300
                ),
                # 赤枠で可視化（位置確認用）
                border=ft.border.all(2, ft.Colors.RED),
                bgcolor="#ffcccc"  # 半透明赤背景
            )
        
        left_slider = create_vslider(self.left_split_level, self.on_left_change)
        right_slider = create_vslider(self.right_split_level, self.on_right_change)
        
        return ft.Container(
            expand=True,
            # padding完全削除で純粋配置
            content=ft.Column([
                ft.Row([
                    # 左ガイド36px（寸法表示付き・透明化）
                    ft.Container(
                        width=36,
                        content=ft.Text("L\n36px", size=8, color=ft.Colors.BLUE, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER),
                        alignment=ft.alignment.center,
                        bgcolor=ft.Colors.TRANSPARENT  # マウスイベント通過
                    ),
                    # 中央領域（余白なし）
                    ft.Container(
                        expand=True,
                        # 縦スライダーを純粋計算で配置
                        content=ft.Stack(
                            alignment=ft.alignment.center,        # 縦中央揃え
                            clip_behavior=ft.ClipBehavior.NONE,   # はみ出し許可
                            controls=[
                                ft.Container(
                                    content=left_slider,
                                    left=-176,  # 元の176px配置
                                ),
                                ft.Container(
                                    content=right_slider,
                                    right=-176,  # 元の176px配置
                                ),
                                # 中央基準線（簡素版）
                                ft.Container(
                                    width=1,
                                    height=200,
                                    bgcolor=ft.Colors.GREEN_300,
                                    opacity=0.5
                                ),
                            ],
                        ),
                    ),
                    # 右ガイド36px（寸法表示付き・透明化）
                    ft.Container(
                        width=36,
                        content=ft.Text("R\n36px", size=8, color=ft.Colors.BLUE, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER),
                        alignment=ft.alignment.center,
                        bgcolor=ft.Colors.TRANSPARENT  # マウスイベント通過
                    ),
                ], expand=True, spacing=0, vertical_alignment=ft.CrossAxisAlignment.STRETCH),
                
                # 下部エリア（横スライダーと同じ高さ）
                ft.Container(height=32),
            ], expand=True, spacing=0),
        )
    
    def _create_demo_pane(self, title: str, bgcolor: str, icon: str) -> ft.Container:
        """デモ用ペイン作成"""
        return ft.Container(
            content=ft.Column([
                ft.Text(f"{icon} {title}", size=16, weight=ft.FontWeight.BOLD),
                ft.Text("レスポンシブ動作確認", size=12, color=ft.Colors.GREY_600),
                ft.Text("スライダーで比率変更", size=12, color=ft.Colors.GREY_600)
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            expand=True, alignment=ft.alignment.center,
            bgcolor=bgcolor, border_radius=8,
            margin=ft.margin.all(4), padding=ft.padding.all(8)
        )
    
    def _create_h_slider(self, label: str, value: int, on_change) -> ft.Container:
        """横スライダー作成（ラベルなし・中央配置精密版）"""
        return ft.Container(
            content=ft.Slider(
                min=1, max=5, value=value, divisions=4,
                on_change=on_change, width=200
            ),
            alignment=ft.alignment.center,
            expand=True
        )
    
    def _update_layout(self):
        """レイアウトを実際に更新（シンプル1パネル版）"""
        # メインパネル更新（シンプル版）
        self.main_panel.content = ft.Text(
            f"テストパネル\n左: {self.left_split_level}\n右: {self.right_split_level}\n横: {self.horizontal_level}",
            size=16, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER
        )
        
        # UI更新
        try:
            if hasattr(self, 'main_panel') and self.main_panel.page:
                self.main_panel.update()
        except:
            pass
    
    def on_left_change(self, e):
        """左スライダー変更（実動作）"""
        self.left_split_level = int(float(e.control.value))

        self._update_layout()
    
    def on_right_change(self, e):
        """右スライダー変更（実動作）"""
        self.right_split_level = int(float(e.control.value))
 
        self._update_layout()
    
    def on_horizontal_change(self, e):
        """横スライダー変更（実動作）"""
        self.horizontal_level = int(float(e.control.value))

        self._update_layout()

