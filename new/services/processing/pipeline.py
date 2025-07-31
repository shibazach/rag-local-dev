# new/services/processing/pipeline.py
# 処理パイプライン統合管理

import asyncio
import logging
from typing import Dict, List, AsyncGenerator, Optional

from .processor import FileProcessor
from new.config import LOGGER

class ProcessingPipeline:
    """ファイル処理パイプライン統合管理"""
    
    def __init__(self):
        self.processor = FileProcessor()
        self.logger = logging.getLogger(__name__)
        self.current_job = None
        self.abort_flag = None
    
    async def process_files(
        self,
        files: List[Dict],
        settings: Dict,
        progress_callback: Optional[callable] = None
    ) -> AsyncGenerator[Dict, None]:
        """
        複数ファイルを順次処理
        
        Args:
            files: ファイル情報リスト
            settings: 処理設定
            progress_callback: 進捗コールバック
            
        Yields:
            処理進捗イベント
        """
        total_files = len(files)
        self.abort_flag = {'flag': False}
        
        try:
            # 開始イベント
            yield {
                'type': 'start',
                'data': {
                    'total_files': total_files,
                    'settings': settings
                }
            }
            
            for idx, file_info in enumerate(files, 1):
                # キャンセルチェック
                if self.abort_flag['flag']:
                    yield {
                        'type': 'cancelled',
                        'message': '処理がキャンセルされました'
                    }
                    break
                
                # ファイル処理開始
                file_id = str(file_info.file_id)
                file_name = file_info.file_name
                file_path = file_info.file_path
                
                yield {
                    'type': 'file_start',
                    'data': {
                        'file_name': file_name,
                        'file_index': idx,
                        'total_files': total_files,
                        'progress': round((idx - 1) / total_files * 100, 1)
                    }
                }
                
                # 個別ファイル処理の進捗処理は後で実装
                # 現在は直接処理実行
                
                # ファイル処理実行
                result = await self.processor.process_file(
                    file_id=file_id,
                    file_name=file_name,
                    file_path=file_path,
                    settings=settings,
                    progress_callback=None,  # 簡略化のため一時的にNone
                    abort_flag=self.abort_flag
                )
                
                # ファイル完了イベント
                yield {
                    'type': 'file_complete',
                    'data': {
                        'file_name': file_name,
                        'file_index': idx,
                        'total_files': total_files,
                        'progress': round(idx / total_files * 100, 1),
                        'result': result
                    }
                }
                
                # エラーチェック
                if result['status'] == 'error':
                    self.logger.error(f"ファイル処理エラー [{file_name}]: {result['error']}")
                elif result['status'] == 'cancelled':
                    self.logger.info(f"ファイル処理キャンセル [{file_name}]")
                    break
            
            # 全体完了
            if not self.abort_flag['flag']:
                yield {
                    'type': 'complete',
                    'data': {
                        'total_files': total_files,
                        'message': 'すべての処理が完了しました'
                    }
                }
            
        except Exception as e:
            self.logger.error(f"パイプライン処理エラー: {e}")
            yield {
                'type': 'error',
                'message': f'処理エラー: {str(e)}'
            }
    
    def cancel_processing(self):
        """処理をキャンセル"""
        if self.abort_flag:
            self.abort_flag['flag'] = True
            self.logger.info("処理キャンセル要求")
    
    def is_processing(self) -> bool:
        """処理中かどうか"""
        return self.current_job is not None