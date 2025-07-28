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

from app.services.ocr import OCREngineFactory
from db.handler import get_all_files

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/try_ocr", response_class=HTMLResponse)
async def try_ocr_page(request: Request):
    """OCR比較ページ"""
    # OCRファクトリを初期化
    ocr_factory = OCREngineFactory()
    
    # 利用可能なOCRエンジンを取得
    available_engines_dict = ocr_factory.get_available_engines()
    engine_names = [engine_info['name'] for engine_id, engine_info in available_engines_dict.items() if engine_info['available']]
    
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
            # OCRファクトリを初期化
            ocr_factory = OCREngineFactory()
            available_engines_dict = ocr_factory.get_available_engines()
            
            # エンジン名からIDを特定
            engine_id = None
            for eid, engine_info in available_engines_dict.items():
                if engine_info['name'] == engine_name and engine_info['available']:
                    engine_id = eid
                    break
            
            if not engine_id:
                raise HTTPException(status_code=404, detail=f"OCRエンジン '{engine_name}' が見つかりません")
            
            # 処理時間を測定
            start_time = time.time()
            
            # ページ番号の処理
            if page_num == -1:  # 全ページ処理
                result = process_all_pages_with_factory(engine_id, temp_path, ocr_factory)
            else:
                result = ocr_factory.process_with_settings(engine_id, temp_path, page_num)
            
            # 誤字修正辞書による置換処理
            if use_correction and result["success"]:
                correction_dict = load_correction_dict()
                original_text = result["text"]  # 元のテキストを保存
                
                # 統合された修正処理を実行（誤字修正 + 全角→半角変換）
                final_text, all_corrections = apply_all_corrections(original_text, correction_dict)
                
                # 置換が行われた場合
                if all_corrections:
                    # 元のテキストを保存
                    result["original_text"] = original_text
                    # 修正後のテキストを設定
                    result["text"] = final_text
                    # 置換情報を追加
                    result["corrections"] = all_corrections
                    # HTMLマークアップを追加（元のテキストを使用）
                    result["html_text"] = highlight_corrections(original_text, all_corrections)
                    # 置換数を追加
                    result["correction_count"] = len(all_corrections)
            
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

# 誤字修正辞書を読み込む関数
def load_correction_dict() -> Dict[str, str]:
    """誤字修正辞書を読み込む"""
    correction_dict = {}
    dict_path = "ocr/dic/ocr_word_mistakes.csv"
    
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
    result_text = text
    for repl in replacements:
        start, end = repl['start'], repl['end']
        correct = repl['correct']
        # 文字列の該当部分を置換
        result_text = result_text[:start] + correct + result_text[end:]
    
    return result_text, corrections

# 重複した関数を削除（apply_all_corrections関数を使用）

