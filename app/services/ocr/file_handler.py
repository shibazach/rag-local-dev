"""
OCR用ファイルハンドラ - DB連携とファイル処理
UUIDベースのファイル特定・PDFバイナリ取得・一時ファイル管理
"""

import tempfile
import os
from pathlib import Path
from typing import Dict, Any, Optional, Union
from contextlib import contextmanager

from app.config import logger
from app.core.db_simple import get_file_with_blob

class OCRFileHandler:
    """OCR用ファイル処理ハンドラ"""
    
    def __init__(self):
        self._temp_files = []  # 一時ファイル管理用
    
    def get_file_info(self, blob_id: str) -> Optional[Dict[str, Any]]:
        """
        DBからファイル情報を取得
        
        Args:
            blob_id: ファイルのUUID
            
        Returns:
            ファイル情報辞書 or None
        """
        try:
            file_info = get_file_with_blob(blob_id)
            if not file_info:
                logger.warning(f"ファイルが見つかりません: {blob_id}")
                return None
            
            # ファイル情報の正規化
            return {
                "blob_id": file_info["file_id"],
                "filename": file_info["filename"],
                "file_size": file_info["file_size"],
                "content_type": file_info["content_type"],
                "blob_data": file_info["blob_data"],
                "created_at": file_info["created_at"],
                "raw_text": file_info.get("raw_text"),
                "refined_text": file_info.get("refined_text"),
                "quality_score": file_info.get("quality_score"),
                "tags": file_info.get("tags", [])
            }
            
        except Exception as e:
            logger.error(f"ファイル情報取得エラー: {blob_id} - {e}")
            return None
    
    def validate_pdf_file(self, file_info: Dict[str, Any]) -> bool:
        """
        PDFファイルとしての妥当性チェック
        
        Args:
            file_info: ファイル情報辞書
            
        Returns:
            妥当性チェック結果
        """
        # MIMEタイプチェック
        content_type = file_info.get("content_type", "")
        if not content_type.startswith("application/pdf"):
            logger.warning(f"PDF以外のファイル: {content_type}")
            return False
        
        # バイナリデータの存在チェック
        blob_data = file_info.get("blob_data")
        if not blob_data:
            logger.warning("PDFバイナリデータが存在しません")
            return False
        
        # ファイルサイズチェック（空ファイル回避）
        if len(blob_data) < 1024:  # 1KB未満は異常とみなす
            logger.warning(f"PDFファイルサイズが小さすぎます: {len(blob_data)}bytes")
            return False
        
        # PDFヘッダーチェック
        try:
            # memoryviewの場合はbytesに変換
            if isinstance(blob_data, memoryview):
                blob_data = blob_data.tobytes()
            
            if not blob_data.startswith(b'%PDF'):
                logger.warning("PDFヘッダーが見つかりません")
                return False
        except Exception as e:
            logger.error(f"PDFヘッダーチェックエラー: {e}")
            return False
        
        return True
    
    @contextmanager
    def create_temp_pdf(self, blob_data: Union[bytes, memoryview], filename: str = None):
        """
        一時PDFファイル作成（コンテキストマネージャ）
        
        Args:
            blob_data: PDFバイナリデータ
            filename: 元ファイル名（ログ用）
            
        Yields:
            一時PDFファイルパス
        """
        temp_path = None
        try:
            # memoryviewの場合はbytesに変換
            if isinstance(blob_data, memoryview):
                blob_data = blob_data.tobytes()
            
            # 一時ファイル作成
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_file:
                temp_path = temp_file.name
                temp_file.write(blob_data)
            
            self._temp_files.append(temp_path)
            logger.debug(f"一時PDFファイル作成: {temp_path} (元: {filename})")
            
            yield temp_path
            
        except Exception as e:
            logger.error(f"一時PDFファイル作成エラー: {e}")
            raise
        
        finally:
            # クリーンアップ
            if temp_path and os.path.exists(temp_path):
                try:
                    os.unlink(temp_path)
                    if temp_path in self._temp_files:
                        self._temp_files.remove(temp_path)
                    logger.debug(f"一時PDFファイル削除: {temp_path}")
                except Exception as e:
                    logger.warning(f"一時ファイル削除エラー: {e}")
    
    def cleanup_temp_files(self):
        """残存一時ファイルのクリーンアップ"""
        cleanup_count = 0
        for temp_path in self._temp_files.copy():
            try:
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
                    cleanup_count += 1
                self._temp_files.remove(temp_path)
            except Exception as e:
                logger.warning(f"一時ファイルクリーンアップエラー: {temp_path} - {e}")
        
        if cleanup_count > 0:
            logger.info(f"一時ファイルクリーンアップ完了: {cleanup_count}件")
    
    def get_pdf_page_count(self, blob_data: Union[bytes, memoryview]) -> int:
        """
        PDFページ数を取得（PyMuPDFベース）
        
        Args:
            blob_data: PDFバイナリデータ
            
        Returns:
            ページ数
        """
        try:
            import fitz
            
            # memoryviewの場合はbytesに変換
            if isinstance(blob_data, memoryview):
                blob_data = blob_data.tobytes()
            
            doc = fitz.open(stream=blob_data, filetype="pdf")
            page_count = len(doc)
            doc.close()
            
            return page_count
            
        except Exception as e:
            logger.error(f"PDFページ数取得エラー: {e}")
            return 1  # エラー時は1ページとみなす
    
    def extract_pdf_metadata(self, blob_data: Union[bytes, memoryview]) -> Dict[str, Any]:
        """
        PDFメタデータ抽出
        
        Args:
            blob_data: PDFバイナリデータ
            
        Returns:
            メタデータ辞書
        """
        try:
            import fitz
            
            # memoryviewの場合はbytesに変換
            if isinstance(blob_data, memoryview):
                blob_data = blob_data.tobytes()
            
            doc = fitz.open(stream=blob_data, filetype="pdf")
            metadata = doc.metadata
            doc.close()
            
            return {
                "title": metadata.get("title", ""),
                "author": metadata.get("author", ""),
                "subject": metadata.get("subject", ""),
                "creator": metadata.get("creator", ""),
                "producer": metadata.get("producer", ""),
                "creation_date": metadata.get("creationDate", ""),
                "modification_date": metadata.get("modDate", "")
            }
            
        except Exception as e:
            logger.error(f"PDFメタデータ抽出エラー: {e}")
            return {}
    
    def prepare_ocr_data(self, blob_id: str) -> Dict[str, Any]:
        """
        OCR処理用データ準備（メインメソッド）
        
        Args:
            blob_id: ファイルUUID
            
        Returns:
            OCR処理用データ辞書
        """
        try:
            # ファイル情報取得
            file_info = self.get_file_info(blob_id)
            if not file_info:
                return {
                    "status": "error",
                    "error": f"ファイルが見つかりません: {blob_id}"
                }
            
            # PDF妥当性チェック
            if not self.validate_pdf_file(file_info):
                return {
                    "status": "error",
                    "error": f"無効なPDFファイルです: {file_info.get('filename', blob_id)}"
                }
            
            blob_data = file_info["blob_data"]
            
            # 追加情報取得
            page_count = self.get_pdf_page_count(blob_data)
            metadata = self.extract_pdf_metadata(blob_data)
            
            return {
                "status": "success",
                "blob_id": blob_id,
                "filename": file_info["filename"],
                "file_size": file_info["file_size"],
                "blob_data": blob_data,
                "page_count": page_count,
                "metadata": metadata,
                "file_info": file_info
            }
            
        except Exception as e:
            logger.error(f"OCR処理用データ準備エラー: {blob_id} - {e}")
            return {
                "status": "error",
                "error": f"データ準備エラー: {str(e)}"
            }


# サービスインスタンス作成ヘルパー
def get_ocr_file_handler() -> OCRFileHandler:
    """OCRファイルハンドラインスタンス取得"""
    return OCRFileHandler()


if __name__ == "__main__":
    """簡易テスト用"""
    handler = get_ocr_file_handler()
    
    # テスト用UUID（実際のUUIDに置き換えてテスト）
    test_uuid = "00000000-0000-0000-0000-000000000000"
    
    print("テスト実行:")
    result = handler.prepare_ocr_data(test_uuid)
    print(f"結果: {result['status']}")
    
    if result["status"] == "success":
        print(f"ファイル名: {result['filename']}")
        print(f"ページ数: {result['page_count']}")
    else:
        print(f"エラー: {result['error']}")
