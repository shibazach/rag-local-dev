# new/services/ocr/__init__.py
# OCRサービスパッケージ初期化

from .factory import OCREngineFactory
from .base import OCRResult, OCREngine

__all__ = ['OCREngineFactory', 'OCRResult', 'OCREngine']