# 統合された修正処理関数
def apply_all_corrections(text: str, correction_dict: Dict[str, str]) -> Tuple[str, List[Dict[str, str]]]:
    """
    誤字修正と全角→半角変換を統合して実行
    
    Returns:
        Tuple[str, List[Dict[str, str]]]: 修正後のテキストと修正情報のリスト
    """
    if not text:
        return text, []
    
    # 全角→半角の変換マップ
    fullwidth_map = {
        # 数字
        '０': '0', '１': '1', '２': '2', '３': '3', '４': '4',
        '５': '5', '６': '6', '７': '7', '８': '8', '９': '9',
        # 英字（大文字）
        'Ａ': 'A', 'Ｂ': 'B', 'Ｃ': 'C', 'Ｄ': 'D', 'Ｅ': 'E',
        'Ｆ': 'F', 'Ｇ': 'G', 'Ｈ': 'H', 'Ｉ': 'I', 'Ｊ': 'J',
        'Ｋ': 'K', 'Ｌ': 'L', 'Ｍ': 'M', 'Ｎ': 'N', 'Ｏ': 'O',
        'Ｐ': 'P', 'Ｑ': 'Q', 'Ｒ': 'R', 'Ｓ': 'S', 'Ｔ': 'T',
        'Ｕ': 'U', 'Ｖ': 'V', 'Ｗ': 'W', 'Ｘ': 'X', 'Ｙ': 'Y', 'Ｚ': 'Z',
        # 英字（小文字）
        'ａ': 'a', 'ｂ': 'b', 'ｃ': 'c', 'ｄ': 'd', 'ｅ': 'e',
        'ｆ': 'f', 'ｇ': 'g', 'ｈ': 'h', 'ｉ': 'i', 'ｊ': 'j',
        'ｋ': 'k', 'ｌ': 'l', 'ｍ': 'm', 'ｎ': 'n', 'ｏ': 'o',
        'ｐ': 'p', 'ｑ': 'q', 'ｒ': 'r', 'ｓ': 's', 'ｔ': 't',
        'ｕ': 'u', 'ｖ': 'v', 'ｗ': 'w', 'ｘ': 'x', 'ｙ': 'y', 'ｚ': 'z',
        # 記号
        '．': '.', '，': ',', '：': ':', '；': ';', '？': '?',
        '！': '!', '（': '(', '）': ')', '［': '[', '］': ']',
        '｛': '{', '｝': '}', '＋': '+', '－': '-', '＊': '*',
        '／': '/', '＝': '=', '＜': '<', '＞': '>', '＠': '@',
        '＃': '#', '％': '%', '＆': '&', '｜': '|', '＼': '\\',
        '＾': '^', '＿': '_', '｀': '`', '～': '~', '　': ' ',  # 全角スペース
        # 長音記号・ハイフン類（技術文書でよく使われる）
        '―': '-',  # 全角ダッシュ（em dash）
        '‐': '-',  # ハイフン
        '–': '-',  # en dash
        '—': '-'   # em dash
        # 注意: 'ー'（カタカナ長音記号）は文脈判定で処理
    }
    
    # 統合された変換辞書を作成（誤字修正 + 全角→半角）
    combined_dict = {}
    
    # 1. 誤字修正辞書を追加
    for wrong, correct in correction_dict.items():
        combined_dict[wrong] = {"correct": correct, "type": "correction"}
    
    # 2. 全角→半角変換を追加
    for fullwidth, halfwidth in fullwidth_map.items():
        combined_dict[fullwidth] = {"correct": halfwidth, "type": "normalization"}
    
    # 修正情報を記録するリスト
    corrections = []
    
    # 置換位置と内容を記録するリスト（位置情報付き）
    replacements = []
    
    # 各変換対象について処理
    for wrong, info in combined_dict.items():
        correct = info["correct"]
        correction_type = info["type"]
        
        start_pos = 0
        while True:
            # 変換対象の位置を検索
            pos = text.find(wrong, start_pos)
            if pos == -1:
                break
            
            # デバッグ: ダッシュ系文字の文字コードを出力
            if wrong in ['—', '―', '‐', '–', 'ー']:
                print(f"🔍 Found '{wrong}' (U+{ord(wrong):04X}) at position {pos}")
            
            # 既に変換予定の範囲と重複していないか確認
            overlap = False
            for repl in replacements:
                repl_start, repl_end = repl['start'], repl['end']
                # 重複チェック
                if not (pos >= repl_end or pos + len(wrong) <= repl_start):
                    overlap = True
                    break
            
            if not overlap:
                # 変換情報を記録
                replacements.append({
                    'start': pos,
                    'end': pos + len(wrong),
                    'wrong': wrong,
                    'correct': correct,
                    'type': correction_type
                })
                corrections.append({
                    "wrong": wrong,
                    "correct": correct,
                    "position": pos,
                    "type": correction_type
                })
            
            # 次の検索開始位置を更新
            start_pos = pos + 1
    
    # カタカナ長音記号「ー」の文脈判定処理
    katakana_dash_replacements = []
    start_pos = 0
    while True:
        pos = text.find('ー', start_pos)
        if pos == -1:
            break
        
        # 前後の文字をチェック
        prev_char = text[pos - 1] if pos > 0 else ''
        next_char = text[pos + 1] if pos < len(text) - 1 else ''
        
        # 英数字かどうかを判定する関数
        def is_alphanumeric(char):
            return char.isalnum() or char in 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789ＡＢＣＤＥＦＧＨＩＪＫＬＭＮＯＰＱＲＳＴＵＶＷＸＹＺａｂｃｄｅｆｇｈｉｊｋｌｍｎｏｐｑｒｓｔｕｖｗｘｙｚ０１２３４５６７８９'
        
        # カタカナかどうかを判定する関数
        def is_katakana(char):
            return '\u30A0' <= char <= '\u30FF'
        
        # ひらがなかどうかを判定する関数
        def is_hiragana(char):
            return '\u3040' <= char <= '\u309F'
        
        # 日本語文字（ひらがな・カタカナ・漢字）かどうかを判定する関数
        def is_japanese(char):
            return (is_hiragana(char) or 
                   is_katakana(char) or 
                   '\u4E00' <= char <= '\u9FAF' or  # 漢字
                   '\u3400' <= char <= '\u4DBF')    # 漢字拡張A
        
        # 前後の文字の種類を判定
        prev_is_alphanumeric = is_alphanumeric(prev_char)
        next_is_alphanumeric = is_alphanumeric(next_char)
        prev_is_japanese = is_japanese(prev_char)
        next_is_japanese = is_japanese(next_char)
        
        # 変換条件：前後のどちらかが英数字で、かつ両方が日本語文字ではない場合のみ変換
        should_convert = ((prev_is_alphanumeric or next_is_alphanumeric) and 
                         not (prev_is_japanese and next_is_japanese))
        
        if should_convert:
            # 既存の置換と重複していないかチェック
            overlap = False
            for repl in replacements:
                if not (pos >= repl['end'] or pos + 1 <= repl['start']):
                    overlap = True
                    break
            
            if not overlap:
                katakana_dash_replacements.append({
                    'start': pos,
                    'end': pos + 1,
                    'wrong': 'ー',
                    'correct': '-',
                    'type': 'normalization'
                })
                corrections.append({
                    "wrong": 'ー',
                    "correct": '-',
                    "position": pos,
                    "type": 'normalization'
                })
                print(f"🔍 Context-based conversion: 'ー' (U+30FC) at position {pos} -> '-' (prev: '{prev_char}', next: '{next_char}')")
        
        start_pos = pos + 1
    
    # カタカナ長音記号の文脈判定による置換を追加
    replacements.extend(katakana_dash_replacements)
    
    # 変換位置でソート（後ろから処理することで位置のずれを防ぐ）
    replacements.sort(key=lambda x: x['start'], reverse=True)
    
    # 変換を実行
    result_text = text
    for repl in replacements:
        start, end = repl['start'], repl['end']
        correct = repl['correct']
        # 文字列の該当部分を変換
        result_text = result_text[:start] + correct + result_text[end:]
    
    return result_text, corrections

