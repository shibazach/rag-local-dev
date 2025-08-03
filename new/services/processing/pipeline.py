# new/services/processing/pipeline.py
# 処理パイプライン統合管理

import asyncio
import logging
import time
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
        pipeline_start_time = time.time()  # パイプライン開始時刻記録
        results = []  # 結果を保存するリスト
        
        try:
            # 開始イベント
            start_event = {
                'type': 'start',
                'data': {
                    'total_files': total_files,
                    'settings': settings
                }
            }
            self.logger.debug(f"[DEBUG-PIPELINE] 開始イベント生成: {total_files}件")
            yield start_event
            
            for idx, file_info in enumerate(files, 1):
                # キャンセルチェック
                if self.abort_flag['flag']:
                    yield {
                        'type': 'cancelled',
                        'message': '処理がキャンセルされました'
                    }
                    break
                
                # ファイル処理開始
                file_id = str(file_info['file_id'])
                file_name = file_info['file_name']
                file_path = file_info['file_path']
                
                yield {
                    'type': 'file_start',
                    'data': {
                        'file_name': file_name,
                        'file_id': file_id,  # file_idを追加
                        'file_index': idx,
                        'total_files': total_files,
                        'progress': round((idx - 1) / total_files * 100, 1)
                    }
                }
                
                # 個別ファイル処理の進捗処理は後で実装
                # 現在は直接処理実行
                
                # ファイル処理実行 + 詳細手順イベント送信（重複イベント削除）
                
                # 詳細手順を受信するコールバック作成
                progress_events = []
                
                def progress_callback(event_data):
                    """processor からの詳細手順を収集"""
                    progress_events.append({
                        'type': 'file_progress',
                        'data': {
                            'file_name': file_name,
                            'file_index': idx,
                            'step': event_data.get('step'),
                            'detail': event_data.get('detail'),
                            'progress': event_data.get('progress'),
                            'ocr_text': event_data.get('ocr_text'),  # OCRテキスト
                            'llm_prompt': event_data.get('llm_prompt'),  # LLMプロンプト
                            'llm_result': event_data.get('llm_result')   # LLM結果
                        }
                    })
                
                result = await self.processor.process_file(
                    file_id=file_id,
                    file_name=file_name,
                    file_path=file_path,
                    settings=settings,
                    progress_callback=progress_callback,  # コールバック有効化
                    abort_flag=self.abort_flag
                )
                
                # 収集した詳細手順イベントを送信（processorからのリアルタイムイベントのみ）
                for progress_event in progress_events:
                    yield progress_event
                
                # 結果を保存
                results.append(result)
                
                # ファイル完了イベント
                event_data = {
                    'type': 'file_complete',
                    'data': {
                        'file_name': file_name,
                        'file_index': idx,
                        'total_files': total_files,
                        'progress': round(idx / total_files * 100, 1),
                        'result': result
                    }
                }
                self.logger.debug(f"[DEBUG-PIPELINE] イベント生成: {event_data['type']}, ファイル: {file_name}")
                yield event_data
                
                # エラーチェック
                if result['status'] == 'error':
                    self.logger.error(f"ファイル処理エラー [{file_name}]: {result['error']}")
                elif result['status'] == 'cancelled':
                    self.logger.info(f"ファイル処理キャンセル [{file_name}]")
                    break
            
            # 全体完了
            if not self.abort_flag['flag']:
                pipeline_end_time = time.time()
                total_pipeline_time = pipeline_end_time - pipeline_start_time
                
                successful_files = len([r for r in results if r.get('success', False)])
                failed_files = len([r for r in results if not r.get('success', False)])
                
                completion_message = f"全{total_files}ファイル処理完了 (成功: {successful_files}, 失敗: {failed_files}) - グランドトータル: {total_pipeline_time:.1f}秒"
                
                complete_event = {
                    'type': 'complete',
                    'data': {
                        'total_files': total_files,
                        'successful_files': successful_files,
                        'failed_files': failed_files,
                        'total_pipeline_time': total_pipeline_time,
                        'average_time_per_file': total_pipeline_time / total_files if total_files > 0 else 0,
                        'message': completion_message
                    }
                }
                self.logger.info(f"📊 パイプライン完了: {completion_message}")
                yield complete_event
            
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