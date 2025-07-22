# app/services/ocr/engines/ocrmypdf.py
# OCRMyPDFエンジンの実装

import os
import subprocess
import tempfile
import time
from typing import Dict, Any, List
import fitz  # PyMuPDF

from ..base import OCREngine

class OCRMyPDFEngine(OCREngine):
    """OCRMyPDFエンジン実装"""
    
    def __init__(self):
        super().__init__("OCRMyPDF")
    
    def process(self, pdf_path: str, page_num: int = 0, **kwargs) -> Dict[str, Any]:
        """OCRMyPDFでPDF処理を実行"""
        start_time = time.time()
        
        try:
            # パラメータの検証と正規化
            params = self.validate_parameters(kwargs)
            
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
                temp_path = temp_file.name
            
            # OCRMyPDFコマンド構築
            cmd = ["ocrmypdf", "--force-ocr", "-l", "jpn+eng"]
            
            # パラメータに基づくオプション追加
            if params.get('deskew', False):
                cmd.append('--deskew')
            
            if params.get('rotate_pages', False):
                cmd.append('--rotate-pages')
            
            if params.get('remove_background', False):
                cmd.append('--remove-background')
            
            if params.get('clean', False):
                cmd.append('--clean')
            
            # DPI設定（整数に変換）
            oversample = int(float(params.get('oversample', 300)))
            cmd.extend(['--oversample', str(oversample)])
            
            # 最適化レベル
            optimize = int(float(params.get('optimize', 1)))
            cmd.extend(['--optimize', str(optimize)])
            
            # JPEG品質設定
            jpeg_quality = params.get('jpeg_quality', 0)
            if jpeg_quality > 0:
                jpeg_quality = int(float(jpeg_quality))
                cmd.extend(['--jpeg-quality', str(jpeg_quality)])
            
            # PNG品質設定
            png_quality = params.get('png_quality', 0)
            if png_quality > 0:
                png_quality = int(float(png_quality))
                cmd.extend(['--png-quality', str(png_quality)])
            
            # JBIG2圧縮
            if params.get('jbig2_lossy', False):
                cmd.append('--jbig2-lossy')
            
            # 色変換戦略
            color_strategy = params.get('color_conversion_strategy', 'auto')
            if color_strategy != 'auto':
                cmd.extend(['--color-conversion-strategy', color_strategy])
            
            # PDF/A画像圧縮
            pdfa_compression = params.get('pdfa_image_compression', 'auto')
            if pdfa_compression != 'auto':
                cmd.extend(['--pdfa-image-compression', pdfa_compression])
            
            # 二値化閾値
            if params.get('threshold', False):
                cmd.append('--threshold')
            
            # Unpaper引数
            unpaper_args = params.get('unpaper_args', '').strip()
            if unpaper_args:
                cmd.extend(['--unpaper-args', unpaper_args])
            
            # Tesseract設定
            tesseract_config = params.get('tesseract_config', '').strip()
            if tesseract_config:
                cmd.extend(['--tesseract-config', tesseract_config])
            
            # Tesseractページセグメンテーション
            pagesegmode = params.get('tesseract_pagesegmode', 'auto')
            if pagesegmode != 'auto':
                cmd.extend(['--tesseract-pagesegmode', pagesegmode])
            
            cmd.extend([pdf_path, temp_path])
            
            # OCRMyPDF実行
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode != 0:
                return {
                    "success": False,
                    "error": f"OCRMyPDF エラー: {result.stderr}",
                    "text": "",
                    "processing_time": time.time() - start_time,
                    "confidence": None
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
                "processing_time": time.time() - start_time,
                "confidence": None,
                "engine": self.name,
                "parameters": params
            }
            
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "OCRMyPDF処理がタイムアウトしました",
                "text": "",
                "processing_time": time.time() - start_time,
                "confidence": None
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"OCRMyPDF処理エラー: {str(e)}",
                "text": "",
                "processing_time": time.time() - start_time,
                "confidence": None
            }
    
    def get_parameters(self) -> List[Dict[str, Any]]:
        """OCRMyPDFの調整可能パラメータ"""
        return [
            {
                "name": "deskew",
                "label": "傾き補正",
                "type": "checkbox",
                "default": False,
                "description": "ページの傾きを自動補正",
                "category": "基本設定"
            },
            {
                "name": "rotate_pages",
                "label": "ページ回転",
                "type": "checkbox", 
                "default": False,
                "description": "ページを自動回転",
                "category": "基本設定"
            },
            {
                "name": "remove_background",
                "label": "背景除去",
                "type": "checkbox",
                "default": False,
                "description": "背景を除去してテキストを強調",
                "category": "基本設定"
            },
            {
                "name": "clean",
                "label": "ノイズ除去",
                "type": "checkbox",
                "default": False,
                "description": "画像のノイズを除去",
                "category": "基本設定"
            },
            {
                "name": "oversample",
                "label": "解像度向上倍率",
                "type": "number",
                "default": 300,
                "min": 150,
                "max": 600,
                "step": 50,
                "description": "DPI設定（高いほど精度向上、処理時間増加）",
                "category": "基本設定"
            },
            {
                "name": "optimize",
                "label": "PDF最適化",
                "type": "select",
                "default": 1,
                "options": [
                    {"value": 0, "label": "最適化なし"},
                    {"value": 1, "label": "標準最適化"},
                    {"value": 2, "label": "積極的最適化"},
                    {"value": 3, "label": "最大最適化"}
                ],
                "description": "PDF出力の最適化レベル",
                "category": "詳細設定"
            },
            {
                "name": "jpeg_quality",
                "label": "JPEG品質",
                "type": "number",
                "default": 0,
                "min": 0,
                "max": 100,
                "step": 5,
                "description": "JPEG圧縮品質（0=自動、1-100=品質指定）",
                "category": "詳細設定"
            },
            {
                "name": "png_quality",
                "label": "PNG品質",
                "type": "number",
                "default": 0,
                "min": 0,
                "max": 100,
                "step": 5,
                "description": "PNG圧縮品質（0=自動、1-100=品質指定）",
                "category": "詳細設定"
            },
            {
                "name": "jbig2_lossy",
                "label": "JBIG2圧縮",
                "type": "checkbox",
                "default": False,
                "description": "JBIG2非可逆圧縮を使用（ファイルサイズ削減）",
                "category": "詳細設定"
            },
            {
                "name": "color_conversion_strategy",
                "label": "色変換戦略",
                "type": "select",
                "default": "auto",
                "options": [
                    {"value": "auto", "label": "自動"},
                    {"value": "LeaveColorUnchanged", "label": "色変更なし"},
                    {"value": "RGB", "label": "RGB変換"},
                    {"value": "CMYK", "label": "CMYK変換"}
                ],
                "description": "カラー画像の変換方法",
                "category": "詳細設定"
            },
            {
                "name": "pdfa_image_compression",
                "label": "PDF/A画像圧縮",
                "type": "select",
                "default": "auto",
                "options": [
                    {"value": "auto", "label": "自動"},
                    {"value": "jpeg", "label": "JPEG"},
                    {"value": "lossless", "label": "可逆圧縮"}
                ],
                "description": "PDF/A準拠時の画像圧縮方式",
                "category": "詳細設定"
            },
            {
                "name": "threshold",
                "label": "二値化閾値",
                "type": "checkbox",
                "default": False,
                "description": "画像の二値化処理を適用",
                "category": "画像処理"
            },
            {
                "name": "unpaper_args",
                "label": "Unpaper引数",
                "type": "text",
                "default": "",
                "description": "Unpaperツールの追加引数（上級者向け）",
                "category": "画像処理"
            },
            {
                "name": "tesseract_config",
                "label": "Tesseract設定",
                "type": "text",
                "default": "",
                "description": "Tesseractの追加設定（例: -c preserve_interword_spaces=1）",
                "category": "OCR設定"
            },
            {
                "name": "tesseract_pagesegmode",
                "label": "ページセグメンテーション",
                "type": "select",
                "default": "auto",
                "options": [
                    {"value": "auto", "label": "自動"},
                    {"value": "1", "label": "自動ページセグメンテーション（OSD付き）"},
                    {"value": "3", "label": "完全自動ページセグメンテーション"},
                    {"value": "6", "label": "単一の均一テキストブロック"},
                    {"value": "7", "label": "単一テキスト行"},
                    {"value": "8", "label": "単一単語"},
                    {"value": "13", "label": "生の行（文字分割なし）"}
                ],
                "description": "Tesseractのページセグメンテーションモード",
                "category": "OCR設定"
            }
        ]
    
    def is_available(self) -> bool:
        """OCRMyPDFが利用可能かチェック"""
        try:
            result = subprocess.run(["ocrmypdf", "--version"], 
                                  capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except:
            return False