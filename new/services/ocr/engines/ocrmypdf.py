# new/services/ocr/engines/ocrmypdf.py
# OCRMyPDFエンジン実装

import subprocess
import tempfile
import time
import logging
from pathlib import Path
from typing import Dict
from ..base import OCREngine, OCRResult

LOGGER = logging.getLogger(__name__)

class OCRMyPDFEngine(OCREngine):
    """OCRMyPDFを使用したOCRエンジン"""
    
    def __init__(self):
        super().__init__()
        self.name = "OCRMyPDF"
        self.version = "1.0.0"
    
    def is_available(self) -> bool:
        """OCRMyPDFが利用可能かチェック"""
        try:
            result = subprocess.run(
                ['ocrmypdf', '--version'], 
                capture_output=True, 
                text=True, 
                timeout=10
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def get_parameters(self) -> list:
        """OCRMyPDF固有のパラメータ定義（UI表示情報含む）"""
        return [
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
            },
            {
                "name": "optimize",
                "label": "PDF最適化レベル",
                "type": "select",
                "default": 1,
                "options": [
                    {"value": 0, "label": "0: 最適化なし"},
                    {"value": 1, "label": "1: 軽度最適化（推奨）"},
                    {"value": 2, "label": "2: 中程度最適化"},
                    {"value": 3, "label": "3: 高度最適化"}
                ],
                "description": "出力PDFの最適化レベル",
                "category": "出力設定"
            },
            {
                "name": "force_ocr",
                "label": "強制OCR実行",
                "type": "checkbox",
                "default": True,
                "description": "既にOCR済みのPDFでも再処理を実行",
                "category": "処理設定"
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
        dpi = kwargs.get('dpi', 300)
        optimize = kwargs.get('optimize', 1)
        
        try:
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_output:
                temp_output_path = temp_output.name
            
            # OCRMyPDFコマンド構築
            cmd = [
                'ocrmypdf',
                '--language', language,
                '--image-dpi', str(dpi),  # --dpi から --image-dpi に修正
                '--optimize', str(optimize),
                '--force-ocr',  # 既にOCR済みでも再処理
                '--sidecar', '-',  # テキストを標準出力に
                file_path,
                temp_output_path
            ]
            
            # OCR実行
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5分タイムアウト
            )
            
            processing_time = time.perf_counter() - start_time
            
            if result.returncode != 0:
                error_msg = result.stderr.strip() or "OCRMyPDF処理エラー"
                return OCRResult(
                    success=False,
                    text="",
                    processing_time=processing_time,
                    error=error_msg
                )
            
            # テキスト抽出成功
            extracted_text = result.stdout.strip()
            
            # 一時ファイル削除
            try:
                Path(temp_output_path).unlink()
            except Exception:
                pass  # 削除失敗は無視
            
            return OCRResult(
                success=True,
                text=extracted_text,
                processing_time=processing_time,
                confidence=None  # OCRMyPDFは信頼度を返さない
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
        """PDF専用の検証"""
        if not Path(file_path).exists():
            return False
        return Path(file_path).suffix.lower() == '.pdf'