# new/services/llm/ollama_client.py
"""
Ollama LLMクライアント実装
旧系の実装パターンを新系に適応
"""

import re
import time
import asyncio
from typing import Optional, Dict, Tuple, Any
from pathlib import Path

# LangChain + Ollama
try:
    from langchain_core.output_parsers import StrOutputParser
    from langchain.prompts import PromptTemplate
    from langchain_community.chat_models import ChatOllama
    from langchain_community.llms.ollama import OllamaEndpointNotFoundError
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    ChatOllama = None
    OllamaEndpointNotFoundError = Exception

from new.config import settings, LOGGER


class OllamaClient:
    """Ollama接続クライアント"""
    
    def __init__(self, base_url: str = None, model: str = None):
        self.base_url = base_url or settings.OLLAMA_BASE_URL
        self.model = model or settings.OLLAMA_MODEL
        self.logger = LOGGER
        
        if not LANGCHAIN_AVAILABLE:
            raise ImportError("LangChain関連パッケージが見つかりません。`pip install langchain langchain-community langchain-ollama` を実行してください。")
    
    async def is_available(self) -> bool:
        """Ollama接続確認（軽量API使用）"""
        try:
            import aiohttp
            import asyncio
            
            # 軽量なAPI確認（バージョン情報取得）
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5.0)) as session:
                async with session.get(f"{self.base_url}/api/version") as response:
                    if response.status == 200:
                        version_data = await response.json()
                        self.logger.debug(f"Ollama接続成功: {self.base_url} (version: {version_data.get('version', 'unknown')})")
                        
                        # モデル存在確認も実行
                        async with session.get(f"{self.base_url}/api/tags") as tags_response:
                            if tags_response.status == 200:
                                tags_data = await tags_response.json()
                                models = [model['name'] for model in tags_data.get('models', [])]
                                
                                if self.model in models or f"{self.model}:latest" in models:
                                    self.logger.debug(f"モデル確認成功: {self.model}")
                                    return True
                                else:
                                    self.logger.warning(f"モデル '{self.model}' が見つかりません。利用可能: {models}")
                                    return False
                            else:
                                self.logger.warning(f"モデル一覧取得失敗: HTTP {tags_response.status}")
                                return False
                    else:
                        self.logger.warning(f"Ollama API応答エラー: HTTP {response.status}")
                        return False
                        
        except asyncio.TimeoutError:
            self.logger.warning(f"Ollama接続タイムアウト: {self.base_url} (5秒)")
            return False
        except ImportError:
            self.logger.warning("aiohttp未インストール: フォールバック接続確認を使用")
            return await self._fallback_availability_check()
        except Exception as e:
            self.logger.warning(f"Ollama接続失敗 ({self.base_url}, {self.model}): {e}")
            return False
    
    async def _fallback_availability_check(self) -> bool:
        """フォールバック接続確認（重い処理）"""
        try:
            # 実際のLLM処理（CPUでは時間がかかる）
            llm = ChatOllama(model=self.model, base_url=self.base_url, max_new_tokens=5)
            result = await asyncio.wait_for(
                asyncio.to_thread(llm.invoke, "Hi"), 
                timeout=30.0  # CPU環境を考慮して長めに設定
            )
            return True
        except asyncio.TimeoutError:
            self.logger.warning(f"Ollama処理タイムアウト（CPU環境では正常）: {self.base_url}")
            return False
        except Exception as e:
            self.logger.warning(f"Ollama処理失敗: {e}")
            return False
    
    async def generate_text(
        self, 
        prompt: str, 
        abort_flag: Optional[Dict] = None,
        generation_params: Optional[Dict] = None
    ) -> str:
        """テキスト生成"""
        try:
            # 中断チェック
            if abort_flag and abort_flag.get('flag', False):
                raise InterruptedError("処理が中断されました")
            
            # デフォルト生成パラメータ
            default_params = {
                "max_new_tokens": 1024,
                "temperature": 0.7,
            }
            params = {**default_params, **(generation_params or {})}
            
            # LLMインスタンス生成
            llm = ChatOllama(
                model=self.model, 
                base_url=self.base_url,
                **params
            )
            
            # 非同期生成実行
            start_time = time.perf_counter()
            result = await asyncio.to_thread(llm.invoke, prompt)
            elapsed = time.perf_counter() - start_time
            
            self.logger.info(f"Ollama生成完了 ({self.model}): {elapsed:.2f}秒")
            
            # AIMessageオブジェクトからテキスト抽出
            if hasattr(result, 'content'):
                text_result = result.content
            elif hasattr(result, 'text'):
                text_result = result.text
            else:
                text_result = str(result)
            
            # 空応答チェック
            if not text_result.strip():
                self.logger.warning("Ollamaが空の応答を返しました")
                return "[EMPTY_RESPONSE]"
            
            return text_result.strip()
            
        except OllamaEndpointNotFoundError as e:
            error_msg = f"Ollamaモデル '{self.model}' が見つかりません。`ollama pull {self.model}` を実行してください。"
            self.logger.error(error_msg)
            raise RuntimeError(error_msg) from e
        except Exception as e:
            self.logger.error(f"Ollama生成エラー: {e}")
            raise


