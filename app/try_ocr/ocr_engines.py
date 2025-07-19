# app/try_ocr/ocr_engines.py
# 各種OCRエンジンの実装

import os
import subprocess
import tempfile
from typing import Dict, Any, List
import fitz  # PyMuPDF
from PIL import Image
import io

class OCREngine:
    """OCRエンジンの基底クラス"""
    
    def __init__(self, name: str):
        self.name = name
    
    def process(self, pdf_path: str, page_num: int = 0) -> Dict[str, Any]:
        """PDFの指定ページをOCR処理"""
        raise NotImplementedError
    
    def is_available(self) -> bool:
        """エンジンが利用可能かチェック"""
        raise NotImplementedError

class OCRMyPDFEngine(OCREngine):
    """現在使用中のOCRMyPDF"""
    
    def __init__(self):
        super().__init__("OCRMyPDF (現在使用中)")
    
    def process(self, pdf_path: str, page_num: int = 0) -> Dict[str, Any]:
        try:
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
                temp_path = temp_file.name
            
            # OCRMyPDFで処理
            cmd = ["ocrmypdf", "--force-ocr", "-l", "jpn+eng", pdf_path, temp_path]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode != 0:
                return {
                    "success": False,
                    "error": f"OCRMyPDF エラー: {result.stderr}",
                    "text": "",
                    "processing_time": 0
                }
            
            # 処理後のPDFからテキスト抽出
            doc = fitz.open(temp_path)
            if page_num < len(doc):
                text = doc[page_num].get_text()
            else:
                text = ""
            doc.close()
            
            # 一時ファイル削除
            os.unlink(temp_path)
            
            return {
                "success": True,
                "text": text,
                "processing_time": 0,  # 実際の時間測定は後で追加
                "confidence": None
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "text": "",
                "processing_time": 0
            }
    
    def is_available(self) -> bool:
        try:
            result = subprocess.run(["ocrmypdf", "--version"], 
                                  capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except:
            return False

class PaddleOCREngine(OCREngine):
    """PaddleOCR エンジン"""
    
    def __init__(self):
        super().__init__("PaddleOCR")
        self._ocr = None
    
    def _get_ocr(self):
        if self._ocr is None:
            try:
                from paddleocr import PaddleOCR
                self._ocr = PaddleOCR(use_angle_cls=True, lang='japan')
            except ImportError:
                raise ImportError("PaddleOCR がインストールされていません")
        return self._ocr
    
    def process(self, pdf_path: str, page_num: int = 0) -> Dict[str, Any]:
        try:
            # PDFを画像に変換
            doc = fitz.open(pdf_path)
            if page_num >= len(doc):
                return {
                    "success": False,
                    "error": f"ページ {page_num} が存在しません",
                    "text": "",
                    "processing_time": 0
                }
            
            page = doc[page_num]
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2倍解像度
            img_data = pix.tobytes("png")
            doc.close()
            
            # PaddleOCRで処理
            ocr = self._get_ocr()
            result = ocr.ocr(img_data, cls=True)
            
            # 結果をテキストに変換
            text_lines = []
            total_confidence = 0
            count = 0
            
            if result and result[0]:
                for line in result[0]:
                    if len(line) >= 2:
                        text = line[1][0]
                        confidence = line[1][1]
                        text_lines.append(text)
                        total_confidence += confidence
                        count += 1
            
            avg_confidence = total_confidence / count if count > 0 else 0
            
            return {
                "success": True,
                "text": "\n".join(text_lines),
                "processing_time": 0,
                "confidence": avg_confidence
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "text": "",
                "processing_time": 0
            }
    
    def is_available(self) -> bool:
        try:
            from paddleocr import PaddleOCR
            return True
        except ImportError:
            return False

class EasyOCREngine(OCREngine):
    """EasyOCR エンジン"""
    
    def __init__(self):
        super().__init__("EasyOCR")
        self._reader = None
    
    def _get_reader(self):
        if self._reader is None:
            try:
                import easyocr
                self._reader = easyocr.Reader(['ja', 'en'])
            except ImportError:
                raise ImportError("EasyOCR がインストールされていません")
        return self._reader
    
    def process(self, pdf_path: str, page_num: int = 0) -> Dict[str, Any]:
        try:
            # PDFを画像に変換
            doc = fitz.open(pdf_path)
            if page_num >= len(doc):
                return {
                    "success": False,
                    "error": f"ページ {page_num} が存在しません",
                    "text": "",
                    "processing_time": 0
                }
            
            page = doc[page_num]
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
            img_data = pix.tobytes("png")
            doc.close()
            
            # EasyOCRで処理
            reader = self._get_reader()
            result = reader.readtext(img_data)
            
            # 結果をテキストに変換
            text_lines = []
            total_confidence = 0
            
            for (bbox, text, confidence) in result:
                text_lines.append(text)
                total_confidence += confidence
            
            avg_confidence = total_confidence / len(result) if result else 0
            
            return {
                "success": True,
                "text": "\n".join(text_lines),
                "processing_time": 0,
                "confidence": avg_confidence
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "text": "",
                "processing_time": 0
            }
    
    def is_available(self) -> bool:
        try:
            import easyocr
            return True
        except ImportError:
            return False

class TesseractEngine(OCREngine):
    """Tesseract エンジン"""
    
    def __init__(self):
        super().__init__("Tesseract")
    
    def process(self, pdf_path: str, page_num: int = 0) -> Dict[str, Any]:
        try:
            import pytesseract
            
            # PDFを画像に変換
            doc = fitz.open(pdf_path)
            if page_num >= len(doc):
                return {
                    "success": False,
                    "error": f"ページ {page_num} が存在しません",
                    "text": "",
                    "processing_time": 0
                }
            
            page = doc[page_num]
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
            img_data = pix.tobytes("png")
            doc.close()
            
            # PIL Imageに変換
            image = Image.open(io.BytesIO(img_data))
            
            # Tesseractで処理（日本語+英語）
            text = pytesseract.image_to_string(image, lang='jpn+eng')
            
            return {
                "success": True,
                "text": text,
                "processing_time": 0,
                "confidence": None
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "text": "",
                "processing_time": 0
            }
    
    def is_available(self) -> bool:
        try:
            import pytesseract
            result = subprocess.run(["tesseract", "--version"], 
                                  capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except:
            return False

# 利用可能なOCRエンジンを取得
def get_available_engines() -> List[OCREngine]:
    """利用可能なOCRエンジンのリストを返す"""
    engines = [
        OCRMyPDFEngine(),
        PaddleOCREngine(),
        EasyOCREngine(),
        TesseractEngine()
    ]
    
    return [engine for engine in engines if engine.is_available()]

def get_engine_by_name(name: str) -> OCREngine:
    """名前でOCRエンジンを取得"""
    engines = get_available_engines()
    for engine in engines:
        if engine.name == name:
            return engine
    raise ValueError(f"OCRエンジン '{name}' が見つかりません")