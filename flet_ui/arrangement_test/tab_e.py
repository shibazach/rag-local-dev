"""
Tab E: Fletコントロールギャラリー（公式サンプル版）
@https://flet-controls-gallery.fly.dev/ にある実際のコントロールを公式サンプルで表示
"""
import sys
import os
import importlib.util
import flet as ft
import webbrowser
from pathlib import Path


class TabE:
    def __init__(self):
        self.examples_path = Path(__file__).parent / "examples"
        
    def create_content(self) -> ft.Control:
        """タブEのメイン表示"""
        return ft.Container(
            content=self._create_main_layout(),
            expand=True,
            padding=ft.padding.all(16)
        )
        
    def _create_main_layout(self):
        """メインレイアウト作成"""
        sections = [
            self._create_charts_section(),
            self._create_input_section(),
            self._create_dialogs_section(),
            self._create_layout_section(),
            self._create_buttons_section(),
        ]
        
        return ft.Column([
            ft.Text("🎨 Fletコントロールギャラリー（公式サンプル版）", 
                   size=24, weight=ft.FontWeight.BOLD),
            ft.Text("🔗 参照: https://flet-controls-gallery.fly.dev/", 
                   size=14, color=ft.Colors.GREY_600),
            ft.Text(f"📊 公式サンプル使用", 
                   size=12, color=ft.Colors.BLUE_600),
            ft.Divider(),
        ] + sections, scroll=ft.ScrollMode.AUTO, expand=True)
        
    def _create_charts_section(self):
        """チャートセクション"""
        controls = []
        
        # PieChart
        piechart = self._load_example("charts/piechart/01_piechart_1.py")
        if piechart:
            controls.append(("PieChart", piechart))
            
        # BarChart
        barchart = self._load_example("charts/barchart/01_barchart_1.py")
        if barchart:
            controls.append(("BarChart", barchart))
            
        # LineChart
        linechart = self._load_example("charts/linechart/01_linechart_1.py")
        if linechart:
            controls.append(("LineChart", linechart))
            
        return self._create_section("チャート", controls, "chart")
        
    def _create_input_section(self):
        """入力コントロールセクション"""
        controls = []
        
        # TextField
        textfield = self._load_example("input/textfield/01_basic_textfields.py")
        if textfield:
            controls.append(("TextField", textfield))
            
        # Dropdown
        dropdown = self._load_example("input/dropdown/01_basic_dropdown.py")
        if dropdown:
            controls.append(("Dropdown", dropdown))
            
        # Slider
        slider = self._load_example("input/slider/01_basic_sliders.py")
        if slider:
            controls.append(("Slider", slider))
            
        return self._create_section("入力コントロール", controls, "input")
        
    def _create_dialogs_section(self):
        """ダイアログセクション"""
        controls = []
        
        # TimePicker
        timepicker = self._load_example("dialogs/timepicker/01_time_picker_example.py")
        if timepicker:
            controls.append(("TimePicker", timepicker))
            
        # DatePicker
        datepicker = self._load_example("dialogs/datepicker/01_date_picker_example.py")
        if datepicker:
            controls.append(("DatePicker", datepicker))
            
        return self._create_section("ダイアログ", controls, "dialog")
        
    def _create_layout_section(self):
        """レイアウトセクション"""
        controls = []
        
        # Container
        container = self._load_example("layout/container/01_clickable_containers.py")
        if container:
            controls.append(("Container", container))
            
        # Row & Column
        row_col = self._load_example("layout/row/01_row_spacing.py")
        if row_col:
            controls.append(("Row", row_col))
            
        return self._create_section("レイアウト", controls, "layout")
        
    def _create_buttons_section(self):
        """ボタンセクション"""
        controls = []
        
        # ElevatedButton
        elevated_btn = self._load_example("buttons/elevatedbutton/01_basic_elevatedbuttons.py")
        if elevated_btn:
            controls.append(("ElevatedButton", elevated_btn))
            
        # TextButton
        text_btn = self._load_example("buttons/textbutton/01_basic_textbuttons.py") 
        if text_btn:
            controls.append(("TextButton", text_btn))
            
        return self._create_section("ボタン", controls, "button")
        
    def _load_example(self, relative_path: str):
        """公式サンプルを動的にロード"""
        try:
            full_path = self.examples_path / relative_path
            if not full_path.exists():
                print(f"❌ サンプルファイルが見つからない: {full_path}")
                return None
                
            spec = importlib.util.spec_from_file_location("example_module", full_path)
            if not spec or not spec.loader:
                print(f"❌ インポート仕様の作成に失敗: {full_path}")
                return None
                
            module = importlib.util.module_from_spec(spec)
            sys.modules["example_module"] = module
            spec.loader.exec_module(module)
            
            if hasattr(module, 'example'):
                return module.example()
            else:
                print(f"❌ example関数が見つからない: {full_path}")
                return None
                
        except Exception as e:
            print(f"❌ サンプルロードエラー {relative_path}: {e}")
            return ft.Text(f"読み込みエラー: {str(e)}", color=ft.Colors.RED)
    
    def _create_section(self, title: str, controls: list, section_id: str):
        """セクション作成"""
        if not controls:
            return ft.Container()
            
        section_controls = []
        for name, control in controls:
            if control:
                section_controls.append(
                    ft.Container(
                        content=ft.Column([
                            ft.Row([
                                ft.Text(name, weight=ft.FontWeight.BOLD, size=16),
                                ft.IconButton(
                                    icon=ft.Icons.OPEN_IN_NEW,
                                    tooltip="ドキュメント",
                                    on_click=lambda e, n=name.lower(): self._open_docs(n)
                                )
                            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                            ft.Container(
                                content=control,
                                border=ft.border.all(1, ft.Colors.GREY_300),
                                border_radius=8,
                                padding=16
                            )
                        ]),
                        margin=ft.margin.only(bottom=16)
                    )
                )
        
        return ft.Container(
            content=ft.Column([
                ft.Text(title, size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_700),
                ft.Divider(),
            ] + section_controls),
            margin=ft.margin.only(bottom=24)
        )
        
    def _open_docs(self, control_name: str):
        """ドキュメント開く"""
        docs_map = {
            "piechart": "https://flet.dev/docs/controls/piechart",
            "barchart": "https://flet.dev/docs/controls/barchart", 
            "linechart": "https://flet.dev/docs/controls/linechart",
            "textfield": "https://flet.dev/docs/controls/textfield",
            "dropdown": "https://flet.dev/docs/controls/dropdown",
            "slider": "https://flet.dev/docs/controls/slider",
            "timepicker": "https://flet.dev/docs/controls/timepicker",
            "datepicker": "https://flet.dev/docs/controls/datepicker",
            "container": "https://flet.dev/docs/controls/container",
            "row": "https://flet.dev/docs/controls/row",
            "elevatedbutton": "https://flet.dev/docs/controls/elevatedbutton",
            "textbutton": "https://flet.dev/docs/controls/textbutton"
        }
        
        url = docs_map.get(control_name.lower())
        if url:
            try:
                webbrowser.open(url)
                print(f"📖 {control_name}ドキュメント: {url}")
            except Exception as e:
                print(f"❌ ドキュメント開けず: {e}")
        else:
            fallback_url = "https://flet.dev/docs/controls/"
            try:
                webbrowser.open(fallback_url)
                print(f"📖 Fletコントロール一覧: {fallback_url}")
            except Exception as e:
                print(f"❌ ドキュメント開けず: {e}")
