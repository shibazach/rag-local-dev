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

@router.post("/presets/{engine_id}")
async def save_preset(engine_id: str, preset: PresetData):
    """プリセットを保存"""
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