class OllamaRefiner:
    """Ollamaによるテキスト整形処理"""
    
    def __init__(self, client: Optional[OllamaClient] = None):
        self.client = client or OllamaClient()
        self.logger = LOGGER
    
    def normalize_text(self, text: str) -> str:
        """テキスト正規化（空行圧縮など）"""
        # 空白のみの行を削除
        text = re.sub(r'^[\s\u3000]+$', '', text, flags=re.MULTILINE)
        # 連続空行を最大1行に圧縮
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text.strip()
    
    def build_refinement_prompt(self, raw_text: str, language: str = "ja") -> str:
        """整形用プロンプト構築（高品質プロンプト使用）"""
        try:
            # 絶対importパスでプロンプトローダーを取得
            import sys
            import os
            
            # ワークスペースルートをパスに追加
            workspace_root = '/workspace'
            if workspace_root not in sys.path:
                sys.path.insert(0, workspace_root)
            
            from new.services.llm.prompt_loader import get_prompt_loader
            
            # 高品質プロンプトローダーから取得
            prompt_loader = get_prompt_loader()
            prompt_template = prompt_loader.load_prompt("refine_prompt_advanced", language)
            
            # テキスト正規化
            normalized_text = self.normalize_text(raw_text)
            
            # プロンプトテンプレートをフォーマット
            prompt = prompt_loader.format_prompt(prompt_template, TEXT=normalized_text)
            
            self.logger.info(f"✅ 高品質プロンプト使用成功: {len(prompt_template)}文字, 言語={language}")
            return prompt
            
        except Exception as e:
            self.logger.warning(f"❌ 高品質プロンプト読み込み失敗、フォールバック使用: {e}")
            import traceback
            self.logger.debug(f"詳細エラー: {traceback.format_exc()}")
            
            # フォールバック：簡易プロンプト
            normalized_text = self.normalize_text(raw_text)
            
            if language == "ja":
                template = """以下のテキストを読みやすく整形してください。
OCRで読み取ったテキストのため、誤字や改行の乱れがある可能性があります。
内容を変更せず、読みやすい形に整えてください。

【整形対象テキスト】
{TEXT}

【整形後テキスト】"""
            else:
                template = """Please format the following text to make it more readable.
This text was extracted using OCR, so there may be typos or irregular line breaks.
Please organize it in a readable format without changing the content.

【Text to format】
{TEXT}

【Formatted text】"""
            
            return template.replace("{TEXT}", normalized_text)
    
    async def refine_text(
        self,
        raw_text: str,
        abort_flag: Optional[Dict] = None,
        language: str = "ja",
        quality_threshold: float = 0.7
    ) -> Tuple[str, str, float]:
        """
        テキスト整形実行
        
        Returns:
            Tuple[refined_text, language, quality_score]
        """
        try:
            # 中断チェック
            if abort_flag and abort_flag.get('flag', False):
                raise InterruptedError("処理が中断されました")
            
            # プロンプト構築
            prompt = self.build_refinement_prompt(raw_text, language)
            
            self.logger.info(f"LLM整形開始 (文字数: {len(raw_text)}, 言語: {language})")
            
            # LLM生成実行
            refined_text = await self.client.generate_text(
                prompt=prompt,
                abort_flag=abort_flag,
                generation_params={
                    "min_length": max(1, int(len(raw_text) * 0.8)),
                    "temperature": 0.7
                }
            )
            
            # 品質スコア算出（簡易版）
            quality_score = self._calculate_quality_score(raw_text, refined_text)
            
            self.logger.info(f"LLM整形完了 (品質スコア: {quality_score:.2f})")
            
            return refined_text, language, quality_score
            
        except Exception as e:
            self.logger.error(f"テキスト整形エラー: {e}")
            # フォールバック：正規化のみ
            return self.normalize_text(raw_text), language, 0.5
    
    def _calculate_quality_score(self, original: str, refined: str) -> float:
        """品質スコア算出（簡易版）"""
        try:
            # 基本的な品質指標
            original_len = len(original.strip())
            refined_len = len(refined.strip())
            
            if original_len == 0:
                return 0.0
            
            # 長さ比率（極端に短縮/拡張されていないか）
            length_ratio = refined_len / original_len
            length_score = 1.0 if 0.8 <= length_ratio <= 1.2 else 0.5
            
            # 空でない確認
            empty_score = 1.0 if refined.strip() else 0.0
            
            # エラーマーカー確認
            error_score = 0.0 if "[EMPTY_RESPONSE]" in refined else 1.0
            
            # 総合スコア
            total_score = (length_score + empty_score + error_score) / 3
            
            return min(1.0, max(0.0, total_score))
            
        except Exception:
            return 0.5