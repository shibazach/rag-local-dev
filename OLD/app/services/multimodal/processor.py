# app/services/multimodal/processor.py
# マルチモーダル処理機能

import os
import logging
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import json
import base64
from PIL import Image
import io
import torch

from OLD.src.config import OLLAMA_MODEL, OLLAMA_BASE, MULTIMODAL_ENABLED, MULTIMODAL_MODEL
from langchain_ollama import OllamaLLM

LOGGER = logging.getLogger("multimodal")

class MultimodalProcessor:
    """マルチモーダル処理クラス"""
    
    def __init__(self):
        self.llm = OllamaLLM(model=OLLAMA_MODEL, base_url=OLLAMA_BASE)
        self.supported_image_formats = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp'}
        
        # GPU環境でのみQwen-VLモデルを初期化
        self.qwen_vl_model = None
        if MULTIMODAL_ENABLED and MULTIMODAL_MODEL:
            try:
                from transformers import AutoTokenizer, AutoModelForCausalLM
                self.qwen_vl_model = AutoModelForCausalLM.from_pretrained(
                    MULTIMODAL_MODEL, 
                    device_map="auto",
                    trust_remote_code=True
                )
                self.qwen_vl_tokenizer = AutoTokenizer.from_pretrained(
                    MULTIMODAL_MODEL, 
                    trust_remote_code=True
                )
                LOGGER.info(f"Qwen-VLモデルを初期化しました: {MULTIMODAL_MODEL}")
            except Exception as e:
                LOGGER.warning(f"Qwen-VLモデルの初期化に失敗しました: {e}")
                self.qwen_vl_model = None
    
    def process_document(
        self, 
        text_content: str, 
        image_paths: List[str] = None,
        structure_info: Dict = None
    ) -> Dict[str, Any]:
        """
        文書のマルチモーダル処理
        
        Args:
            text_content: テキスト内容
            image_paths: 画像ファイルパスのリスト
            structure_info: 文書構造情報
            
        Returns:
            処理結果の辞書
        """
        try:
            # GPU環境でない場合は基本的な処理のみ実行
            if not MULTIMODAL_ENABLED:
                return {
                    "success": True,
                    "text_content": self._process_text(text_content),
                    "image_descriptions": [],
                    "structure_info": structure_info or {},
                    "integrated_result": {
                        "text_summary": "CPU環境のため基本的なテキスト処理のみ実行",
                        "image_summary": "画像処理はスキップ（GPU環境が必要）",
                        "structure_summary": "構造情報あり" if structure_info else "構造情報なし",
                        "multimodal_insights": ["CPU環境のため高度なマルチモーダル処理は無効"]
                    }
                }
            
            # 1. テキスト処理
            processed_text = self._process_text(text_content)
            
            # 2. 画像処理（GPU環境でのみ）
            image_descriptions = []
            if image_paths and self.qwen_vl_model:
                image_descriptions = self._process_images_with_qwen_vl(image_paths)
            elif image_paths:
                image_descriptions = self._process_images_basic(image_paths)
            
            # 3. 構造情報処理
            processed_structure = self._process_structure(structure_info) if structure_info else {}
            
            # 4. マルチモーダル統合
            integrated_result = self._integrate_multimodal_data(
                processed_text, 
                image_descriptions, 
                processed_structure
            )
            
            return {
                "success": True,
                "text_content": processed_text,
                "image_descriptions": image_descriptions,
                "structure_info": processed_structure,
                "integrated_result": integrated_result
            }
            
        except Exception as e:
            LOGGER.exception("マルチモーダル処理エラー")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _process_text(self, text_content: str) -> str:
        """テキスト内容の前処理"""
        # 基本的なテキスト正規化
        processed = text_content.strip()
        
        # 特殊文字の正規化
        processed = self._normalize_special_characters(processed)
        
        return processed
    
    def _normalize_special_characters(self, text: str) -> str:
        """特殊文字の正規化"""
        # 機種依存文字の変換
        char_map = {
            '㈱': '(株)', '㈲': '(有)', '㈳': '(社)', '㈴': '(財)',
            '㈵': '(学)', '㈶': '(協)', '㈷': '(組)', '㈸': '(連)',
            '㈹': '(企)', '㈺': '(協)', '㈻': '(中)', '㈼': '(審)',
            '㈽': '(監)', '㈾': '(企)', '㈿': '(特)'
        }
        
        for old_char, new_char in char_map.items():
            text = text.replace(old_char, new_char)
        
        return text
    
    def _extract_image_info(self, image_path: str) -> Dict[str, Any]:
        """画像情報の抽出"""
        try:
            with Image.open(image_path) as img:
                return {
                    "format": img.format,
                    "mode": img.mode,
                    "size": img.size,
                    "width": img.width,
                    "height": img.height,
                    "filename": os.path.basename(image_path)
                }
        except Exception as e:
            LOGGER.error(f"画像情報抽出エラー: {e}")
            return {"error": str(e)}
    
    def _process_structure(self, structure_info: Dict) -> Dict[str, Any]:
        """文書構造情報の処理"""
        processed = {}
        
        # 見出し階層の処理
        if 'headings' in structure_info:
            processed['headings'] = self._process_headings(structure_info['headings'])
        
        # 段落情報の処理
        if 'paragraphs' in structure_info:
            processed['paragraphs'] = self._process_paragraphs(structure_info['paragraphs'])
        
        # リスト情報の処理
        if 'lists' in structure_info:
            processed['lists'] = self._process_lists(structure_info['lists'])
        
        # テーブル情報の処理
        if 'tables' in structure_info:
            processed['tables'] = self._process_tables(structure_info['tables'])
        
        return processed
    
    def _process_headings(self, headings: List[Dict]) -> List[Dict]:
        """見出し情報の処理"""
        processed = []
        for heading in headings:
            processed.append({
                "level": heading.get("level", 1),
                "text": heading.get("text", ""),
                "page": heading.get("page", 1),
                "position": heading.get("position", 0)
            })
        return processed
    
    def _process_paragraphs(self, paragraphs: List[Dict]) -> List[Dict]:
        """段落情報の処理"""
        processed = []
        for para in paragraphs:
            processed.append({
                "text": para.get("text", ""),
                "page": para.get("page", 1),
                "position": para.get("position", 0),
                "length": len(para.get("text", ""))
            })
        return processed
    
    def _process_lists(self, lists: List[Dict]) -> List[Dict]:
        """リスト情報の処理"""
        processed = []
        for lst in lists:
            processed.append({
                "type": lst.get("type", "bullet"),
                "items": lst.get("items", []),
                "page": lst.get("page", 1),
                "position": lst.get("position", 0)
            })
        return processed
    
    def _process_tables(self, tables: List[Dict]) -> List[Dict]:
        """テーブル情報の処理"""
        processed = []
        for table in tables:
            processed.append({
                "rows": table.get("rows", 0),
                "columns": table.get("columns", 0),
                "content": table.get("content", []),
                "page": table.get("page", 1),
                "position": table.get("position", 0)
            })
        return processed
    
    def _integrate_multimodal_data(
        self, 
        text_content: str, 
        image_descriptions: List[Dict], 
        structure_info: Dict
    ) -> Dict[str, Any]:
        """マルチモーダルデータの統合"""
        
        # 統合結果の構築
        integrated = {
            "text_summary": self._summarize_text(text_content),
            "image_summary": self._summarize_images(image_descriptions),
            "structure_summary": self._summarize_structure(structure_info),
            "multimodal_insights": self._generate_multimodal_insights(
                text_content, image_descriptions, structure_info
            )
        }
        
        return integrated
    
    def _summarize_text(self, text_content: str) -> str:
        """テキスト内容の要約"""
        if len(text_content) <= 500:
            return text_content
        
        # 長いテキストの要約
        prompt = f"""
以下のテキストを200文字程度で要約してください:

{text_content[:2000]}...

要約:
"""
        
        try:
            response = self.llm.invoke(prompt)
            return response.strip()
        except Exception as e:
            LOGGER.error(f"テキスト要約エラー: {e}")
            return text_content[:200] + "..."
    
    def _summarize_images(self, image_descriptions: List[Dict]) -> str:
        """画像の要約"""
        if not image_descriptions:
            return "画像なし"
        
        summaries = []
        for img in image_descriptions:
            if "description" in img:
                summaries.append(img["description"][:100] + "...")
        
        return " | ".join(summaries) if summaries else "画像あり（詳細不明）"
    
    def _summarize_structure(self, structure_info: Dict) -> str:
        """構造情報の要約"""
        summary_parts = []
        
        if "headings" in structure_info:
            summary_parts.append(f"見出し: {len(structure_info['headings'])}個")
        
        if "paragraphs" in structure_info:
            summary_parts.append(f"段落: {len(structure_info['paragraphs'])}個")
        
        if "tables" in structure_info:
            summary_parts.append(f"表: {len(structure_info['tables'])}個")
        
        return ", ".join(summary_parts) if summary_parts else "構造情報なし"
    
    def _generate_multimodal_insights(
        self, 
        text_content: str, 
        image_descriptions: List[Dict], 
        structure_info: Dict
    ) -> List[str]:
        """マルチモーダル洞察の生成"""
        insights = []
        
        # テキストと画像の関連性分析
        if image_descriptions and text_content:
            insights.append("テキストと画像の統合情報が利用可能")
        
        # 構造情報の活用
        if structure_info:
            insights.append("文書構造情報が利用可能")
        
        # 画像の種類分析
        image_types = []
        for img in image_descriptions:
            if "description" in img:
                desc = img["description"].lower()
                if "グラフ" in desc or "chart" in desc:
                    image_types.append("グラフ")
                elif "表" in desc or "table" in desc:
                    image_types.append("表")
                elif "写真" in desc or "photo" in desc:
                    image_types.append("写真")
        
        if image_types:
            insights.append(f"画像タイプ: {', '.join(set(image_types))}")
        
        return insights

    def _process_images_with_qwen_vl(self, image_paths: List[str]) -> List[Dict[str, Any]]:
        """Qwen-VLを使用した高度な画像処理"""
        descriptions = []
        
        for image_path in image_paths:
            try:
                if not os.path.exists(image_path):
                    LOGGER.warning(f"画像ファイルが見つかりません: {image_path}")
                    continue
                
                # 画像形式チェック
                file_ext = Path(image_path).suffix.lower()
                if file_ext not in self.supported_image_formats:
                    LOGGER.warning(f"未対応の画像形式: {file_ext}")
                    continue
                
                # Qwen-VLで画像を処理
                description = self._generate_qwen_vl_description(image_path)
                
                descriptions.append({
                    "path": image_path,
                    "description": description,
                    "method": "qwen_vl"
                })
                
            except Exception as e:
                LOGGER.exception(f"Qwen-VL画像処理エラー: {image_path}")
                descriptions.append({
                    "path": image_path,
                    "error": str(e),
                    "method": "qwen_vl"
                })
        
        return descriptions

    def _process_images_basic(self, image_paths: List[str]) -> List[Dict[str, Any]]:
        """基本的な画像処理（CPU環境用）"""
        descriptions = []
        
        for image_path in image_paths:
            try:
                if not os.path.exists(image_path):
                    LOGGER.warning(f"画像ファイルが見つかりません: {image_path}")
                    continue
                
                # 画像情報の取得
                image_info = self._extract_image_info(image_path)
                
                # 基本的な説明生成
                description = f"画像ファイル: {image_info.get('filename', 'unknown')}, サイズ: {image_info.get('width', 0)}x{image_info.get('height', 0)}"
                
                descriptions.append({
                    "path": image_path,
                    "info": image_info,
                    "description": description,
                    "method": "basic"
                })
                
            except Exception as e:
                LOGGER.exception(f"基本画像処理エラー: {image_path}")
                descriptions.append({
                    "path": image_path,
                    "error": str(e),
                    "method": "basic"
                })
        
        return descriptions

    def _generate_qwen_vl_description(self, image_path: str) -> str:
        """Qwen-VLを使用して画像の詳細な説明を生成"""
        try:
            if not self.qwen_vl_model:
                return "Qwen-VLモデルが利用できません"
            
            # 画像を読み込み
            image = Image.open(image_path)
            
            # Qwen-VLプロンプト
            prompt = "この画像の詳細な説明を日本語で行ってください。画像の内容、テキスト、図表、色やスタイルの特徴を含めて説明してください。"
            
            # Qwen-VLで画像処理
            inputs = self.qwen_vl_tokenizer.from_list_format([
                {'image': image},
                {'text': prompt}
            ])
            
            with torch.no_grad():
                response = self.qwen_vl_model.generate(
                    **inputs,
                    max_new_tokens=512,
                    temperature=0.7,
                    do_sample=True
                )
            
            # レスポンスをデコード
            response_text = self.qwen_vl_tokenizer.decode(response[0], skip_special_tokens=True)
            
            return response_text.strip()
            
        except Exception as e:
            LOGGER.error(f"Qwen-VL画像説明生成エラー: {e}")
            return f"Qwen-VL画像処理エラー: {str(e)}"

# グローバルインスタンス
multimodal_processor = MultimodalProcessor() 