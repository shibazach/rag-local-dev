#!/usr/bin/env python3
"""
OCRオーケストレーター - OCR調整とRAGデータ作成の両用サービス
UI層とRAGプロセスから共通して利用される汎用OCRサービス
"""

import asyncio
from typing import Dict, Any, Optional, Callable, List
from datetime import datetime

from app.services.ocr.ocr_simple import get_unified_ocr_service
from app.services.ocr.file_handler import get_ocr_file_handler


class OCROrchestrator:
    """OCR処理統合管理サービス（OCR調整・RAGデータ作成両用）"""
    
    def __init__(self):
        """初期化"""
        self.ocr_service = get_unified_ocr_service()
        self.file_handler = get_ocr_file_handler()
    
    def get_engine_parameters(self, engine_name: str) -> Dict[str, Any]:
        """エンジン別パラメータ取得（両用）"""
        if engine_name == "OCRMyPDF":
            return {
                "language": "jpn",
                "dpi": 300,
                "force_ocr": True
            }
        elif engine_name == "EasyOCR":
            return {
                "languages": ["ja", "en"],
                "gpu": False
            }
        elif engine_name == "Tesseract":
            return {
                "language": "jpn",
                "config": "--psm 6"
            }
        elif engine_name == "PaddleOCR":
            return {
                "use_angle_cls": True,
                "lang": "japan"
            }
        else:
            return {}
    
    async def execute_ocr_for_file(self, 
                                  file_id: str,
                                  engine_name: str = "OCRMyPDF",
                                  enable_spell_correction: bool = True,
                                  custom_parameters: Optional[Dict[str, Any]] = None,
                                  progress_callback: Optional[Callable[[str], None]] = None,
                                  error_callback: Optional[Callable[[str], None]] = None) -> Dict[str, Any]:
        """
        ファイルIDからOCR実行（OCR調整・RAGデータ作成両用）
        
        Args:
            file_id: DBファイルID
            engine_name: OCRエンジン名
            enable_spell_correction: 誤字修正有効フラグ
            custom_parameters: カスタムパラメータ（オプション）
            progress_callback: 進捗通知コールバック
            error_callback: エラー通知コールバック
            
        Returns:
            OCR実行結果辞書
        """
        try:
            if progress_callback:
                progress_callback("OCR処理を開始しています...")
            
            # ファイルデータ準備
            file_data = self.file_handler.prepare_ocr_data(file_id)
            if file_data["status"] != "success":
                error_msg = f"ファイル準備エラー: {file_data['error']}"
                if error_callback:
                    error_callback(error_msg)
                return {"status": "error", "error": error_msg}
            
            if progress_callback:
                progress_callback(f"OCR実行中（{engine_name}エンジン）...")
            
            # エンジンパラメータ取得
            engine_params = custom_parameters or self.get_engine_parameters(engine_name)
            
            # OCR実行
            result = self.ocr_service.process_pdf(
                blob_data=file_data["blob_data"],
                engine_name=engine_name,
                parameters=engine_params,
                enable_spell_correction=enable_spell_correction
            )
            
            if result["status"] != "success":
                if error_callback:
                    error_callback(f"OCRエラー: {result['error']}")
                return result
            
            # 成功結果に追加情報を付与
            result.update({
                "file_id": file_id,
                "filename": file_data.get("filename", "unknown"),
                "page_count": file_data.get("page_count", 1),
                "blob_id": file_data.get("blob_id", ""),
                "processing_timestamp": datetime.now().isoformat()
            })
            
            return result
            
        except Exception as e:
            error_msg = f"予期しないエラー: {str(e)}"
            if error_callback:
                error_callback(error_msg)
            return {"status": "error", "error": error_msg}
    
    async def execute_ocr_for_pdf_bytes(self,
                                       pdf_bytes: bytes,
                                       filename: str = "document.pdf",
                                       engine_name: str = "OCRMyPDF",
                                       enable_spell_correction: bool = True,
                                       custom_parameters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        PDFバイナリから直接OCR実行（RAGデータ作成用）
        
        Args:
            pdf_bytes: PDFバイナリデータ
            filename: ファイル名
            engine_name: OCRエンジン名
            enable_spell_correction: 誤字修正有効フラグ
            custom_parameters: カスタムパラメータ
            
        Returns:
            OCR実行結果辞書
        """
        try:
            # エンジンパラメータ取得
            engine_params = custom_parameters or self.get_engine_parameters(engine_name)
            
            # OCR実行
            result = self.ocr_service.process_pdf(
                blob_data=pdf_bytes,
                engine_name=engine_name,
                parameters=engine_params,
                enable_spell_correction=enable_spell_correction
            )
            
            if result["status"] == "success":
                result.update({
                    "filename": filename,
                    "processing_timestamp": datetime.now().isoformat()
                })
            
            return result
            
        except Exception as e:
            return {"status": "error", "error": f"OCR実行エラー: {str(e)}"}
    
    async def batch_process_files(self,
                                 file_ids: List[str],
                                 engine_name: str = "OCRMyPDF",
                                 enable_spell_correction: bool = True,
                                 progress_callback: Optional[Callable[[str], None]] = None) -> List[Dict[str, Any]]:
        """
        複数ファイルの一括OCR処理（RAGデータ作成用）
        
        Args:
            file_ids: ファイルIDリスト
            engine_name: OCRエンジン名
            enable_spell_correction: 誤字修正有効フラグ
            progress_callback: 進捗通知コールバック
            
        Returns:
            OCR結果リスト
        """
        results = []
        total_files = len(file_ids)
        
        for i, file_id in enumerate(file_ids, 1):
            if progress_callback:
                progress_callback(f"処理中 {i}/{total_files}: {file_id}")
            
            result = await self.execute_ocr_for_file(
                file_id=file_id,
                engine_name=engine_name,
                enable_spell_correction=enable_spell_correction
            )
            
            results.append(result)
        
        return results


# オーケストレーターインスタンス取得
_orchestrator_instance = None

def get_ocr_orchestrator() -> OCROrchestrator:
    """OCRオーケストレーターインスタンス取得（シングルトン）"""
    global _orchestrator_instance
    if _orchestrator_instance is None:
        _orchestrator_instance = OCROrchestrator()
    return _orchestrator_instance


if __name__ == "__main__":
    """テスト実行"""
    orchestrator = get_ocr_orchestrator()
    print(f"✅ OCRオーケストレーター初期化完了")
    print(f"   - 対応エンジン: OCRMyPDF, EasyOCR, Tesseract, PaddleOCR")
    print(f"   - 用途: OCR調整ページ、RAGデータ作成プロセス両用")
    print(f"   - 機能: ファイルベースOCR、バイナリベースOCR、一括処理")