# HTMLで置換箇所をマークアップする関数（完全修正版）
def highlight_corrections(original_text: str, corrections: List[Dict[str, str]]) -> str:
    """
    置換箇所を赤文字でマークアップしたHTMLを生成（完全修正版）
    original_text: 元のテキスト（置換前）
    corrections: 置換情報のリスト（position情報を含む）
    """
    if not corrections:
        # 置換がない場合は通常のHTMLエスケープのみ
        html_text = original_text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        return html_text.replace("\n", "<br>")
    
    # 置換情報を位置でソート（前から処理）
    sorted_corrections = sorted(corrections, key=lambda x: x.get('position', 0))
    
    # 文字列を分割してHTMLを構築
    result_parts = []
    last_pos = 0
    
    for correction in sorted_corrections:
        wrong = correction['wrong']
        correct = correction['correct']
        position = correction.get('position', 0)
        
        # 前の部分（置換されない部分）をエスケープして追加
        before_part = original_text[last_pos:position]
        escaped_before = before_part.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        result_parts.append(escaped_before)
        
        # 置換部分を赤字でマークアップ（種類に応じて色を変える）
        escaped_wrong = wrong.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        escaped_correct = correct.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        
        # 正規化（全角→半角）の場合は青色、誤字修正は赤色
        if correction.get('type') == 'normalization':
            marked_part = f'<span style="color:blue; font-weight:bold;" title="全角→半角: {escaped_wrong}">{escaped_correct}</span>'
        else:
            marked_part = f'<span style="color:red; font-weight:bold;" title="修正前: {escaped_wrong}">{escaped_correct}</span>'
        
        result_parts.append(marked_part)
        
        # 次の開始位置を更新（元のテキストでの位置）
        last_pos = position + len(wrong)
    
    # 残りの部分をエスケープして追加
    remaining_part = original_text[last_pos:]
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
            # OCRファクトリを初期化
            ocr_factory = OCREngineFactory()
            available_engines_dict = ocr_factory.get_available_engines()
            
            # エンジン名からIDを特定
            engine_id = None
            for eid, engine_info in available_engines_dict.items():
                if engine_info['name'] == engine_name and engine_info['available']:
                    engine_id = eid
                    break
            
            if not engine_id:
                raise HTTPException(status_code=404, detail=f"OCRエンジン '{engine_name}' が見つかりません")
            
            # 処理時間を測定
            start_time = time.time()
            
            # ページ番号の処理
            if page_num == -1:  # 全ページ処理
                result = process_all_pages_with_factory(engine_id, temp_path, ocr_factory)
            else:
                result = ocr_factory.process_with_settings(engine_id, temp_path, page_num)
            
            # 誤字修正辞書による置換処理
            if use_correction and result["success"]:
                correction_dict = load_correction_dict()
                original_text = result["text"]  # 元のテキストを保存
                
                # 統合された修正処理を実行（誤字修正 + 全角→半角変換）
                final_text, all_corrections = apply_all_corrections(original_text, correction_dict)
                
                # 置換が行われた場合
                if all_corrections:
                    # 元のテキストを保存
                    result["original_text"] = original_text
                    # 修正後のテキストを設定
                    result["text"] = final_text
                    # 置換情報を追加
                    result["corrections"] = all_corrections
                    # HTMLマークアップを追加（元のテキストを使用）
                    result["html_text"] = highlight_corrections(original_text, all_corrections)
                    # 置換数を追加
                    result["correction_count"] = len(all_corrections)
            
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
    """全ページをOCR処理（旧版・互換性のため残存）"""
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

