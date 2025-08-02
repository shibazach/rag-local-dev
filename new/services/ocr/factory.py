# new/services/ocr/factory.py
# OCRエンジンファクトリ（新系）

from typing import Dict, List, Optional
import logging
from .base import OCREngine, OCRResult
from .engines.ocrmypdf import OCRMyPDFEngine
from .engines.tesseract import TesseractEngine
from .engines.paddleocr import PaddleOCREngine
from .engines.easyocr import EasyOCREngine

LOGGER = logging.getLogger(__name__)

class OCREngineFactory:
    """OCRエンジンの作成と管理"""
    
    def __init__(self):
        self._engines = {
            'ocrmypdf': OCRMyPDFEngine,
            'tesseract': TesseractEngine,
            'paddleocr': PaddleOCREngine,
            'easyocr': EasyOCREngine,
        }
        self._default_engine_id = 'ocrmypdf'
    
    def get_available_engines(self) -> Dict[str, Dict]:
        """利用可能なエンジンの一覧を取得"""
        available = {}
        for engine_id, engine_class in self._engines.items():
            try:
                engine = engine_class()
                available[engine_id] = {
                    'id': engine_id,
                    'name': engine.name,
                    'available': engine.is_available(),
                    'parameters': engine.get_parameters()
                }
            except Exception as e:
                LOGGER.error(f"エンジン {engine_id} の初期化に失敗: {e}")
                available[engine_id] = {
                    'id': engine_id,
                    'name': f"Unknown ({engine_id})",
                    'available': False,
                    'parameters': {},
                    'error': str(e)
                }
        return available
    
    def create_engine(self, engine_id: str) -> Optional[OCREngine]:
        """指定されたIDのエンジンを作成"""
        if engine_id not in self._engines:
            LOGGER.warning(f"未知のOCRエンジン: {engine_id}")
            return None
        
        try:
            engine_class = self._engines[engine_id]
            return engine_class()
        except Exception as e:
            LOGGER.error(f"OCRエンジン {engine_id} の作成に失敗: {e}")
            return None
    
    def get_default_engine(self) -> OCREngine:
        """デフォルトエンジンを取得"""
        engine = self.create_engine(self._default_engine_id)
        
        if engine is None or not engine.is_available():
            # デフォルトが利用できない場合、利用可能な最初のエンジンを使用
            for engine_id, engine_class in self._engines.items():
                try:
                    engine = engine_class()
                    if engine.is_available():
                        LOGGER.info(f"デフォルトエンジンを {engine_id} に変更")
                        return engine
                except Exception:
                    continue
            
            # どのエンジンも利用できない場合はフォールバック
            LOGGER.warning("利用可能なOCRエンジンがありません")
            return OCRMyPDFEngine()  # エラーハンドリングは呼び出し側で
        
        return engine
    
    def process_file(self, file_path: str, engine_id: str = None, **kwargs) -> OCRResult:
        """設定を適用してOCR処理を実行"""
        if engine_id is None:
            engine = self.get_default_engine()
        else:
            engine = self.create_engine(engine_id)
            if engine is None:
                return OCRResult(
                    success=False,
                    text="",
                    processing_time=0,
                    error=f"エンジン '{engine_id}' が見つかりません"
                )
        
        if not engine.is_available():
            return OCRResult(
                success=False,
                text="",
                processing_time=0,
                error=f"エンジン '{engine.name}' が利用できません"
            )
        
        return engine.process_file(file_path, **kwargs)
    
    def register_engine(self, engine_id: str, engine_class):
        """新しいエンジンを登録"""
        self._engines[engine_id] = engine_class
        LOGGER.info(f"OCRエンジン {engine_id} を登録")