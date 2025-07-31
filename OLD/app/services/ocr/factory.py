# app/services/ocr/factory.py
# OCRエンジンファクトリ

from typing import Dict, List, Optional
from .base import OCREngine
from .engines import OCRMyPDFEngine, TesseractEngine, EasyOCREngine, PaddleOCREngine
from .settings import OCRSettingsManager

class OCREngineFactory:
    """OCRエンジンの作成と管理"""
    
    def __init__(self):
        self.settings_manager = OCRSettingsManager()
        self._engines = {
            'ocrmypdf': OCRMyPDFEngine,
            'tesseract': TesseractEngine,
            'easyocr': EasyOCREngine,
            'paddleocr': PaddleOCREngine
        }
    
    def get_available_engines(self) -> Dict[str, Dict[str, any]]:
        """利用可能なエンジンの一覧を取得"""
        available = {}
        for engine_id, engine_class in self._engines.items():
            engine = engine_class()
            available[engine_id] = {
                'name': engine.name,
                'available': engine.is_available(),
                'parameters': engine.get_parameters()
            }
        return available
    
    def create_engine(self, engine_id: str) -> Optional[OCREngine]:
        """指定されたIDのエンジンを作成"""
        if engine_id not in self._engines:
            return None
        
        engine_class = self._engines[engine_id]
        return engine_class()
    
    def get_default_engine(self) -> OCREngine:
        """デフォルトエンジンを取得"""
        default_id = self.settings_manager.get_default_engine()
        engine = self.create_engine(default_id)
        
        if engine is None or not engine.is_available():
            # デフォルトが利用できない場合、利用可能な最初のエンジンを使用
            for engine_id, engine_class in self._engines.items():
                engine = engine_class()
                if engine.is_available():
                    return engine
            
            # どのエンジンも利用できない場合はOCRMyPDFを返す（エラーハンドリングは呼び出し側で）
            return OCRMyPDFEngine()
        
        return engine
    
    def process_with_settings(self, engine_id: str, pdf_path: str, page_num: int = 0, custom_params: Optional[Dict] = None) -> Dict:
        """設定を適用してOCR処理を実行"""
        engine = self.create_engine(engine_id)
        if engine is None:
            return {
                "success": False,
                "error": f"エンジン '{engine_id}' が見つかりません",
                "text": "",
                "processing_time": 0,
                "confidence": None
            }
        
        if not engine.is_available():
            return {
                "success": False,
                "error": f"エンジン '{engine_id}' が利用できません",
                "text": "",
                "processing_time": 0,
                "confidence": None
            }
        
        # 保存された設定を取得
        saved_settings = self.settings_manager.get_engine_settings(engine_id)
        
        # カスタムパラメータがある場合はマージ
        if custom_params:
            saved_settings.update(custom_params)
        
        return engine.process(pdf_path, page_num, **saved_settings)
    
    def register_engine(self, engine_id: str, engine_class):
        """新しいエンジンを登録"""
        self._engines[engine_id] = engine_class
    
    def get_engine_settings(self, engine_id: str) -> Dict:
        """エンジンの現在の設定を取得"""
        return self.settings_manager.get_engine_settings(engine_id)
    
    def update_engine_settings(self, engine_id: str, settings: Dict):
        """エンジンの設定を更新"""
        self.settings_manager.update_engine_settings(engine_id, settings)
    
    def get_presets(self) -> Dict:
        """プリセット一覧を取得"""
        return self.settings_manager.load_presets()
    
    def save_preset(self, preset_name: str, engine_id: str, settings: Dict):
        """プリセットを保存"""
        self.settings_manager.save_preset(preset_name, engine_id, settings)
    
    def load_preset(self, preset_name: str) -> Optional[Dict]:
        """プリセットを読み込み"""
        presets = self.settings_manager.load_presets()
        return presets.get(preset_name)
    
    def delete_preset(self, preset_name: str):
        """プリセットを削除"""
        self.settings_manager.delete_preset(preset_name)