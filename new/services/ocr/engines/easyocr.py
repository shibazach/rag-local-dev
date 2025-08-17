# new/services/ocr/engines/easyocr.py
# EasyOCRエンジン実装

import time
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path
from ..base import OCREngine, OCRResult

LOGGER = logging.getLogger(__name__)

class EasyOCREngine(OCREngine):
    """EasyOCRエンジン実装"""
    
    def __init__(self):
        self.name = "EasyOCR"
        self.engine_id = "easyocr"
        self._reader = None
    
    def is_available(self) -> bool:
        """EasyOCRの利用可能性をチェック"""
        try:
            import easyocr
            return True
        except ImportError:
            LOGGER.warning("EasyOCRがインストールされていません")
            return False
    
    def get_parameters(self) -> list:
        """EasyOCRのパラメータ定義"""
        return [
            {
                "name": "languages",
                "label": "認識言語",
                "type": "select",
                "default": ["ja", "en"],
                "options": [
                    {"value": ["ja"], "label": "日本語のみ"},
                    {"value": ["en"], "label": "英語のみ"},
                    {"value": ["ja", "en"], "label": "日本語 + 英語"},
                    {"value": ["zh"], "label": "中国語"},
                    {"value": ["ko"], "label": "韓国語"},
                    {"value": ["ja", "en", "zh"], "label": "日本語 + 英語 + 中国語"}
                ],
                "description": "OCR認識対象言語（複数選択可能）",
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
                "name": "detail",
                "label": "詳細情報",
                "type": "select",
                "default": 1,
                "options": [
                    {"value": 0, "label": "テキストのみ"},
                    {"value": 1, "label": "座標と信頼度を含む"}
                ],
                "description": "出力する情報の詳細レベル",
                "category": "基本設定"
            },
            {
                "name": "paragraph",
                "label": "段落モード",
                "type": "boolean",
                "default": False,
                "description": "段落単位でテキストをグループ化",
                "category": "基本設定"
            },
            {
                "name": "high_quality_mode",
                "label": "高精度モード",
                "type": "boolean",
                "default": False,
                "description": "高精度処理（処理時間が増加しますが精度向上）",
                "category": "高精度設定"
            },
            {
                "name": "text_threshold",
                "label": "テキスト検出閾値",
                "type": "number",
                "default": 0.7,
                "min": 0.1,
                "max": 1.0,
                "step": 0.1,
                "description": "テキスト検出の信頼度閾値（低いほど多くのテキストを検出）",
                "category": "高精度設定"
            },
            {
                "name": "link_threshold",
                "label": "リンク閾値",
                "type": "number",
                "default": 0.4,
                "min": 0.1,
                "max": 1.0,
                "step": 0.1,
                "description": "文字間のリンク閾値（低いほど文字を繋げやすい）",
                "category": "高精度設定"
            },
            {
                "name": "low_text",
                "label": "低信頼度テキスト検出",
                "type": "number",
                "default": 0.4,
                "min": 0.1,
                "max": 1.0,
                "step": 0.1,
                "description": "低信頼度テキストの検出閾値",
                "category": "高精度設定"
            },
            {
                "name": "canvas_size",
                "label": "キャンバスサイズ",
                "type": "number",
                "default": 2560,
                "min": 1280,
                "max": 5120,
                "step": 256,
                "description": "処理用キャンバスサイズ（大きいほど高精度、メモリ使用量増加）",
                "category": "高精度設定"
            },
            {
                "name": "mag_ratio",
                "label": "拡大比率",
                "type": "number",
                "default": 1.5,
                "min": 1.0,
                "max": 3.0,
                "step": 0.1,
                "description": "画像の拡大比率（高精度モード時に使用）",
                "category": "高精度設定"
            }
        ]
    
    def _initialize_reader(self, **kwargs):
        """EasyOCRリーダーを初期化"""
        if self._reader is not None:
            return
        
        try:
            import easyocr
            
            # 言語設定
            languages = kwargs.get('languages', ['ja', 'en'])
            if isinstance(languages, str):
                languages = [languages]
            
            # GPU設定
            gpu = kwargs.get('gpu', False)
            
            self._reader = easyocr.Reader(
                languages,
                gpu=gpu,
                verbose=False
            )
            
        except Exception as e:
            LOGGER.error(f"EasyOCR初期化エラー: {e}")
            raise
    
    def process_file(self, file_path: str, **kwargs) -> OCRResult:
        """EasyOCRでファイルを処理"""
        start_time = time.perf_counter()
        
        try:
            if not self.is_available():
                return OCRResult(
                    success=False,
                    text="",
                    processing_time=0,
                    error="EasyOCRが利用できません"
                )
            
            # リーダー初期化
            self._initialize_reader(**kwargs)
            
            # ファイル存在確認
            if not Path(file_path).exists():
                return OCRResult(
                    success=False,
                    text="",
                    processing_time=time.perf_counter() - start_time,
                    error=f"ファイルが見つかりません: {file_path}"
                )
            
            # パラメータ設定
            detail = 0  # テキストのみ返却
            width_ths = kwargs.get('width_ths', 0.7)
            height_ths = kwargs.get('height_ths', 0.7)
            decoder = kwargs.get('decoder', 'greedy')
            beamWidth = kwargs.get('beamWidth', 5)
            batch_size = kwargs.get('batch_size', 1)
            workers = kwargs.get('workers', 0)
            allowlist = kwargs.get('allowlist', '')
            blocklist = kwargs.get('blocklist', '')
            
            # OCR実行
            result = self._reader.readtext(
                file_path,
                detail=detail,
                width_ths=width_ths,
                height_ths=height_ths,
                decoder=decoder,
                beamWidth=beamWidth,
                batch_size=batch_size,
                workers=workers,
                allowlist=allowlist if allowlist else None,
                blocklist=blocklist if blocklist else None
            )
            
            # 結果をテキストに変換
            if isinstance(result, list) and len(result) > 0:
                if isinstance(result[0], str):
                    # detail=0の場合、文字列のリスト
                    extracted_text = '\n'.join(result)
                else:
                    # detail=1の場合、詳細情報付き
                    text_lines = [item[1] for item in result if len(item) > 1]
                    extracted_text = '\n'.join(text_lines)
            else:
                extracted_text = ""
            
            processing_time = time.perf_counter() - start_time
            
            return OCRResult(
                success=True,
                text=extracted_text,
                processing_time=processing_time
            )
            
        except Exception as e:
            processing_time = time.perf_counter() - start_time
            error_msg = f"EasyOCR処理エラー: {str(e)}"
            LOGGER.error(error_msg)
            
            return OCRResult(
                success=False,
                text="",
                processing_time=processing_time,
                error=error_msg
            )