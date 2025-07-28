# app/routes/dict_editor.py
# OCR辞書編集用API

from fastapi import APIRouter, HTTPException, Form, Request
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
import os
import csv
from typing import List, Dict, Any
import shutil
from datetime import datetime

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/edit", response_class=HTMLResponse)
async def dict_editor_page(request: Request):
    """OCR辞書編集ページを表示"""
    return templates.TemplateResponse("dict_editor.html", {
        "request": request
    })

# 辞書ファイルの定義
DICT_FILES = {
    "一般用語": {
        "file": "ocr/dic/known_words_common.csv",
        "description": "契約書、請求書などの一般的な業務用語",
        "type": "single_column",
        "header": "common_word"
    },
    "専門用語": {
        "file": "ocr/dic/known_words_custom.csv", 
        "description": "航宇、熱交などの専門用語・略語",
        "type": "single_column",
        "header": "custom_word"
    },
    "誤字修正": {
        "file": "ocr/dic/ocr_word_mistakes.csv",
        "description": "OCRでよく発生する誤字とその修正",
        "type": "two_column",
        "headers": ["wrong", "correct"]
    },
    "形態素辞書": {
        "file": "ocr/dic/user_dict.csv",
        "description": "MeCab用のユーザー辞書（高度な設定）",
        "type": "mecab_dict",
        "headers": ["表層形", "左文脈ID", "右文脈ID", "コスト", "品詞1", "品詞2", "品詞3", "品詞4", "活用形", "活用型", "原形", "読み", "発音"]
    }
}

@router.get("/api/dict/list")
async def get_dict_list():
    """辞書ファイル一覧を取得"""
    result = []
    for name, config in DICT_FILES.items():
        file_path = config["file"]
        try:
            # ファイルサイズと更新日時を取得
            if os.path.exists(file_path):
                stat = os.stat(file_path)
                size = stat.st_size
                modified = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M")
                
                # エントリ数をカウント
                with open(file_path, 'r', encoding='utf-8') as f:
                    reader = csv.reader(f)
                    rows = list(reader)
                    # ヘッダーを除いたエントリ数
                    entry_count = max(0, len(rows) - 1) if rows else 0
            else:
                size = 0
                modified = "未作成"
                entry_count = 0
                
            result.append({
                "name": name,
                "description": config["description"],
                "type": config["type"],
                "file_path": file_path,
                "size": size,
                "modified": modified,
                "entry_count": entry_count
            })
        except Exception as e:
            result.append({
                "name": name,
                "description": config["description"],
                "type": config["type"],
                "file_path": file_path,
                "size": 0,
                "modified": f"エラー: {str(e)}",
                "entry_count": 0
            })
    
    return result

@router.get("/api/dict/content/{dict_name}")
async def get_dict_content(dict_name: str):
    """指定された辞書の内容を取得"""
    if dict_name not in DICT_FILES:
        raise HTTPException(status_code=404, detail="辞書が見つかりません")
    
    config = DICT_FILES[dict_name]
    file_path = config["file"]
    
    try:
        if not os.path.exists(file_path):
            # ファイルが存在しない場合は空の構造を返す
            return {
                "name": dict_name,
                "type": config["type"],
                "headers": config.get("headers", [config.get("header", "")]),
                "data": []
            }
        
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            rows = list(reader)
        
        # ヘッダーとデータを分離
        if rows:
            headers = rows[0] if rows else []
            data = rows[1:] if len(rows) > 1 else []
        else:
            headers = config.get("headers", [config.get("header", "")])
            data = []
        
        return {
            "name": dict_name,
            "type": config["type"],
            "headers": headers,
            "data": data
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ファイル読み込みエラー: {str(e)}")

@router.post("/api/dict/save/{dict_name}")
async def save_dict_content(dict_name: str, content: str = Form(...)):
    """辞書内容を保存"""
    if dict_name not in DICT_FILES:
        raise HTTPException(status_code=404, detail="辞書が見つかりません")
    
    config = DICT_FILES[dict_name]
    file_path = config["file"]
    
    try:
        # バックアップを作成
        if os.path.exists(file_path):
            # バックアップファイルはocr/dic/back/に保存
            backup_dir = "ocr/dic/back"
            os.makedirs(backup_dir, exist_ok=True)
            filename = os.path.basename(file_path)
            backup_filename = f"{filename}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            backup_path = os.path.join(backup_dir, backup_filename)
            shutil.copy2(file_path, backup_path)
        
        # ディレクトリが存在しない場合は作成
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # 内容を保存
        with open(file_path, 'w', encoding='utf-8', newline='') as f:
            f.write(content)
        
        return {"success": True, "message": "保存しました"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"保存エラー: {str(e)}")

@router.post("/api/dict/add_entry/{dict_name}")
async def add_dict_entry(
    dict_name: str,
    entry_data: str = Form(...),
    description: str = Form("")
):
    """辞書にエントリを追加（ingest/OCR中からの呼び出し用）"""
    if dict_name not in DICT_FILES:
        raise HTTPException(status_code=404, detail="辞書が見つかりません")
    
    config = DICT_FILES[dict_name]
    file_path = config["file"]
    
    try:
        # ファイルが存在しない場合は作成
        if not os.path.exists(file_path):
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, 'w', encoding='utf-8', newline='') as f:
                writer = csv.writer(f)
                if config["type"] == "single_column":
                    writer.writerow([config["header"]])
                elif config["type"] == "two_column":
                    writer.writerow(config["headers"])
        
        # エントリを追加
        with open(file_path, 'a', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            if config["type"] == "single_column":
                writer.writerow([entry_data])
            elif config["type"] == "two_column":
                # entry_dataは "誤字,正字" の形式を想定
                parts = entry_data.split(',', 1)
                if len(parts) == 2:
                    writer.writerow([parts[0].strip(), parts[1].strip()])
                else:
                    raise ValueError("誤字修正は '誤字,正字' の形式で入力してください")
        
        return {"success": True, "message": "エントリを追加しました"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"追加エラー: {str(e)}")