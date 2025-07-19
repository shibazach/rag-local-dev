# app/try_ocr/ocr_engines.py
# 各種OCRエンジンの実装

import os
import subprocess
import tempfile
from typing import Dict, Any, List
import fitz  # PyMuPDF
from PIL import Image
import io

class OCREngine:
    """OCRエンジンの基底クラス"""
    
    def __init__(self, name: str):
        self.name = name
    
    def process(self, pdf_path: str, page_num: int = 0, **kwargs) -> Dict[str, Any]:
        """PDFの指定ページをOCR処理"""
        raise NotImplementedError
    
    def is_available(self) -> bool:
        """エンジンが利用可能かチェック"""
        raise NotImplementedError
    
    def get_parameters(self) -> List[Dict[str, Any]]:
        """調整可能なパラメータの定義を返す"""
        return []

class OCRMyPDFEngine(OCREngine):
    """現在使用中のOCRMyPDF"""
    
    def __init__(self):
        super().__init__("OCRMyPDF (現在使用中)")
    
    def process(self, pdf_path: str, page_num: int = 0) -> Dict[str, Any]:
        try:
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
                temp_path = temp_file.name
            
            # OCRMyPDFで処理
            cmd = ["ocrmypdf", "--force-ocr", "-l", "jpn+eng", pdf_path, temp_path]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode != 0:
                return {
                    "success": False,
                    "error": f"OCRMyPDF エラー: {result.stderr}",
                    "text": "",
                    "processing_time": 0
                }
            
            # 処理後のPDFからテキスト抽出
            doc = fitz.open(temp_path)
            if page_num < len(doc):
                text = doc[page_num].get_text()
            else:
                text = ""
            doc.close()
            
            # 一時ファイル削除
            os.unlink(temp_path)
            
            return {
                "success": True,
                "text": text,
                "processing_time": 0,  # 実際の時間測定は後で追加
                "confidence": None
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "text": "",
                "processing_time": 0
            }
    
    def get_parameters(self) -> List[Dict[str, Any]]:
        """OCRMyPDFの調整可能パラメータ"""
        return [
            {
                "name": "deskew",
                "label": "傾き補正",
                "type": "checkbox",
                "default": False,
                "description": "ページの傾きを自動補正"
            },
            {
                "name": "rotate_pages",
                "label": "ページ回転",
                "type": "checkbox", 
                "default": False,
                "description": "ページを自動回転"
            },
            {
                "name": "remove_background",
                "label": "背景除去",
                "type": "checkbox",
                "default": False,
                "description": "背景を除去してテキストを強調"
            },
            {
                "name": "clean",
                "label": "ノイズ除去",
                "type": "checkbox",
                "default": False,
                "description": "画像のノイズを除去"
            },
            {
                "name": "oversample",
                "label": "解像度向上倍率",
                "type": "number",
                "default": 300,
                "min": 150,
                "max": 600,
                "step": 50,
                "description": "DPI設定（高いほど精度向上、処理時間増加）"
            }
        ]
    
    def is_available(self) -> bool:
        try:
            result = subprocess.run(["ocrmypdf", "--version"], 
                                  capture_output=True, text=True, timeout=5)
            print(f"🔍 OCRMyPDF check: returncode={result.returncode}, stdout={result.stdout[:50]}")
            return result.returncode == 0
        except Exception as e:
            print(f"🔍 OCRMyPDF check failed: {e}")
            return False

