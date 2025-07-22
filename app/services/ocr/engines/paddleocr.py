# app/services/ocr/engines/paddleocr.py
# PaddleOCRエンジンの実装

import time
import tempfile
import os
from typing import Dict, Any, List
import fitz  # PyMuPDF
from PIL import Image

from ..base import OCREngine

class PaddleOCREngine(OCREngine):
    """PaddleOCRエンジン実装"""
    
    def __init__(self):
        super().__init__("PaddleOCR")
    
    def process(self, pdf_path: str, page_num: int = 0, **kwargs) -> Dict[str, Any]:
        """PaddleOCRでPDF処理を実行"""
        start_time = time.time()
        
        try:
            from paddleocr import PaddleOCR
            
            # パラメータの検証と正規化
            params = self.validate_parameters(kwargs)
            
            # PDFから画像を抽出
            doc = fitz.open(pdf_path)
            if page_num >= len(doc):
                return {
                    "success": False,
                    "error": f"ページ {page_num} が存在しません",
                    "text": "",
                    "processing_time": time.time() - start_time,
                    "confidence": None
                }
            
            page = doc[page_num]
            # 解像度を上げて画像を取得
            zoom = params.get('zoom_factor', 2.0)
            pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom))
            img_data = pix.tobytes("png")
            
            # 一時ファイルに画像保存
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
                temp_file.write(img_data)
                temp_path = temp_file.name
            
            # PaddleOCRを初期化
            lang = params.get('lang', 'japan')
            use_gpu = params.get('use_gpu', False)
            show_log = params.get('show_log', False)
            
            # PaddleOCRの初期化パラメータを構築
            ocr_params = {
                'lang': lang,
                'show_log': show_log,
                'use_angle_cls': params.get('use_angle_cls', True),
                'det': params.get('use_detection', True),
                'rec': params.get('use_recognition', True),
                'cls': params.get('use_classification', True)
            }
            
            # GPU使用設定（バージョンによって異なる可能性があるため条件付き）
            if use_gpu:
                ocr_params['use_gpu'] = True
            
            try:
                ocr = PaddleOCR(**ocr_params)
            except TypeError as e:
                # use_gpuパラメータが認識されない場合は除外して再試行
                if 'use_gpu' in str(e):
                    print(f"⚠️ PaddleOCR: use_gpuパラメータが認識されません。CPUモードで実行します。")
                    ocr_params.pop('use_gpu', None)
                    ocr = PaddleOCR(**ocr_params)
                else:
                    raise
            
            # OCR実行
            results = ocr.ocr(temp_path, cls=params.get('use_classification', True))
            
            # テキストと信頼度を抽出
            texts = []
            confidences = []
            
            if results and results[0]:  # PaddleOCRの結果構造に対応
                for line in results[0]:
                    if line and len(line) >= 2:
                        bbox, (text, confidence) = line[0], line[1]
                        texts.append(text)
                        confidences.append(confidence)
            
            combined_text = '\n'.join(texts)
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
            
            # クリーンアップ
            doc.close()
            os.unlink(temp_path)
            
            return {
                "success": True,
                "text": combined_text,
                "processing_time": time.time() - start_time,
                "confidence": avg_confidence,
                "engine": self.name,
                "parameters": params
            }
            
        except ImportError:
            return {
                "success": False,
                "error": "paddleocrがインストールされていません",
                "text": "",
                "processing_time": time.time() - start_time,
                "confidence": None
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"PaddleOCR処理エラー: {str(e)}",
                "text": "",
                "processing_time": time.time() - start_time,
                "confidence": None
            }
    
    def get_parameters(self) -> List[Dict[str, Any]]:
        """PaddleOCRの調整可能パラメータ"""
        return [
            {
                "name": "lang",
                "label": "認識言語",
                "type": "select",
                "default": "japan",
                "options": [
                    {"value": "japan", "label": "日本語"},
                    {"value": "en", "label": "英語"},
                    {"value": "ch", "label": "中国語（簡体字）"},
                    {"value": "chinese_cht", "label": "中国語（繁体字）"},
                    {"value": "korean", "label": "韓国語"},
                    {"value": "german", "label": "ドイツ語"},
                    {"value": "french", "label": "フランス語"},
                    {"value": "arabic", "label": "アラビア語"},
                    {"value": "russian", "label": "ロシア語"},
                    {"value": "spanish", "label": "スペイン語"}
                ],
                "description": "OCR認識対象言語",
                "category": "基本設定"
            },
            {
                "name": "use_gpu",
                "label": "GPU使用",
                "type": "checkbox",
                "default": False,
                "description": "GPU加速を使用（CUDA対応GPU必要）",
                "category": "基本設定"
            },
            {
                "name": "zoom_factor",
                "label": "画像拡大倍率",
                "type": "number",
                "default": 2.0,
                "min": 1.0,
                "max": 4.0,
                "step": 0.5,
                "description": "画像の拡大倍率（高いほど精度向上、処理時間増加）",
                "category": "基本設定"
            },
            {
                "name": "use_angle_cls",
                "label": "角度分類",
                "type": "checkbox",
                "default": True,
                "description": "テキストの角度を自動分類・補正",
                "category": "基本設定"
            },
            {
                "name": "use_detection",
                "label": "テキスト検出",
                "type": "checkbox",
                "default": True,
                "description": "テキスト領域の検出を実行",
                "category": "基本設定"
            },
            {
                "name": "use_recognition",
                "label": "テキスト認識",
                "type": "checkbox",
                "default": True,
                "description": "テキストの認識を実行",
                "category": "基本設定"
            },
            {
                "name": "det_algorithm",
                "label": "検出アルゴリズム",
                "type": "select",
                "default": "DB",
                "options": [
                    {"value": "DB", "label": "DB（Differentiable Binarization）"},
                    {"value": "EAST", "label": "EAST"},
                    {"value": "SAST", "label": "SAST"},
                    {"value": "PSE", "label": "PSE"},
                    {"value": "FCE", "label": "FCE"}
                ],
                "description": "テキスト検出に使用するアルゴリズム",
                "category": "検出設定"
            },
            {
                "name": "det_limit_side_len",
                "label": "検出画像サイズ制限",
                "type": "number",
                "default": 960,
                "min": 480,
                "max": 2048,
                "step": 32,
                "description": "検出処理時の画像サイズ制限",
                "category": "検出設定"
            },
            {
                "name": "det_limit_type",
                "label": "サイズ制限タイプ",
                "type": "select",
                "default": "max",
                "options": [
                    {"value": "max", "label": "最大値制限"},
                    {"value": "min", "label": "最小値制限"}
                ],
                "description": "画像サイズ制限の適用方法",
                "category": "検出設定"
            },
            {
                "name": "det_db_thresh",
                "label": "DB閾値",
                "type": "number",
                "default": 0.3,
                "min": 0.1,
                "max": 0.9,
                "step": 0.1,
                "description": "DB検出アルゴリズムの閾値",
                "category": "検出設定"
            },
            {
                "name": "det_db_box_thresh",
                "label": "DBボックス閾値",
                "type": "number",
                "default": 0.6,
                "min": 0.1,
                "max": 0.9,
                "step": 0.1,
                "description": "DBボックス検出の閾値",
                "category": "検出設定"
            },
            {
                "name": "det_db_unclip_ratio",
                "label": "DBアンクリップ比率",
                "type": "number",
                "default": 1.5,
                "min": 1.0,
                "max": 3.0,
                "step": 0.1,
                "description": "DBテキストボックス拡張比率",
                "category": "検出設定"
            },
            {
                "name": "rec_algorithm",
                "label": "認識アルゴリズム",
                "type": "select",
                "default": "SVTR_LCNet",
                "options": [
                    {"value": "SVTR_LCNet", "label": "SVTR_LCNet（推奨）"},
                    {"value": "CRNN", "label": "CRNN"},
                    {"value": "RARE", "label": "RARE"},
                    {"value": "SRN", "label": "SRN"},
                    {"value": "NRTR", "label": "NRTR"}
                ],
                "description": "テキスト認識に使用するアルゴリズム",
                "category": "認識設定"
            },
            {
                "name": "rec_image_shape",
                "label": "認識画像サイズ",
                "type": "select",
                "default": "3,48,320",
                "options": [
                    {"value": "3,32,320", "label": "32x320（高速）"},
                    {"value": "3,48,320", "label": "48x320（標準）"},
                    {"value": "3,64,320", "label": "64x320（高精度）"}
                ],
                "description": "認識処理時の画像サイズ",
                "category": "認識設定"
            },
            {
                "name": "rec_batch_num",
                "label": "認識バッチサイズ",
                "type": "number",
                "default": 6,
                "min": 1,
                "max": 32,
                "step": 1,
                "description": "認識処理のバッチサイズ",
                "category": "認識設定"
            },
            {
                "name": "use_classification",
                "label": "テキスト分類",
                "type": "checkbox",
                "default": True,
                "description": "テキストの向きを分類",
                "category": "分類設定"
            },
            {
                "name": "cls_thresh",
                "label": "分類閾値",
                "type": "number",
                "default": 0.9,
                "min": 0.5,
                "max": 1.0,
                "step": 0.05,
                "description": "テキスト分類の信頼度閾値",
                "category": "分類設定"
            },
            {
                "name": "cls_batch_num",
                "label": "分類バッチサイズ",
                "type": "number",
                "default": 6,
                "min": 1,
                "max": 32,
                "step": 1,
                "description": "分類処理のバッチサイズ",
                "category": "分類設定"
            },
            {
                "name": "show_log",
                "label": "ログ表示",
                "type": "checkbox",
                "default": False,
                "description": "処理ログを表示",
                "category": "デバッグ"
            },
            {
                "name": "save_crop_res",
                "label": "切り抜き画像保存",
                "type": "checkbox",
                "default": False,
                "description": "切り抜いたテキスト画像を保存（デバッグ用）",
                "category": "デバッグ"
            }
        ]
    
    def is_available(self) -> bool:
        """PaddleOCRが利用可能かチェック"""
        try:
            from paddleocr import PaddleOCR
            return True
        except ImportError:
            return False