# app/services/ocr/engines/__init__.py
# OCRエンジン実装

from .ocrmypdf import OCRMyPDFEngine
from .tesseract import TesseractEngine
from .easyocr import EasyOCREngine
from .paddleocr import PaddleOCREngine

__all__ = ['OCRMyPDFEngine', 'TesseractEngine', 'EasyOCREngine', 'PaddleOCREngine']