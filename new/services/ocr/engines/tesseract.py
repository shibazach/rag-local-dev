# new/services/ocr/engines/tesseract.py
# Tesseractエンジン実装

import subprocess
import time
import logging
from pathlib import Path
from typing import Dict
from ..base import OCREngine, OCRResult

LOGGER = logging.getLogger(__name__)

class TesseractEngine(OCREngine):
    """Tesseractを使用したOCRエンジン"""
    
    def __init__(self):
        super().__init__()
        self.name = "Tesseract"
        self.version = "1.0.0"
    
    def is_available(self) -> bool:
        """Tesseractが利用可能かチェック"""
        try:
            result = subprocess.run(
                ['tesseract', '--version'], 
                capture_output=True, 
                text=True, 
                timeout=10
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def get_parameters(self) -> list:
        """Tesseract固有のパラメータ定義（UI表示情報含む）"""
        return [
            {
                "name": "psm",
                "label": "ページセグメンテーションモード",
                "type": "select",
                "default": 6,
                "options": [
                    {"value": 0, "label": "0: 向きとスクリプト検出のみ"},
                    {"value": 1, "label": "1: 自動ページセグメンテーション（OSD付き）"},
                    {"value": 3, "label": "3: 完全自動ページセグメンテーション"},
                    {"value": 6, "label": "6: 単一の均一テキストブロック"},
                    {"value": 7, "label": "7: 単一テキスト行"},
                    {"value": 8, "label": "8: 単一単語"},
                    {"value": 13, "label": "13: 生の行（文字分割なし）"}
                ],
                "description": "テキスト認識のセグメンテーション方法",
                "category": "基本設定"
            },
            {
                "name": "oem",
                "label": "OCRエンジンモード",
                "type": "select",
                "default": 3,
                "options": [
                    {"value": 0, "label": "0: レガシーエンジンのみ"},
                    {"value": 1, "label": "1: ニューラルネットワークLSTMエンジンのみ"},
                    {"value": 2, "label": "2: レガシー + LSTMエンジン"},
                    {"value": 3, "label": "3: デフォルト（利用可能なものを使用）"}
                ],
                "description": "使用するOCRエンジンの種類",
                "category": "基本設定"
            },
            {
                "name": "language",
                "label": "認識言語",
                "type": "select",
                "default": "jpn+eng",
                "options": [
                    {"value": "jpn", "label": "日本語のみ"},
                    {"value": "eng", "label": "英語のみ"},
                    {"value": "jpn+eng", "label": "日本語 + 英語"},
                    {"value": "chi_sim", "label": "中国語（簡体字）"},
                    {"value": "chi_tra", "label": "中国語（繁体字）"},
                    {"value": "kor", "label": "韓国語"},
                    {"value": "deu", "label": "ドイツ語"},
                    {"value": "fra", "label": "フランス語"}
                ],
                "description": "OCR認識対象言語",
                "category": "基本設定"
            },
            {
                "name": "dpi",
                "label": "DPI設定",
                "type": "number",
                "default": 300,
                "min": 150,
                "max": 600,
                "step": 50,
                "description": "画像解像度（高いほど精度向上、処理時間増加）",
                "category": "基本設定"
            }
        ]
    
    def process_file(self, file_path: str, **kwargs) -> OCRResult:
        """ファイルをOCR処理"""
        start_time = time.perf_counter()
        
        if not self.validate_file(file_path):
            return OCRResult(
                success=False,
                text="",
                processing_time=0,
                error=f"サポートされていないファイル形式: {file_path}"
            )
        
        # パラメータ設定
        language = kwargs.get('language', 'jpn+eng')
        psm = kwargs.get('psm', 6)
        oem = kwargs.get('oem', 3)
        
        try:
            # Tesseractコマンド構築
            cmd = [
                'tesseract',
                file_path,
                'stdout',  # 標準出力に結果を出力
                '-l', language,
                '--psm', str(psm),
                '--oem', str(oem)
            ]
            
            # OCR実行
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=180  # 3分タイムアウト
            )
            
            processing_time = time.perf_counter() - start_time
            
            if result.returncode != 0:
                error_msg = result.stderr.strip() or "Tesseract処理エラー"
                return OCRResult(
                    success=False,
                    text="",
                    processing_time=processing_time,
                    error=error_msg
                )
            
            # テキスト抽出成功
            extracted_text = result.stdout.strip()
            
            return OCRResult(
                success=True,
                text=extracted_text,
                processing_time=processing_time,
                confidence=None  # 基本版では信頼度取得なし
            )
            
        except subprocess.TimeoutExpired:
            return OCRResult(
                success=False,
                text="",
                processing_time=time.perf_counter() - start_time,
                error="OCR処理がタイムアウトしました"
            )
        except Exception as e:
            return OCRResult(
                success=False,
                text="",
                processing_time=time.perf_counter() - start_time,
                error=f"OCR処理エラー: {str(e)}"
            )
    
    def validate_file(self, file_path: str) -> bool:
        """画像ファイル専用の検証"""
        if not Path(file_path).exists():
            return False
        
        supported_extensions = {'.png', '.jpg', '.jpeg', '.tiff', '.bmp', '.pdf'}
        return Path(file_path).suffix.lower() in supported_extensions