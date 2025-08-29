#!/usr/bin/env python3
"""
OCR結果管理サービス - OCR調整とRAGデータ作成の両用
OCR結果の保存、管理、出力機能を提供
"""

import csv
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path


class OCRResultManager:
    """OCR結果管理サービス（OCR調整・RAGデータ作成両用）"""
    
    def __init__(self, session_id: Optional[str] = None):
        """
        初期化
        
        Args:
            session_id: セッション識別子（RAG作成時は処理バッチID等を使用）
        """
        self.session_id = session_id or f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.results: List[Dict[str, Any]] = []
        self.counter = 0
    
    def add_result(self, ocr_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        OCR結果を追加
        
        Args:
            ocr_result: OCR実行結果
            
        Returns:
            追加された結果データ（カウンタ付き）
        """
        self.counter += 1
        
        result_data = {
            "counter": self.counter,
            "session_id": self.session_id,
            "filename": ocr_result.get("filename", "unknown"),
            "engine": ocr_result.get("engine", "unknown"),
            "page_count": ocr_result.get("page_count", 1),
            "timestamp": ocr_result.get("timestamp") or ocr_result.get("processing_timestamp", datetime.now().isoformat()),
            "original_text": ocr_result.get("original_text", ""),
            "corrected_text": ocr_result.get("corrected_text", ""),
            "corrections": ocr_result.get("corrections", []),
            "file_id": ocr_result.get("file_id", ""),
            "blob_id": ocr_result.get("blob_id", ""),
            "parameters": ocr_result.get("parameters", {}),
            "processing_duration": ocr_result.get("processing_duration", 0),
            "status": ocr_result.get("status", "success")
        }
        
        self.results.append(result_data)
        return result_data
    
    def get_results(self) -> List[Dict[str, Any]]:
        """すべての結果を取得"""
        return self.results.copy()
    
    def get_result_by_counter(self, counter: int) -> Optional[Dict[str, Any]]:
        """カウンタ番号で結果を取得"""
        for result in self.results:
            if result.get("counter") == counter:
                return result
        return None
    
    def get_results_by_engine(self, engine_name: str) -> List[Dict[str, Any]]:
        """エンジン名で結果を絞り込み"""
        return [r for r in self.results if r.get("engine") == engine_name]
    
    def get_successful_results(self) -> List[Dict[str, Any]]:
        """成功した結果のみを取得"""
        return [r for r in self.results if r.get("status") == "success"]
    
    def clear_results(self):
        """すべての結果をクリア"""
        self.results.clear()
        self.counter = 0
    
    def get_result_count(self) -> int:
        """結果数を取得"""
        return len(self.results)
    
    def get_total_text_length(self) -> int:
        """全結果のテキスト総文字数を取得"""
        total = 0
        for result in self.results:
            text = result.get("corrected_text") or result.get("original_text", "")
            total += len(text)
        return total
    
    def export_to_csv(self, file_path: str, include_text: bool = True) -> Dict[str, Any]:
        """
        結果をCSVファイルに出力
        
        Args:
            file_path: 出力ファイルパス
            include_text: テキスト内容を含めるかどうか
            
        Returns:
            出力結果
        """
        try:
            if not self.results:
                return {"status": "error", "error": "出力する結果がありません"}
            
            with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                
                # ヘッダー行
                headers = [
                    '番号', 'セッションID', 'ファイル名', 'OCRエンジン', 'ページ数', 
                    '実行日時', '処理時間(秒)', '誤字修正', 'ステータス'
                ]
                
                if include_text:
                    headers.extend(['OCRテキスト', '修正後テキスト'])
                
                writer.writerow(headers)
                
                # データ行
                for result in self.results:
                    row = [
                        result.get('counter', ''),
                        result.get('session_id', ''),
                        result.get('filename', ''),
                        result.get('engine', ''),
                        result.get('page_count', 0),
                        result.get('timestamp', ''),
                        result.get('processing_duration', 0),
                        'あり' if result.get('corrections') else 'なし',
                        result.get('status', '')
                    ]
                    
                    if include_text:
                        row.extend([
                            result.get('original_text', ''),
                            result.get('corrected_text', '')
                        ])
                    
                    writer.writerow(row)
            
            return {
                "status": "success", 
                "message": f"CSVファイルを保存しました: {file_path}",
                "file_path": file_path,
                "record_count": len(self.results)
            }
            
        except Exception as e:
            return {"status": "error", "error": f"CSVファイル保存エラー: {str(e)}"}
    
    def export_to_json(self, file_path: str) -> Dict[str, Any]:
        """
        結果をJSONファイルに出力（RAGデータ作成用）
        
        Args:
            file_path: 出力ファイルパス
            
        Returns:
            出力結果
        """
        try:
            import json
            
            if not self.results:
                return {"status": "error", "error": "出力する結果がありません"}
            
            export_data = {
                "session_id": self.session_id,
                "export_timestamp": datetime.now().isoformat(),
                "total_results": len(self.results),
                "results": self.results
            }
            
            with open(file_path, 'w', encoding='utf-8') as jsonfile:
                json.dump(export_data, jsonfile, ensure_ascii=False, indent=2)
            
            return {
                "status": "success",
                "message": f"JSONファイルを保存しました: {file_path}",
                "file_path": file_path,
                "record_count": len(self.results)
            }
            
        except Exception as e:
            return {"status": "error", "error": f"JSONファイル保存エラー: {str(e)}"}
    
    def get_statistics(self) -> Dict[str, Any]:
        """結果統計を取得"""
        if not self.results:
            return {"total": 0, "engines": {}, "success_rate": 0}
        
        engines = {}
        successful = 0
        
        for result in self.results:
            engine = result.get("engine", "unknown")
            engines[engine] = engines.get(engine, 0) + 1
            
            if result.get("status") == "success":
                successful += 1
        
        return {
            "total": len(self.results),
            "successful": successful,
            "success_rate": successful / len(self.results) * 100,
            "engines": engines,
            "total_text_length": self.get_total_text_length(),
            "session_id": self.session_id
        }


# 結果管理インスタンス用ファクトリー
def create_result_manager(session_id: Optional[str] = None) -> OCRResultManager:
    """OCR結果管理インスタンス作成"""
    return OCRResultManager(session_id)


if __name__ == "__main__":
    """テスト実行"""
    manager = create_result_manager("test_session")
    print(f"✅ OCR結果管理サービス初期化完了")
    print(f"   - セッションID: {manager.session_id}")
    print(f"   - 機能: 結果管理、CSV/JSON出力、統計情報")
    print(f"   - 用途: OCR調整ページ、RAGデータ作成プロセス両用")
