#!/usr/bin/env python3
"""
Flet RAGシステム - 配置テスト タブD (縦スライダーレイヤー検討)
OCR調整ページの4分割+3スライダー構造の動作検証
真のオーバーレイ縦スライダー実装（定数なし・自動レイアウト対応）
"""

import flet as ft
import math
from ..shared.style_constants import CommonComponents, PageStyles

# スライダー定数（縦操作領域確保版）
SL_LEN = 320      # 縦スライダーの"横幅"（= Container.width）
SL_HEIGHT = 200   # 縦スライダーの"縦操作領域"（= Container.height）
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
                ft.Text("⚡ 完成版 - 4象限+縦スライダー操作可能", 
                       size=16, weight=ft.FontWeight.BOLD),
                ft.Container(height=4),
                ft.Row([
                    ft.Text("🔴 赤枠: 200px×200px（操作領域確保）", size=12, color=ft.Colors.RED_700),
                    ft.Container(width=16),
                    ft.Text("🔵 青枠: 36px（中央基準）", size=12, color=ft.Colors.BLUE_700),
                    ft.Container(width=16),
                    ft.Text("✅ 完了: -84px配置・横共通コンポーネント適用", size=12, color=ft.Colors.GREEN_700),
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
        
        # 4つのペイン作成
        self.top_left_container = ft.Container(expand=1)
        self.bottom_left_container = ft.Container(expand=1)  
        self.top_right_container = ft.Container(expand=1)
        self.bottom_right_container = ft.Container(expand=1)
        
        # 左右カラム作成  
        self.left_column = ft.Column([
            self.top_left_container,
            ft.Divider(height=1, thickness=1, color=ft.Colors.GREY_400),
            self.bottom_left_container
        ], spacing=0, expand=True)
        
        self.right_column = ft.Column([
            self.top_right_container,
            ft.Divider(height=1, thickness=1, color=ft.Colors.GREY_400),
            self.bottom_right_container  
        ], spacing=0, expand=True)
        
        # メイン行作成（中央4分割）
        self.main_row = ft.Row([
            ft.Container(content=self.left_column, expand=1),
            ft.VerticalDivider(width=1, thickness=1, color=ft.Colors.GREY_400),
            ft.Container(content=self.right_column, expand=1)
        ], spacing=0, expand=True)
        
        # 横スライダー作成（OCR調整と同じ共通コンポーネント使用）
        horizontal_slider = CommonComponents.create_horizontal_slider(
            self.horizontal_level, self.on_horizontal_change
        )
        
        # メインコンテンツ部分のみ返す（横スライダーは共通コンポーネントで配置）
        main_content = ft.Container(
            expand=True,
            content=ft.Row([
                # 左ガイド（青枠）純粋36px
                ft.Container(width=36, bgcolor=ft.Colors.BLUE_50,
                            border=ft.border.all(1, ft.Colors.BLUE_300),
                            disabled=True),
                # 中央領域（4分割パネル）
                ft.Container(content=self.main_row, expand=True),
                # 右ガイド（青枠）純粋36px
                ft.Container(width=36, bgcolor=ft.Colors.BLUE_50,
                            border=ft.border.all(1, ft.Colors.BLUE_300),
                            disabled=True),
            ], expand=True, spacing=0, vertical_alignment=ft.CrossAxisAlignment.STRETCH)
        )
        
        # OCR調整と全く同じ実装：共通コンポーネントで横スライダー配置
        # 横スライダーに赤枠追加（可視化分析用）
        red_bordered_slider = ft.Container(
            content=horizontal_slider,
            border=ft.border.all(2, ft.Colors.RED)
        )
        complete_layout = PageStyles.create_complete_layout_with_slider(
            main_content, red_bordered_slider
        )
        # 横スライダー収容コンテナに青枠追加（階層可視化用）
        return ft.Container(
            content=complete_layout,
            border=ft.border.all(2, ft.Colors.BLUE)
        )
    
    def _create_overlay_layer(self) -> ft.Container:
        """オーバーレイレイヤー: 余白なし純粋配置で縦スライダー中央配置"""
        
        # 縦スライダー作成（縦操作領域確保版）
        def create_vslider(value=50, on_change=None):
            return ft.Container(
                width=200,         # Sliderの実サイズに合わせる
                height=200,        # 操作可能領域確保
                content=ft.Slider(
                    min=1, max=5, value=value, divisions=4,
                    rotate=math.pi / 2, on_change=on_change, width=200, height=30
                ),
                # 赤枠で可視化（位置確認用）
                border=ft.border.all(2, ft.Colors.RED),
                bgcolor=ft.Colors.TRANSPARENT  # 透明化で内部確認
            )
        
        left_slider = create_vslider(self.left_split_level, self.on_left_change)
        right_slider = create_vslider(self.right_split_level, self.on_right_change)
        
        return ft.Container(
            expand=True,
            # padding完全削除で純粋配置
            content=ft.Column([
                # スライダーのみ直接配置（青枠削除）
                ft.Stack(
                    alignment=ft.alignment.center,
                    clip_behavior=ft.ClipBehavior.NONE,
                    expand=True,
                    controls=[
                        ft.Container(
                            content=left_slider,
                            left=-84,   # (200-32)/2=84px（200px基準）
                        ),
                        ft.Container(
                            content=right_slider,
                            right=-84,  # (200-32)/2=84px（200px基準）
                        ),
                    ],
                ),
                
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
    

    
    def _update_layout(self):
        """レイアウトを実際に更新（4分割版）"""
        # 比率計算
        left_top_ratio, left_bottom_ratio = self.ratios[self.left_split_level] 
        right_top_ratio, right_bottom_ratio = self.ratios[self.right_split_level]
        left_ratio, right_ratio = self.ratios[self.horizontal_level]
        
        # ペイン内容更新
        self.top_left_container.content = self._create_demo_pane("OCR設定", ft.Colors.BLUE_100, "🔧")
        self.bottom_left_container.content = self._create_demo_pane("OCR結果", ft.Colors.GREEN_100, "📄")
        self.top_right_container.content = self._create_demo_pane("詳細設定", ft.Colors.ORANGE_100, "⚙️")
        self.bottom_right_container.content = self._create_demo_pane("PDFプレビュー", ft.Colors.PURPLE_100, "📖")
        
        # 比率適用
        self.top_left_container.expand = left_top_ratio
        self.bottom_left_container.expand = left_bottom_ratio
        self.top_right_container.expand = right_top_ratio  
        self.bottom_right_container.expand = right_bottom_ratio
        
        # 左右比率
        self.left_column.expand = left_ratio
        self.right_column.expand = right_ratio
        
        # UI更新
        try:
            if hasattr(self, 'main_row') and self.main_row.page:
                self.main_row.update()
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