class PaddleOCREngine(OCREngine):
    """PaddleOCR エンジン"""
    
    def __init__(self):
        super().__init__("PaddleOCR")
        self._ocr = None
    
    def _get_ocr(self):
        if self._ocr is None:
            try:
                from paddleocr import PaddleOCR
                self._ocr = PaddleOCR(use_angle_cls=True, lang='japan')
            except ImportError:
                raise ImportError("PaddleOCR がインストールされていません")
        return self._ocr
    
    def process(self, pdf_path: str, page_num: int = 0) -> Dict[str, Any]:
        try:
            # PDFを画像に変換
            doc = fitz.open(pdf_path)
            if page_num >= len(doc):
                return {
                    "success": False,
                    "error": f"ページ {page_num} が存在しません",
                    "text": "",
                    "processing_time": 0
                }
            
            page = doc[page_num]
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2倍解像度
            img_data = pix.tobytes("png")
            doc.close()
            
            # PaddleOCRで処理
            ocr = self._get_ocr()
            result = ocr.ocr(img_data, cls=True)
            
            # 結果をテキストに変換
            text_lines = []
            total_confidence = 0
            count = 0
            
            if result and result[0]:
                for line in result[0]:
                    if len(line) >= 2:
                        text = line[1][0]
                        confidence = line[1][1]
                        text_lines.append(text)
                        total_confidence += confidence
                        count += 1
            
            avg_confidence = total_confidence / count if count > 0 else 0
            
            return {
                "success": True,
                "text": "\n".join(text_lines),
                "processing_time": 0,
                "confidence": avg_confidence
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "text": "",
                "processing_time": 0
            }
    
    def get_parameters(self) -> List[Dict[str, Any]]:
        """PaddleOCRの調整可能パラメータ"""
        return [
            {
                "name": "use_angle_cls",
                "label": "角度分類使用",
                "type": "checkbox",
                "default": True,
                "description": "テキストの角度を自動分類"
            },
            {
                "name": "det_db_thresh",
                "label": "検出閾値",
                "type": "number",
                "default": 0.3,
                "min": 0.1,
                "max": 0.9,
                "step": 0.1,
                "description": "テキスト検出の閾値（低いほど検出感度高）"
            },
            {
                "name": "det_db_box_thresh",
                "label": "ボックス閾値",
                "type": "number",
                "default": 0.5,
                "min": 0.1,
                "max": 0.9,
                "step": 0.1,
                "description": "テキストボックス生成の閾値"
            },
            {
                "name": "det_db_unclip_ratio",
                "label": "アンクリップ比率",
                "type": "number",
                "default": 1.6,
                "min": 1.0,
                "max": 3.0,
                "step": 0.1,
                "description": "テキスト領域の拡張比率"
            },
            {
                "name": "max_text_length",
                "label": "最大テキスト長",
                "type": "number",
                "default": 25,
                "min": 10,
                "max": 100,
                "step": 5,
                "description": "認識する最大文字数"
            }
        ]
    
    def is_available(self) -> bool:
        try:
            import paddleocr
            print(f"🔍 PaddleOCR import: ✅ 成功")
            return True
        except ImportError as e:
            print(f"🔍 PaddleOCR import: ❌ 失敗 - {e}")
            return False
        except Exception as e:
            print(f"🔍 PaddleOCR check: ❌ エラー - {e}")
            return False

class EasyOCREngine(OCREngine):
    """EasyOCR エンジン"""
    
    def __init__(self):
        super().__init__("EasyOCR")
        self._reader = None
    
    def _get_reader(self):
        if self._reader is None:
            try:
                import easyocr
                self._reader = easyocr.Reader(['ja', 'en'])
            except ImportError:
                raise ImportError("EasyOCR がインストールされていません")
        return self._reader
    
    def process(self, pdf_path: str, page_num: int = 0) -> Dict[str, Any]:
        try:
            # PDFを画像に変換
            doc = fitz.open(pdf_path)
            if page_num >= len(doc):
                return {
                    "success": False,
                    "error": f"ページ {page_num} が存在しません",
                    "text": "",
                    "processing_time": 0
                }
            
            page = doc[page_num]
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
            img_data = pix.tobytes("png")
            doc.close()
            
            # EasyOCRで処理
            reader = self._get_reader()
            result = reader.readtext(img_data)
            
            # 結果をテキストに変換
            text_lines = []
            total_confidence = 0
            
            for (bbox, text, confidence) in result:
                text_lines.append(text)
                total_confidence += confidence
            
            avg_confidence = total_confidence / len(result) if result else 0
            
            return {
                "success": True,
                "text": "\n".join(text_lines),
                "processing_time": 0,
                "confidence": avg_confidence
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "text": "",
                "processing_time": 0
            }
    
    def get_parameters(self) -> List[Dict[str, Any]]:
        """EasyOCRの調整可能パラメータ"""
        return [
            {
                "name": "width_ths",
                "label": "幅閾値",
                "type": "number",
                "default": 0.7,
                "min": 0.1,
                "max": 1.0,
                "step": 0.1,
                "description": "テキスト幅の閾値"
            },
            {
                "name": "height_ths",
                "label": "高さ閾値",
                "type": "number",
                "default": 0.7,
                "min": 0.1,
                "max": 1.0,
                "step": 0.1,
                "description": "テキスト高さの閾値"
            },
            {
                "name": "decoder",
                "label": "デコーダー",
                "type": "select",
                "default": "greedy",
                "options": [
                    {"value": "greedy", "label": "Greedy（高速）"},
                    {"value": "beamsearch", "label": "BeamSearch（高精度）"}
                ],
                "description": "テキスト認識アルゴリズム"
            },
            {
                "name": "beamWidth",
                "label": "ビーム幅",
                "type": "number",
                "default": 5,
                "min": 1,
                "max": 20,
                "step": 1,
                "description": "BeamSearch使用時のビーム幅"
            },
            {
                "name": "paragraph",
                "label": "段落グループ化",
                "type": "checkbox",
                "default": False,
                "description": "テキストを段落単位でグループ化"
            }
        ]
    
    def is_available(self) -> bool:
        try:
            import easyocr
            print(f"🔍 EasyOCR import: ✅ 成功")
            return True
        except ImportError as e:
            print(f"🔍 EasyOCR import: ❌ 失敗 - {e}")
            return False
        except Exception as e:
            print(f"🔍 EasyOCR check: ❌ エラー - {e}")
            return False

