"""
OCRサービスモジュール - Prototype統合版
PDFからのテキスト抽出・補正機能
"""

# 基本OCRサービス（必須）
from .ocr_process import OCRProcessor, get_ocr_processor

# スペルチェッカー（オプショナル依存関係）
try:
    from .spellcheck import SpellChecker, get_spell_checker
except ImportError:
    # フォールバック：ダミー実装
    class SpellChecker:
        def __init__(self, dict_dir=None):
            pass
        def correct_text(self, text, **kwargs):
            return text
        def load_known_words(self, csv_paths):
            return set()
        def load_kanji_mistakes(self, csv_path):
            return {}
    
    def get_spell_checker(dict_dir=None):
        return SpellChecker(dict_dir)

# オプショナル依存関係（エラー時はフォールバック）
try:
    from .orientation_corrector import OrientationCorrector, get_orientation_corrector
except ImportError:
    # フォールバック：ダミー実装
    class OrientationCorrector:
        def __init__(self):
            pass
        def detect_rotation_angle(self, image):
            return 0
        def correct_orientation(self, image, angle):
            return image
    
    def get_orientation_corrector():
        return OrientationCorrector()

try:
    from .bert_corrector import BertCorrector, get_bert_corrector
except ImportError:
    # フォールバック：ダミー実装
    class BertCorrector:
        def __init__(self, model_key="tohoku"):
            pass
        def correct_text(self, text, **kwargs):
            return text
    
    def get_bert_corrector(model_key="tohoku"):
        return BertCorrector(model_key)

__all__ = [
    # OCRメイン処理
    'OCRProcessor',
    'get_ocr_processor',
    # 向き補正
    'OrientationCorrector',
    'get_orientation_corrector',
    # スペルチェック
    'SpellChecker',
    'get_spell_checker',
    # BERT補正
    'BertCorrector',
    'get_bert_corrector'
]