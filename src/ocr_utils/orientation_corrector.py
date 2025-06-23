# src/ocr_utils/orientation_corrector.py
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
from io import BytesIO

from src import bootstrap
from src.error_handler import install_global_exception_handler

# REM: 例外発生時のログをグローバルに記録するハンドラを有効化
install_global_exception_handler()

def pdf_page_to_image(page, dpi=300):
    zoom = dpi / 72
    mat = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat)
    img_data = pix.tobytes("png")
    return Image.open(BytesIO(img_data))

def detect_rotation_angle(image):
    try:
        osd = pytesseract.image_to_osd(image, lang="jpn+eng")
        lines = osd.split("\n")
        for line in lines:
            if line.startswith("Rotate:"):
                rotate = int(line.split(":")[1].strip())
                return rotate  # 0, 90, 180, 270 のいずれか
    except Exception as e:
        print(f"⚠️ 向き検出失敗: {e}")
    return 0  # デフォルトは無回転

def correct_orientation(image, angle):
    if angle == 0:
        return image
    return image.rotate(-angle, expand=True)  # 時計回りに補正

def ocr_pdf_with_orientation_correction(pdf_path):
    doc = fitz.open(pdf_path)
    all_text = []
    for i, page in enumerate(doc):
        print(f"\n📄 Page {i+1}")
        image = pdf_page_to_image(page, dpi=300)
        angle = detect_rotation_angle(image)
        print(f"🔄 回転角度（補正前）: {angle}°")

        corrected_image = correct_orientation(image, angle)
        text = pytesseract.image_to_string(corrected_image, lang="jpn+eng")
        all_text.append(text.strip())

    return "\n\n".join(all_text)