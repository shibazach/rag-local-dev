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
        
        # ===== 分離型コンポーネントで横+縦組み合わせ実装 =====
        # 4分割メインコンテンツ作成
        main_4quad_content = self._create_4quad_layout()
        
        # 横スライダー（共通化済み）
        horizontal_slider = CommonComponents.create_horizontal_slider(
            self.horizontal_level, self.on_horizontal_change
        )
        
        # 基本レイアウト（横スライダー付き）
        base_layout = PageStyles.create_complete_layout_with_slider(
            main_4quad_content, horizontal_slider
        )
        
        # 縦スライダーオーバーレイ要素作成
        vertical_overlays = self._create_vertical_slider_overlays()
        
        # Stack構成（基本レイアウト + 縦スライダーオーバーレイ）
        main_content = ft.Container(
            content=ft.Stack([
                base_layout
            ] + vertical_overlays, expand=True, clip_behavior=ft.ClipBehavior.NONE),
            expand=True
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
        self._update_vertical_layout()
        
        # 4分割部分のみ返す
        return ft.Container(content=self.main_row, expand=True)
    
    def _create_vertical_slider_overlays(self) -> list:
        """縦スライダーオーバーレイ要素作成（共通コンポーネント分離版）"""
        # 左縦スライダー
        left_vslider = CommonComponents.create_vertical_slider(
            self.left_split_level, self.on_left_change
        )
        
        # 右縦スライダー
        right_vslider = CommonComponents.create_vertical_slider(
            self.right_split_level, self.on_right_change
        )
        
        # 左オーバーレイ配置
        left_overlay = ft.Container(
            content=ft.Column([
                ft.Container(expand=1),  # 上部（25%）
                ft.Container(
                    content=left_vslider,
                    expand=2,  # 中央部分（50%）
                    alignment=ft.alignment.center,
                    bgcolor="#FFCCCC"  # デバッグ用
                ),
                ft.Container(expand=1),  # 下部（25%）
            ], spacing=0),
            left=-84,  # 標準配置位置
            top=0, bottom=32,  # 32px = 横スライダー高さを除外
            width=200,
        )
        
        # 右オーバーレイ配置
        right_overlay = ft.Container(
            content=ft.Column([
                ft.Container(expand=1),  # 上部（25%）
                ft.Container(
                    content=right_vslider,
                    expand=2,  # 中央部分（50%）
                    alignment=ft.alignment.center,
                    bgcolor="#FFCCCC"  # デバッグ用
                ),
                ft.Container(expand=1),  # 下部（25%）
            ], spacing=0),
            right=-84,  # 標準配置位置
            top=0, bottom=32,  # 32px = 横スライダー高さを除外
            width=200,
        )
        
        return [left_overlay, right_overlay]
    
    def _create_demo_pane(self, title: str, bgcolor: str, icon: str) -> ft.Container:
        """デモ用ペイン作成"""
        # 基本コンテンツ
        content_items = [
            ft.Text(f"{icon} {title}", size=16, weight=ft.FontWeight.BOLD),
            ft.Text("レスポンシブ動作確認", size=12, color=ft.Colors.GREY_600),
            ft.Text("スライダーで比率変更", size=12, color=ft.Colors.GREY_600)
        ]
        
        # OCR設定ペインのみダイアログテスト用ボタン追加
        if title == "OCR設定":
            content_items.append(ft.Container(height=8))
            
            def test_dialog_click(e):
                def close_dialog(e):
                    e.control.page.close(dialog)
                
                dialog = ft.AlertDialog(
                    title=ft.Text("🧪 tab_d ダイアログテスト", size=16, weight=ft.FontWeight.BOLD),
                    content=ft.Container(
                        content=ft.Text("縦スライダーあり環境でのダイアログ表示テスト\n\nこのダイアログが見えていますか？"),
                        width=400,
                        height=150,
                        bgcolor=ft.Colors.ORANGE_50,
                        border=ft.border.all(2, ft.Colors.ORANGE),
                        padding=ft.padding.all(20)
                    ),
                    actions=[
                        ft.TextButton("閉じる", on_click=close_dialog)
                    ],
                    modal=True
                )
                # tab_a成功方式: page.open()
                current_page = e.control.page
                current_page.open(dialog)
            
            content_items.append(ft.ElevatedButton(
                text="🧪 ダイアログテスト",
                on_click=test_dialog_click,
                bgcolor=ft.Colors.ORANGE_100
            ))
        
        return ft.Container(
            content=ft.Column(content_items, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            expand=True, alignment=ft.alignment.center,
            bgcolor=bgcolor, border_radius=8,
            margin=ft.margin.all(4), padding=ft.padding.all(8)
        )
    

    
    def _update_vertical_layout(self):
        """縦スライダーのみレイアウト更新（横スライダーは共通メソッドが担当）"""
        # 縦比率計算
        left_top_ratio, left_bottom_ratio = self.ratios[self.left_split_level] 
        right_top_ratio, right_bottom_ratio = self.ratios[self.right_split_level]
        
        # ペイン内容更新（初回のみ）
        if not self.top_left_container.content:
            self.top_left_container.content = self._create_demo_pane("OCR設定", ft.Colors.BLUE_100, "🔧")
            self.bottom_left_container.content = self._create_demo_pane("OCR結果", ft.Colors.GREEN_100, "📄")
            self.top_right_container.content = self._create_demo_pane("詳細設定", ft.Colors.ORANGE_100, "⚙️")
            self.bottom_right_container.content = self._create_demo_pane("PDFプレビュー", ft.Colors.PURPLE_100, "📖")
        
        # 縦比率適用
        self.top_left_container.expand = left_top_ratio
        self.bottom_left_container.expand = left_bottom_ratio
        self.top_right_container.expand = right_top_ratio  
        self.bottom_right_container.expand = right_bottom_ratio
        
        # 縦コンテナUI更新
        try:
            if hasattr(self, 'left_column') and self.left_column.page:
                self.left_column.update()
            if hasattr(self, 'right_column') and self.right_column.page:
                self.right_column.update()
        except:
            pass
    
    def on_left_change(self, e):
        """左スライダー変更（縦比率のみ）"""
        self.left_split_level = int(float(e.control.value))
        self._update_vertical_layout()
        print(f"⚡ tab_d 左縦スライダー変更: レベル{self.left_split_level}")
    
    def on_right_change(self, e):
        """右スライダー変更（縦比率のみ）"""
        self.right_split_level = int(float(e.control.value))
        self._update_vertical_layout()
        print(f"⚡ tab_d 右縦スライダー変更: レベル{self.right_split_level}")
    
    def on_horizontal_change(self, e):
        """横スライダー変更時に左右比率を調整（共通メソッド使用）"""
        self.horizontal_level = int(float(e.control.value))
        
        # 共通メソッドで比率適用（0対策自動適用）
        if hasattr(self, 'main_row') and self.main_row:
            CommonComponents.apply_slider_ratios_to_row(
                self.main_row, self.ratios, self.horizontal_level
            )
        
        print(f"⚡ tab_d 横スライダー変更: レベル{self.horizontal_level}")

