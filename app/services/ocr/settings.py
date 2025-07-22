# app/services/ocr/settings.py
# OCR設定管理

import os
import json
from typing import Dict, Any, Optional
from pathlib import Path

class OCRSettingsManager:
    """OCR設定の保存・読み込み管理"""
    
    def __init__(self, settings_dir: str = "ocr/settings"):
        self.settings_dir = Path(settings_dir)
        self.settings_dir.mkdir(parents=True, exist_ok=True)
        self.settings_file = self.settings_dir / "ocr_settings.json"
        self.presets_file = self.settings_dir / "ocr_presets.json"
        
        # デフォルト設定
        self.default_settings = {
            "default_engine": "ocrmypdf",
            "engines": {
                "ocrmypdf": {
                    "deskew": False,
                    "rotate_pages": False,
                    "remove_background": False,
                    "clean": False,
                    "oversample": 300
                },
                "tesseract": {
                    "psm": 6,
                    "oem": 3,
                    "lang": "jpn+eng"
                },
                "easyocr": {
                    "languages": ["ja", "en"],
                    "use_gpu": False,
                    "zoom_factor": 2.0,
                    "detail": 1,
                    "paragraph": False
                },
                "paddleocr": {
                    "lang": "japan",
                    "use_gpu": False,
                    "zoom_factor": 2.0,
                    "use_angle_cls": True,
                    "use_detection": True,
                    "use_recognition": True,
                    "use_classification": True,
                    "show_log": False
                }
            },
            "global": {
                "timeout": 300,
                "max_retries": 3
            }
        }
        
        # 初期化時に設定ファイルを作成
        self._ensure_settings_file()
    
    def _ensure_settings_file(self):
        """設定ファイルが存在しない場合は作成"""
        if not self.settings_file.exists():
            self.save_settings(self.default_settings)
    
    def load_settings(self) -> Dict[str, Any]:
        """設定を読み込み"""
        try:
            with open(self.settings_file, 'r', encoding='utf-8') as f:
                settings = json.load(f)
            
            # デフォルト設定とマージ
            merged = self._merge_settings(self.default_settings, settings)
            return merged
            
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"設定ファイル読み込みエラー: {e}")
            return self.default_settings.copy()
    
    def save_settings(self, settings: Dict[str, Any]):
        """設定を保存"""
        try:
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"設定ファイル保存エラー: {e}")
    
    def get_engine_settings(self, engine_name: str) -> Dict[str, Any]:
        """指定エンジンの設定を取得"""
        settings = self.load_settings()
        return settings.get("engines", {}).get(engine_name, {})
    
    def update_engine_settings(self, engine_name: str, engine_settings: Dict[str, Any]):
        """指定エンジンの設定を更新"""
        settings = self.load_settings()
        if "engines" not in settings:
            settings["engines"] = {}
        settings["engines"][engine_name] = engine_settings
        self.save_settings(settings)
    
    def get_default_engine(self) -> str:
        """デフォルトエンジン名を取得"""
        settings = self.load_settings()
        return settings.get("default_engine", "ocrmypdf")
    
    def set_default_engine(self, engine_name: str):
        """デフォルトエンジンを設定"""
        settings = self.load_settings()
        settings["default_engine"] = engine_name
        self.save_settings(settings)
    
    def load_presets(self) -> Dict[str, Dict[str, Any]]:
        """プリセット設定を読み込み"""
        try:
            with open(self.presets_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}
    
    def save_preset(self, preset_name: str, engine_name: str, settings: Dict[str, Any]):
        """プリセット設定を保存"""
        presets = self.load_presets()
        presets[preset_name] = {
            "engine": engine_name,
            "settings": settings,
            "created_at": self._get_timestamp()
        }
        
        try:
            with open(self.presets_file, 'w', encoding='utf-8') as f:
                json.dump(presets, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"プリセット保存エラー: {e}")
    
    def delete_preset(self, preset_name: str):
        """プリセット設定を削除"""
        presets = self.load_presets()
        if preset_name in presets:
            del presets[preset_name]
            try:
                with open(self.presets_file, 'w', encoding='utf-8') as f:
                    json.dump(presets, f, indent=2, ensure_ascii=False)
            except Exception as e:
                print(f"プリセット削除エラー: {e}")
    
    def _merge_settings(self, default: Dict[str, Any], user: Dict[str, Any]) -> Dict[str, Any]:
        """設定をマージ（ユーザー設定を優先）"""
        result = default.copy()
        for key, value in user.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_settings(result[key], value)
            else:
                result[key] = value
        return result
    
    def _get_timestamp(self) -> str:
        """現在のタイムスタンプを取得"""
        from datetime import datetime
        return datetime.now().isoformat()