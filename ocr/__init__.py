# ocr/__init__.py
from .spellcheck import correct_text
from .ocr_process import run_ocr
from .orientation_corrector import correct_orientation, detect_rotation_angle
