#!/usr/bin/env python3
# new/services/image_processor.py
# 画像処理サービス

import logging
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import json
import base64
from PIL import Image
import io

from ..config import LOGGER

class ImageProcessor:
    """画像処理クラス"""
    
    def __init__(self):
        self.supported_formats = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp'}
        self.max_image_size = (1920, 1080)  # 最大画像サイズ
    
    def extract_images_from_pdf(self, pdf_path: Path) -> List[Dict[str, Any]]:
        """PDFから画像を抽出"""
        try:
            LOGGER.info(f"🖼️ PDF画像抽出開始: {pdf_path}")
            
            # pdfplumberを使用して画像抽出
            import pdfplumber
            
            images = []
            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages, 1):
                    page_images = page.images
                    
                    for img_num, img in enumerate(page_images, 1):
                        try:
                            # 画像データを取得
                            img_data = {
                                "page_number": page_num,
                                "image_number": img_num,
                                "x": img['x'],
                                "y": img['y'],
                                "width": img['width'],
                                "height": img['height'],
                                "image_data": img['stream'].get_data(),
                                "format": self._detect_image_format(img['stream'].get_data())
                            }
                            images.append(img_data)
                            LOGGER.info(f"✅ 画像抽出: ページ{page_num}, 画像{img_num}")
                            
                        except Exception as e:
                            LOGGER.warning(f"⚠️ 画像抽出エラー: ページ{page_num}, 画像{img_num} - {e}")
            
            LOGGER.info(f"🎉 PDF画像抽出完了: {len(images)}個の画像")
            return images
            
        except Exception as e:
            LOGGER.error(f"PDF画像抽出エラー: {e}")
            return []
    
    def _detect_image_format(self, image_data: bytes) -> str:
        """画像形式を検出"""
        try:
            img = Image.open(io.BytesIO(image_data))
            return img.format.lower() if img.format else 'unknown'
        except Exception:
            return 'unknown'
    
    def process_image(self, image_data: bytes, page_num: int, img_num: int, file_id: str) -> Dict[str, Any]:
        """画像の完全処理"""
        try:
            LOGGER.info(f"🖼️ 画像処理開始: ページ{page_num}, 画像{img_num}")
            
            # PILで画像を開く
            img = Image.open(io.BytesIO(image_data))
            
            # 画像情報を取得
            img_info = {
                "width": img.width,
                "height": img.height,
                "format": img.format.lower() if img.format else 'unknown',
                "mode": img.mode
            }
            
            # 画像のリサイズ（必要に応じて）
            if img.width > self.max_image_size[0] or img.height > self.max_image_size[1]:
                img.thumbnail(self.max_image_size, Image.Resampling.LANCZOS)
                img_info["resized"] = True
                img_info["width"] = img.width
                img_info["height"] = img.height
            
            # OCR処理
            ocr_result = self._perform_ocr(img)
            
            # LLM分析（将来的に実装）
            llm_result = self._analyze_with_llm(img, ocr_result)
            
            # 結果を構築
            result = {
                "file_id": file_id,
                "page_number": page_num,
                "image_number": img_num,
                "image_info": img_info,
                "ocr_text": ocr_result.get("text", ""),
                "ocr_confidence": ocr_result.get("confidence", 0.0),
                "llm_description": llm_result.get("description", ""),
                "llm_analysis": llm_result.get("analysis", {}),
                "processing_status": "completed"
            }
            
            LOGGER.info(f"🎉 画像処理完了: ページ{page_num}, 画像{img_num}")
            return result
            
        except Exception as e:
            LOGGER.error(f"画像処理エラー: {e}")
            return {
                "file_id": file_id,
                "page_number": page_num,
                "image_number": img_num,
                "processing_status": "failed",
                "error": str(e)
            }
    
    def _perform_ocr(self, img: Image.Image) -> Dict[str, Any]:
        """OCR処理"""
        try:
            # EasyOCRを使用
            import easyocr
            
            reader = easyocr.Reader(['ja', 'en'])
            result = reader.readtext(img)
            
            if result:
                # テキストを結合
                text = '\n'.join([item[1] for item in result])
                # 平均信頼度を計算
                confidence = sum([item[2] for item in result]) / len(result)
                
                return {
                    "text": text,
                    "confidence": confidence,
                    "detections": len(result)
                }
            else:
                return {
                    "text": "",
                    "confidence": 0.0,
                    "detections": 0
                }
                
        except ImportError:
            LOGGER.warning("EasyOCRが見つかりません")
            return {"text": "", "confidence": 0.0, "detections": 0}
        except Exception as e:
            LOGGER.error(f"OCRエラー: {e}")
            return {"text": "", "confidence": 0.0, "detections": 0}
    
    def _analyze_with_llm(self, img: Image.Image, ocr_result: Dict[str, Any]) -> Dict[str, Any]:
        """LLMによる画像分析（将来的に実装）"""
        # 現在はプレースホルダー
        return {
            "description": f"画像（{img.width}x{img.height}）",
            "analysis": {
                "ocr_text_length": len(ocr_result.get("text", "")),
                "ocr_confidence": ocr_result.get("confidence", 0.0)
            }
        }
    
    def save_image_to_file(self, image_data: bytes, output_path: Path, format: str = "PNG") -> bool:
        """画像をファイルに保存"""
        try:
            img = Image.open(io.BytesIO(image_data))
            img.save(output_path, format=format)
            LOGGER.info(f"✅ 画像保存: {output_path}")
            return True
        except Exception as e:
            LOGGER.error(f"画像保存エラー: {e}")
            return False
    
    def get_image_metadata(self, image_path: Path) -> Dict[str, Any]:
        """画像のメタデータを取得"""
        try:
            with Image.open(image_path) as img:
                return {
                    "format": img.format,
                    "size": img.size,
                    "mode": img.mode,
                    "info": img.info
                }
        except Exception as e:
            LOGGER.error(f"画像メタデータ取得エラー: {e}")
            return {} 