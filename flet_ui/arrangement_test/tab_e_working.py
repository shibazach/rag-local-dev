"""
Tab E: 動作するセクション化Fletコントロールギャラリー
ExpansionTileを使用して正常な展開/折畳機能を実装
"""
import sys
import os
import importlib.util
import flet as ft
import webbrowser
from pathlib import Path


class TabEWorking:
    def __init__(self):
        self.examples_path = Path(__file__).parent / "examples"
        self.all_samples = self._scan_all_samples()
        
    def create_content(self) -> ft.Control:
        """動作するセクション化ギャラリー表示"""
        return ft.Container(
            content=self._create_main_layout(),
            expand=True,
            padding=ft.padding.all(16)
        )
        
    def _scan_all_samples(self):
        """全サンプルを自動スキャン"""
        categories = {}
        
        if not self.examples_path.exists():
            return categories
            
        for category_dir in self.examples_path.iterdir():
            if not category_dir.is_dir() or category_dir.name.startswith('.'):
                continue
                
            category_name = category_dir.name
            categories[category_name] = []
            
            for control_dir in category_dir.iterdir():
                if not control_dir.is_dir():
                    continue
                    
                control_name = control_dir.name
                examples = []
                
                for sample_file in control_dir.iterdir():
                    if (sample_file.is_file() and 
                        sample_file.name.endswith('.py') and 
                        sample_file.name != 'index.py' and
                        not sample_file.name.startswith('__')):
                        
                        relative_path = f"{category_name}/{control_name}/{sample_file.name}"
                        examples.append({
                            'name': sample_file.stem,
                            'path': relative_path,
                            'display_name': self._create_display_name(sample_file.stem)
                        })
                
                if examples:
                    categories[category_name].append({
                        'control': control_name,
                        'examples': sorted(examples, key=lambda x: x['name'])
                    })
                    
        return categories
        
    def _create_display_name(self, filename):
        """ファイル名から表示名を生成"""
        name = filename
        if name.startswith(('01_', '02_', '03_', '04_', '05_', '06_', '07_', '08_', '09_')):
            name = name[3:]
        name = name.replace('_', ' ').title()
        return name
        
    def _create_main_layout(self):
        """メインレイアウト"""
        total_samples = sum(
            len(control['examples']) 
            for controls in self.all_samples.values() 
            for control in controls
        )
        
        # ExpansionTileセクション作成
        expansion_tiles = []
        for category_name, controls in sorted(self.all_samples.items()):
            if controls:
                tile = self._create_expansion_tile(category_name, controls)
                if tile:
                    expansion_tiles.append(tile)
        
        return ft.Column([
            # ヘッダー
            ft.Container(
                content=ft.Column([
                    ft.Text("🎨 Fletコントロールギャラリー（動作版）", 
                           size=24, weight=ft.FontWeight.BOLD),
                    ft.Row([
                        ft.Text(f"📊 全{total_samples}サンプル", 
                               size=14, color=ft.Colors.BLUE_600),
                        ft.Text(f"📁 {len(self.all_samples)}カテゴリ", 
                               size=14, color=ft.Colors.GREEN_600),
                        ft.Text("👆 カテゴリをクリックして展開", 
                               size=12, color=ft.Colors.GREY_600),
                    ], spacing=16),
                ]),
                bgcolor=ft.Colors.BLUE_50,
                padding=16,
                border_radius=12,
                margin=ft.margin.only(bottom=16)
            ),
            
            # ExpansionTile一覧（自動で展開/折畳が動作）
            ft.Column(expansion_tiles, spacing=4),
            
        ], scroll=ft.ScrollMode.AUTO, expand=True)
        
    def _create_expansion_tile(self, category_name: str, controls: list):
        """ExpansionTileを使った展開可能セクション"""
        if not controls:
            return None
            
        category_display_name = self._get_category_display_name(category_name)
        total_examples = sum(len(control['examples']) for control in controls)
        
        # 重要コントロール優先ソート
        sorted_controls = self._sort_controls_by_importance(controls)
        
        # コントロールグリッド作成
        control_items = []
        for control_info in sorted_controls:
            control_name = control_info['control']
            examples = control_info['examples']
            
            # サンプルウィジェット（最初の1つ）
            sample_widget = None
            if examples:
                sample_widget = self._load_example(examples[0]['path'])
            
            control_items.append(
                ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Text(control_name.title(), 
                                   weight=ft.FontWeight.BOLD, size=14),
                            ft.Text(f"{len(examples)}例", 
                                   size=11, color=ft.Colors.GREY_500),
                            ft.IconButton(
                                icon=ft.Icons.OPEN_IN_NEW,
                                tooltip="ドキュメント",
                                on_click=lambda e, n=control_name.lower(): self._open_docs(n),
                                scale=0.7
                            )
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        ft.Container(
                            content=sample_widget if sample_widget else ft.Text("読み込み中...", size=10),
                            border=ft.border.all(1, ft.Colors.GREY_300),
                            border_radius=6,
                            padding=8,
                            height=100
                        )
                    ]),
                    width=280,
                    margin=ft.margin.only(right=12, bottom=8),
                    padding=8,
                    border=ft.border.all(1, ft.Colors.GREY_200),
                    border_radius=8
                )
            )
        
        # 3列グリッド配置
        grid_rows = []
        controls_per_row = 3
        for i in range(0, len(control_items), controls_per_row):
            row_controls = control_items[i:i + controls_per_row]
            grid_rows.append(
                ft.Row(row_controls, spacing=8, wrap=True)
            )
        
        # ExpansionTile作成（Flet標準コンポーネント）
        return ft.ExpansionTile(
            title=ft.Text(
                f"{self._get_category_icon_text(category_name)} {category_display_name}",
                size=16,
                weight=ft.FontWeight.BOLD
            ),
            subtitle=ft.Text(
                f"{len(controls)}コントロール, {total_examples}サンプル",
                size=12,
                color=ft.Colors.GREY_600
            ),
            leading=ft.Icon(
                self._get_category_icon(category_name),
                color=self._get_category_color(category_name)
            ),
            controls=grid_rows,
            bgcolor=ft.Colors.GREY_50,
            collapsed_bgcolor=ft.Colors.WHITE,
        )
        
    def _sort_controls_by_importance(self, controls):
        """重要コントロール優先ソート"""
        importance_order = {
            # 入力カテゴリの重要コントロール
            'slider': 1,
            'textfield': 2,
            'dropdown': 3,
            'checkbox': 4,
            'rangeslider': 5,
            
            # ダイアログカテゴリの重要コントロール
            'timepicker': 1,
            'datepicker': 2,
            'alertdialog': 3,
            
            # ボタンカテゴリの重要コントロール
            'elevatedbutton': 1,
            'textbutton': 2,
            'iconbutton': 3,
            
            # チャートカテゴリ
            'piechart': 1,
            'barchart': 2,
            'linechart': 3,
        }
        
        def get_importance(control_info):
            control_name = control_info['control'].lower()
            return importance_order.get(control_name, 999)
        
        return sorted(controls, key=get_importance)
        
    def _get_category_icon(self, category_name: str):
        """カテゴリアイコン"""
        icons = {
            'animations': ft.Icons.ANIMATION,
            'buttons': ft.Icons.SMART_BUTTON,
            'charts': ft.Icons.ANALYTICS,
            'colors': ft.Icons.PALETTE,
            'contrib': ft.Icons.EXTENSION,
            'dialogs': ft.Icons.CHAT_BUBBLE,
            'displays': ft.Icons.MONITOR,
            'input': ft.Icons.INPUT,
            'layout': ft.Icons.VIEW_QUILT,
            'navigation': ft.Icons.NAVIGATION,
            'utility': ft.Icons.BUILD
        }
        return icons.get(category_name, ft.Icons.FOLDER)
        
    def _get_category_icon_text(self, category_name: str):
        """カテゴリアイコン文字"""
        icons = {
            'animations': '🎬',
            'buttons': '🔘',
            'charts': '📊',
            'colors': '🎨',
            'contrib': '🔧',
            'dialogs': '💬',
            'displays': '📺',
            'input': '⌨️',
            'layout': '📐',
            'navigation': '🧭',
            'utility': '🛠️'
        }
        return icons.get(category_name, '📁')
        
    def _get_category_color(self, category_name: str):
        """カテゴリ色"""
        colors = {
            'animations': ft.Colors.PURPLE_600,
            'buttons': ft.Colors.BLUE_600,
            'charts': ft.Colors.GREEN_600,
            'colors': ft.Colors.ORANGE_600,
            'contrib': ft.Colors.PINK_600,
            'dialogs': ft.Colors.TEAL_600,
            'displays': ft.Colors.INDIGO_600,
            'input': ft.Colors.RED_600,
            'layout': ft.Colors.BROWN_600,
            'navigation': ft.Colors.CYAN_600,
            'utility': ft.Colors.GREY_600
        }
        return colors.get(category_name, ft.Colors.BLUE_600)
        
    def _get_category_display_name(self, category_name: str):
        """カテゴリ表示名"""
        mapping = {
            'animations': 'アニメーション',
            'buttons': 'ボタン',
            'charts': 'チャート',
            'colors': '色・テーマ',
            'contrib': 'コントリビューション',
            'dialogs': 'ダイアログ',
            'displays': '表示',
            'input': '入力',
            'layout': 'レイアウト',
            'navigation': 'ナビゲーション',
            'utility': 'ユーティリティ'
        }
        return mapping.get(category_name, category_name.title())
        
    def _load_example(self, relative_path: str):
        """公式サンプルを動的にロード"""
        try:
            full_path = self.examples_path / relative_path
            if not full_path.exists():
                return ft.Text("❌", size=10, color=ft.Colors.RED)
                
            spec = importlib.util.spec_from_file_location("example_module", full_path)
            if not spec or not spec.loader:
                return ft.Text("❌", size=10, color=ft.Colors.RED)
                
            module = importlib.util.module_from_spec(spec)
            sys.modules[f"example_module_{id(self)}_{hash(relative_path)}"] = module
            spec.loader.exec_module(module)
            
            if hasattr(module, 'example'):
                try:
                    result = module.example()
                    return result
                except Exception as e:
                    return ft.Text(f"❌", size=10, color=ft.Colors.ORANGE)
            else:
                return ft.Text("❌", size=10, color=ft.Colors.ORANGE)
                
        except Exception as e:
            return ft.Text("❌", size=10, color=ft.Colors.RED)
        
    def _open_docs(self, control_name: str):
        """ドキュメント開く"""
        base_url = "https://flet.dev/docs/controls/"
        url = f"{base_url}{control_name.lower()}"
        
        try:
            webbrowser.open(url)
            print(f"📖 {control_name}ドキュメント: {url}")
        except Exception as e:
            print(f"❌ ドキュメント開けず: {e}")