def process_all_pages_with_factory(engine_id: str, file_path: str, ocr_factory: OCREngineFactory) -> dict:
    """全ページをOCR処理（統一されたOCRサービス使用）"""
    import fitz
    
    try:
        doc = fitz.open(file_path)
        total_pages = len(doc)
        doc.close()
        
        all_text = []
        total_confidence = 0
        confidence_count = 0
        
        for page_num in range(total_pages):
            result = ocr_factory.process_with_settings(engine_id, file_path, page_num)
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
    ocr_factory = OCREngineFactory()
    available_engines_dict = ocr_factory.get_available_engines()
    return [
        {
            "name": engine_info['name'],
            "available": engine_info['available']
        }
        for engine_id, engine_info in available_engines_dict.items()
    ]

@router.get("/api/try_ocr/engine_parameters/{engine_name}")
async def get_engine_parameters(engine_name: str):
    """指定されたOCRエンジンのパラメータ定義を取得"""
    try:
        ocr_factory = OCREngineFactory()
        available_engines_dict = ocr_factory.get_available_engines()
        
        for engine_id, engine_info in available_engines_dict.items():
            if engine_info['name'] == engine_name and engine_info['available']:
                return {
                    "engine_name": engine_name,
                    "parameters": engine_info['parameters']
                }
        raise ValueError(f"OCRエンジン '{engine_name}' が見つかりません")
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))