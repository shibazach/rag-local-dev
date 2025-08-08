"""
OCR処理サービス - Prototype統合版
PDFからのテキスト抽出・構造化処理
"""

import os
import subprocess
import fitz  # PyMuPDF
from collections import defaultdict
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

from app.config import config, logger

class OCRProcessor:
    """OCR処理サービス"""
    
    def __init__(self):
        self.ocr_language = config.OCR_LANGUAGE
        self.ocr_dpi = config.OCR_DPI
        self.ocr_optimize = config.OCR_OPTIMIZE
    
    def has_embedded_text(self, pdf_path: str) -> bool:
        """PDF内にテキストが埋め込まれているか確認"""
        try:
            doc = fitz.open(pdf_path)
            for page in doc:
                if page.get_text().strip():
                    return True
            return False
        except Exception as e:
            logger.error(f"PDF埋め込みテキスト確認エラー: {e}")
            return False
    
    def remove_embedded_text(self, pdf_path: str) -> str:
        """PDFからテキストを削除して新しいPDFを作成"""
        try:
            doc = fitz.open(pdf_path)
            for page in doc:
                page.clean_contents()
            temp_path = pdf_path.replace(".pdf", "_no_text.pdf")
            doc.save(temp_path)
            return temp_path
        except Exception as e:
            logger.error(f"PDFテキスト削除エラー: {e}")
            raise
    
    def run_ocr(self, input_pdf: str, output_pdf: str) -> None:
        """OCRを実行してテキストを埋め込む"""
        try:
            cmd = [
                "ocrmypdf",
                "--force-ocr",
                "-l", self.ocr_language,
                "--dpi", str(self.ocr_dpi),
                "--optimize", str(self.ocr_optimize),
                input_pdf,
                output_pdf
            ]
            
            logger.info(f"OCR実行: {' '.join(cmd)}")
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            
            if result.stderr:
                logger.warning(f"OCR警告: {result.stderr}")
                
        except subprocess.CalledProcessError as e:
            logger.error(f"OCRエラー: {e.stderr}")
            raise
    
    def extract_text_blocks(self, page) -> List[Dict[str, Any]]:
        """PDFページからテキストブロックを抽出"""
        blocks = page.get_text("dict")["blocks"]
        text_blocks = []
        
        for block in blocks:
            if block['type'] == 0:  # テキストブロック
                block_text = ""
                bbox = block['bbox']
                
                for line in block["lines"]:
                    line_text = " ".join(span["text"] for span in line["spans"])
                    block_text += line_text + "\n"
                    
                text_blocks.append({
                    "text": block_text.strip(),
                    "bbox": bbox
                })
                
        return text_blocks
    
    def cluster_columns(self, blocks: List[Dict], x_threshold: int = 100) -> List[List[Dict]]:
        """X座標で段組み（左本文／右表など）を分ける"""
        columns = defaultdict(list)
        
        for block in blocks:
            x0 = block['bbox'][0]
            col_key = int(x0 // x_threshold)
            columns[col_key].append(block)
            
        return [columns[k] for k in sorted(columns)]
    
    def group_rows_by_y(self, blocks: List[Dict], y_threshold: int = 15) -> List[List[Dict]]:
        """Y座標で行グループ化"""
        rows = []
        
        for block in sorted(blocks, key=lambda b: b["bbox"][1]):
            added = False
            
            for row in rows:
                if abs(row[0]["bbox"][1] - block["bbox"][1]) < y_threshold:
                    row.append(block)
                    added = True
                    break
                    
            if not added:
                rows.append([block])
                
        return rows
    
    def extract_label_value_pairs_from_rows(self, rows: List[List[Dict]]) -> List[str]:
        """ラベルと値のペアを抽出"""
        structured = []
        
        for i in range(len(rows) - 1):
            label_row = sorted(rows[i], key=lambda b: b["bbox"][0])
            value_row = sorted(rows[i + 1], key=lambda b: b["bbox"][0])
            
            for j in range(min(len(label_row), len(value_row))):
                label = label_row[j]["text"]
                value = value_row[j]["text"]
                structured.append(f"{label.strip()}: {value.strip()}")
                
        return structured
    
    def extract_and_structure_text(self, doc) -> List[str]:
        """PDFドキュメントからテキストを抽出し、構造化された形式に変換"""
        structured_text = []
        
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            blocks = self.extract_text_blocks(page)
            columns = self.cluster_columns(blocks)
            
            for col_blocks in columns:
                rows = self.group_rows_by_y(col_blocks)
                structured_text.extend(self.extract_label_value_pairs_from_rows(rows))
                
        return structured_text
    
    def process_pdf(self, input_path: str, output_dir: str = None) -> Dict[str, Any]:
        """
        PDFファイルを処理
        
        Args:
            input_path: 入力PDFパス
            output_dir: 出力ディレクトリ（省略時は同じディレクトリ）
            
        Returns:
            処理結果情報
        """
        try:
            input_path = Path(input_path)
            if not input_path.exists():
                raise FileNotFoundError(f"ファイルが見つかりません: {input_path}")
            
            if output_dir is None:
                output_dir = input_path.parent
            else:
                output_dir = Path(output_dir)
                output_dir.mkdir(parents=True, exist_ok=True)
            
            output_path = output_dir / input_path.name
            
            # 埋め込みテキストチェックとOCR処理
            if self.has_embedded_text(str(input_path)):
                doc = fitz.open(str(input_path))
                text = "".join([page.get_text() for page in doc])
                
                if not text.strip():
                    # テキストが空の場合はOCR実行
                    temp_path = self.remove_embedded_text(str(input_path))
                    self.run_ocr(temp_path, str(output_path))
                    os.remove(temp_path)
                else:
                    # テキストがある場合はそのまま保存
                    doc.save(str(output_path))
            else:
                # 埋め込みテキストがない場合はOCR実行
                self.run_ocr(str(input_path), str(output_path))
            
            # 構造化テキスト抽出
            doc = fitz.open(str(output_path))
            structured = self.extract_and_structure_text(doc)
            
            # テキストファイル保存
            txt_output = output_path.with_suffix('.txt')
            with open(txt_output, "w", encoding="utf-8") as f:
                for line in structured:
                    f.write(line + "\n")
            
            logger.info(f"✅ OCR処理完了: {output_path}")
            
            return {
                "status": "success",
                "input_path": str(input_path),
                "output_path": str(output_path),
                "text_path": str(txt_output),
                "structured_text": structured
            }
            
        except Exception as e:
            logger.error(f"PDF処理エラー: {e}")
            return {
                "status": "error",
                "error": str(e)
            }

# サービスインスタンス作成ヘルパー
def get_ocr_processor() -> OCRProcessor:
    """OCRプロセッサインスタンス取得"""
    return OCRProcessor()

def extract_text_from_pdf(pdf_path: str, ocr_engine: str = "ocrmypdf") -> Dict[str, Any]:
    """
    PDFからテキストを抽出（簡易版）
    
    Args:
        pdf_path: PDFファイルパス
        ocr_engine: OCRエンジン（現在はocrmypdfのみ対応）
        
    Returns:
        抽出結果の辞書
    """
    processor = get_ocr_processor()
    result = processor.process_pdf(pdf_path)
    
    if result["status"] == "success":
        # 構造化テキストを結合
        text = "\n".join(result.get("structured_text", []))
        return {
            "text": text,
            "structured_text": result.get("structured_text", []),
            "status": "success"
        }
    else:
        return {
            "text": "",
            "error": result.get("error", "Unknown error"),
            "status": "error"
        }