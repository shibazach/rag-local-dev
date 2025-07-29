# app/services/async_cancellation.py
# 非同期処理のキャンセル機能

import asyncio
import threading
import time
from typing import Dict, Any, Optional, Callable
from concurrent.futures import ThreadPoolExecutor, Future
import logging

LOGGER = logging.getLogger("async_cancellation")

class AsyncCancellationManager:
    """非同期処理のキャンセル管理"""
    
    def __init__(self):
        self.active_tasks: Dict[str, Future] = {}
        self.cancellation_events: Dict[str, asyncio.Event] = {}
        self.executor = ThreadPoolExecutor(max_workers=4)
        self._lock = threading.Lock()
    
    def register_task(self, task_id: str, task: Future) -> None:
        """タスクを登録"""
        with self._lock:
            self.active_tasks[task_id] = task
            self.cancellation_events[task_id] = asyncio.Event()
    
    def unregister_task(self, task_id: str) -> None:
        """タスクを登録解除"""
        with self._lock:
            self.active_tasks.pop(task_id, None)
            self.cancellation_events.pop(task_id, None)
    
    def cancel_task(self, task_id: str) -> bool:
        """タスクをキャンセル"""
        with self._lock:
            if task_id in self.active_tasks:
                task = self.active_tasks[task_id]
                cancelled = task.cancel()
                if cancelled:
                    LOGGER.info(f"タスク {task_id} をキャンセルしました")
                return cancelled
            return False
    
    def cancel_all_tasks(self) -> int:
        """全タスクをキャンセル"""
        with self._lock:
            cancelled_count = 0
            for task_id, task in self.active_tasks.items():
                if task.cancel():
                    cancelled_count += 1
                    LOGGER.info(f"タスク {task_id} をキャンセルしました")
            return cancelled_count
    
    def is_cancelled(self, task_id: str) -> bool:
        """タスクがキャンセルされているかチェック"""
        with self._lock:
            if task_id in self.cancellation_events:
                return self.cancellation_events[task_id].is_set()
            return False
    
    def set_cancelled(self, task_id: str) -> None:
        """タスクをキャンセル状態に設定"""
        with self._lock:
            if task_id in self.cancellation_events:
                self.cancellation_events[task_id].set()
    
    async def run_with_cancellation(
        self, 
        task_id: str, 
        func: Callable, 
        *args, 
        timeout: Optional[float] = None,
        **kwargs
    ) -> Any:
        """キャンセル可能な非同期処理を実行"""
        
        # キャンセルイベントを作成
        cancel_event = asyncio.Event()
        self.cancellation_events[task_id] = cancel_event
        
        try:
            # タイムアウト付きで実行
            if timeout:
                result = await asyncio.wait_for(
                    self._run_in_executor(func, *args, **kwargs),
                    timeout=timeout
                )
            else:
                result = await self._run_in_executor(func, *args, **kwargs)
            
            return result
            
        except asyncio.CancelledError:
            LOGGER.info(f"タスク {task_id} がキャンセルされました")
            raise
        except asyncio.TimeoutError:
            LOGGER.warning(f"タスク {task_id} がタイムアウトしました")
            raise
        finally:
            self.unregister_task(task_id)
    
    async def _run_in_executor(self, func: Callable, *args, **kwargs) -> Any:
        """スレッドプールで関数を実行"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.executor, func, *args, **kwargs)
    
    def cleanup(self):
        """リソースをクリーンアップ"""
        self.executor.shutdown(wait=False)

# グローバルインスタンス
cancellation_manager = AsyncCancellationManager()

class OllamaCancellationHelper:
    """Ollama処理のキャンセルヘルパー"""
    
    def __init__(self, task_id: str):
        self.task_id = task_id
        self.cancel_event = asyncio.Event()
    
    async def check_cancellation(self):
        """キャンセルチェック"""
        if self.cancel_event.is_set():
            raise asyncio.CancelledError(f"タスク {self.task_id} がキャンセルされました")
    
    def cancel(self):
        """キャンセル実行"""
        self.cancel_event.set()
        cancellation_manager.cancel_task(self.task_id)
    
    async def run_ollama_with_cancellation(
        self, 
        ollama_func: Callable, 
        *args, 
        timeout: float = 300,
        **kwargs
    ) -> Any:
        """キャンセル可能なOllama処理を実行"""
        
        try:
            return await cancellation_manager.run_with_cancellation(
                self.task_id,
                ollama_func,
                *args,
                timeout=timeout,
                **kwargs
            )
        except asyncio.CancelledError:
            LOGGER.info(f"Ollama処理 {self.task_id} がキャンセルされました")
            raise
        except Exception as e:
            LOGGER.error(f"Ollama処理 {self.task_id} でエラー: {e}")
            raise

# 使用例
async def example_ollama_cancellation():
    """使用例"""
    helper = OllamaCancellationHelper("example_task")
    
    try:
        # キャンセル可能なOllama処理を実行
        result = await helper.run_ollama_with_cancellation(
            lambda: "Ollama処理の結果",
            timeout=60
        )
        return result
    except asyncio.CancelledError:
        print("処理がキャンセルされました")
        return None 