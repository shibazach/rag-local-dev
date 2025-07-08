# src/ocr_utils/orientation_corrector.py

import logging
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
from io import BytesIO

from src import bootstrap
from src.error_handler import install_global_exception_handler

# REM: 例外発生時のログをグローバルに記録するハンドラを有効化
install_global_exception_handler()

# ロガー設定
logger = logging.getLogger(__name__)


def pdf_page_to_image(page, dpi=300):
    """
    PDFページを指定DPIで画像化し、PIL Imageで返却
    """
    zoom = dpi / 72
    mat = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat)
    img_data = pix.tobytes("png")
    return Image.open(BytesIO(img_data))


def detect_rotation_angle(image, dpi=300):
    """
    画像の向き検出を行い、回転角度（0, 90, 180, 270）を返却。
    失敗時は0°としてフォールバック。
    """
    try:
        # 解像度を指定してOSDを実行
        config = f"-l jpn+eng --dpi {dpi}"
        osd = pytesseract.image_to_osd(image, config=config)
        for line in osd.splitlines():
            if line.startswith("Rotate:"):
                angle = int(line.split(":")[1].strip())
                return angle
    except Exception as e:
        logger.warning(f"向き検出失敗, フォールバック 0°: {e}")
    return 0


def correct_orientation(image, angle):
    """
    検出された角度に応じて画像を回転補正
    """
    if angle % 360 == 0:
        return image
    return image.rotate(-angle, expand=True)


def ocr_pdf_with_orientation_correction(pdf_path, dpi=300, ocr_lang="jpn+eng"):
    """
    PDFをページ単位で画像化し、向き補正→OCRを実行
    各ページのテキストを結合して返却
    """
    doc = fitz.open(pdf_path)
    all_text = []
    for i, page in enumerate(doc):
        logger.debug(f"📄 Page {i+1}")
        image = pdf_page_to_image(page, dpi=dpi)

        # 向き検出および補正
        angle = detect_rotation_angle(image, dpi=dpi)
        logger.debug(f"🔄 回転角度（補正前）: {angle}°")
        corrected_image = correct_orientation(image, angle)

        # OCR 実行
        try:
            text = pytesseract.image_to_string(
                corrected_image,
                lang=ocr_lang,
                config=f"--dpi {dpi}"
            )
        except Exception as e:
            logger.warning(f"OCR 文字列取得失敗: {e}")
            text = ""

        all_text.append(text.strip())

    return "\n\n".join(all_text)
