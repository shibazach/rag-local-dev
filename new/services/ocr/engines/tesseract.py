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
    
    def get_parameters(self) -> Dict:
        """Tesseract固有のパラメータ定義"""
        return {
            'language': {
                'type': 'string',
                'default': 'jpn+eng',
                'description': 'Tesseract言語コード'
            },
            'psm': {
                'type': 'integer',
                'default': 6,
                'min': 0,
                'max': 13,
                'description': 'ページセグメンテーションモード'
            },
            'oem': {
                'type': 'integer',
                'default': 3,
                'min': 0,
                'max': 3,
                'description': 'OCRエンジンモード'
            }
        }
    
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