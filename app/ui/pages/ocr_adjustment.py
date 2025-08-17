"""
OCR調整ページ - new/系準拠実装（4ペイン構成）
"""
from nicegui import ui
from datetime import datetime
from pathlib import Path
import json
import os
import tempfile
import base64

from app.ui.components.layout import RAGHeader, RAGFooter, MainContentArea
from app.ui.components.elements import CommonPanel
from app.ui.components.common.layout import CommonSplitter
from app.ui.components.base.button import BaseButton

from app.core.db_simple import get_file_list, get_file_with_blob
from app.services.file_service import get_file_service

# OCRエンジン
from new.services.ocr.factory import OCREngineFactory


class OCRAdjustmentPage:
    """OCR調整ページクラス - new/系準拠4ペイン構成"""
    
    def __init__(self):
        """初期化"""
        # ファイル関連
        self.selected_file = None  # blob_id
        self.selected_filename = None
        self.pdf_page_count = 0

        # OCR関連
        self.selected_engine = None  # engine_id ('ocrmypdf' 等)
        self.selected_engine_label = None
        self.selected_page = 1
        self.use_correction = True
        self.ocr_results = []
        self.engine_parameters = {}
        self.engine_param_controls = {}
        self._select_value_maps = {}

        # エンジン選択肢（表示名 -> id）
        self.engine_name_to_id = {
            'OCRMyPDF': 'ocrmypdf',
            'Tesseract': 'tesseract',
            'PaddleOCR': 'paddleocr',
            'EasyOCR': 'easyocr',
        }
        self.engine_id_to_name = {v: k for k, v in self.engine_name_to_id.items()}
        self.available_engine_options = {}  # {engine_id: label}

        # UI参照
        self.file_info_label = None
        self.engine_select = None
        self.page_input = None
        self.correction_checkbox = None
        self.engine_details_container = None
        self.results_container = None
        self.pdf_iframe = None

        # 設定保存先
        self.config_root = Path('app/config/ocr')
        self.dict_root = self.config_root / 'dic'
    
    def render(self):
        """ページレンダリング"""
        from app.utils.auth import SimpleAuth
        
        if not SimpleAuth.is_authenticated():
            ui.navigate.to('/login')
            return
        
        # エンジン一覧の準備
        self._prepare_engine_options()

        # 共通ヘッダー
        RAGHeader(show_site_name=True, current_page="ocr-adjustment")
        
        # 全ページ共通メインコンテンツエリア
        with MainContentArea():
            # 共通スプリッタースタイル・JS追加
            CommonSplitter.add_splitter_styles()
            CommonSplitter.add_splitter_javascript()
            
            self._create_main_layout()
        
        # 共通フッター
        RAGFooter()
    
    def _prepare_engine_options(self):
        """OCRエンジン選択肢を準備"""
        try:
            factory = OCREngineFactory()
            available = factory.get_available_engines()
            options = {}
            for engine_id, info in available.items():
                label = info.get('name', self.engine_id_to_name.get(engine_id, engine_id))
                options[engine_id] = label
            # ラベルでソートした順序の辞書を生成
            self.available_engine_options = dict(sorted(options.items(), key=lambda kv: kv[1]))
        except Exception:
            # フォールバック
            self.available_engine_options = {eid: name for name, eid in self.engine_name_to_id.items()}

    def _create_main_layout(self):
        """メインレイアウト作成（4ペイン構成）"""
        with ui.element('div').style(
            'width: 100%; height: 100%; '
            'display: flex; margin: 0; padding: 4px; gap: 4px;'
        ).props('id="ocr-main-container"'):
            
            # 左ペイン：OCR設定・結果（50%幅）
            with ui.element('div').style(
                'width: 50%; height: 100%; '
                'display: flex; flex-direction: column; '
                'margin: 0; padding: 0; gap: 4px;'
            ).props('id="ocr-left-pane"'):
                self._create_ocr_settings_pane()
                CommonSplitter.create_horizontal(splitter_id="ocr-hsplitter", height="4px")
                self._create_ocr_results_pane()
            
            # 縦スプリッター
            CommonSplitter.create_vertical(splitter_id="ocr-vsplitter", width="4px")
            
            # 右ペイン：詳細設定・PDF（50%幅）
            with ui.element('div').style(
                'width: 50%; height: 100%; '
                'display: flex; flex-direction: column; '
                'margin: 0; padding: 0; gap: 4px;'
            ).props('id="ocr-right-pane"'):
                self._create_engine_details_pane()
                CommonSplitter.create_horizontal(splitter_id="ocr-hsplitter-right", height="4px")
                self._create_pdf_preview_pane()
    
    def _create_ocr_settings_pane(self):
        """左上: OCR設定ペイン"""
        with CommonPanel(
            title="⚙️ OCR設定",
            gradient="#334155",
            header_color="white",
            width="100%",
            height="50%"
        ) as panel:
            
            # ヘッダーにボタン配置
            with panel.header_element:
                with ui.element('div').style('display: flex; gap: 6px; margin-right: 8px;'):
                    BaseButton.create_type_a("📁 ファイル選択", on_click=self._open_file_dialog)
                    BaseButton.create_type_a("🚀 OCR実行", on_click=self._start_ocr)
            
            # パネル内容
            panel.content_element.style('padding: 0; height: 100%;')
            
            with panel.content_element:
                with ui.element('div').style('padding: 4px; height: 100%; box-sizing: border-box;'):
                    with ui.element('div').style('display: flex; flex-direction: column; gap: 10px; height: 100%;'):
                        
                        # 選択ファイル情報
                        with ui.element('div').style('background: #f3f4f6; padding: 6px; border-radius: 4px;'):
                            with ui.element('div').style('display: flex; align-items: center; gap: 8px;'):
                                ui.label('ファイル:').style('font-weight: 600; min-width: 60px; font-size: 12px;')
                                self.file_info_label = ui.label('未選択').style('color: #6b7280; font-size: 12px;')
                        
                        # OCRエンジン選択
                        with ui.element('div').style('display: flex; align-items: center; gap: 8px;'):
                            ui.label('🔧 OCRエンジン').style('min-width: 100px; font-weight: 500; font-size: 13px;')
                            self.engine_select = ui.select(
                                options=self.available_engine_options,
                                with_input=False,
                                on_change=self._on_engine_change
                            ).style('flex: 1;').props('outlined dense')
                        
                        # ページ設定と誤字修正（横並び）
                        with ui.element('div').style('display: flex; align-items: center; gap: 16px;'):
                            # ページ設定
                            with ui.element('div').style('display: flex; align-items: center; gap: 6px;'):
                                ui.label('📄 処理ページ').style('font-weight: 500; font-size: 13px;')
                                self.page_input = ui.number(
                                    value=self.selected_page,
                                    min=0,
                                    step=1,
                                    on_change=self._on_page_change
                                ).style('width: 80px;').props('outlined dense')
                                ui.label('0=全て').style('font-size: 11px; color: #6b7280;')
                            
                            # 誤字修正チェックボックス
                            with ui.element('div').style('display: flex; align-items: center; gap: 6px;'):
                                self.correction_checkbox = ui.checkbox(
                                    '🔤 誤字修正',
                                    value=self.use_correction,
                                    on_change=self._on_correction_change
                                ).style('font-size: 13px;')
    
                        # 区切り線
                        ui.element('div').style('height: 1px; background: #e5e7eb; width: 100%;')

                        # 辞書編集ボタン群
                        with ui.element('div').style('display: flex; flex-wrap: wrap; gap: 6px;'):
                            for label, filename in self._get_dict_buttons():
                                BaseButton.create_type_b(f"✏️ {label}", on_click=lambda f=filename, l=label: self._open_dict_editor(l, f))

    def _create_engine_details_pane(self):
        """右上: エンジン詳細設定ペイン"""
        with CommonPanel(
            title="🔧 詳細設定",
            gradient="#334155",
            header_color="white",
            width="100%",
            height="50%"
        ) as panel:
            
            # ヘッダーにボタンを追加
            with panel.header_element:
                with ui.element('div').style('display: flex; gap: 6px; margin-right: 8px;'):
                    BaseButton.create_type_b('📂 読込', on_click=self._load_settings)
                    BaseButton.create_type_a('💾 保存', on_click=self._save_settings)
            
            # パネル内容
            panel.content_element.style('padding: 0; height: 100%;')
            
            with panel.content_element:
                self.engine_details_container = ui.element('div').style('padding: 4px; height: 100%; box-sizing: border-box; overflow-y: auto;')
                
                with self.engine_details_container:
                    # 初期状態：空の説明
                    with ui.element('div').style(
                        'height: 100%; display: flex; align-items: center; justify-content: center; '
                        'color: #9ca3af; text-align: center;'
                    ):
                        with ui.element('div'):
                            ui.icon('settings', size='3em').style('margin-bottom: 12px; opacity: 0.5;')
                            ui.label('OCRエンジンを選択すると').style('font-size: 14px; margin-bottom: 2px;')
                            ui.label('詳細設定が表示されます').style('font-size: 14px;')
    
    def _create_ocr_results_pane(self):
        """左下: OCR結果ペイン"""
        with CommonPanel(
            title="📋 OCR結果",
            gradient="#334155",
            header_color="white",
            width="100%",
            height="50%"
        ) as panel:
            
            # ヘッダーにボタン配置
            with panel.header_element:
                with ui.element('div').style('display: flex; gap: 6px; margin-right: 8px;'):
                    BaseButton.create_type_b("🗑️ クリア", on_click=self._clear_results)
                    BaseButton.create_type_a("📄 エクスポート", on_click=self._export_results)
            
            # パネル内容
            panel.content_element.style('padding: 0; height: 100%;')
            
            with panel.content_element:
                with ui.element('div').style('padding: 4px; height: 100%; box-sizing: border-box;'):
                    self.results_container = ui.element('div').style('height: 100%; overflow-y: auto;')
                    
                    with self.results_container:
                        with ui.element('div').style('height: 100%; display: flex; align-items: center; justify-content: center; color: #9ca3af; text-align: center;'):
                            with ui.element('div'):
                                ui.icon('text_snippet', size='3em').style('margin-bottom: 12px; opacity: 0.5;')
                                ui.label('OCR実行すると').style('font-size: 14px; margin-bottom: 2px;')
                                ui.label('結果がここに表示されます').style('font-size: 14px;')
    
    def _create_pdf_preview_pane(self):
        """右下: PDFプレビューペイン"""
        with ui.element('div').style(
            'width: 100%; height: 50%; background: white; border-radius: 12px; '
            'box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15); border: 1px solid #e5e7eb; '
            'display: flex; flex-direction: column; overflow: hidden;'
        ):
            with ui.element('div').style('flex: 1; background: #f3f4f6;'):
                # iframeを用意（/api/files/{id}/preview#page=N を使用）
                self.pdf_iframe = ui.element('iframe').style(
                    'width: 100%; height: 100%; border: none; display: none;'
                ).props('id="ocr-pdf-frame"')

                # プレースホルダー
                with ui.element('div').style('width: 100%; height: 100%; display: flex; align-items: center; justify-content: center; color: #6b7280;').props('id="ocr-pdf-placeholder"'):
                    with ui.element('div').style('text-align: center;'):
                        ui.icon('picture_as_pdf', size='48px').style('margin-bottom: 8px;')
                        ui.label('PDFプレビュー').style('font-size: 14px; font-weight: 500; margin-bottom: 4px;')
                        ui.label('ファイルを選択してください').style('font-size: 12px;')

    # ========= イベント/動作 =========
    def _on_engine_change(self, e):
        self.selected_engine = e.value
        self.selected_engine_label = self.engine_id_to_name.get(self.selected_engine, self.selected_engine)
        self._render_engine_parameters()

    def _on_page_change(self, e):
        # 0は全ページ扱い。プレビュー移動は1ページ目へ
        try:
            page = int(e.value)
        except Exception:
            page = 1
        self.selected_page = page
        if self.selected_file:
            move_to = 1 if page == 0 else max(1, page)
            self._update_pdf_preview_page(move_to)

    def _on_correction_change(self, e):
        self.use_correction = bool(e.value)

    # ========= OCR実行 =========
    def _start_ocr(self):
        if not self.selected_file:
            ui.notify('ファイルを選択してください', type='warning')
            return
        if not self.selected_engine:
            ui.notify('OCRエンジンを選択してください', type='warning')
            return
        
        ui.notify(f'OCR実行: {self.selected_engine_label}')

        try:
            # 一時ファイルへPDFを書き出し
            file_info = get_file_with_blob(self.selected_file)
            if not file_info or not file_info.get('blob_data'):
                ui.notify('ファイルデータ取得に失敗しました', type='negative')
                return

            blob_data = file_info['blob_data']
            if isinstance(blob_data, memoryview):
                blob_data = blob_data.tobytes()

            # PDFを一時保存
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
                tmp.write(blob_data)
                temp_pdf_path = tmp.name

            # エンジンファクトリ
            factory = OCREngineFactory()

            # パラメータ収集
            params = self._collect_engine_parameters()

            # ページ番号: 0は全ページ
            target_pages = []
            if self.selected_page == 0:
                # すべてのページ
                page_count = self._compute_pdf_page_count_from_bytes(blob_data)
                target_pages = list(range(1, max(1, page_count) + 1))
            else:
                target_pages = [max(1, int(self.selected_page))]

            results = []
            for page_no in target_pages:
                # 各エンジンごとに入力を調整
                input_path = temp_pdf_path
                cleanup_paths = []

                try:
                    if self.selected_engine in ('tesseract', 'easyocr', 'paddleocr'):
                        # 画像ベース: 指定ページを画像にして渡す（0=全ページは上で分解）
                        img_path = self._export_pdf_page_to_image(temp_pdf_path, page_no)
                        input_path = img_path
                        cleanup_paths.append(img_path)
                    elif self.selected_engine == 'ocrmypdf' and self.selected_page != 0:
                        # 単一ページPDFに抽出
                        single_pdf = self._export_single_page_pdf(temp_pdf_path, page_no)
                        input_path = single_pdf
                        cleanup_paths.append(single_pdf)

                    # 実行
                    result = factory.process_file(input_path, self.selected_engine, **params)
                    text = result.text if getattr(result, 'success', False) else ''

                    # 誤字修正
                    if self.use_correction and text:
                        try:
                            corrected = self._apply_correction(text)
                            text = corrected
                        except Exception:
                            pass

                    results.append({
                        'page': page_no,
                        'text': text,
                        'confidence': getattr(result, 'confidence', None) or 0.0,
                        'processing_time': getattr(result, 'processing_time', 0.0),
                    })
                finally:
                    for p in cleanup_paths:
                        try:
                            Path(p).unlink(missing_ok=True)
                        except Exception:
                            pass

            # 保存/表示
            self.ocr_results = results
            self._display_ocr_results()
        
        except Exception as e:
            ui.notify(f'OCR失敗: {e}', type='negative')

    # ========= 詳細設定UI =========
    def _render_engine_parameters(self):
        if not self.engine_details_container:
            return
        self.engine_details_container.clear()

        # パラメータ定義取得
        params_def = []
        try:
            factory = OCREngineFactory()
            engine = factory.create_engine(self.selected_engine) if self.selected_engine else None
            params_def = engine.get_parameters() if engine else []
        except Exception:
            params_def = []

        self.engine_param_controls = {}
        self.engine_parameters = {}

        with self.engine_details_container:
            if not params_def:
                ui.label('このエンジンに設定項目はありません').style('font-size: 12px; color: #6b7280;')
                return

            # 行ごとに「項目名：コントロール　簡易説明」
            for p in params_def:
                name = p.get('name')
                label = p.get('label', name)
                ptype = (p.get('type') or '').lower()
                default = p.get('default')
                desc = p.get('description', '')
                options = p.get('options', [])

                with ui.element('div').style('display: flex; align-items: center; gap: 10px; padding: 2px 0;'):
                    ui.label(f"{label}：").style('min-width: 160px; font-size: 12px;')

                    ctrl = None
                    if ptype in ('select',):
                        # options: list[dict] or list[primitive] → dict[encoded]=label, and map back to original
                        sel_opts_map_encoded = {}
                        value_map = {}
                        for opt in (options or []):
                            if isinstance(opt, dict):
                                val = opt.get('value')
                                lab = opt.get('label', val)
                            else:
                                val = opt
                                lab = opt
                            # エンコード（list/dictはJSON化、それ以外はstr）
                            try:
                                if isinstance(val, (list, dict)):
                                    enc = json.dumps(val, ensure_ascii=False)
                                else:
                                    enc = str(val)
                            except Exception:
                                enc = str(val)
                            sel_opts_map_encoded[enc] = str(lab)
                            value_map[enc] = val

                        # デフォルト値のエンコード
                        try:
                            if isinstance(default, (list, dict)):
                                default_enc = json.dumps(default, ensure_ascii=False)
                            else:
                                default_enc = str(default)
                        except Exception:
                            default_enc = str(default)

                        # UI作成
                        ctrl = ui.select(options=sel_opts_map_encoded, value=default_enc if default_enc in sel_opts_map_encoded else None).props('outlined dense').style('min-width: 220px;')
                        # 値の同期（エンコード→オリジナルへ復元）
                        def _on_select_change(ev, param_name=name, vmap=value_map):
                            self.engine_parameters[param_name] = vmap.get(ev.value, ev.value)
                        ctrl.on('update:model-value', _on_select_change)
                        # 初期値を格納
                        self.engine_parameters[name] = value_map.get(default_enc, default)
                        # マップ保持（必要時のデバッグ用）
                        self._select_value_maps[name] = value_map
                    elif ptype in ('number',):
                        ctrl = ui.number(value=default, step=p.get('step', 1)).props('outlined dense').style('width: 120px;')
                        def _on_num_change(ev, param_name=name):
                            try:
                                new_val = float(ev.args) if hasattr(ev, 'args') else float(ev.value)
                            except Exception:
                                new_val = default
                            self.engine_parameters[param_name] = new_val
                        ctrl.on('update:model-value', _on_num_change)
                        self.engine_parameters[name] = default
                    elif ptype in ('checkbox', 'boolean'):
                        ctrl = ui.checkbox('', value=bool(default))
                        def _on_bool_change(ev, param_name=name):
                            val = getattr(ev, 'value', None)
                            if val is None and hasattr(ev, 'args'):
                                val = bool(ev.args)
                            self.engine_parameters[param_name] = bool(val)
                        ctrl.on('update:model-value', _on_bool_change)
                        self.engine_parameters[name] = bool(default)
                    else:
                        # フォールバック: テキスト
                        ctrl = ui.input(value=str(default) if default is not None else '').props('outlined dense').style('min-width: 220px;')
                        def _on_text_change(ev, param_name=name):
                            self.engine_parameters[param_name] = getattr(ev, 'value', None) or getattr(ev, 'args', '')
                        ctrl.on('update:model-value', _on_text_change)
                        self.engine_parameters[name] = str(default) if default is not None else ''

                    # 説明
                    ui.label(desc or '').style('font-size: 11px; color: #6b7280;')
                    self.engine_param_controls[name] = ctrl

    def _collect_engine_parameters(self):
        # エンジンパラメータは self.engine_parameters に最新値が保持されている
        return dict(self.engine_parameters)

    # ========= 保存/読込 =========
    def _save_settings(self):
        if not self.selected_engine:
            ui.notify('先にOCRエンジンを選択してください', type='warning')
            return

        # 提案ファイル名: YYYYMMDD_HHMMSS_Engine.json
        engine_folder = self.engine_id_to_name.get(self.selected_engine, self.selected_engine)
        suggested = datetime.now().strftime('%Y%m%d_%H%M%S') + f"_{engine_folder}.json"
        target_dir = self.config_root / engine_folder
        target_dir.mkdir(parents=True, exist_ok=True)

        def do_save(dialog, filename_ctrl):
            name = (filename_ctrl.value or suggested).strip()
            if not name.endswith('.json'):
                name += '.json'
            path = target_dir / name
            payload = {
                'engine': self.selected_engine,
                'engine_label': self.engine_id_to_name.get(self.selected_engine, self.selected_engine),
                'page': self.selected_page,
            'use_correction': self.use_correction,
                'parameters': self._collect_engine_parameters(),
            }
            try:
                with open(path, 'w', encoding='utf-8') as f:
                    json.dump(payload, f, ensure_ascii=False, indent=2)
                ui.notify(f'保存しました: {path}', type='positive')
            except Exception as e:
                ui.notify(f'保存失敗: {e}', type='negative')
            finally:
                dialog.close()

        with ui.dialog() as dialog, ui.card():
            ui.label('設定の保存').style('font-size: 14px; font-weight: 600;')
            filename_ctrl = ui.input(label='ファイル名', value=suggested).props('outlined dense').style('width: 360px;')
            with ui.row():
                ui.button('保存', on_click=lambda d=dialog, f=filename_ctrl: do_save(d, f))
                ui.button('キャンセル', on_click=dialog.close)
        dialog.open()
    
    def _load_settings(self):
        if not self.selected_engine:
            ui.notify('先にOCRエンジンを選択してください', type='warning')
            return

        engine_folder = self.engine_id_to_name.get(self.selected_engine, self.selected_engine)
        target_dir = self.config_root / engine_folder
        target_dir.mkdir(parents=True, exist_ok=True)
        files = sorted([p for p in target_dir.glob('*.json')], key=lambda p: p.name)
        if not files:
            ui.notify('保存済み設定がありません', type='warning')
            return
        
        def apply_selected(dialog, select_ctrl):
            path = Path(select_ctrl.value)
            try:
                data = json.loads(Path(path).read_text(encoding='utf-8'))
                # 反映
                self.selected_page = int(data.get('page', 1))
                if self.page_input:
                    self.page_input.value = self.selected_page
                self.use_correction = bool(data.get('use_correction', True))
                if self.correction_checkbox:
                    self.correction_checkbox.value = self.use_correction
                params = data.get('parameters', {})
                for k, v in params.items():
                    if k in self.engine_param_controls:
                        self.engine_param_controls[k].value = v
                ui.notify('設定を読み込みました', type='positive')
            except Exception as e:
                ui.notify(f'読込失敗: {e}', type='negative')
            finally:
                dialog.close()

        with ui.dialog() as dialog, ui.card():
            ui.label('設定の読込').style('font-size: 14px; font-weight: 600;')
            options_map = {str(p): p.name for p in files}
            select_ctrl = ui.select(options=options_map, value=str(files[0])).style('width: 360px;').props('outlined dense')
            with ui.row():
                ui.button('読込', on_click=lambda d=dialog, s=select_ctrl: apply_selected(d, s))
                ui.button('キャンセル', on_click=dialog.close)
        dialog.open()

    # ========= ファイル選択/プレビュー =========
    def _open_file_dialog(self):
        # DBからPDFファイル一覧を取得
        result = get_file_list(limit=1000, offset=0)
        if not result or 'files' not in result:
            ui.notify('ファイルが見つかりません', type='warning')
            return
        
        src_files = [f for f in result['files'] if f.get('content_type') == 'application/pdf']
        if not src_files:
            ui.notify('PDFファイルが見つかりません', type='warning')
            return
        
        # 行データを構築（files.py準拠）
        rows_all = []
        for f in src_files:
            status_value = f.get('status', 'pending')
            if status_value == 'processed':
                status = '処理完了'
            elif status_value == 'processing':
                status = '処理中'
            else:
                status = '未処理'

            size = f.get('file_size', 0)
            if size < 1024:
                size_str = f"{size}B"
            elif size < 1024 * 1024:
                size_str = f"{size / 1024:.1f}KB"
            elif size < 1024 * 1024 * 1024:
                size_str = f"{size / 1024 / 1024:.1f}MB"
            else:
                size_str = f"{size / 1024 / 1024 / 1024:.1f}GB"

            rows_all.append({
                'file_id': f.get('file_id'),
                'filename': f.get('filename', '不明'),
                'size': size_str,
                'status': status,
                'created_at': f.get('created_at', '').split('T')[0] if f.get('created_at') else '',
            })

        # 各行にID付与
        for idx, row in enumerate(rows_all):
            row['id'] = idx

        # 状態をクロージャで保持
        selection = {'file_id': None, 'filename': None}
        filtered_rows = rows_all.copy()

        # フィルタ関数
        def apply_filters(table_ref, status_val, query_text):
            q = (query_text or '').lower()
            rows = []
            for r in rows_all:
                if status_val != '全て' and r['status'] != status_val:
                    continue
                if q and q not in r['filename'].lower():
                    continue
                rows.append(r)
            for idx, r in enumerate(rows):
                r['id'] = idx
            table_ref.rows[:] = rows
            table_ref.update()

        # 大きめのダイアログ
        with ui.dialog() as dialog:
            with ui.card().style('width: 92vw; height: 85vh; margin: 0; display: flex; flex-direction: column; overflow: hidden;'):
                # ヘッダー
                with ui.element('div').style('display: flex; align-items: center; justify-content: space-between; padding: 8px 12px; border-bottom: 1px solid #e5e7eb;'):
                    ui.label('📁 PDFファイル選択').style('font-size: 16px; font-weight: 600;')
                    ui.button(icon='close', on_click=dialog.close).props('flat round')

                # フィルタ行
                with ui.element('div').style('display: flex; gap: 8px; align-items: center; padding: 8px 12px;'):
                    status_select = ui.select(options=['全て', '処理完了', '処理中', '未処理'], value='全て').props('outlined dense').style('width: 140px;')
                    search_input = ui.input(placeholder='ファイル名で検索...').props('outlined dense').style('flex: 1;')
                    selected_label = ui.label('未選択').style('color: #6b7280;')

                # テーブル
                columns = [
                    {'name': 'filename', 'label': 'ファイル名', 'field': 'filename', 'sortable': True, 'align': 'left'},
                    {'name': 'size', 'label': 'サイズ', 'field': 'size', 'sortable': True, 'align': 'right'},
                    {'name': 'status', 'label': 'ステータス', 'field': 'status', 'sortable': True, 'align': 'center'},
                    {'name': 'created_at', 'label': '作成日', 'field': 'created_at', 'sortable': True, 'align': 'center'},
                ]

                # メインコンテンツ（左: テーブル / 右: プレビュー）
                with ui.element('div').style('flex: 1; min-height: 0; overflow: hidden; display: flex; gap: 8px; padding: 0 12px 8px;'):
                    # 左（テーブル）
                    with ui.element('div').style('flex: 3; min-width: 0; display: flex; flex-direction: column; min-height: 0;'):
                        table_ref = ui.table(
                            columns=columns,
                            rows=filtered_rows,
                            row_key='id',
                            selection='single',
                            pagination=20
                        ).classes('w-full').style('flex: 1; height: 100%;')\
                            .props('dense flat virtual-scroll :virtual-scroll-sticky-size-start="48"')
                    # 右（PDFプレビュー）
                    with ui.element('div').style('flex: 2; min-width: 0; display: flex; flex-direction: column; min-height: 0; border: 1px solid #e5e7eb; border-radius: 6px; overflow: hidden; background: #f3f4f6;'):
                        with ui.element('div').style('padding: 8px 10px; background: white; border-bottom: 1px solid #e5e7eb;'):
                            ui.label('📄 プレビュー').style('font-size: 13px; font-weight: 600;')
                        with ui.element('div').style('flex: 1; min-height: 0; position: relative;'):
                            with ui.element('div').props('id="file-select-preview-placeholder"').style('position: absolute; inset: 0; display: flex; align-items: center; justify-content: center; color: #6b7280;'):
                                ui.label('行を選択するとプレビューが表示されます')
                            ui.element('iframe').props('id="file-select-preview-frame"')\
                                .style('position: absolute; inset: 0; width: 100%; height: 100%; border: none; background: white; display: none;')

                # イベント
                def on_selection(e):
                    # NiceGUIのselectionイベントは配列または辞書で届くことがある
                    sel_rows = []
                    if isinstance(e.args, list):
                        sel_rows = e.args
                    elif isinstance(e.args, dict):
                        sel_rows = e.args.get('selection') or []
                    # フォールバック: テーブルの現在の選択
                    try:
                        if (not sel_rows) and getattr(table_ref, 'selected', None):
                            sel_rows = table_ref.selected
                    except Exception:
                        pass
                    if sel_rows and isinstance(sel_rows[0], dict):
                        row = sel_rows[0]
                        fid = row.get('file_id')
                        fname = row.get('filename')
                        if fid:
                            selection['file_id'] = fid
                            selection['filename'] = fname or ''
                            selected_label.text = f"選択中: {selection['filename']}"
                            self._update_dialog_preview(fid)
                            return
                    # 未選択処理
                    selection['file_id'] = None
                    selection['filename'] = None
                    selected_label.text = '未選択'
                    self._update_dialog_preview(None)

                table_ref.on('selection', on_selection)

                def on_row_dblclick(e):
                    if e.args and len(e.args) > 0:
                        row = e.args[0]
                        fid = row.get('file_id')
                        fname = row.get('filename')
                        if fid:
                            self._update_dialog_preview(fid)
                            self._select_file(fid, fname)
                            dialog.close()

                table_ref.on('row-dblclick', on_row_dblclick)

                # 行クリックでも選択確定用データを更新
                def on_row_click(e):
                    if e.args and len(e.args) > 0 and isinstance(e.args[0], dict):
                        row = e.args[0]
                        fid = row.get('file_id')
                        fname = row.get('filename')
                        if fid:
                            selection['file_id'] = fid
                            selection['filename'] = fname or ''
                            selected_label.text = f"選択中: {selection['filename']}"
                            self._update_dialog_preview(fid)
                table_ref.on('row-click', on_row_click)

                def on_filter_change(_=None):
                    apply_filters(table_ref, status_select.value, search_input.value)

                status_select.on('update:model-value', lambda e: on_filter_change())
                search_input.on('update:model-value', lambda e: on_filter_change())

                # フッター
                def confirm_select():
                    # まず現在のテーブル選択から取得
                    chosen_id = selection.get('file_id')
                    chosen_name = selection.get('filename')
                    try:
                        sel_rows = getattr(table_ref, 'selected', None)
                        if sel_rows and len(sel_rows) > 0 and isinstance(sel_rows[0], dict):
                            chosen_id = sel_rows[0].get('file_id') or chosen_id
                            chosen_name = sel_rows[0].get('filename') or chosen_name
                    except Exception:
                        pass
                    if chosen_id:
                        self._select_file(chosen_id, chosen_name)
                        dialog.close()
                    else:
                        ui.notify('ファイルを選択してください', type='warning')

                with ui.element('div').style('display: flex; justify-content: flex-end; gap: 8px; padding: 8px 12px; border-top: 1px solid #e5e7eb;'):
                    ui.button('選択', on_click=confirm_select).props('unelevated')
                    ui.button('キャンセル', on_click=dialog.close).props('flat')
        
        dialog.open()
    
    def _select_file(self, file_id: str, file_name: str = None):
        self.selected_file = file_id
        self.selected_filename = file_name or file_id
        if self.file_info_label:
            self.file_info_label.text = self.selected_filename

        # PDFプレビューを表示
        self._show_pdf_preview(1)

        # ページ数を計算してスピンのmaxを設定
        try:
            info = get_file_with_blob(file_id)
            blob = info.get('blob_data') if info else None
            if isinstance(blob, memoryview):
                blob = blob.tobytes()
            self.pdf_page_count = self._compute_pdf_page_count_from_bytes(blob or b'')
            # PDF検知フォールバック
            if self.pdf_page_count == 0 and info and info.get('content_type') == 'application/pdf':
                self.pdf_page_count = 1
        except Exception:
            self.pdf_page_count = 1

        # ページ最大値（0=全ページ, 1..max=個別）
        try:
            if self.page_input and self.pdf_page_count:
                # NiceGUIのnumber.maxは数値を期待するため明示的に数値を渡す
                self.page_input.props(f'max={int(self.pdf_page_count)}')
        except Exception:
            pass
        ui.notify(f'ページ数: {self.pdf_page_count}（0=全ページ）', type='info')

    def _show_pdf_preview(self, page: int = 1):
        if not self.selected_file:
            return
        page = max(1, int(page))
        url = f"/api/files/{self.selected_file}/preview#page={page}"
        # プレースホルダを隠し、iframeを表示
        ui.run_javascript(f'''
            const ph = document.getElementById('ocr-pdf-placeholder');
            const f = document.getElementById('ocr-pdf-frame');
            if (ph) ph.style.display = 'none';
            if (f) {{ f.style.display = 'block'; f.src = {json.dumps(url)}; }}
        ''')

    def _update_pdf_preview_page(self, page: int):
        if not self.selected_file:
            return
        page = max(1, int(page))
        url = f"/api/files/{self.selected_file}/preview#page={page}"
        ui.run_javascript(f'''
            const f = document.getElementById('ocr-pdf-frame');
            if (f) {{ f.src = {json.dumps(url)}; }}
        ''')

    def _update_dialog_preview(self, file_id: str | None):
        if not file_id:
            ui.run_javascript('''
                const ph = document.getElementById('file-select-preview-placeholder');
                const f = document.getElementById('file-select-preview-frame');
                if (ph) ph.style.display = 'flex';
                if (f) { f.style.display = 'none'; f.src = 'about:blank'; }
            ''')
            return
        url = f"/api/files/{file_id}/preview"
        ui.run_javascript(f'''
            const ph = document.getElementById('file-select-preview-placeholder');
            const f = document.getElementById('file-select-preview-frame');
            if (ph) ph.style.display = 'none';
            if (f) {{ f.style.display = 'block'; f.src = {json.dumps(url)}; }}
        ''')

    # ========= OCR結果表示 =========
    def _display_ocr_results(self):
        if not self.ocr_results or not self.results_container:
            return
        
        self.results_container.clear()
        with self.results_container:
            ui.label(f'OCR結果: {len(self.ocr_results)}ページ').style('font-size: 14px; font-weight: 600; margin-bottom: 8px;')
            for result in sorted(self.ocr_results, key=lambda r: r['page']):
                with ui.card().style('margin-bottom: 6px; padding: 8px;'):
                    ui.label(f'ページ {result["page"]} (信頼度: {result.get("confidence", 0):.0%}, {result.get("processing_time", 0):.1f}s)').style('font-size: 12px; font-weight: 600; margin-bottom: 6px;')
                    ui.label(result.get('text', '')).style('font-size: 12px; white-space: pre-wrap;')

    def _export_results(self):
        ui.notify('未実装: 必要ならエクスポート処理を追加してください')

    def _clear_results(self):
        self.ocr_results = []
        if self.results_container:
            self.results_container.clear()
            
    # ========= 辞書編集 =========
    def _get_dict_buttons(self):
        self._ensure_dict_files()
        return [
            ("一般用語", 'known_words_common.csv'),
            ("専門用語", 'known_words_custom.csv'),
            ("誤字修正", 'ocr_word_mistakes.csv'),
            ("ユーザー辞書", 'user_dict.csv'),
            ("誤字辞書(予備)", 'word_mistakes.csv'),
        ]

    def _ensure_dict_files(self):
        self.dict_root.mkdir(parents=True, exist_ok=True)
        back_dir = self.dict_root / 'back'
        back_dir.mkdir(parents=True, exist_ok=True)
        # 旧ファイルからの初期コピー
        old_root = Path('OLD/ocr/dic')
        for fname in ['known_words_common.csv', 'known_words_custom.csv', 'ocr_word_mistakes.csv', 'user_dict.csv', 'word_mistakes.csv']:
            dst = self.dict_root / fname
            if not dst.exists():
                src = old_root / fname
                try:
                    if src.exists():
                        dst.write_bytes(src.read_bytes())
                    else:
                        dst.write_text('', encoding='utf-8')
                except Exception:
                    try:
                        dst.write_text('', encoding='utf-8')
                    except Exception:
                        pass

    def _open_dict_editor(self, label: str, filename: str):
        self._ensure_dict_files()
        path = self.dict_root / filename
        content = ''
        try:
            content = path.read_text(encoding='utf-8')
        except Exception:
            content = ''

        def save_and_close(dialog, textarea):
            try:
                # バックアップ
                back = self.dict_root / 'back' / f"{filename}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                if path.exists():
                    back.write_bytes(path.read_bytes())
                path.write_text(textarea.value or '', encoding='utf-8')
                ui.notify(f'{label} を保存しました', type='positive')
            except Exception as e:
                ui.notify(f'保存失敗: {e}', type='negative')
            finally:
                dialog.close()

        with ui.dialog() as dialog, ui.card():
            ui.label(f'辞書編集: {label}').style('font-size: 14px; font-weight: 600;')
            textarea = ui.textarea(value=content).style('width: 600px; height: 320px;')
            with ui.row():
                ui.button('保存', on_click=lambda d=dialog, t=textarea: save_and_close(d, t))
                ui.button('キャンセル', on_click=dialog.close)
        dialog.open()

    # ========= 補助処理 =========
    def _export_pdf_page_to_image(self, pdf_path: str, page_no: int) -> str:
        """指定ページをPNGに書き出してパスを返す"""
        import fitz  # PyMuPDF
        doc = fitz.open(pdf_path)
        page_index = max(0, min(page_no - 1, len(doc) - 1))
        page = doc.load_page(page_index)
        pix = page.get_pixmap()
        img_path = tempfile.mktemp(suffix='.png')
        pix.save(img_path)
        doc.close()
        return img_path

    def _export_single_page_pdf(self, pdf_path: str, page_no: int) -> str:
        import fitz
        src = fitz.open(pdf_path)
        dst = fitz.open()
        page_index = max(0, min(page_no - 1, len(src) - 1))
        dst.insert_pdf(src, from_page=page_index, to_page=page_index)
        out_path = tempfile.mktemp(suffix='.pdf')
        dst.save(out_path)
        dst.close()
        src.close()
        return out_path

    def _compute_pdf_page_count_from_bytes(self, data: bytes) -> int:
        if not data:
            return 0
        try:
            import fitz
            doc = fitz.open(stream=data, filetype='pdf')
            n = len(doc)
            doc.close()
            return n
        except Exception:
            return 0

    def _apply_correction(self, text: str) -> str:
        # SpellCheckerを使用し、app/config/ocr/dic を参照
        try:
            from app.services.ocr.spellcheck import get_spell_checker
            checker = get_spell_checker(str(self.dict_root))
            return checker.correct_text(text)
        except Exception:
            # フォールバックなし
            return text