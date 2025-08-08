"""
ファイルサービス - db_simpleベースのシンプル版
"""
import hashlib
import os
import tempfile
import uuid
from pathlib import Path
from typing import Dict, Any, Optional, List, BinaryIO
from app.config import config, logger
from app.core.db_simple import (
    get_file_list,
    get_file_with_blob,
    check_file_exists,
    insert_file_blob,
    insert_file_meta,
    insert_file_text,
    delete_file,
    get_files_for_export
)

class FileService:
    """ファイル管理サービス（シンプル版）"""
    
    def __init__(self):
        """初期化"""
        self.upload_dir = config.UPLOAD_DIR
        self.processed_dir = config.PROCESSED_DIR
        
        # ディレクトリ作成
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.processed_dir.mkdir(parents=True, exist_ok=True)
    
        # サポート対象拡張子
        self.supported_extensions = set(config.ALLOWED_EXTENSIONS)
    
    def upload_file(self, file_data: BinaryIO, filename: str, content_type: str = None) -> Dict[str, Any]:
        """
        ファイルアップロード
        
        Args:
            file_data: ファイルデータ
            filename: ファイル名
            content_type: MIMEタイプ
            
        Returns:
            アップロード結果
        """
        try:
            # ファイルバリデーション
            file_ext = Path(filename).suffix.lower()
            if file_ext not in self.supported_extensions:
                return {
                    "status": "error",
                    "message": f"サポートされていない拡張子です: {file_ext}"
                }
            
            # ファイルデータを読み込み
            file_data.seek(0)
            file_content = file_data.read()
            file_size = len(file_content)
            
            # チェックサム計算
            checksum = hashlib.sha256(file_content).hexdigest()
            
            # 重複チェック
            existing_id = check_file_exists(checksum)
            if existing_id:
                return {
                    "status": "duplicate",
                    "message": f"ファイル '{filename}' は既に存在します",
                    "file_id": existing_id,
                    "is_existing": True
                }
            
            # 新規ファイルとして保存
            file_id = str(uuid.uuid4())
            
            # DB保存
            if not insert_file_blob(file_id, checksum, file_content):
                return {
                    "status": "error",
                    "message": "ファイルBLOBの保存に失敗しました"
                }
            
            if not insert_file_meta(file_id, filename, content_type or "application/octet-stream", file_size):
                # ロールバック的な処理
                delete_file(file_id)
                return {
                    "status": "error",
                    "message": "ファイルメタデータの保存に失敗しました"
                }
            
            logger.info(f"ファイルアップロード成功: {filename} (ID: {file_id})")
            
            return {
                "status": "success",
                "message": f"ファイル '{filename}' をアップロードしました",
                "file_id": file_id,
                "file_name": filename,
                "size": file_size,
                "checksum": checksum,
                "is_existing": False
            }
            
        except Exception as e:
            logger.error(f"ファイルアップロードエラー: {e}")
            return {
                "status": "error",
                "message": f"アップロードに失敗しました: {str(e)}"
            }
    
    def get_file_list(self, limit: int = 100, offset: int = 0) -> Dict[str, Any]:
        """
        ファイルリスト取得（db_simpleのラッパー）
        """
        return get_file_list(limit, offset)
    
    def get_file_info(self, file_id: str) -> Optional[Dict[str, Any]]:
        """
        ファイル情報取得（blob含む）
        """
        return get_file_with_blob(file_id)
    
    def delete_file(self, file_id: str) -> Dict[str, Any]:
        """
        ファイル削除
        """
        try:
            if delete_file(file_id):
                return {
                    "status": "success",
                    "message": "ファイルを削除しました"
                }
            else:
                return {
                    "status": "error",
                    "message": "ファイルが見つかりません"
                }
        except Exception as e:
            logger.error(f"ファイル削除エラー: {e}")
            return {
                "status": "error",
                "message": f"削除に失敗しました: {str(e)}"
            }
    
    def update_file_text(self, file_id: str, raw_text: str = None, refined_text: str = None) -> Dict[str, Any]:
        """
        ファイルテキスト更新
        """
        try:
            if insert_file_text(file_id, raw_text, refined_text):
                return {
                    "status": "success",
                    "message": "テキストを更新しました"
                }
            else:
                return {
                    "status": "error",
                    "message": "テキスト更新に失敗しました"
                }
        except Exception as e:
            logger.error(f"テキスト更新エラー: {e}")
            return {
                "status": "error",
                "message": f"更新に失敗しました: {str(e)}"
            }
    
    def upload_batch_files(self, files) -> Dict[str, Any]:
        """
        バッチファイルアップロード
        """
        results = []
        for file in files:
            result = self.upload_file(file.file, file.filename, file.content_type)
            results.append(result)
        
        successful = [r for r in results if r["status"] == "success"]
        duplicates = [r for r in results if r["status"] == "duplicate"]
        failed = [r for r in results if r["status"] == "error"]
        
        return {
            "status": "success",
            "message": f"アップロード完了: 成功 {len(successful)}件, 重複 {len(duplicates)}件, 失敗 {len(failed)}件",
            "results": results,
            "summary": {
                "total": len(results),
                "successful": len(successful),
                "duplicates": len(duplicates),
                "failed": len(failed)
            }
        }
    
    def upload_folder(self, folder_path: str, include_subfolders: bool = False) -> Dict[str, Any]:
        """
        フォルダアップロード（サーバー側）
        """
        try:
            import os
            from pathlib import Path
            
            folder = Path(folder_path)
            if not folder.exists() or not folder.is_dir():
                return {
                    "status": "error",
                    "message": f"フォルダが見つかりません: {folder_path}"
                }
            
            files_to_upload = []
            if include_subfolders:
                for file_path in folder.rglob("*"):
                    if file_path.is_file() and file_path.suffix.lower() in self.supported_extensions:
                        files_to_upload.append(file_path)
            else:
                for file_path in folder.iterdir():
                    if file_path.is_file() and file_path.suffix.lower() in self.supported_extensions:
                        files_to_upload.append(file_path)
            
            results = []
            for file_path in files_to_upload:
                with open(file_path, 'rb') as f:
                    result = self.upload_file(f, file_path.name)
                    results.append(result)
            
            successful = [r for r in results if r["status"] == "success"]
            duplicates = [r for r in results if r["status"] == "duplicate"]
            failed = [r for r in results if r["status"] == "error"]
            
            return {
                "status": "success",
                "message": f"フォルダアップロード完了: 成功 {len(successful)}件, 重複 {len(duplicates)}件, 失敗 {len(failed)}件",
                "results": results,
                "summary": {
                    "total": len(results),
                    "successful": len(successful),
                    "duplicates": len(duplicates),
                    "failed": len(failed)
                }
            }
        except Exception as e:
            logger.error(f"フォルダアップロードエラー: {e}")
            return {
                "status": "error",
                "message": f"アップロードに失敗しました: {str(e)}"
            }
    
    def get_upload_status(self) -> Dict[str, Any]:
        """
        アップロード機能ステータス取得
        """
        return {
            "status": "active",
            "data": {
                "supported_extensions": list(self.supported_extensions),
                "max_file_size": "100MB",
                "max_batch_size": 50
            }
        }
    
    def list_server_folders(self, path: str = "/") -> Dict[str, Any]:
        """
        サーバーフォルダリスト取得
        """
        try:
            import os
            from pathlib import Path
            
            base_path = Path(path)
            if not base_path.exists():
                return {
                    "status": "error",
                    "message": f"パスが見つかりません: {path}"
                }
            
            folders = []
            files = []
            
            for item in base_path.iterdir():
                if item.is_dir():
                    folders.append({
                        "name": item.name,
                        "path": str(item),
                        "type": "folder"
                    })
                elif item.is_file() and item.suffix.lower() in self.supported_extensions:
                    files.append({
                        "name": item.name,
                        "path": str(item),
                        "type": "file",
                        "size": item.stat().st_size
                    })
            
            return {
                "status": "success",
                "data": {
                    "current_path": str(base_path),
                    "folders": sorted(folders, key=lambda x: x["name"]),
                    "files": sorted(files, key=lambda x: x["name"]),
                    "parent": str(base_path.parent) if base_path.parent != base_path else None
                }
            }
        except Exception as e:
            logger.error(f"フォルダリスト取得エラー: {e}")
            return {
                "status": "error",
                "message": f"フォルダリスト取得に失敗しました: {str(e)}"
            }
    
    def export_files(self) -> List[Dict[str, Any]]:
        """
        エクスポート用ファイルリスト取得
        """
        return get_files_for_export()
    
    def calculate_checksum(self, file_path: str) -> str:
        """
        ファイルのチェックサム計算
        """
        with open(file_path, 'rb') as f:
            return hashlib.sha256(f.read()).hexdigest()

# シングルトンインスタンス
_file_service_instance = None

def get_file_service() -> FileService:
    """FileServiceのシングルトンインスタンスを取得"""
    global _file_service_instance
    if _file_service_instance is None:
        _file_service_instance = FileService()
    return _file_service_instance