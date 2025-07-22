# app/services/ocr/engines/easyocr.py
# EasyOCRエンジンの実装

import time
import tempfile
import os
from typing import Dict, Any, List
import fitz  # PyMuPDF
from PIL import Image

from ..base import OCREngine

class EasyOCREngine(OCREngine):
    """EasyOCRエンジン実装"""
    
    def __init__(self):
        super().__init__("EasyOCR")
    
    def process(self, pdf_path: str, page_num: int = 0, **kwargs) -> Dict[str, Any]:
        """EasyOCRでPDF処理を実行"""
        start_time = time.time()
        
        try:
            import easyocr
            
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
            # 解像度を上げて画像を取得
            zoom = params.get('zoom_factor', 2.0)
            pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom))
            img_data = pix.tobytes("png")
            
            # 一時ファイルに画像保存
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
                temp_file.write(img_data)
                temp_path = temp_file.name
            
            # EasyOCRリーダーを初期化
            languages = params.get('languages', ['ja', 'en'])
            use_gpu = params.get('use_gpu', False)
            
            # 言語パラメータの正規化
            if isinstance(languages, str):
                languages = [languages]
            elif not isinstance(languages, list):
                languages = ['ja', 'en']
            
            print(f"🔍 EasyOCR初期化中... 言語: {languages}, GPU: {use_gpu}")
            
            try:
                # タイムアウト付きでEasyOCRを初期化
                import signal
                
                def timeout_handler(signum, frame):
                    raise TimeoutError("EasyOCR初期化がタイムアウトしました")
                
                # 60秒のタイムアウトを設定
                signal.signal(signal.SIGALRM, timeout_handler)
                signal.alarm(60)
                
                try:
                    reader = easyocr.Reader(languages, gpu=use_gpu, verbose=False)
                    print(f"✅ EasyOCR初期化完了")
                finally:
                    signal.alarm(0)  # タイムアウトをクリア
                    
            except TimeoutError:
                print(f"⏰ EasyOCR初期化タイムアウト（60秒）")
                return {
                    "success": False,
                    "error": "EasyOCR初期化がタイムアウトしました（モデルダウンロード中の可能性があります）",
                    "text": "",
                    "processing_time": time.time() - start_time,
                    "confidence": None
                }
            except Exception as init_error:
                print(f"❌ EasyOCR初期化エラー: {init_error}")
                # GPU使用時にエラーが発生した場合はCPUモードで再試行
                if use_gpu:
                    print("🔄 CPUモードで再試行中...")
                    try:
                        signal.signal(signal.SIGALRM, timeout_handler)
                        signal.alarm(60)
                        try:
                            reader = easyocr.Reader(languages, gpu=False, verbose=False)
                            print(f"✅ EasyOCR初期化完了（CPUモード）")
                        finally:
                            signal.alarm(0)
                    except TimeoutError:
                        print(f"⏰ EasyOCR CPUモード初期化もタイムアウト")
                        return {
                            "success": False,
                            "error": "EasyOCR初期化がタイムアウトしました（CPUモードでも失敗）",
                            "text": "",
                            "processing_time": time.time() - start_time,
                            "confidence": None
                        }
                else:
                    raise
            
            # OCR実行（詳細パラメータを適用）
            readtext_params = {
                'detail': params.get('detail', 1),
                'paragraph': params.get('paragraph', False)
            }
            
            # 高精度モードの場合は追加パラメータを設定
            if params.get('high_quality_mode', False):
                readtext_params.update({
                    'text_threshold': params.get('text_threshold', 0.7),
                    'link_threshold': params.get('link_threshold', 0.4),
                    'low_text': params.get('low_text', 0.4),
                    'canvas_size': params.get('canvas_size', 2560),
                    'mag_ratio': params.get('mag_ratio', 1.5)
                })
            
            results = reader.readtext(temp_path, **readtext_params)
            
            # テキストと信頼度を抽出
            if params.get('detail', 1) == 1:
                # 詳細情報ありの場合
                texts = []
                confidences = []
                for (bbox, text, confidence) in results:
                    texts.append(text)
                    confidences.append(confidence)
                
                combined_text = '\n'.join(texts)
                avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
            else:
                # テキストのみの場合
                combined_text = '\n'.join(results)
                avg_confidence = None
            
            # クリーンアップ
            doc.close()
            os.unlink(temp_path)
            
            return {
                "success": True,
                "text": combined_text,
                "processing_time": time.time() - start_time,
                "confidence": avg_confidence,
                "engine": self.name,
                "parameters": params
            }
            
        except ImportError:
            return {
                "success": False,
                "error": "easyocrがインストールされていません",
                "text": "",
                "processing_time": time.time() - start_time,
                "confidence": None
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"EasyOCR処理エラー: {str(e)}",
                "text": "",
                "processing_time": time.time() - start_time,
                "confidence": None
            }
    
    def get_parameters(self) -> List[Dict[str, Any]]:
        """EasyOCRの調整可能パラメータ"""
        return [
            {
                "name": "languages",
                "label": "認識言語",
                "type": "select",
                "default": ["ja", "en"],
                "options": [
                    {"value": ["ja"], "label": "日本語のみ"},
                    {"value": ["en"], "label": "英語のみ"},
                    {"value": ["ja", "en"], "label": "日本語 + 英語"},
                    {"value": ["zh"], "label": "中国語"},
                    {"value": ["ko"], "label": "韓国語"},
                    {"value": ["ja", "en", "zh"], "label": "日本語 + 英語 + 中国語"}
                ],
                "description": "OCR認識対象言語（複数選択可能）",
                "category": "基本設定"
            },
            {
                "name": "use_gpu",
                "label": "GPU使用",
                "type": "checkbox",
                "default": False,
                "description": "GPU加速を使用（CUDA対応GPU必要）",
                "category": "基本設定"
            },
            {
                "name": "zoom_factor",
                "label": "画像拡大倍率",
                "type": "number",
                "default": 2.0,
                "min": 1.0,
                "max": 4.0,
                "step": 0.5,
                "description": "画像の拡大倍率（高いほど精度向上、処理時間増加）",
                "category": "基本設定"
            },
            {
                "name": "detail",
                "label": "詳細情報",
                "type": "select",
                "default": 1,
                "options": [
                    {"value": 0, "label": "テキストのみ"},
                    {"value": 1, "label": "座標と信頼度を含む"}
                ],
                "description": "出力する情報の詳細レベル",
                "category": "基本設定"
            },
            {
                "name": "paragraph",
                "label": "段落モード",
                "type": "checkbox",
                "default": False,
                "description": "段落単位でテキストをグループ化",
                "category": "基本設定"
            },
            {
                "name": "high_quality_mode",
                "label": "高精度モード",
                "type": "checkbox",
                "default": False,
                "description": "高精度処理（処理時間が増加しますが精度向上）",
                "category": "高精度設定"
            },
            {
                "name": "text_threshold",
                "label": "テキスト検出閾値",
                "type": "number",
                "default": 0.7,
                "min": 0.1,
                "max": 1.0,
                "step": 0.1,
                "description": "テキスト検出の信頼度閾値（低いほど多くのテキストを検出）",
                "category": "高精度設定"
            },
            {
                "name": "link_threshold",
                "label": "リンク閾値",
                "type": "number",
                "default": 0.4,
                "min": 0.1,
                "max": 1.0,
                "step": 0.1,
                "description": "文字間のリンク閾値（低いほど文字を繋げやすい）",
                "category": "高精度設定"
            },
            {
                "name": "low_text",
                "label": "低信頼度テキスト検出",
                "type": "number",
                "default": 0.4,
                "min": 0.1,
                "max": 1.0,
                "step": 0.1,
                "description": "低信頼度テキストの検出閾値",
                "category": "高精度設定"
            },
            {
                "name": "canvas_size",
                "label": "キャンバスサイズ",
                "type": "number",
                "default": 2560,
                "min": 1280,
                "max": 5120,
                "step": 256,
                "description": "処理用キャンバスサイズ（大きいほど高精度、メモリ使用量増加）",
                "category": "高精度設定"
            },
            {
                "name": "mag_ratio",
                "label": "拡大比率",
                "type": "number",
                "default": 1.5,
                "min": 1.0,
                "max": 3.0,
                "step": 0.1,
                "description": "画像の拡大比率（高精度モード時に使用）",
                "category": "高精度設定"
            }
        ]
    
    def is_available(self) -> bool:
        """EasyOCRが利用可能かチェック"""
        try:
            import easyocr
            return True
        except ImportError:
            return False