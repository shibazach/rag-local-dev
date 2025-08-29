"""
シンプルOCRサービス - OCRMyPDFベース
確実に動作することを保証した最小限実装
"""

import os
import subprocess
import tempfile
import fitz  # PyMuPDF
from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path

from app.config import config, logger

class SimpleOCRService:
    """シンプルOCRサービス（OCRMyPDFベース）"""
    
    def __init__(self):
        self.language = config.OCR_LANGUAGE
        self.dpi = config.OCR_DPI
        self.optimize = config.OCR_OPTIMIZE
    
    def check_ocrmypdf_available(self) -> bool:
        """OCRMyPDF利用可能性チェック"""
        try:
            result = subprocess.run(
                ["ocrmypdf", "--version"], 
                capture_output=True, 
                text=True, 
                timeout=10
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def process_pdf_bytes(self, pdf_bytes: bytes, filename: str = "document.pdf") -> Dict[str, Any]:
        """
        PDFバイナリからOCR処理を実行
        
        Args:
            pdf_bytes: PDFバイナリデータ
            filename: ファイル名（ログ用）
            
        Returns:
            処理結果辞書
        """
        temp_input = None
        temp_output = None
        
        try:
            # OCRMyPDF利用可能性チェック
            if not self.check_ocrmypdf_available():
                return {
                    "status": "error",
                    "error": "OCRMyPDFが利用できません。システム管理者に確認してください。",
                    "engine": "OCRMyPDF",
                    "timestamp": datetime.now().isoformat()
                }
            
            # 入力用一時ファイル作成
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_in:
                temp_input = temp_in.name
                temp_in.write(pdf_bytes)
            
            # 出力用一時ファイル作成
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_out:
                temp_output = temp_out.name
            
            # OCRMyPDF実行（最適化は環境によるエラーを避けるため無効）
            cmd = [
                "ocrmypdf",
                "--force-ocr",  # 既存テキストを無視してOCR実行
                "-l", self.language,
                "--image-dpi", str(self.dpi),  # 正しいオプション名
                "--quiet",  # 詳細ログを抑制
                temp_input,
                temp_output
            ]
            
            logger.info(f"OCR実行開始: {filename}")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5分タイムアウト
            )
            
            if result.returncode != 0:
                error_msg = result.stderr or "OCR処理でエラーが発生しました"
                logger.error(f"OCR失敗: {error_msg}")
                return {
                    "status": "error",
                    "error": f"OCR処理エラー: {error_msg}",
                    "engine": "OCRMyPDF",
                    "timestamp": datetime.now().isoformat()
                }
            
            # テキスト抽出
            doc = fitz.open(temp_output)
            all_text = []
            
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                text = page.get_text().strip()
                if text:  # 空でないページのみ追加
                    all_text.append(f"=== ページ {page_num + 1} ===\n{text}")
            
            doc.close()
            
            if not all_text:
                return {
                    "status": "error",
                    "error": "OCR処理は完了しましたが、テキストを抽出できませんでした",
                    "engine": "OCRMyPDF",
                    "timestamp": datetime.now().isoformat()
                }
            
            combined_text = "\n\n".join(all_text)
            
            logger.info(f"OCR完了: {filename} - {len(all_text)}ページ、{len(combined_text)}文字")
            
            return {
                "status": "success",
                "engine": "OCRMyPDF",
                "original_text": combined_text,
                "corrected_text": combined_text,  # 誤字修正は後で実装
                "corrections": [],
                "page_count": len(all_text),
                "parameters": {
                    "language": self.language,
                    "dpi": self.dpi,
                    "optimize": self.optimize
                },
                "timestamp": datetime.now().isoformat()
            }
            
        except subprocess.TimeoutExpired:
            logger.error(f"OCRタイムアウト: {filename}")
            return {
                "status": "error",
                "error": "OCR処理がタイムアウトしました（5分）",
                "engine": "OCRMyPDF",
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"OCR予期しないエラー: {filename} - {e}")
            return {
                "status": "error",
                "error": f"予期しないエラー: {str(e)}",
                "engine": "OCRMyPDF",
                "timestamp": datetime.now().isoformat()
            }
        
        finally:
            # クリーンアップ
            for temp_file in [temp_input, temp_output]:
                if temp_file and os.path.exists(temp_file):
                    try:
                        os.unlink(temp_file)
                    except Exception as e:
                        logger.warning(f"一時ファイル削除エラー: {temp_file} - {e}")
    
    def apply_spell_correction(self, text: str) -> Dict[str, Any]:
        """
        誤字修正適用（OCR辞書ベース）
        
        Args:
            text: 元テキスト
            
        Returns:
            修正結果辞書
        """
        try:
            # OCR誤字辞書の読み込み
            dict_path = Path(__file__).parent.parent.parent / "config" / "ocr" / "dic" / "ocr_word_mistakes.csv"
            
            if not dict_path.exists():
                logger.warning(f"誤字辞書が見つかりません: {dict_path}")
                return {
                    "corrected_text": text,
                    "corrections": []
                }
            
            corrections = []
            corrected_text = text
            
            # 辞書読み込みと適用
            import csv
            with open(dict_path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                next(reader, None)  # ヘッダーをスキップ
                
                for row in reader:
                    if len(row) >= 2:
                        wrong, correct = row[0].strip(), row[1].strip()
                        if wrong and correct and wrong in corrected_text:
                            old_text = corrected_text
                            corrected_text = corrected_text.replace(wrong, correct)
                            if old_text != corrected_text:
                                corrections.append({
                                    "type": "dictionary",
                                    "wrong": wrong,
                                    "correct": correct
                                })
                                logger.debug(f"誤字修正: {wrong} → {correct}")
            
            if corrections:
                logger.info(f"誤字修正完了: {len(corrections)}箇所")
            
            return {
                "corrected_text": corrected_text,
                "corrections": corrections
            }
            
        except Exception as e:
            logger.error(f"誤字修正エラー: {e}")
            return {
                "corrected_text": text,
                "corrections": []
            }

# サービスインスタンス取得
def get_simple_ocr_service() -> SimpleOCRService:
    """シンプルOCRサービスインスタンス取得"""
    return SimpleOCRService()


# 統合インターフェース（既存実装との互換性）
class UnifiedOCRService:
    """統合OCRサービス（フォールバック対応）"""
    
    def __init__(self):
        self.simple_service = get_simple_ocr_service()
    
    def process_pdf(self, blob_data: bytes, engine_name: str, parameters: Dict[str, Any], 
                   enable_spell_correction: bool = True, page_range: Optional[str] = None) -> Dict[str, Any]:
        """
        PDFのOCR処理を実行（統合インターフェース）
        """
        # まず基本的なOCR処理を実行
        result = self.simple_service.process_pdf_bytes(blob_data)
        
        if result["status"] != "success":
            return result
        
        # 誤字修正適用
        if enable_spell_correction:
            correction_result = self.simple_service.apply_spell_correction(result["original_text"])
            result.update(correction_result)
        
        return result

# 統合サービスインスタンス取得
def get_unified_ocr_service() -> UnifiedOCRService:
    """統合OCRサービスインスタンス取得"""
    return UnifiedOCRService()


if __name__ == "__main__":
    """テスト実行"""
    service = get_simple_ocr_service()
    
    # OCRMyPDF利用可能性チェック
    if service.check_ocrmypdf_available():
        print("✅ OCRMyPDF利用可能")
    else:
        print("❌ OCRMyPDF利用不可")
    
    print(f"設定: 言語={service.language}, DPI={service.dpi}, 最適化={service.optimize}")
