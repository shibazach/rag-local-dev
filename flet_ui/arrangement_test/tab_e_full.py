"""
Tab E: 完全自動スキャン版Fletコントロールギャラリー（172サンプル全対応）
@https://flet-controls-gallery.fly.dev/ の完全再現
"""
import sys
import os
import importlib.util
import flet as ft
import webbrowser
from pathlib import Path


class TabEFull:
    def __init__(self):
        self.examples_path = Path(__file__).parent / "examples"
        self.all_samples = self._scan_all_samples()
        
    def create_content(self) -> ft.Control:
        """完全版ギャラリー表示（172サンプル全対応）"""
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
            
            # カテゴリ内の全サンプルをスキャン
            for control_dir in category_dir.iterdir():
                if not control_dir.is_dir():
                    continue
                    
                control_name = control_dir.name
                examples = []
                
                # コントロール内の全サンプルファイルをスキャン
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
        # 01_basic_buttons.py -> "Basic Buttons"
        name = filename
        if name.startswith(('01_', '02_', '03_', '04_', '05_', '06_', '07_', '08_', '09_')):
            name = name[3:]  # 番号プレフィックス削除
        name = name.replace('_', ' ').title()
        return name
        
    def _create_main_layout(self):
        """完全版メインレイアウト"""
        total_samples = sum(
            len(control['examples']) 
            for controls in self.all_samples.values() 
            for control in controls
        )
        
        sections = []
        for category_name, controls in sorted(self.all_samples.items()):
            if controls:
                section = self._create_category_section(category_name, controls)
                if section:
                    sections.append(section)
        
        return ft.Column([
            ft.Text("🎨 Fletコントロールギャラリー（完全自動スキャン版）", 
                   size=24, weight=ft.FontWeight.BOLD),
            ft.Text("🔗 参照: https://flet-controls-gallery.fly.dev/", 
                   size=14, color=ft.Colors.GREY_600),
            ft.Text(f"📊 全サンプル数: {total_samples} / 172サンプル", 
                   size=12, color=ft.Colors.BLUE_600),
            ft.Text(f"📁 カテゴリ数: {len(self.all_samples)}", 
                   size=12, color=ft.Colors.GREEN_600),
            ft.Divider(),
        ] + sections, scroll=ft.ScrollMode.AUTO, expand=True)
        
    def _create_category_section(self, category_name: str, controls: list):
        """カテゴリセクション作成"""
        if not controls:
            return None
            
        category_display_name = self._get_category_display_name(category_name)
        control_sections = []
        total_examples = 0
        
        for control_info in controls:
            control_name = control_info['control']
            examples = control_info['examples']
            total_examples += len(examples)
            
            control_section = self._create_control_section(control_name, examples)
            if control_section:
                control_sections.append(control_section)
        
        # コントロールセクションをグリッド表示用に再配置
        grid_rows = []
        controls_per_row = 2  # 1行に2つのコントロール
        
        for i in range(0, len(control_sections), controls_per_row):
            row_controls = control_sections[i:i + controls_per_row]
            if row_controls:
                grid_rows.append(
                    ft.Row(
                        row_controls,
                        spacing=16,
                        wrap=True,
                        scroll=ft.ScrollMode.AUTO
                    )
                )
        
        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Text(f"📂 {category_display_name}", 
                           size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_700),
                    ft.Text(f"{len(controls)}コントロール, {total_examples}サンプル", 
                           size=12, color=ft.Colors.GREY_600)
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Divider(),
            ] + grid_rows),
            margin=ft.margin.only(bottom=24)
        )
        
    def _create_control_section(self, control_name: str, examples: list):
        """コントロールセクション作成"""
        if not examples:
            return None
            
        example_widgets = []
        for example in examples[:2]:  # 最初の2つのサンプルを表示（横並び用）
            widget = self._load_example(example['path'])
            if widget:
                example_widgets.append(
                    ft.Container(
                        content=ft.Column([
                            ft.Text(example['display_name'], 
                                   size=11, weight=ft.FontWeight.W_500),
                            ft.Container(
                                content=widget,
                                border=ft.border.all(1, ft.Colors.GREY_300),
                                border_radius=6,
                                padding=6,
                                width=200,  # 横並び用固定幅
                                height=120  # 横並び用固定高さ
                            )
                        ]),
                        width=220,
                        margin=ft.margin.only(right=12, bottom=8)
                    )
                )
        
        if not example_widgets:
            return None
            
        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Text(control_name.title(), 
                           weight=ft.FontWeight.BOLD, size=14),
                    ft.Text(f"{len(examples)}例", 
                           size=10, color=ft.Colors.GREY_500),
                    ft.IconButton(
                        icon=ft.Icons.OPEN_IN_NEW,
                        tooltip="ドキュメント",
                        on_click=lambda e, n=control_name.lower(): self._open_docs(n),
                        scale=0.6
                    )
                ], alignment=ft.MainAxisAlignment.START),
                ft.Row(
                    example_widgets,  # 横に並べて表示
                    wrap=True,
                    spacing=6,
                    scroll=ft.ScrollMode.AUTO  # 横スクロール可能
                )
            ], spacing=4),
            width=480,  # 固定幅でグリッド表示
            margin=ft.margin.only(bottom=12),
            border=ft.border.all(1, ft.Colors.GREY_200),
            border_radius=8,
            padding=12
        )
        
    def _get_category_display_name(self, category_name: str):
        """カテゴリ表示名マッピング"""
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
                return ft.Text("❌ ファイル未検出", size=10, color=ft.Colors.RED)
                
            spec = importlib.util.spec_from_file_location("example_module", full_path)
            if not spec or not spec.loader:
                return ft.Text("❌ インポート失敗", size=10, color=ft.Colors.RED)
                
            module = importlib.util.module_from_spec(spec)
            sys.modules[f"example_module_{id(self)}"] = module
            spec.loader.exec_module(module)
            
            if hasattr(module, 'example'):
                try:
                    result = module.example()
                    return result
                except Exception as e:
                    return ft.Text(f"❌ 実行エラー: {str(e)[:50]}...", 
                                 size=9, color=ft.Colors.ORANGE)
            else:
                return ft.Text("❌ example()未定義", size=10, color=ft.Colors.ORANGE)
                
        except Exception as e:
            return ft.Text(f"❌ ロードエラー: {str(e)[:30]}...", 
                         size=9, color=ft.Colors.RED)
        
    def _open_docs(self, control_name: str):
        """ドキュメント開く"""
        base_url = "https://flet.dev/docs/controls/"
        url = f"{base_url}{control_name.lower()}"
        
        try:
            webbrowser.open(url)
            print(f"📖 {control_name}ドキュメント: {url}")
        except Exception as e:
            print(f"❌ ドキュメント開けず: {e}")
            # フォールバック
            try:
                webbrowser.open(base_url)
                print(f"📖 Fletコントロール一覧: {base_url}")
            except:
                pass
