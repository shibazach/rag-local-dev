"""
OCRエンジン統合ファクトリ - 調整・本番両用設計
4つのOCRエンジン（EasyOCR, Tesseract, PaddleOCR, OCRMyPDF）を統一インターフェースで提供
"""

import os
import tempfile
import subprocess
import fitz  # PyMuPDF
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any, Optional, List, Union
from datetime import datetime

from app.config import config, logger
from .spellcheck import get_spell_checker
from .bert_corrector import get_bert_corrector

# OCRエンジンの抽象基底クラス
class OCREngine(ABC):
    """OCRエンジンの基底クラス"""
    
    def __init__(self, engine_name: str):
        self.engine_name = engine_name
        self.spell_checker = None
        self.bert_corrector = None
    
    @abstractmethod
    def extract_text(self, pdf_path: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        PDFからテキストを抽出
        
        Args:
            pdf_path: PDFファイルパス
            parameters: エンジン固有パラメータ
            
        Returns:
            抽出結果辞書
        """
        pass
    
    def apply_spell_correction(self, text: str, enable_spell_correction: bool = True) -> Tuple[str, List[Dict[str, Any]]]:
        """
        誤字修正適用
        
        Args:
            text: 元テキスト
            enable_spell_correction: 誤字修正有効フラグ
            
        Returns:
            (修正後テキスト, 修正箇所リスト)
        """
        if not enable_spell_correction:
            return text, []
        
        corrections = []
        
        # スペルチェッカーによる辞書ベース修正
        if self.spell_checker is None:
            self.spell_checker = get_spell_checker()
        
        corrected_text = self.spell_checker.correct_text(text)
        
        # 修正箇所を検出して記録（簡易版）
        if corrected_text != text:
            corrections.append({
                "type": "dictionary",
                "original": text,
                "corrected": corrected_text,
                "changes": "辞書ベース修正"
            })
        
        return corrected_text, corrections
    
    def get_page_count(self, pdf_path: str) -> int:
        """PDFページ数を取得"""
        try:
            doc = fitz.open(pdf_path)
            count = len(doc)
            doc.close()
            return count
        except Exception as e:
            logger.error(f"PDF ページ数取得エラー: {e}")
            return 1


class EasyOCREngine(OCREngine):
    """EasyOCR エンジン"""
    
    def __init__(self):
        super().__init__("EasyOCR")
    
    def extract_text(self, pdf_path: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        try:
            import easyocr
            
            # パラメータ取得
            languages = parameters.get("languages", ["ja", "en"])
            gpu = parameters.get("gpu", True)
            width_ths = parameters.get("width_ths", 0.7)
            height_ths = parameters.get("height_ths", 0.7)
            
            # EasyOCR Reader 初期化
            reader = easyocr.Reader(languages, gpu=gpu)
            
            # PDF → 画像変換してOCR実行
            doc = fitz.open(pdf_path)
            all_text = []
            
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                
                # 画像化（DPI=300で高品質）
                zoom = 300 / 72
                mat = fitz.Matrix(zoom, zoom)
                pix = page.get_pixmap(matrix=mat)
                img_data = pix.tobytes("png")
                
                # EasyOCR実行
                results = reader.readtext(
                    img_data,
                    width_ths=width_ths,
                    height_ths=height_ths,
                    detail=0  # テキストのみ取得
                )
                
                page_text = "\n".join(results)
                all_text.append(f"=== ページ {page_num + 1} ===\n{page_text}")
            
            doc.close()
            combined_text = "\n\n".join(all_text)
            
            return {
                "status": "success",
                "text": combined_text,
                "engine": self.engine_name,
                "page_count": len(all_text),
                "parameters": parameters
            }
            
        except Exception as e:
            logger.error(f"EasyOCR エラー: {e}")
            return {
                "status": "error",
                "error": str(e),
                "engine": self.engine_name
            }


class TesseractEngine(OCREngine):
    """Tesseract エンジン"""
    
    def __init__(self):
        super().__init__("Tesseract")
    
    def extract_text(self, pdf_path: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        try:
            import pytesseract
            from PIL import Image
            from io import BytesIO
            
            # パラメータ取得
            lang = parameters.get("language", "jpn+eng")
            dpi = parameters.get("dpi", 300)
            psm = parameters.get("psm", 3)
            oem = parameters.get("oem", 3)
            
            # Tesseract設定
            config_str = f"--dpi {dpi} --psm {psm} --oem {oem}"
            
            # PDF → 画像変換してOCR実行
            doc = fitz.open(pdf_path)
            all_text = []
            
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                
                # 画像化
                zoom = dpi / 72
                mat = fitz.Matrix(zoom, zoom)
                pix = page.get_pixmap(matrix=mat)
                img_data = pix.tobytes("png")
                
                # PIL Image に変換
                image = Image.open(BytesIO(img_data))
                
                # Tesseract実行
                text = pytesseract.image_to_string(
                    image,
                    lang=lang,
                    config=config_str
                )
                
                all_text.append(f"=== ページ {page_num + 1} ===\n{text.strip()}")
            
            doc.close()
            combined_text = "\n\n".join(all_text)
            
            return {
                "status": "success",
                "text": combined_text,
                "engine": self.engine_name,
                "page_count": len(all_text),
                "parameters": parameters
            }
            
        except Exception as e:
            logger.error(f"Tesseract エラー: {e}")
            return {
                "status": "error",
                "error": str(e),
                "engine": self.engine_name
            }


class PaddleOCREngine(OCREngine):
    """PaddleOCR エンジン"""
    
    def __init__(self):
        super().__init__("PaddleOCR")
    
    def extract_text(self, pdf_path: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        try:
            from paddleocr import PaddleOCR
            import numpy as np
            from PIL import Image
            from io import BytesIO
            
            # パラメータ取得
            lang = parameters.get("lang", "japan")
            use_gpu = parameters.get("use_gpu", True)
            det = parameters.get("det", True)
            rec = parameters.get("rec", True)
            cls = parameters.get("cls", True)
            
            # PaddleOCR 初期化
            ocr = PaddleOCR(
                lang=lang,
                use_gpu=use_gpu,
                det=det,
                rec=rec,
                cls=cls
            )
            
            # PDF → 画像変換してOCR実行
            doc = fitz.open(pdf_path)
            all_text = []
            
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                
                # 画像化
                zoom = 300 / 72
                mat = fitz.Matrix(zoom, zoom)
                pix = page.get_pixmap(matrix=mat)
                img_data = pix.tobytes("png")
                
                # numpy array に変換
                image = Image.open(BytesIO(img_data))
                img_array = np.array(image)
                
                # PaddleOCR実行
                results = ocr.ocr(img_array)
                
                # 結果からテキストを抽出
                page_text = []
                if results and results[0]:
                    for line in results[0]:
                        if len(line) >= 2:
                            text = line[1][0]  # 認識テキスト
                            page_text.append(text)
                
                all_text.append(f"=== ページ {page_num + 1} ===\n" + "\n".join(page_text))
            
            doc.close()
            combined_text = "\n\n".join(all_text)
            
            return {
                "status": "success",
                "text": combined_text,
                "engine": self.engine_name,
                "page_count": len(all_text),
                "parameters": parameters
            }
            
        except Exception as e:
            logger.error(f"PaddleOCR エラー: {e}")
            return {
                "status": "error",
                "error": str(e),
                "engine": self.engine_name
            }


class OCRMyPDFEngine(OCREngine):
    """OCRMyPDF エンジン（既存実装ベース）"""
    
    def __init__(self):
        super().__init__("OCRMyPDF")
    
    def extract_text(self, pdf_path: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        try:
            # パラメータ取得
            language = parameters.get("language", config.OCR_LANGUAGE)
            dpi = parameters.get("dpi", config.OCR_DPI)
            optimize_level = parameters.get("optimize", config.OCR_OPTIMIZE)
            force_ocr = parameters.get("force_ocr", True)
            
            # 一時出力ファイル作成
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_out:
                temp_output_path = temp_out.name
            
            try:
                # OCRMyPDF コマンド構築
                cmd = ["ocrmypdf"]
                if force_ocr:
                    cmd.append("--force-ocr")
                cmd.extend([
                    "-l", language,
                    "--dpi", str(dpi),
                    "--optimize", str(optimize_level),
                    pdf_path,
                    temp_output_path
                ])
                
                # OCR実行
                result = subprocess.run(
                    cmd,
                    check=True,
                    capture_output=True,
                    text=True,
                    timeout=300  # 5分タイムアウト
                )
                
                # テキスト抽出
                doc = fitz.open(temp_output_path)
                all_text = []
                
                for page_num in range(len(doc)):
                    page = doc.load_page(page_num)
                    text = page.get_text()
                    all_text.append(f"=== ページ {page_num + 1} ===\n{text.strip()}")
                
                doc.close()
                combined_text = "\n\n".join(all_text)
                
                return {
                    "status": "success",
                    "text": combined_text,
                    "engine": self.engine_name,
                    "page_count": len(all_text),
                    "parameters": parameters
                }
                
            finally:
                # 一時ファイルクリーンアップ
                if os.path.exists(temp_output_path):
                    os.unlink(temp_output_path)
                    
        except subprocess.TimeoutExpired:
            logger.error("OCRMyPDF タイムアウト")
            return {
                "status": "error",
                "error": "処理がタイムアウトしました",
                "engine": self.engine_name
            }
        except subprocess.CalledProcessError as e:
            logger.error(f"OCRMyPDF エラー: {e.stderr}")
            return {
                "status": "error",
                "error": f"OCR処理エラー: {e.stderr}",
                "engine": self.engine_name
            }
        except Exception as e:
            logger.error(f"OCRMyPDF 予期しないエラー: {e}")
            return {
                "status": "error",
                "error": str(e),
                "engine": self.engine_name
            }


class OCREngineFactory:
    """OCRエンジンファクトリ"""
    
    _engines = {
        "EasyOCR": EasyOCREngine,
        "Tesseract": TesseractEngine,
        "PaddleOCR": PaddleOCREngine,
        "OCRMyPDF": OCRMyPDFEngine
    }
    
    @classmethod
    def get_engine(cls, engine_name: str) -> OCREngine:
        """指定されたOCRエンジンのインスタンスを取得"""
        if engine_name not in cls._engines:
            raise ValueError(f"未対応のOCRエンジン: {engine_name}")
        
        return cls._engines[engine_name]()
    
    @classmethod
    def get_available_engines(cls) -> List[str]:
        """利用可能なOCRエンジン一覧を取得"""
        return list(cls._engines.keys())


class OCRService:
    """OCR統合サービス（メインインターフェース）"""
    
    def __init__(self):
        self.factory = OCREngineFactory()
    
    def process_pdf(
        self,
        blob_data: bytes,
        engine_name: str,
        parameters: Dict[str, Any],
        enable_spell_correction: bool = True,
        page_range: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        PDFのOCR処理を実行
        
        Args:
            blob_data: PDFバイナリデータ
            engine_name: OCRエンジン名
            parameters: エンジン固有パラメータ
            enable_spell_correction: 誤字修正フラグ
            page_range: 処理ページ範囲（"1-3" or "all"）
            
        Returns:
            処理結果辞書
        """
        temp_pdf_path = None
        
        try:
            # 一時PDFファイル作成
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_file:
                temp_pdf_path = temp_file.name
                temp_file.write(blob_data)
            
            # OCRエンジン取得
            engine = self.factory.get_engine(engine_name)
            
            # OCR実行
            ocr_result = engine.extract_text(temp_pdf_path, parameters)
            
            if ocr_result["status"] != "success":
                return ocr_result
            
            # 誤字修正適用
            original_text = ocr_result["text"]
            corrected_text, corrections = engine.apply_spell_correction(
                original_text, enable_spell_correction
            )
            
            # 結果をまとめる
            return {
                "status": "success",
                "engine": engine_name,
                "original_text": original_text,
                "corrected_text": corrected_text,
                "corrections": corrections,
                "page_count": ocr_result.get("page_count", 1),
                "parameters": parameters,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"OCR処理エラー: {e}")
            return {
                "status": "error",
                "error": str(e),
                "engine": engine_name,
                "timestamp": datetime.now().isoformat()
            }
        
        finally:
            # 一時ファイルクリーンアップ
            if temp_pdf_path and os.path.exists(temp_pdf_path):
                os.unlink(temp_pdf_path)


# サービスインスタンス作成ヘルパー
def get_ocr_service() -> OCRService:
    """OCR統合サービスインスタンス取得"""
    return OCRService()


if __name__ == "__main__":
    """簡易テスト用"""
    service = get_ocr_service()
    print("利用可能なOCRエンジン:", OCREngineFactory.get_available_engines())
    
    # テストPDFがある場合の処理例
    # with open("test.pdf", "rb") as f:
    #     result = service.process_pdf(
    #         blob_data=f.read(),
    #         engine_name="OCRMyPDF",
    #         parameters={"language": "jpn+eng", "dpi": 300},
    #         enable_spell_correction=True
    #     )
    #     print("OCR結果:", result)
