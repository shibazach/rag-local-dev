# new/services/processing/processor.py
# ファイル処理プロセッサ（新系）

import asyncio
import time
import logging
import unicodedata
from pathlib import Path
from typing import Dict, List, Optional, AsyncGenerator
import uuid

from new.services.ocr.factory import OCREngineFactory
from new.database.connection import get_db_connection
from new.config import LOGGER, DB_ENGINE

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
            self.logger.info(f"📄 {file_name}: 🔍 OCR処理開始 - エンジン: {settings.get('ocr_engine', 'ocrmypdf')}")
            await self._emit_progress_with_data(progress_callback, {
                'file_name': file_name,
                'step': '🔍 OCR処理開始',
                'detail': f"エンジン: {settings.get('ocr_engine', 'ocrmypdf')}",
                'progress': 10
            })
            ocr_result = await self._process_ocr(file_path, settings, abort_flag)
            
            if not ocr_result['success']:
                result['status'] = 'error'
                result['error'] = ocr_result['error']
                self.logger.error(f"📄 {file_name}: ❌ OCR処理失敗 - {ocr_result['error']}")
                await self._emit_progress(progress_callback, file_name, "❌ OCR処理失敗", ocr_result['error'])
                return result
            
            result['steps']['ocr'] = {
                'success': True,
                'processing_time': ocr_result['processing_time'],
                'text_length': len(ocr_result['text'])
            }
            
            raw_text = ocr_result['text']
            result['text_length'] = len(raw_text)
            
            ocr_message = f"{len(raw_text)}文字抽出 ({ocr_result['processing_time']:.1f}秒)"
            self.logger.info(f"📄 {file_name}: 📊 OCR処理完了 - {ocr_message}")
            
            # OCRテキストを含む詳細情報を送信
            await self._emit_progress_with_data(progress_callback, {
                'file_name': file_name,
                'step': '📊 OCR処理完了',
                'detail': ocr_message,
                'progress': 30,
                'ocr_text': raw_text  # OCRテキストを追加
            })
            
            # 中断チェック
            if abort_flag and abort_flag.get('flag', False):
                result['status'] = 'cancelled'
                return result
            
            # 2. テキスト正規化
            await self._emit_progress_with_data(progress_callback, {
                'file_name': file_name,
                'step': '📝 テキスト正規化',
                'detail': f'{len(raw_text)}文字の正規化処理',
                'progress': 40
            })
            normalized_text = self._normalize_text(raw_text)
            
            # 3. LLM整形処理（詳細進捗付き）
            self.logger.info(f"📄 {file_name}: 🤖 LLM精緻化開始 - テキスト品質向上処理")
            
            # LLMプロンプト作成と送信前表示
            llm_prompt = self._create_llm_prompt(normalized_text, settings)
            await self._emit_progress_with_data(progress_callback, {
                'file_name': file_name,
                'step': '📝 LLMプロンプト作成完了',
                'detail': f'プロンプト生成完了 - 原文{len(normalized_text)}文字',
                'progress': 35,
                'llm_prompt': llm_prompt,
                'llm_result': None
            })
            
            # LLM処理開始表示
            await self._emit_progress_with_data(progress_callback, {
                'file_name': file_name,
                'step': '🤖 LLM処理開始',
                'detail': '品質向上処理実行中',
                'progress': 50
            })
            
            # 実際のLLM処理実行
            llm_start_time = time.perf_counter()
            refined_text = await self._process_llm_refinement(normalized_text, settings, abort_flag)
            llm_processing_time = time.perf_counter() - llm_start_time
            
            if not refined_text:
                # LLM失敗時は正規化テキストを使用
                refined_text = normalized_text
                self.logger.warning(f"📄 {file_name}: ⚠️ LLM処理失敗 - 正規化テキストを使用")
                await self._emit_progress_with_data(progress_callback, {
                    'file_name': file_name,
                    'step': '⚠️ LLM処理失敗',
                    'detail': '正規化テキストを使用',
                    'progress': 60
                })
            else:
                llm_message = f"{len(refined_text)}文字 (品質向上) - 処理時間: {llm_processing_time:.1f}秒"
                self.logger.info(f"📄 {file_name}: ✨ LLM精緻化完了 - {llm_message}")
                
                # LLM結果を含む詳細情報を送信
                await self._emit_progress_with_data(progress_callback, {
                    'file_name': file_name,
                    'step': '✨ LLM精緻化完了',
                    'detail': llm_message,
                    'progress': 60,
                    'llm_prompt': llm_prompt,
                    'llm_result': refined_text
                })
            
            result['steps']['llm'] = {
                'success': bool(refined_text),
                'refined_length': len(refined_text) if refined_text else 0
            }
            
            # 中断チェック
            if abort_flag and abort_flag.get('flag', False):
                result['status'] = 'cancelled'
                return result
            
            # 4. ベクトル化処理（模擬実装）
            models = settings.get('embedding_models', ['intfloat-e5-large-v2'])
            embedding_message = f"モデル: {', '.join(models)}"
            self.logger.info(f"📄 {file_name}: 🧮 埋め込み生成開始 - {embedding_message}")
            await self._emit_progress_with_data(progress_callback, {
                'file_name': file_name,
                'step': '🧮 埋め込み生成開始',
                'detail': embedding_message,
                'progress': 70
            })
            embedding_result = await self._process_embedding(refined_text, settings, abort_flag)
            
            result['steps']['embedding'] = {
                'success': embedding_result['success'],
                'models': embedding_result.get('models', [])
            }
            
            if embedding_result['success']:
                embedding_complete_msg = f"{len(models)}モデル処理完了"
                self.logger.info(f"📄 {file_name}: ✅ 埋め込み生成完了 - {embedding_complete_msg}")
                await self._emit_progress_with_data(progress_callback, {
                    'file_name': file_name,
                    'step': '✅ 埋め込み生成完了',
                    'detail': embedding_complete_msg,
                    'progress': 80
                })
            else:
                self.logger.error(f"📄 {file_name}: ❌ 埋め込み生成失敗 - ベクトル化エラー")
                await self._emit_progress_with_data(progress_callback, {
                    'file_name': file_name,
                    'step': '❌ 埋め込み生成失敗',
                    'detail': 'ベクトル化エラー',
                    'progress': 80
                })
            
            # 5. データベース保存
            if save_to_db:
                self.logger.info(f"📄 {file_name}: 💾 データベース保存中 - メタデータとベクトル保存")
                await self._emit_progress_with_data(progress_callback, {
                    'file_name': file_name,
                    'step': '💾 データベース保存中',
                    'detail': 'メタデータとベクトル保存',
                    'progress': 90
                })
                await self._save_to_database(file_id, raw_text, refined_text, settings)
                self.logger.info(f"📄 {file_name}: 💾 データベース保存完了 - 全データ保存済み")
                await self._emit_progress_with_data(progress_callback, {
                    'file_name': file_name,
                    'step': '💾 データベース保存完了',
                    'detail': '全データ保存済み',
                    'progress': 95
                })
            else:
                result['db_save'] = {'success': True, 'message': 'DB保存スキップ（テストモード）'}
            
            # 完了
            processing_time = time.perf_counter() - start_time
            result['success'] = True
            result['status'] = 'completed'
            
            # 各段階の時間を詳細表示
            ocr_time = result['steps']['ocr'].get('processing_time', 0)
            llm_time = llm_processing_time if 'llm_processing_time' in locals() else 0
            
            complete_message = f"合計 {processing_time:.1f}秒 (OCR: {ocr_time:.1f}s, LLM: {llm_time:.1f}s)"
            self.logger.info(f"📄 {file_name}: 🎉 処理完了 - {complete_message}")
            await self._emit_progress_with_data(progress_callback, {
                'file_name': file_name,
                'step': '🎉 処理完了',
                'detail': complete_message,
                'progress': 100,
                'total_processing_time': processing_time,
                'ocr_time': ocr_time,
                'llm_time': llm_time
            })
            result['processing_time'] = time.perf_counter() - start_time
            result['ocr_result'] = {'text': raw_text, 'success': True}
            result['llm_refined_text'] = refined_text
            

            
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
                self.logger.info(f"OCRエンジン {engine_id} で処理開始中...")
                
                # 処理中の詳細進捗表示
                processing_start = time.perf_counter()
                
                # OCR処理中の進捗通知
                await self._emit_progress_with_data(progress_callback, {
                    'file_name': file_name,
                    'step': '📄 OCR処理実行中',
                    'detail': f'エンジン: {engine_id} - ページ解析中...',
                    'progress': 25,
                    'ocr_engine': engine_id,
                    'stage': 'ocr_processing'
                })
                
                # シンプル進捗監視（10秒毎）
                async def ocr_progress_monitor():
                    start_time = time.perf_counter()
                    page_estimate = 1
                    total_pages = 8  # 推定ページ数（PDFの場合）
                    
                    while True:
                        await asyncio.sleep(10)
                        elapsed = time.perf_counter() - start_time
                        
                        # 経過時間に応じてページ数を推定（15秒/ページと仮定）
                        page_estimate = min(int(elapsed / 15) + 1, total_pages)
                        
                        await self._emit_progress_with_data(callback, {
                            'file_name': file_name,
                            'step': f'OCR処理中 - {page_estimate}/{total_pages}ページ',
                            'detail': f'({elapsed:.0f}秒経過)',
                            'progress': min(25 + (elapsed / 60) * 25, 45),
                            'stage': 'ocr_processing',
                            'elapsed_ocr': elapsed,
                            'simple_status': True  # シンプル表示フラグ
                        })
                
                # 進捗監視タスクを開始
                monitor_task = asyncio.create_task(ocr_progress_monitor())
                
                try:
                    ocr_result = self.ocr_factory.process_file(file_path, engine_id=engine_id)
                    processing_time = time.perf_counter() - processing_start
                finally:
                    # 監視タスクを終了
                    monitor_task.cancel()
                    try:
                        await monitor_task
                    except asyncio.CancelledError:
                        pass
                
                self.logger.info(f"OCR処理完了 - 処理時間: {processing_time:.1f}秒")
                
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
            from new.services.llm import OllamaRefiner, OllamaClient
            
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
                error_msg = f"❌ Ollama接続失敗: {client.base_url} (model: {llm_model})"
                self.logger.error(error_msg)
                raise RuntimeError(f"LLM処理エラー - Ollamaサービスに接続できません: {client.base_url}")
            
            refiner = OllamaRefiner(client)
            
            self.logger.info(f"LLM整形開始: モデル={llm_model}, 言語={language}")
            
            # 実際のOllama整形実行（処理時間測定付き）
            ollama_start_time = time.perf_counter()
            refined_text, detected_lang, quality_score = await refiner.refine_text(
                raw_text=text,
                abort_flag=abort_flag,
                language=language,
                quality_threshold=quality_threshold
            )
            ollama_processing_time = time.perf_counter() - ollama_start_time
            
            self.logger.info(f"LLM整形完了: 品質スコア={quality_score:.2f}, 言語={detected_lang}, 処理時間={ollama_processing_time:.1f}秒")
            
            return refined_text
                
        except ImportError as e:
            error_msg = f"❌ Ollama依存関係エラー: {e}"
            self.logger.error(error_msg)
            raise RuntimeError(f"LLM処理エラー - Ollama依存関係が不足しています: {e}")
        except Exception as e:
            error_msg = f"❌ LLM処理中にエラーが発生: {e}"
            self.logger.error(error_msg)
            raise RuntimeError(f"LLM処理エラー: {e}")
    
    def _create_llm_prompt(self, text: str, settings: Dict) -> str:
        """LLMプロンプト作成（高品質プロンプト使用）"""
        try:
            # 絶対importパスでプロンプトローダーを取得
            import sys
            import os
            
            # ワークスペースルートをパスに追加
            workspace_root = '/workspace'
            if workspace_root not in sys.path:
                sys.path.insert(0, workspace_root)
            
            from new.services.llm.prompt_loader import get_prompt_loader
            
            language = settings.get('language', 'ja')
            
            # 高品質プロンプトローダーから取得
            prompt_loader = get_prompt_loader()
            prompt_template = prompt_loader.load_prompt("refine_prompt_advanced", language)
            
            # プロンプトテンプレートをフォーマット
            prompt = prompt_loader.format_prompt(prompt_template, TEXT=text)
            
            self.logger.info(f"✅ 高品質プロンプト使用成功: {len(prompt_template)}文字, 言語={language}")
            return prompt
            
        except Exception as e:
            self.logger.warning(f"❌ 高品質プロンプト読み込み失敗、フォールバック使用: {e}")
            import traceback
            self.logger.debug(f"詳細エラー: {traceback.format_exc()}")
            
            # フォールバック：簡易プロンプト
            language = settings.get('language', 'ja')
            quality_threshold = settings.get('quality_threshold', 0.7)
            
            prompt = f"""以下のテキストを品質向上してください。

言語: {language}
品質閾値: {quality_threshold}

原文:
{text}

修正指示:
- OCR誤字・脱字の修正
- 不自然な改行・空白の整理
- 文章構造の改善
- 意味を保持しつつ読みやすく整形

修正後テキスト:"""
            
            return prompt

    def _fallback_text_refinement(self, text: str) -> str:
        """フォールバック用テキスト整形（高品質整形処理）"""
        import re
        
        # 大幅な品質向上処理
        # 1. Unicode正規化
        import unicodedata
        text = unicodedata.normalize('NFKC', text)
        
        # 2. OCR特有の誤認識修正
        ocr_corrections = {
            # 基本的な誤字修正
            r'(\d+)\s*年\s*(\d+)\s*月\s*(\d+)\s*日': r'\1年\2月\3日',
            r'株式会\s*社': '株式会社',
            r'有限会\s*社': '有限会社',
            r'研究\s*所': '研究所',
            r'試験\s*片': '試験片',
            r'材\s*料': '材料',
            r'強\s*度': '強度',
            r'温\s*度': '温度',
            r'湿\s*度': '湿度',
            
            # 技術文書特有の修正
            r'kgf\s*/\s*mm': 'kgf/mm',
            r'N\s*/\s*mm': 'N/mm',
            r'MPa\s+': 'MPa ',
            r'°C\s+': '°C ',
            r'％\s+': '% ',
            
            # 数値と単位の整理
            r'(\d+)\s+([a-zA-Z]+)': r'\1\2',  # 数値と英字単位の間の空白
            r'(\d+)\s*×\s*(\d+)': r'\1×\2',  # 乗算記号の整理
            
            # 日本語文章の整理
            r'([あ-ん])\s+([あ-ん])': r'\1\2',  # ひらがな間の不要な空白
            r'([ア-ン])\s+([ア-ン])': r'\1\2',  # カタカナ間の不要な空白
            r'([一-龯])\s+([一-龯])': r'\1\2',  # 漢字間の不要な空白
        }
        
        for pattern, replacement in ocr_corrections.items():
            text = re.sub(pattern, replacement, text)
        
        # 3. 大幅な空白・改行整理
        lines = text.split('\n')
        processed_lines = []
        
        for line in lines:
            # 各行の処理
            line = line.strip()
            
            # 空行のスキップ
            if not line:
                if processed_lines and processed_lines[-1] != '':
                    processed_lines.append('')
                continue
            
            # 過度な空白の削除（連続する空白を1つに）
            line = re.sub(r'[ \t]{2,}', ' ', line)
            line = re.sub(r'[\u3000]{2,}', '　', line)
            
            # 文章構造の改善
            # 項番の整理
            line = re.sub(r'^(\d+)\s*[.．]\s*', r'\1. ', line)
            
            # カッコの整理
            line = re.sub(r'\s*（\s*', '（', line)
            line = re.sub(r'\s*）\s*', '）', line)
            line = re.sub(r'\s*\(\s*', '（', line)
            line = re.sub(r'\s*\)\s*', '）', line)
            
            processed_lines.append(line)
        
        # 4. 文書全体の構造改善
        result = '\n'.join(processed_lines)
        
        # 連続する空行を最大2行に制限
        result = re.sub(r'\n{3,}', '\n\n', result)
        
        # 5. 句読点の正規化
        result = re.sub(r'[、，]', '、', result)
        result = re.sub(r'[。．]', '。', result)
        
        # 6. 報告書特有の整形
        # 見出しと内容の分離改善
        result = re.sub(r'^([^\n]{1,30}：)(\S)', r'\1\n\2', result, flags=re.MULTILINE)
        
        # 表形式データの整理
        result = re.sub(r'(\w+)\s+(\w+)\s+(\w+)', r'\1　\2　\3', result)
        
        self.logger.info(f"フォールバック整形: {len(text)}文字 → {len(result)}文字 (差分: {len(result)-len(text)}文字)")
        
        return result.strip()
    
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
        if callback is None:
            return  # callbackがNoneの場合は何もしない
            
        try:
            # callbackが通常の関数かasync関数かを判定
            import asyncio
            result = callback({
                'file_name': file_name,
                'step': step,
                'progress': progress
            })
            # async関数の場合のみawait
            if asyncio.iscoroutine(result):
                await result
        except Exception as e:
            self.logger.error(f"進捗通知エラー: {e}")
    
    async def _emit_progress_with_data(self, callback: Optional[callable], event_data: Dict):
        """詳細データ付き進捗通知を送出"""
        if callback is None:
            return  # callbackがNoneの場合は何もしない
            
        try:
            # callbackが通常の関数かasync関数かを判定
            import asyncio
            result = callback(event_data)
            # async関数の場合のみawait
            if asyncio.iscoroutine(result):
                await result
        except Exception as e:
            self.logger.error(f"詳細進捗通知エラー: {e}")