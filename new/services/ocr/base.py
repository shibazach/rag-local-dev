# new/services/ocr/base.py
# OCRエンジンの基底クラス

from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from dataclasses import dataclass
from pathlib import Path
import time

@dataclass
class OCRResult:
    """OCR処理結果"""
    success: bool
    text: str
    processing_time: float
    confidence: Optional[float] = None
    error: Optional[str] = None
    page_count: Optional[int] = None

class OCREngine(ABC):
    """OCRエンジンの抽象基底クラス"""
    
    def __init__(self):
        self.name = "Base OCR Engine"
        self.version = "1.0.0"
    
    @abstractmethod
    def is_available(self) -> bool:
        """エンジンが利用可能かチェック"""
        pass
    
    @abstractmethod
    def get_parameters(self) -> List[Dict]:
        """エンジン固有のパラメータ定義を取得（UI表示情報含む配列形式）"""
        pass
    
    @abstractmethod
    def process_file(self, file_path: str, **kwargs) -> OCRResult:
        """ファイルをOCR処理"""
        pass
    
    def validate_file(self, file_path: str) -> bool:
        """ファイルの形式をチェック"""
        if not Path(file_path).exists():
            return False
        
        supported_extensions = {'.pdf', '.png', '.jpg', '.jpeg', '.tiff', '.bmp'}
        return Path(file_path).suffix.lower() in supported_extensions
    
    def get_engine_info(self) -> Dict:
        """エンジン情報を取得"""
        return {
            'name': self.name,
            'version': self.version,
            'available': self.is_available(),
            'parameters': self.get_parameters()
        }