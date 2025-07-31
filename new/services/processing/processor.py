# new/services/processing/processor.py
# ファイル処理プロセッサ（新系）

import asyncio
import time
import logging
import unicodedata
from pathlib import Path
from typing import Dict, List, Optional, AsyncGenerator
import uuid

from services.ocr import OCREngineFactory
from database.connection import get_db_connection
from config import LOGGER, DB_ENGINE

class FileProcessor:
    """新系ファイル処理プロセッサ"""
    
    def __init__(self):
        self.ocr_factory = OCREngineFactory()
        self.logger = logging.getLogger(__name__)
    
    async def process_file(
        self,
        file_id: str,
        file_name: str,
        file_path: str,
        settings: Dict,
        progress_callback: Optional[callable] = None,
        abort_flag: Optional[Dict] = None,
        save_to_db: bool = True
    ) -> Dict:
        """
        1つのファイルを処理する
        
        Args:
            file_id: ファイルID
            file_name: ファイル名
            file_path: ファイルパス
            settings: 処理設定
            progress_callback: 進捗コールバック
            abort_flag: 中断フラグ
            
        Returns:
            処理結果辞書
        """
        start_time = time.perf_counter()
        result = {
            'success': False,
            'file_id': file_id,
            'file_name': file_name,
            'status': 'processing',
            'steps': {},
            'text_length': 0,
            'processing_time': 0,
            'error': None,
            'ocr_result': {},
            'llm_refined_text': '',
            'quality_score': 0.0
        }
        
        try:
            # 中断チェック
            if abort_flag and abort_flag.get('flag', False):
                result['status'] = 'cancelled'
                return result
            
            # 1. OCR処理
            await self._emit_progress(progress_callback, file_name, "OCR処理開始", 10)
            ocr_result = await self._process_ocr(file_path, settings, abort_flag)
            
            if not ocr_result['success']:
                result['status'] = 'error'
                result['error'] = ocr_result['error']
                return result
            
            result['steps']['ocr'] = {
                'success': True,
                'processing_time': ocr_result['processing_time'],
                'text_length': len(ocr_result['text'])
            }
            
            raw_text = ocr_result['text']
            result['text_length'] = len(raw_text)
            
            # 中断チェック
            if abort_flag and abort_flag.get('flag', False):
                result['status'] = 'cancelled'
                return result
            
            # 2. テキスト正規化
            await self._emit_progress(progress_callback, file_name, "テキスト正規化", 40)
            normalized_text = self._normalize_text(raw_text)
            
            # 3. LLM整形処理（模擬実装）
            await self._emit_progress(progress_callback, file_name, "LLM整形処理", 60)
            refined_text = await self._process_llm_refinement(normalized_text, settings, abort_flag)
            
            if not refined_text:
                # LLM失敗時は正規化テキストを使用
                refined_text = normalized_text
                self.logger.warning(f"LLM処理失敗、正規化テキストを使用: {file_name}")
            
            result['steps']['llm'] = {
                'success': bool(refined_text),
                'refined_length': len(refined_text) if refined_text else 0
            }
            
            # 中断チェック
            if abort_flag and abort_flag.get('flag', False):
                result['status'] = 'cancelled'
                return result
            
            # 4. ベクトル化処理（模擬実装）
            await self._emit_progress(progress_callback, file_name, "ベクトル化処理", 80)
            embedding_result = await self._process_embedding(refined_text, settings, abort_flag)
            
            result['steps']['embedding'] = {
                'success': embedding_result['success'],
                'models': embedding_result.get('models', [])
            }
            
            # 5. データベース保存
            if save_to_db:
                await self._emit_progress(progress_callback, file_name, "データベース保存", 95)
                await self._save_to_database(file_id, raw_text, refined_text, settings)
            else:
                result['db_save'] = {'success': True, 'message': 'DB保存スキップ（テストモード）'}
            
            # 完了
            result['success'] = True
            result['status'] = 'completed'
            result['processing_time'] = time.perf_counter() - start_time
            result['ocr_result'] = {'text': raw_text, 'success': True}
            result['llm_refined_text'] = refined_text
            
            await self._emit_progress(progress_callback, file_name, "処理完了", 100)
            
        except Exception as e:
            self.logger.error(f"ファイル処理エラー [{file_name}]: {e}")
            result['status'] = 'error'
            result['error'] = str(e)
            result['processing_time'] = time.perf_counter() - start_time
        
        return result
    
    async def _process_ocr(self, file_path: str, settings: Dict, abort_flag: Optional[Dict]) -> Dict:
        """OCR処理を実行（テキストファイル対応）"""
        start_time = time.perf_counter()
        
        try:
            # ファイル存在確認
            if not Path(file_path).exists():
                return {
                    'success': False,
                    'error': f'ファイルが見つかりません: {file_path}',
                    'text': '',
                    'processing_time': 0
                }
            
            file_ext = Path(file_path).suffix.lower()
            
            # テキストファイルの場合は直接読み込み
            if file_ext in ['.txt', '.csv', '.json']:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        text = f.read()
                    
                    processing_time = time.perf_counter() - start_time
                    
                    return {
                        'success': True,
                        'error': None,
                        'text': text,
                        'processing_time': processing_time
                    }
                except Exception as e:
                    return {
                        'success': False,
                        'error': f'テキスト読み込みエラー: {str(e)}',
                        'text': '',
                        'processing_time': time.perf_counter() - start_time
                    }
            
            # PDF/画像ファイルの場合はOCRエンジン使用
            elif file_ext in ['.pdf', '.png', '.jpg', '.jpeg', '.tiff', '.bmp']:
                # OCRエンジン取得
                engine_id = settings.get('ocr_engine', 'ocrmypdf')
                ocr_result = self.ocr_factory.process_file(file_path, engine_id=engine_id)
                
                # 中断チェック
                if abort_flag and abort_flag.get('flag', False):
                    return {
                        'success': False,
                        'error': 'キャンセルされました',
                        'text': '',
                        'processing_time': ocr_result.processing_time
                    }
                
                return {
                    'success': ocr_result.success,
                    'error': ocr_result.error,
                    'text': ocr_result.text or '',
                    'processing_time': ocr_result.processing_time
                }
            
            else:
                return {
                    'success': False,
                    'error': f'サポートされていないファイル形式: {file_ext}',
                    'text': '',
                    'processing_time': time.perf_counter() - start_time
                }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'OCR処理エラー: {str(e)}',
                'text': '',
                'processing_time': time.perf_counter() - start_time
            }
    
    def _normalize_text(self, text: str) -> str:
        """テキスト正規化"""
        if not text:
            return ""
        
        # Unicode正規化
        normalized = unicodedata.normalize("NFKC", text)
        
        # 改行・空白の正規化
        lines = []
        for line in normalized.split('\n'):
            line = line.strip()
            if line:
                lines.append(line)
        
        return '\n'.join(lines)
    
    async def _process_llm_refinement(self, text: str, settings: Dict, abort_flag: Optional[Dict]) -> str:
        """LLM整形処理（Ollama統合版）"""
        try:
            # Ollamaクライアント初期化
            from services.llm import OllamaRefiner, OllamaClient
            
            # LLM設定取得
            llm_model = settings.get('llm_model', 'phi4-mini')
            language = settings.get('language', 'ja')
            quality_threshold = settings.get('quality_threshold', 0.7)
            
            # 無効なモデル名チェック（フォールバック判定）
            if 'invalid' in llm_model.lower():
                self.logger.info(f"無効なモデル指定検出: {llm_model} → フォールバック処理")
                return self._fallback_text_refinement(text)
            
            # Ollama接続確認
            client = OllamaClient(model=llm_model)
            is_available = await client.is_available()
            
            if not is_available:
                self.logger.warning(f"Ollama利用不可 → フォールバック処理")
                return self._fallback_text_refinement(text)
            
            refiner = OllamaRefiner(client)
            
            self.logger.info(f"LLM整形開始: モデル={llm_model}, 言語={language}")
            
            # 実際のOllama整形実行
            refined_text, detected_lang, quality_score = await refiner.refine_text(
                raw_text=text,
                abort_flag=abort_flag,
                language=language,
                quality_threshold=quality_threshold
            )
            
            self.logger.info(f"LLM整形完了: 品質スコア={quality_score:.2f}, 言語={detected_lang}")
            
            return refined_text
                
        except ImportError as e:
            self.logger.warning(f"Ollama統合未使用（依存関係不足）: {e}")
            # フォールバック：正規化処理のみ
            return self._fallback_text_refinement(text)
        except Exception as e:
            self.logger.error(f"LLM整形エラー: {e}")
            # フォールバック：正規化処理のみ  
            return self._fallback_text_refinement(text)
    
    def _fallback_text_refinement(self, text: str) -> str:
        """フォールバック用テキスト整形"""
        import re
        # 基本的な正規化のみ
        text = re.sub(r'^[\s\u3000]+$', '', text, flags=re.MULTILINE)
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text.strip()
    
    async def _process_embedding(self, text: str, settings: Dict, abort_flag: Optional[Dict]) -> Dict:
        """ベクトル化処理（模擬実装）"""
        try:
            await asyncio.sleep(1.0)  # ベクトル化時間をシミュレート
            
            # 中断チェック
            if abort_flag and abort_flag.get('flag', False):
                return {'success': False, 'models': []}
            
            # 模擬実装
            embedding_models = settings.get('embedding_models', ['intfloat-e5-large-v2'])
            
            return {
                'success': True,
                'models': embedding_models,
                'vector_count': len(text.split()) // 10  # 模擬ベクトル数
            }
            
        except Exception as e:
            self.logger.error(f"ベクトル化エラー: {e}")
            return {'success': False, 'models': []}
    
    async def _save_to_database(self, file_id: str, raw_text: str, refined_text: str, settings: Dict):
        """データベースにテキストデータを保存"""
        try:
            conn = DB_ENGINE.connect()
            try:
                from sqlalchemy import text
                
                # files_textテーブルに保存/更新
                query = text("""
                    INSERT INTO files_text (blob_id, raw_text, refined_text, quality_score, updated_at)
                    VALUES (:blob_id, :raw_text, :refined_text, :quality_score, NOW())
                    ON CONFLICT (blob_id) 
                    DO UPDATE SET 
                        raw_text = EXCLUDED.raw_text,
                        refined_text = EXCLUDED.refined_text,
                        quality_score = EXCLUDED.quality_score,
                        updated_at = NOW()
                """)
                
                conn.execute(query, {
                    'blob_id': file_id,
                    'raw_text': raw_text,
                    'refined_text': refined_text,
                    'quality_score': 0.8  # 模擬品質スコア
                })
                conn.commit()
                
            finally:
                conn.close()
                
        except Exception as e:
            self.logger.error(f"データベース保存エラー [{file_id}]: {e}")
            raise
    
    async def _emit_progress(self, callback: Optional[callable], file_name: str, step: str, progress: int):
        """進捗通知を送出"""
        if callback:
            try:
                await callback({
                    'file_name': file_name,
                    'step': step,
                    'progress': progress
                })
            except Exception as e:
                self.logger.error(f"進捗通知エラー: {e}")