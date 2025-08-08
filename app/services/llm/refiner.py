"""
LLM整形サービス - Prototype統合版
LangChain + Ollamaを使用したテキスト整形・精緻化
"""

import re
import time
from typing import Tuple, Optional, Dict, Any

from langchain_core.output_parsers import StrOutputParser
from langchain.prompts import PromptTemplate
from langchain_community.chat_models import ChatOllama
from langchain_community.llms.ollama import OllamaEndpointNotFoundError

from app.config import config, logger
from app.services.ocr import get_spell_checker
from .prompt_loader import PromptLoader
from .llm_utils import detect_language
from .scorer import TextScorer

class TextRefiner:
    """LLMテキスト整形サービス"""
    
    def __init__(self):
        self.ollama_base = config.OLLAMA_BASE_URL
        self.default_model = config.OLLAMA_MODEL
        self.spell_checker = get_spell_checker()
        self.prompt_loader = PromptLoader()
        self.text_scorer = TextScorer()
    
    def normalize_empty_lines(self, text: str) -> str:
        """
        空白のみの行を削除し、連続空行は最大１行に圧縮する
        
        Args:
            text: 入力テキスト
            
        Returns:
            正規化されたテキスト
        """
        # 空白のみの行を削除（全角スペース含む）
        text = re.sub(r'^[\s\u3000]+$', '', text, flags=re.MULTILINE)
        # 連続する3つ以上の改行を2つに圧縮
        return re.sub(r'\n{3,}', '\n\n', text)
    
    def build_prompt(self, raw_text: str, lang: str = "ja") -> str:
        """
        プロンプト組み立て
        
        Args:
            raw_text: 生テキスト
            lang: 言語コード
            
        Returns:
            組み立てられたプロンプト
        """
        # プロンプトテンプレート取得
        template = self.prompt_loader.get_prompt_by_lang(lang)
        
        # OCR誤字補正と空行正規化
        cleaned = self.normalize_empty_lines(
            self.spell_checker.correct_text(raw_text)
        )
        
        # テンプレート内の{TEXT}を置換
        return template.replace("{TEXT}", cleaned)
    
    def refine_text_with_llm(
        self,
        raw_text: str,
        model: Optional[str] = None,
        force_lang: Optional[str] = None,
        abort_flag: Optional[Dict[str, bool]] = None,
        temperature: float = 0.7,
        max_new_tokens: int = 1024
    ) -> Tuple[str, str, float, str]:
        """
        LangChain + Ollama で raw_text を整形
        
        Args:
            raw_text: 生テキスト
            model: 使用モデル（省略時はデフォルト）
            force_lang: 強制言語指定
            abort_flag: 中断フラグ
            temperature: 生成温度
            max_new_tokens: 最大生成トークン数
            
        Returns:
            (refined_text, lang, quality_score, prompt_used)のタプル
        """
        if model is None:
            model = self.default_model
        
        # 中断チェック関数
        def check_abort():
            if abort_flag and abort_flag.get("flag"):
                raise InterruptedError("処理が中断されました")
        
        try:
            # 1) OCR 誤字補正＋空行圧縮
            check_abort()
            corrected = self.normalize_empty_lines(
                self.spell_checker.correct_text(raw_text)
            )
            
            # 2) 言語判定
            check_abort()
            lang = detect_language(corrected, force_lang) or "ja"
            if force_lang == "ja":
                lang = "ja"
            
            # デバッグ出力
            text_len = len(corrected)
            token_estimate = int(text_len * 1.6)  # 日本語の場合の推定
            logger.info(
                f"🧠 LLM整形を開始（文字数: {text_len}, "
                f"推定トークン: {token_estimate}）"
            )
            logger.info(f"🔤 整形言語: {lang}")
            
            # 3) プロンプト組み立て
            check_abort()
            prompt_text = self.build_prompt(raw_text, lang)
            
            # PromptTemplate 用にエスケープ
            safe_prompt = prompt_text.replace("{", "{{").replace("}", "}}")
            
            # 4) 生成パラメータ
            gen_kw = {
                "max_new_tokens": max_new_tokens,
                "min_length": max(1, int(len(corrected) * 0.8)),
                "temperature": temperature,
            }
            
            # 5) LLM インスタンス生成
            check_abort()
            llm = ChatOllama(
                model=model,
                base_url=self.ollama_base,
                **gen_kw
            )
            
            # 6) LangChain チェーン構築
            chain = (
                PromptTemplate.from_template(safe_prompt) |
                llm |
                StrOutputParser()
            )
            
            # 7) 推論実行
            check_abort()
            logger.debug(
                f"[DEBUG] LLM呼び出し: model={model}, "
                f"prompt_len={len(prompt_text)}"
            )
            logger.debug(
                f"[DEBUG] プロンプトプレビュー:\n---\n"
                f"{prompt_text[:300]}...\n---"
            )
            
            start_time = time.time()
            try:
                refined = chain.invoke({})
            except OllamaEndpointNotFoundError as e:
                # モデル未ロード時の明示的エラー
                raise RuntimeError(
                    f"Ollama モデル '{model}' が見つかりません。"
                    f"`ollama pull {model}` を実行してください。"
                ) from e
            
            elapsed = time.time() - start_time
            logger.debug(f"[DEBUG] LLM推論時間: {elapsed:.2f}秒")
            
            if not refined.strip():
                logger.warning("[WARNING] LLMが空の応答を返しました")
                refined = "[EMPTY]"
            
            # 8) 品質スコア算出
            check_abort()
            score = self.text_scorer.score_text_quality(
                corrected, refined, lang
            )
            
            logger.info(f"✅ LLM整形完了（品質スコア: {score:.2f}）")
            
            return refined, lang, score, prompt_text
            
        except InterruptedError:
            raise
        except Exception as e:
            logger.error(f"LLM整形エラー: {e}")
            raise
    
    def batch_refine_texts(
        self,
        texts: list[str],
        model: Optional[str] = None,
        force_lang: Optional[str] = None,
        **kwargs
    ) -> list[Tuple[str, str, float, str]]:
        """
        複数テキストのバッチ整形
        
        Args:
            texts: テキストのリスト
            model: 使用モデル
            force_lang: 強制言語指定
            **kwargs: その他のパラメータ
            
        Returns:
            各テキストの(refined_text, lang, score, prompt)のリスト
        """
        results = []
        
        for i, text in enumerate(texts):
            logger.info(f"バッチ処理: {i+1}/{len(texts)}")
            try:
                result = self.refine_text_with_llm(
                    text,
                    model=model,
                    force_lang=force_lang,
                    **kwargs
                )
                results.append(result)
            except Exception as e:
                logger.error(f"バッチ処理エラー (テキスト {i+1}): {e}")
                # エラー時は元のテキストを返す
                results.append((text, "ja", 0.0, ""))
        
        return results

# サービスインスタンス作成ヘルパー
def get_text_refiner() -> TextRefiner:
    """テキスト整形サービスインスタンス取得"""
    return TextRefiner()

def refine_text(text: str, model_name: Optional[str] = None) -> Dict[str, Any]:
    """
    テキスト整形（簡易版）
    
    Args:
        text: 入力テキスト
        model_name: 使用するモデル名
        
    Returns:
        整形結果の辞書
    """
    refiner = get_text_refiner()
    try:
        refined_text, lang, score, prompt = refiner.refine_text_with_llm(
            text,
            model=model_name
        )
        return {
            "text": refined_text,
            "language": lang,
            "score": score,
            "prompt": prompt
        }
    except Exception as e:
        logger.error(f"テキスト整形エラー: {e}")
        return {
            "text": text,
            "language": "ja",
            "score": 0.0,
            "prompt": ""
        }