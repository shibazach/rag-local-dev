# new/services/ocr/engines/paddleocr.py
# PaddleOCRエンジン実装

import time
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path
from ..base import OCREngine, OCRResult

LOGGER = logging.getLogger(__name__)

class PaddleOCREngine(OCREngine):
    """PaddleOCRエンジン実装"""
    
    def __init__(self):
        self.name = "PaddleOCR"
        self.engine_id = "paddleocr"
        self._ocr = None
    
    def is_available(self) -> bool:
        """PaddleOCRの利用可能性をチェック"""
        try:
            import paddleocr
            return True
        except ImportError:
            LOGGER.warning("PaddleOCRがインストールされていません")
            return False
    
    def get_parameters(self) -> List[Dict[str, Any]]:
        """PaddleOCRのパラメータ定義"""
        return [
            {
                "name": "lang",
                "label": "認識言語",
                "type": "select",
                "default": "japan",
                "options": [
                    {"value": "japan", "label": "日本語"},
                    {"value": "ch", "label": "中国語（簡体字）"},
                    {"value": "en", "label": "英語"},
                    {"value": "korean", "label": "韓国語"},
                    {"value": "french", "label": "フランス語"},
                    {"value": "german", "label": "ドイツ語"},
                    {"value": "russian", "label": "ロシア語"},
                    {"value": "spanish", "label": "スペイン語"}
                ],
                "description": "OCR認識対象言語",
                "category": "基本設定"
            },
            {
                "name": "use_gpu",
                "label": "GPU使用",
                "type": "boolean",
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
                "type": "boolean",
                "default": True,
                "description": "テキストの角度を自動分類・補正",
                "category": "基本設定"
            },
            {
                "name": "use_detection",
                "label": "テキスト検出",
                "type": "boolean",
                "default": True,
                "description": "テキスト領域の検出を実行",
                "category": "基本設定"
            },
            {
                "name": "use_recognition",
                "label": "テキスト認識",
                "type": "boolean",
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
                "name": "rec_batch_num",
                "label": "認識バッチサイズ",
                "type": "number",
                "default": 6,
                "min": 1,
                "max": 20,
                "step": 1,
                "description": "認識バッチサイズ",
                "category": "認識設定"
            }
        ]
    
    def _initialize_ocr(self, **kwargs):
        """PaddleOCRインスタンスを初期化"""
        if self._ocr is not None:
            return
        
        try:
            import paddleocr
            
            # パラメータ設定
            use_angle_cls = kwargs.get('use_angle_cls', True)
            lang = kwargs.get('lang', 'japan')
            use_gpu = kwargs.get('use_gpu', False)
            
            self._ocr = paddleocr.PaddleOCR(
                use_angle_cls=use_angle_cls,
                lang=lang,
                use_gpu=use_gpu,
                show_log=False
            )
            
        except Exception as e:
            LOGGER.error(f"PaddleOCR初期化エラー: {e}")
            raise
    
    def process_file(self, file_path: str, **kwargs) -> OCRResult:
        """PaddleOCRでファイルを処理"""
        start_time = time.perf_counter()
        
        try:
            if not self.is_available():
                return OCRResult(
                    success=False,
                    text="",
                    processing_time=0,
                    error="PaddleOCRが利用できません"
                )
            
            # OCRインスタンス初期化
            self._initialize_ocr(**kwargs)
            
            # ファイル存在確認
            if not Path(file_path).exists():
                return OCRResult(
                    success=False,
                    text="",
                    processing_time=time.perf_counter() - start_time,
                    error=f"ファイルが見つかりません: {file_path}"
                )
            
            # OCR実行
            result = self._ocr.ocr(file_path, cls=kwargs.get('use_angle_cls', True))
            
            # 結果をテキストに変換
            text_lines = []
            if result and result[0]:
                for line in result[0]:
                    if line and len(line) >= 2:
                        text_lines.append(line[1][0])
            
            extracted_text = '\n'.join(text_lines)
            processing_time = time.perf_counter() - start_time
            
            return OCRResult(
                success=True,
                text=extracted_text,
                processing_time=processing_time,
                metadata={
                    "engine": "PaddleOCR",
                    "lang": kwargs.get('lang', 'japan'),
                    "lines_detected": len(text_lines)
                }
            )
            
        except Exception as e:
            processing_time = time.perf_counter() - start_time
            error_msg = f"PaddleOCR処理エラー: {str(e)}"
            LOGGER.error(error_msg)
            
            return OCRResult(
                success=False,
                text="",
                processing_time=processing_time,
                error=error_msg
            )