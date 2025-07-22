# app/services/ingest/settings.py
# Ingest機能の設定管理

import json
from pathlib import Path
from typing import Dict, Any, List

class IngestSettingsManager:
    """Ingest機能の設定管理"""
    
    def __init__(self, settings_dir: str = "ocr/settings"):
        self.settings_dir = Path(settings_dir)
        self.settings_dir.mkdir(parents=True, exist_ok=True)
        self.ingest_settings_file = self.settings_dir / "ingest_settings.json"
        
        # デフォルト設定
        self.default_settings = {
            "ocr": {
                "default_engine": "easyocr",
                "batch_processing": {
                    "max_concurrent": 3,
                    "timeout_per_page": 60,
                    "retry_count": 2
                }
            },
            "processing": {
                "chunk_size": 500,
                "overlap_size": 50,
                "quality_threshold": 0.7,
                "llm_timeout_sec": 300
            },
            "ui": {
                "show_ocr_progress": True,
                "show_llm_prompts": False,
                "auto_scroll": True
            }
        }
        
        self._ensure_settings_file()
    
    def _ensure_settings_file(self):
        """設定ファイルが存在しない場合は作成"""
        if not self.ingest_settings_file.exists():
            self.save_settings(self.default_settings)
    
    def load_settings(self) -> Dict[str, Any]:
        """設定を読み込み"""
        try:
            with open(self.ingest_settings_file, 'r', encoding='utf-8') as f:
                settings = json.load(f)
            
            # デフォルト設定とマージ
            merged = self._merge_settings(self.default_settings, settings)
            return merged
            
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Ingest設定ファイル読み込みエラー: {e}")
            return self.default_settings.copy()
    
    def save_settings(self, settings: Dict[str, Any]):
        """設定を保存"""
        try:
            with open(self.ingest_settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Ingest設定ファイル保存エラー: {e}")
    
    def get_ocr_settings(self) -> Dict[str, Any]:
        """OCR関連設定を取得"""
        settings = self.load_settings()
        return settings.get("ocr", {})
    
    def update_ocr_settings(self, ocr_settings: Dict[str, Any]):
        """OCR関連設定を更新"""
        settings = self.load_settings()
        settings["ocr"] = ocr_settings
        self.save_settings(settings)
    
    def get_processing_settings(self) -> Dict[str, Any]:
        """処理関連設定を取得"""
        settings = self.load_settings()
        return settings.get("processing", {})
    
    def update_processing_settings(self, processing_settings: Dict[str, Any]):
        """処理関連設定を更新"""
        settings = self.load_settings()
        settings["processing"] = processing_settings
        self.save_settings(settings)
    
    def get_ui_settings(self) -> Dict[str, Any]:
        """UI関連設定を取得"""
        settings = self.load_settings()
        return settings.get("ui", {})
    
    def update_ui_settings(self, ui_settings: Dict[str, Any]):
        """UI関連設定を更新"""
        settings = self.load_settings()
        settings["ui"] = ui_settings
        self.save_settings(settings)
    
    def get_default_ocr_engine(self) -> str:
        """デフォルトOCRエンジンを取得"""
        ocr_settings = self.get_ocr_settings()
        return ocr_settings.get("default_engine", "ocrmypdf")
    
    def set_default_ocr_engine(self, engine_id: str):
        """デフォルトOCRエンジンを設定"""
        ocr_settings = self.get_ocr_settings()
        ocr_settings["default_engine"] = engine_id
        self.update_ocr_settings(ocr_settings)
    
    def _merge_settings(self, default: Dict[str, Any], user: Dict[str, Any]) -> Dict[str, Any]:
        """設定をマージ（ユーザー設定を優先）"""
        result = default.copy()
        for key, value in user.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_settings(result[key], value)
            else:
                result[key] = value
        return result