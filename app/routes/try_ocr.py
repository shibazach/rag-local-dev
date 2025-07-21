# app/routes/try_ocr.py
# OCR比較用ルート

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from starlette.requests import Request
import os
import tempfile
import time
import csv
import re
from typing import List, Dict, Tuple

from app.try_ocr.ocr_engines import get_available_engines, get_engine_by_name
from db.handler import get_all_files

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/try_ocr", response_class=HTMLResponse)
async def try_ocr_page(request: Request):
    """OCR比較ページ"""
    # 利用可能なOCRエンジンを取得
    engines = get_available_engines()
    engine_names = [engine.name for engine in engines]
    
    # デバッグ情報
    print(f"🔍 利用可能なOCRエンジン: {engine_names}")
    
    # データベースからファイル一覧を取得
    files = get_all_files()
    
    return templates.TemplateResponse("try_ocr.html", {
        "request": request,
        "engines": engine_names,
        "files": files
    })

@router.post("/api/try_ocr/process")
async def process_ocr(
    file_id: str = Form(...),
    engine_name: str = Form(...),
    page_num: int = Form(0)
):
    """指定されたファイルとエンジンでOCR処理を実行"""
    try:
        # ファイル情報を取得
        from db.handler import get_file_path
        file_path = get_file_path(file_id)
        
        if not file_path or not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="ファイルが見つかりません")
        
        # OCRエンジンを取得
        engine = get_engine_by_name(engine_name)
        
        # 処理時間を測定
        start_time = time.time()
        
        # ページ番号の処理
        if page_num == -1:  # 全ページ処理
            result = process_all_pages(engine, file_path)
        else:
            result = engine.process(file_path, page_num)
        
        processing_time = time.time() - start_time
        
        # 処理時間を結果に追加
        result["processing_time"] = round(processing_time, 2)
        result["engine_name"] = engine_name
        result["page_num"] = page_num
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 誤字修正辞書を読み込む関数
def load_correction_dict() -> Dict[str, str]:
    """誤字修正辞書を読み込む"""
    correction_dict = {}
    dict_path = "ocr/ocr_word_mistakes.csv"
    
    if not os.path.exists(dict_path):
        return correction_dict
    
    try:
        with open(dict_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            # ヘッダー行をスキップ
            next(reader, None)
            for row in reader:
                if len(row) >= 2:
                    wrong, correct = row[0], row[1]
                    # 空の文字列は無視
                    if wrong and correct:
                        correction_dict[wrong] = correct
    except Exception as e:
        print(f"誤字修正辞書の読み込みエラー: {e}")
    
    return correction_dict

# テキストに誤字修正を適用する関数（改善版）
def apply_corrections(text: str, correction_dict: Dict[str, str]) -> Tuple[str, List[Dict[str, str]]]:
    """
    テキストに誤字修正を適用し、置換情報を返す（改善版）
    
    Returns:
        Tuple[str, List[Dict[str, str]]]: 修正後のテキストと置換情報のリスト
    """
    if not correction_dict or not text:
        return text, []
    
    # 置換情報を記録するリスト
    corrections = []
    
    # 置換位置と内容を記録するリスト（位置情報付き）
    replacements = []
    
    # 辞書の順序を維持して処理
    # 各置換対象について処理
    for wrong, correct in correction_dict.items():
        correct = correction_dict[wrong]
        
        # 現在のテキスト内で置換対象を検索
        start_pos = 0
        while True:
            # 置換対象の位置を検索
            pos = text.find(wrong, start_pos)
            if pos == -1:
                break
            
            # 既に置換予定の範囲と重複していないか確認
            overlap = False
            for repl in replacements:
                repl_start, repl_end = repl['start'], repl['end']
                # 重複チェック
                if not (pos >= repl_end or pos + len(wrong) <= repl_start):
                    overlap = True
                    break
            
            if not overlap:
                # 置換情報を記録
                replacements.append({
                    'start': pos,
                    'end': pos + len(wrong),
                    'wrong': wrong,
                    'correct': correct
                })
                corrections.append({
                    "wrong": wrong,
                    "correct": correct,
                    "position": pos
                })
            
            # 次の検索開始位置を更新
            start_pos = pos + 1
    
    # 置換位置でソート（後ろから処理することで位置のずれを防ぐ）
    replacements.sort(key=lambda x: x['start'], reverse=True)
    
    # 置換を実行
    result_text = list(text)
    for repl in replacements:
        start, end = repl['start'], repl['end']
        correct = repl['correct']
        # リスト内の該当部分を置換
        result_text[start:end] = correct
    
    # リストを文字列に戻す
    result_text = ''.join(result_text)
    
    return result_text, corrections

# HTMLで置換箇所をマークアップする関数（修正版）
def highlight_corrections(text: str, corrections: List[Dict[str, str]]) -> str:
    """
    置換箇所を赤文字でマークアップしたHTMLを生成（修正版）
    """
    if not corrections:
        # 置換がない場合は通常のHTMLエスケープのみ
        html_text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        return html_text.replace("\n", "<br>")
    
    # 置換情報を位置でソート（前から処理）
    sorted_corrections = sorted(
        [c for c in corrections if 'position' in c],
        key=lambda x: x['position']
    )
    
    # 文字列を分割してHTMLを構築
    result_parts = []
    last_pos = 0
    
    for correction in sorted_corrections:
        pos = correction.get('position')
        if pos is None:
            continue
            
        wrong = correction['wrong']
        correct = correction['correct']
        
        # 前の部分をエスケープして追加
        before_part = text[last_pos:pos]
        escaped_before = before_part.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        result_parts.append(escaped_before)
        
        # 置換部分を赤字でマークアップ
        escaped_wrong = wrong.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        escaped_correct = correct.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        marked_part = f'<span style="color:red; font-weight:bold;" title="修正前: {escaped_wrong}">{escaped_correct}</span>'
        result_parts.append(marked_part)
        
        # 次の開始位置を更新
        last_pos = pos + len(correct)
    
    # 残りの部分をエスケープして追加
    remaining_part = text[last_pos:]
    escaped_remaining = remaining_part.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    result_parts.append(escaped_remaining)
    
    # 結合してHTMLを生成
    html_text = ''.join(result_parts)
    
    # 改行をHTMLの改行タグに変換
    html_text = html_text.replace("\n", "<br>")
    
    return html_text

@router.post("/api/try_ocr/process_file")
async def process_ocr_file(
    file: UploadFile = File(...),
    engine_name: str = Form(...),
    page_num: int = Form(0),
    use_correction: bool = Form(False)
):
    """アップロードされたファイルでOCR処理を実行"""
    try:
        # 一時ファイルに保存
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_path = temp_file.name
        
        try:
            # OCRエンジンを取得
            engine = get_engine_by_name(engine_name)
            
            # 処理時間を測定
            start_time = time.time()
            
            # ページ番号の処理
            if page_num == -1:  # 全ページ処理
                result = process_all_pages(engine, temp_path)
            else:
                result = engine.process(temp_path, page_num)
            
            # 誤字修正辞書による置換処理
            if use_correction and result["success"]:
                correction_dict = load_correction_dict()
                corrected_text, corrections = apply_corrections(result["text"], correction_dict)
                
                # 置換が行われた場合
                if corrections:
                    # 元のテキストを保存
                    result["original_text"] = result["text"]
                    # 修正後のテキストを設定
                    result["text"] = corrected_text
                    # 置換情報を追加
                    result["corrections"] = corrections
                    # HTMLマークアップを追加
                    result["html_text"] = highlight_corrections(corrected_text, corrections)
                    # 置換数を追加
                    result["correction_count"] = len(corrections)
            
            processing_time = time.time() - start_time
            
            # 処理時間を結果に追加
            result["processing_time"] = round(processing_time, 2)
            result["engine_name"] = engine_name
            result["page_num"] = page_num
            result["file_name"] = file.filename
            
            return result
            
        finally:
            # 一時ファイルを削除
            if os.path.exists(temp_path):
                os.unlink(temp_path)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def process_all_pages(engine, file_path: str) -> dict:
    """全ページをOCR処理"""
    import fitz
    
    try:
        doc = fitz.open(file_path)
        total_pages = len(doc)
        doc.close()
        
        all_text = []
        total_confidence = 0
        confidence_count = 0
        
        for page_num in range(total_pages):
            result = engine.process(file_path, page_num)
            if result["success"]:
                all_text.append(f"=== ページ {page_num + 1} ===")
                all_text.append(result["text"])
                all_text.append("")  # 空行
                
                if result.get("confidence"):
                    total_confidence += result["confidence"]
                    confidence_count += 1
        
        avg_confidence = total_confidence / confidence_count if confidence_count > 0 else None
        
        return {
            "success": True,
            "text": "\n".join(all_text),
            "confidence": avg_confidence,
            "pages_processed": total_pages
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"全ページ処理エラー: {str(e)}",
            "text": ""
        }

@router.get("/api/try_ocr/engines")
async def get_engines():
    """利用可能なOCRエンジン一覧を取得"""
    engines = get_available_engines()
    return [
        {
            "name": engine.name,
            "available": engine.is_available()
        }
        for engine in engines
    ]

@router.get("/api/try_ocr/engine_parameters/{engine_name}")
async def get_engine_parameters(engine_name: str):
    """指定されたOCRエンジンのパラメータ定義を取得"""
    try:
        engine = get_engine_by_name(engine_name)
        return {
            "engine_name": engine_name,
            "parameters": engine.get_parameters()
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))