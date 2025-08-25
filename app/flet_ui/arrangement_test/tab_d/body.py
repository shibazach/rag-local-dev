#!/usr/bin/env python3
"""
Flet RAGシステム - 配置テスト タブD (縦スライダーレイヤー検討)
OCR調整ページの4分割+3スライダー構造の動作検証
真のオーバーレイ縦スライダー実装（定数なし・自動レイアウト対応）
"""

import flet as ft
import math
from app.flet_ui.shared.style_constants import CommonComponents, PageStyles, SLIDER_RATIOS




class TabD:
    """タブD: 縦スライダーレイヤー検討（真のオーバーレイ実装）"""
    
    def __init__(self):
        # 動的比率制御（OCR調整ページと同様）
        self.left_split_level = 3   # 左側の上下比率
        self.right_split_level = 3  # 右側の上下比率
        self.horizontal_level = 3   # 左右比率
        
        # 共通比率テーブル使用
        self.ratios = SLIDER_RATIOS
    
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
        
        # ===== 一体型コンポーネントでワンアクション配置 =====
        # 4分割メインコンテンツ作成
        main_4quad_content = self._create_4quad_layout()
        
        # 完全一体型レイアウト適用
        main_content = CommonComponents.create_complete_layout_with_full_sliders(
            main_4quad_content,
            self.left_split_level, self.on_left_change,
            self.right_split_level, self.on_right_change, 
            self.horizontal_level, self.on_horizontal_change
        )
        
        return ft.Container(
            content=ft.Column([
                explanation,
                ft.Container(height=8),
                main_content
            ], spacing=0, expand=True),
            expand=True
        )
    
    def _create_4quad_layout(self) -> ft.Container:
        """4分割レイアウトのみ作成（ガイドエリア・スライダーは一体型コンポーネントが担当）"""
        
        # 4つのペインコンテナ作成
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
        
        # Container参照保持（比率更新用）
        self.left_container = ft.Container(content=self.left_column, expand=1)
        self.right_container = ft.Container(content=self.right_column, expand=1)
        
        # 4分割メイン行作成
        self.main_row = ft.Row([
            self.left_container,
            ft.VerticalDivider(width=1, thickness=1, color=ft.Colors.GREY_400),
            self.right_container
        ], spacing=0, expand=True)
        
        # 初期レイアウト適用
        self._update_layout()
        
        # 4分割部分のみ返す
        return ft.Container(content=self.main_row, expand=True)
    
    def _create_demo_pane(self, title: str, bgcolor: str, icon: str) -> ft.Container:
        """デモ用ペイン作成"""
        # 基本コンテンツ
        content_items = [
            ft.Text(f"{icon} {title}", size=16, weight=ft.FontWeight.BOLD),
            ft.Text("レスポンシブ動作確認", size=12, color=ft.Colors.GREY_600),
            ft.Text("スライダーで比率変更", size=12, color=ft.Colors.GREY_600)
        ]
        
        # OCR設定ペインのみフォーカステスト用ボタン追加（機能なし）
        if title == "OCR設定":
            content_items.append(ft.Container(height=8))
            content_items.append(ft.ElevatedButton("テストボタン"))
        
        return ft.Container(
            content=ft.Column(content_items, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
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
        
        # 左右比率（files/page.pyパターン適用：Container直接更新）
        self.left_container.expand = left_ratio
        self.right_container.expand = right_ratio
        
        # UI更新（Container直接更新）
        try:
            if hasattr(self, 'left_container') and self.left_container.page:
                self.left_container.update()
            if hasattr(self, 'right_container') and self.right_container.page:
                self.right_container.update()
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

