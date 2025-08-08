"""
画像向き補正サービス - Prototype統合版
Tesseractを使用した画像の向き検出と補正
"""

import fitz  # PyMuPDF
import pytesseract
from PIL import Image
from io import BytesIO
from typing import Optional, Tuple

from app.config import config, logger

class OrientationCorrector:
    """画像向き補正サービス"""
    
    def __init__(self):
        self.ocr_language = config.OCR_LANGUAGE
        self.ocr_dpi = config.OCR_DPI
    
    def pdf_page_to_image(self, page, dpi: int = None) -> Image.Image:
        """
        PDFページを指定DPIで画像化し、PIL Imageで返却
        
        Args:
            page: PyMuPDFページオブジェクト
            dpi: 解像度（省略時は設定値を使用）
            
        Returns:
            PIL Image object
        """
        if dpi is None:
            dpi = self.ocr_dpi
            
        zoom = dpi / 72
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat)
        img_data = pix.tobytes("png")
        return Image.open(BytesIO(img_data))
    
    def detect_rotation_angle(self, image: Image.Image, dpi: int = None) -> int:
        """
        画像の向き検出を行い、回転角度（0, 90, 180, 270）を返却。
        失敗時は0°としてフォールバック。
        
        Args:
            image: PIL Image object
            dpi: 解像度（省略時は設定値を使用）
            
        Returns:
            回転角度（0, 90, 180, 270）
        """
        if dpi is None:
            dpi = self.ocr_dpi
            
        try:
            # 解像度を指定してOSDを実行
            config_str = f"-l {self.ocr_language} --dpi {dpi}"
            osd = pytesseract.image_to_osd(image, config=config_str)
            
            for line in osd.splitlines():
                if line.startswith("Rotate:"):
                    angle = int(line.split(":")[1].strip())
                    logger.debug(f"向き検出成功: {angle}°")
                    return angle
                    
        except Exception as e:
            logger.warning(f"向き検出失敗, フォールバック 0°: {e}")
            
        return 0
    
    def correct_orientation(self, image: Image.Image, angle: int) -> Image.Image:
        """
        検出された角度に応じて画像を回転補正
        
        Args:
            image: PIL Image object
            angle: 回転角度
            
        Returns:
            回転補正されたPIL Image object
        """
        if angle % 360 == 0:
            return image
            
        # 画像を回転（expandで画像全体が収まるように）
        return image.rotate(-angle, expand=True)
    
    def ocr_pdf_with_orientation_correction(
        self,
        pdf_path: str,
        dpi: int = None,
        ocr_lang: str = None
    ) -> str:
        """
        PDFをページ単位で画像化し、向き補正→OCRを実行
        各ページのテキストを結合して返却
        
        Args:
            pdf_path: PDFファイルパス
            dpi: 解像度（省略時は設定値を使用）
            ocr_lang: OCR言語（省略時は設定値を使用）
            
        Returns:
            OCR結果テキスト
        """
        if dpi is None:
            dpi = self.ocr_dpi
        if ocr_lang is None:
            ocr_lang = self.ocr_language
            
        try:
            doc = fitz.open(pdf_path)
            all_text = []
            
            for i, page in enumerate(doc):
                logger.debug(f"📄 ページ {i+1}/{len(doc)} 処理中")
                
                # ページを画像化
                image = self.pdf_page_to_image(page, dpi=dpi)
                
                # 向き検出および補正
                angle = self.detect_rotation_angle(image, dpi=dpi)
                logger.debug(f"🔄 回転角度（補正前）: {angle}°")
                corrected_image = self.correct_orientation(image, angle)
                
                # OCR 実行
                try:
                    text = pytesseract.image_to_string(
                        corrected_image,
                        lang=ocr_lang,
                        config=f"--dpi {dpi}"
                    )
                    all_text.append(text.strip())
                    
                except Exception as e:
                    logger.warning(f"OCR 文字列取得失敗 (ページ {i+1}): {e}")
                    all_text.append("")
            
            return "\n\n".join(all_text)
            
        except Exception as e:
            logger.error(f"PDFのOCR処理エラー: {e}")
            raise
    
    def process_image_orientation(
        self,
        image_path: str,
        output_path: Optional[str] = None
    ) -> Tuple[Image.Image, int]:
        """
        画像ファイルの向きを検出して補正
        
        Args:
            image_path: 入力画像パス
            output_path: 出力画像パス（省略時は補正画像のみ返す）
            
        Returns:
            (補正後画像, 回転角度)のタプル
        """
        try:
            # 画像を開く
            image = Image.open(image_path)
            
            # 向き検出
            angle = self.detect_rotation_angle(image)
            
            # 向き補正
            corrected_image = self.correct_orientation(image, angle)
            
            # 保存（指定された場合）
            if output_path:
                corrected_image.save(output_path)
                logger.info(f"✅ 向き補正画像を保存: {output_path}")
            
            return corrected_image, angle
            
        except Exception as e:
            logger.error(f"画像向き補正エラー: {e}")
            raise

# サービスインスタンス作成ヘルパー
def get_orientation_corrector() -> OrientationCorrector:
    """向き補正サービスインスタンス取得"""
    return OrientationCorrector()