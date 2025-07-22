# app/services/ocr/engines/tesseract.py
# Tesseractエンジンの実装

import time
import tempfile
import os
from typing import Dict, Any, List
import fitz  # PyMuPDF
from PIL import Image

from ..base import OCREngine

class TesseractEngine(OCREngine):
    """Tesseractエンジン実装"""
    
    def __init__(self):
        super().__init__("Tesseract")
    
    def process(self, pdf_path: str, page_num: int = 0, **kwargs) -> Dict[str, Any]:
        """TesseractでPDF処理を実行"""
        start_time = time.time()
        
        try:
            import pytesseract
            
            # パラメータの検証と正規化
            params = self.validate_parameters(kwargs)
            
            # PDFから画像を抽出
            doc = fitz.open(pdf_path)
            if page_num >= len(doc):
                return {
                    "success": False,
                    "error": f"ページ {page_num} が存在しません",
                    "text": "",
                    "processing_time": time.time() - start_time,
                    "confidence": None
                }
            
            page = doc[page_num]
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2倍解像度
            img_data = pix.tobytes("png")
            
            # 一時ファイルに画像保存
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
                temp_file.write(img_data)
                temp_path = temp_file.name
            
            # PIL Imageとして読み込み
            image = Image.open(temp_path)
            
            # Tesseract設定
            config = self._build_tesseract_config(params)
            
            # OCR実行
            text = pytesseract.image_to_string(image, lang=params.get('lang', 'jpn+eng'), config=config)
            
            # 信頼度取得（可能な場合）
            confidence = None
            try:
                data = pytesseract.image_to_data(image, lang=params.get('lang', 'jpn+eng'), config=config, output_type=pytesseract.Output.DICT)
                confidences = [int(conf) for conf in data['conf'] if int(conf) > 0]
                if confidences:
                    # 平均信頼度を計算（0-100の範囲）
                    confidence = sum(confidences) / len(confidences)
                    # 異常値チェック（100を超える場合は100に制限）
                    confidence = min(confidence, 100.0)
            except:
                pass
            
            # クリーンアップ
            doc.close()
            os.unlink(temp_path)
            
            return {
                "success": True,
                "text": text,
                "processing_time": time.time() - start_time,
                "confidence": confidence,
                "engine": self.name,
                "parameters": params
            }
            
        except ImportError:
            return {
                "success": False,
                "error": "pytesseractがインストールされていません",
                "text": "",
                "processing_time": time.time() - start_time,
                "confidence": None
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Tesseract処理エラー: {str(e)}",
                "text": "",
                "processing_time": time.time() - start_time,
                "confidence": None
            }
    
    def _build_tesseract_config(self, params: Dict[str, Any]) -> str:
        """Tesseract設定文字列を構築"""
        config_parts = []
        
        psm = params.get('psm', 6)
        config_parts.append(f'--psm {psm}')
        
        oem = params.get('oem', 3)
        config_parts.append(f'--oem {oem}')
        
        return ' '.join(config_parts)
    
    def get_parameters(self) -> List[Dict[str, Any]]:
        """Tesseractの調整可能パラメータ"""
        return [
            {
                "name": "psm",
                "label": "ページセグメンテーションモード",
                "type": "select",
                "default": 6,
                "options": [
                    {"value": 0, "label": "0: 向きとスクリプト検出のみ"},
                    {"value": 1, "label": "1: 自動ページセグメンテーション（OSD付き）"},
                    {"value": 3, "label": "3: 完全自動ページセグメンテーション"},
                    {"value": 6, "label": "6: 単一の均一テキストブロック"},
                    {"value": 7, "label": "7: 単一テキスト行"},
                    {"value": 8, "label": "8: 単一単語"},
                    {"value": 13, "label": "13: 生の行（文字分割なし）"}
                ],
                "description": "テキスト認識のセグメンテーション方法",
                "category": "基本設定"
            },
            {
                "name": "oem",
                "label": "OCRエンジンモード",
                "type": "select",
                "default": 3,
                "options": [
                    {"value": 0, "label": "0: レガシーエンジンのみ"},
                    {"value": 1, "label": "1: ニューラルネットワークLSTMエンジンのみ"},
                    {"value": 2, "label": "2: レガシー + LSTMエンジン"},
                    {"value": 3, "label": "3: デフォルト（利用可能なものを使用）"}
                ],
                "description": "使用するOCRエンジンの種類",
                "category": "基本設定"
            },
            {
                "name": "lang",
                "label": "認識言語",
                "type": "select",
                "default": "jpn+eng",
                "options": [
                    {"value": "jpn", "label": "日本語のみ"},
                    {"value": "eng", "label": "英語のみ"},
                    {"value": "jpn+eng", "label": "日本語 + 英語"},
                    {"value": "chi_sim", "label": "中国語（簡体字）"},
                    {"value": "chi_tra", "label": "中国語（繁体字）"},
                    {"value": "kor", "label": "韓国語"},
                    {"value": "deu", "label": "ドイツ語"},
                    {"value": "fra", "label": "フランス語"}
                ],
                "description": "OCR認識対象言語",
                "category": "基本設定"
            },
            {
                "name": "dpi",
                "label": "DPI設定",
                "type": "number",
                "default": 300,
                "min": 150,
                "max": 600,
                "step": 50,
                "description": "画像解像度（高いほど精度向上、処理時間増加）",
                "category": "基本設定"
            },
            {
                "name": "preserve_interword_spaces",
                "label": "単語間スペース保持",
                "type": "checkbox",
                "default": True,
                "description": "単語間のスペースを保持",
                "category": "基本設定"
            },
            {
                "name": "tessedit_char_whitelist",
                "label": "許可文字リスト",
                "type": "text",
                "default": "",
                "description": "認識を許可する文字のリスト（空白=全文字）",
                "category": "文字認識"
            },
            {
                "name": "tessedit_char_blacklist",
                "label": "禁止文字リスト",
                "type": "text",
                "default": "",
                "description": "認識を禁止する文字のリスト",
                "category": "文字認識"
            },
            {
                "name": "classify_bln_numeric_mode",
                "label": "数値認識モード",
                "type": "checkbox",
                "default": False,
                "description": "数値認識を強化",
                "category": "文字認識"
            },
            {
                "name": "textord_really_old_xheight",
                "label": "従来のx高さ計算",
                "type": "checkbox",
                "default": False,
                "description": "従来のx高さ計算方法を使用",
                "category": "レイアウト"
            },
            {
                "name": "textord_min_linesize",
                "label": "最小行サイズ",
                "type": "number",
                "default": 1.25,
                "min": 0.5,
                "max": 3.0,
                "step": 0.25,
                "description": "認識する最小行サイズ",
                "category": "レイアウト"
            },
            {
                "name": "tosp_threshold_bias1",
                "label": "スペース閾値バイアス1",
                "type": "number",
                "default": 1.5,
                "min": 0.5,
                "max": 3.0,
                "step": 0.1,
                "description": "スペース検出の閾値調整1",
                "category": "スペース検出"
            },
            {
                "name": "tosp_threshold_bias2",
                "label": "スペース閾値バイアス2",
                "type": "number",
                "default": 0.0,
                "min": -1.0,
                "max": 1.0,
                "step": 0.1,
                "description": "スペース検出の閾値調整2",
                "category": "スペース検出"
            },
            {
                "name": "edges_max_children_per_outline",
                "label": "輪郭あたり最大子要素数",
                "type": "number",
                "default": 10,
                "min": 5,
                "max": 50,
                "step": 5,
                "description": "輪郭検出の最大子要素数",
                "category": "輪郭検出"
            },
            {
                "name": "edges_children_per_grandchild",
                "label": "孫要素あたり子要素数",
                "type": "number",
                "default": 2,
                "min": 1,
                "max": 10,
                "step": 1,
                "description": "輪郭検出の階層設定",
                "category": "輪郭検出"
            },
            {
                "name": "language_model_penalty_non_freq_dict_word",
                "label": "非頻出語ペナルティ",
                "type": "number",
                "default": 0.1,
                "min": 0.0,
                "max": 1.0,
                "step": 0.05,
                "description": "辞書にない単語のペナルティ",
                "category": "言語モデル"
            },
            {
                "name": "language_model_penalty_case",
                "label": "大文字小文字ペナルティ",
                "type": "number",
                "default": 0.1,
                "min": 0.0,
                "max": 1.0,
                "step": 0.05,
                "description": "大文字小文字の不一致ペナルティ",
                "category": "言語モデル"
            }
        ]
    
    def is_available(self) -> bool:
        """Tesseractが利用可能かチェック"""
        try:
            import pytesseract
            # 簡単なテストを実行
            pytesseract.get_tesseract_version()
            return True
        except ImportError:
            return False
        except Exception:
            return False