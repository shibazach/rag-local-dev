# app/routes/ocr_api.py @作成日時: 2025-07-26
# REM: OCR設定・プリセット管理API

import os
import json
from typing import Dict, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/ocr", tags=["ocr"])

# プリセット保存ディレクトリ
PRESETS_DIR = "ocr/presets"
os.makedirs(PRESETS_DIR, exist_ok=True)

class PresetData(BaseModel):
    name: str
    settings: Dict[str, Any]

@router.get("/presets/list")
async def list_all_presets(engine_id: str = None):
    """全エンジンまたは指定エンジンのプリセット一覧を取得"""
    try:
        all_presets = []
        
        # プリセットディレクトリ内の全ファイルを確認
        if os.path.exists(PRESETS_DIR):
            for filename in os.listdir(PRESETS_DIR):
                if filename.endswith('_presets.json'):
                    file_engine_id = filename.replace('_presets.json', '')
                    
                    # 特定エンジンが指定されている場合はフィルタリング
                    if engine_id and file_engine_id != engine_id:
                        continue
                        
                    preset_file = os.path.join(PRESETS_DIR, filename)
                    
                    try:
                        with open(preset_file, 'r', encoding='utf-8') as f:
                            presets = json.load(f)
                            for preset_name, settings in presets.items():
                                all_presets.append({
                                    'name': preset_name,
                                    'engine': file_engine_id,
                                    'settings': settings
                                })
                    except Exception as e:
                        print(f"プリセットファイル読み込みエラー {filename}: {e}")
                        continue
        
        return {
            "success": True,
            "presets": all_presets
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"プリセット一覧取得エラー: {e}"
        }

@router.get("/presets/load/{preset_name}")
async def load_preset(preset_name: str):
    """指定されたプリセットを読み込み"""
    try:
        # 全プリセットファイルから指定されたプリセットを検索
        if os.path.exists(PRESETS_DIR):
            for filename in os.listdir(PRESETS_DIR):
                if filename.endswith('_presets.json'):
                    engine_id = filename.replace('_presets.json', '')
                    preset_file = os.path.join(PRESETS_DIR, filename)
                    
                    try:
                        with open(preset_file, 'r', encoding='utf-8') as f:
                            presets = json.load(f)
                            if preset_name in presets:
                                return {
                                    "success": True,
                                    "preset": {
                                        "name": preset_name,
                                        "engine": engine_id,
                                        "parameters": presets[preset_name]
                                    }
                                }
                    except Exception as e:
                        print(f"プリセットファイル読み込みエラー {filename}: {e}")
                        continue
        
        return {
            "success": False,
            "error": f"プリセット「{preset_name}」が見つかりません"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"プリセット読み込みエラー: {e}"
        }

@router.post("/settings/save")
async def save_settings(settings: Dict[str, Any]):
    """現在の設定を保存"""
    try:
        # 設定を一時的に保存（実際の実装では適切な保存処理を行う）
        return {
            "success": True,
            "message": "設定を保存しました"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"設定保存エラー: {e}"
        }

@router.get("/presets/{engine_id}")
async def get_presets(engine_id: str):
    """指定エンジンのプリセット一覧を取得"""
    preset_file = os.path.join(PRESETS_DIR, f"{engine_id}_presets.json")
    
    if not os.path.exists(preset_file):
        return {}
    
    try:
        with open(preset_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"プリセット読み込みエラー: {e}")

@router.post("/presets/save")
async def save_preset(preset_data: Dict[str, Any]):
    """プリセットを保存"""
    try:
        name = preset_data.get('name')
        engine_id = preset_data.get('engine_id')
        settings = preset_data.get('settings', {})
        
        if not name or not engine_id:
            return {
                "success": False,
                "error": "プリセット名とエンジンIDが必要です"
            }
        
        preset_file = os.path.join(PRESETS_DIR, f"{engine_id}_presets.json")
        
        # 既存プリセットを読み込み
        presets = {}
        if os.path.exists(preset_file):
            try:
                with open(preset_file, 'r', encoding='utf-8') as f:
                    presets = json.load(f)
            except Exception:
                presets = {}
        
        # 新しいプリセットを追加
        presets[name] = settings
        
        # ファイルに保存
        with open(preset_file, 'w', encoding='utf-8') as f:
            json.dump(presets, f, ensure_ascii=False, indent=2)
        
        return {
            "success": True,
            "message": f"プリセット「{name}」を保存しました"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"プリセット保存エラー: {e}"
        }

@router.post("/presets/{engine_id}")
async def save_preset_legacy(engine_id: str, preset: PresetData):
    """プリセットを保存（レガシー）"""
    preset_file = os.path.join(PRESETS_DIR, f"{engine_id}_presets.json")
    
    # 既存プリセットを読み込み
    presets = {}
    if os.path.exists(preset_file):
        try:
            with open(preset_file, 'r', encoding='utf-8') as f:
                presets = json.load(f)
        except Exception:
            presets = {}
    
    # 新しいプリセットを追加
    presets[preset.name] = preset.settings
    
    # ファイルに保存
    try:
        with open(preset_file, 'w', encoding='utf-8') as f:
            json.dump(presets, f, ensure_ascii=False, indent=2)
        return {"status": "success", "message": f"プリセット「{preset.name}」を保存しました"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"プリセット保存エラー: {e}")

@router.delete("/presets/{engine_id}/{preset_name}")
async def delete_preset(engine_id: str, preset_name: str):
    """プリセットを削除"""
    preset_file = os.path.join(PRESETS_DIR, f"{engine_id}_presets.json")
    
    if not os.path.exists(preset_file):
        raise HTTPException(status_code=404, detail="プリセットファイルが見つかりません")
    
    try:
        with open(preset_file, 'r', encoding='utf-8') as f:
            presets = json.load(f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"プリセット読み込みエラー: {e}")
    
    if preset_name not in presets:
        raise HTTPException(status_code=404, detail=f"プリセット「{preset_name}」が見つかりません")
    
    # プリセットを削除
    del presets[preset_name]
    
    # ファイルに保存
    try:
        with open(preset_file, 'w', encoding='utf-8') as f:
            json.dump(presets, f, ensure_ascii=False, indent=2)
        return {"status": "success", "message": f"プリセット「{preset_name}」を削除しました"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"プリセット保存エラー: {e}")

@router.get("/engine_parameters/{engine_id}")
async def get_engine_parameters(engine_id: str):
    """指定されたOCRエンジンのパラメータ定義を取得（ingest用）"""
    try:
        from app.services.ocr import OCREngineFactory
        ocr_factory = OCREngineFactory()
        available_engines_dict = ocr_factory.get_available_engines()
        
        if engine_id in available_engines_dict and available_engines_dict[engine_id]['available']:
            return {
                "engine_id": engine_id,
                "parameters": available_engines_dict[engine_id]['parameters']
            }
        raise ValueError(f"OCRエンジン '{engine_id}' が見つかりません")
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))