class TesseractEngine(OCREngine):
    """Tesseract エンジン"""
    
    def __init__(self):
        super().__init__("Tesseract")
    
    def process(self, pdf_path: str, page_num: int = 0) -> Dict[str, Any]:
        try:
            import pytesseract
            
            # PDFを画像に変換
            doc = fitz.open(pdf_path)
            if page_num >= len(doc):
                return {
                    "success": False,
                    "error": f"ページ {page_num} が存在しません",
                    "text": "",
                    "processing_time": 0
                }
            
            page = doc[page_num]
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
            img_data = pix.tobytes("png")
            doc.close()
            
            # PIL Imageに変換
            image = Image.open(io.BytesIO(img_data))
            
            # Tesseractで処理（日本語+英語）
            text = pytesseract.image_to_string(image, lang='jpn+eng')
            
            return {
                "success": True,
                "text": text,
                "processing_time": 0,
                "confidence": None
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "text": "",
                "processing_time": 0
            }
    
    def get_parameters(self) -> List[Dict[str, Any]]:
        """Tesseractの調整可能パラメータ"""
        return [
            {
                "name": "psm",
                "label": "ページセグメンテーションモード",
                "type": "select",
                "default": "6",
                "options": [
                    {"value": "0", "label": "0: 向き・スクリプト検出のみ"},
                    {"value": "1", "label": "1: 自動ページセグメンテーション（OSD付き）"},
                    {"value": "3", "label": "3: 完全自動ページセグメンテーション"},
                    {"value": "6", "label": "6: 単一テキストブロック（デフォルト）"},
                    {"value": "7", "label": "7: 単一テキスト行"},
                    {"value": "8", "label": "8: 単一単語"},
                    {"value": "13", "label": "13: 生テキスト行（セグメンテーション無し）"}
                ],
                "description": "テキスト認識の方法を指定"
            },
            {
                "name": "oem",
                "label": "OCRエンジンモード",
                "type": "select",
                "default": "3",
                "options": [
                    {"value": "0", "label": "0: レガシーエンジンのみ"},
                    {"value": "1", "label": "1: ニューラルネットワークLSTMのみ"},
                    {"value": "2", "label": "2: レガシー + LSTM"},
                    {"value": "3", "label": "3: デフォルト（利用可能なもの）"}
                ],
                "description": "使用するOCRエンジンの種類"
            },
            {
                "name": "dpi",
                "label": "DPI設定",
                "type": "number",
                "default": 300,
                "min": 150,
                "max": 600,
                "step": 50,
                "description": "画像解像度（高いほど精度向上）"
            },
            {
                "name": "preserve_interword_spaces",
                "label": "単語間スペース保持",
                "type": "checkbox",
                "default": False,
                "description": "単語間のスペースを保持"
            },
            {
                "name": "char_whitelist",
                "label": "許可文字",
                "type": "text",
                "default": "",
                "description": "認識を許可する文字（空白=全て許可）"
            }
        ]
    
    def is_available(self) -> bool:
        try:
            import pytesseract
            result = subprocess.run(["tesseract", "--version"], 
                                  capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except:
            return False

# 利用可能なOCRエンジンを取得
def get_available_engines() -> List[OCREngine]:
    """利用可能なOCRエンジンのリストを返す"""
    engines = [
        OCRMyPDFEngine(),
        PaddleOCREngine(),
        EasyOCREngine(),
        TesseractEngine()
    ]
    
    # デバッグ情報を追加
    available_engines = []
    for engine in engines:
        is_avail = engine.is_available()
        print(f"🔍 {engine.name}: {'✅ 利用可能' if is_avail else '❌ 利用不可'}")
        if is_avail:
            available_engines.append(engine)
    
    return available_engines

def get_engine_by_name(name: str) -> OCREngine:
    """名前でOCRエンジンを取得"""
    engines = get_available_engines()
    for engine in engines:
        if engine.name == name:
            return engine
    raise ValueError(f"OCRエンジン '{name}' が見つかりません")