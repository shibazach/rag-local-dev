"""
チャットサービス
Chat and search service with embedding-based retrieval
"""

import asyncio
import json
from datetime import datetime
from typing import List, Dict, Any, Optional, AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text

from app.config import config, logger
from app.core.database import get_db
from app.core.models import FilesMeta, FilesText
from app.core.schemas import ChatRequest, ChatResponse, SearchResult


class ChatService:
    """チャット・検索サービス"""
    
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
        self.embedding_options = config.EMBEDDING_OPTIONS
        self.default_embedding = config.DEFAULT_EMBEDDING_OPTION
    
    async def search_documents(
        self,
        query: str,
        mode: str = "file_separate",
        embedding_option: str = None,
        limit: int = 10,
        min_score: float = 0.0,
        timeout: int = 10
    ) -> List[SearchResult]:
        """文書検索"""
        try:
            # 埋め込みオプション決定
            if not embedding_option:
                embedding_option = self.default_embedding
            
            embedding_config = self.embedding_options.get(embedding_option, {})
            if not embedding_config:
                raise ValueError(f"無効な埋め込みオプション: {embedding_option}")
            
            logger.info(f"検索開始: query='{query}', mode={mode}, embedding={embedding_config['model_name']}")
            
            # 検索実行
            if mode == "chunk_merge":
                results = await self._search_chunks(
                    query=query,
                    embedding_config=embedding_config,
                    limit=limit,
                    min_score=min_score,
                    timeout=timeout
                )
            else:  # file_separate
                results = await self._search_files(
                    query=query,
                    embedding_config=embedding_config,
                    limit=limit,
                    min_score=min_score,
                    timeout=timeout
                )
            
            logger.info(f"検索完了: {len(results)}件の結果")
            return results
            
        except asyncio.TimeoutError:
            logger.warning(f"検索タイムアウト: {timeout}秒")
            return []
        except Exception as e:
            logger.error(f"検索エラー: {e}")
            return []
    
    async def generate_chat_response(
        self,
        query: str,
        search_results: List[SearchResult],
        chat_history: Optional[List[Dict]] = None
    ) -> AsyncGenerator[str, None]:
        """チャット応答生成（ストリーミング）"""
        try:
            # コンテキスト構築
            context = self._build_context(search_results)
            
            # プロンプト構築
            prompt = self._build_chat_prompt(query, context, chat_history)
            
            # LLM呼び出し（ストリーミング）
            async for chunk in self._call_llm_streaming(prompt):
                yield chunk
                
        except Exception as e:
            logger.error(f"チャット応答生成エラー: {e}")
            yield f"申し訳ございません。応答の生成中にエラーが発生しました: {str(e)}"
    
    async def get_chat_history(
        self,
        user_id: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """チャット履歴取得"""
        try:
            # TODO: チャット履歴テーブルの実装
            # 現在はダミーデータを返す
            return [
                {
                    "id": "1",
                    "query": "AI技術の動向について教えて",
                    "response": "AI技術は急速に発展しており...",
                    "timestamp": datetime.utcnow().isoformat(),
                    "user_id": user_id
                }
            ]
            
        except Exception as e:
            logger.error(f"チャット履歴取得エラー: {e}")
            return []
    
    async def save_chat_history(
        self,
        user_id: str,
        query: str,
        response: str,
        search_results: Optional[List[SearchResult]] = None
    ) -> bool:
        """チャット履歴保存"""
        try:
            # TODO: チャット履歴テーブルの実装
            logger.info(f"チャット履歴保存: user={user_id}, query='{query[:50]}...'")
            return True
            
        except Exception as e:
            logger.error(f"チャット履歴保存エラー: {e}")
            return False
    
    # プライベートメソッド
    
    async def _search_chunks(
        self,
        query: str,
        embedding_config: Dict,
        limit: int,
        min_score: float,
        timeout: int
    ) -> List[SearchResult]:
        """チャンク単位検索"""
        try:
            # TODO: ベクトル検索の実装
            # pgvectorを使用した類似度検索
            
            # ダミー実装
            await asyncio.sleep(0.1)  # 検索処理のシミュレーション
            
            return [
                SearchResult(
                    file_id="dummy-file-1",
                    filename="技術報告書.pdf",
                    chunk_text="AI技術の発展により、自然言語処理の精度が大幅に向上しています。",
                    score=0.85,
                    page_number=1,
                    chunk_index=0
                ),
                SearchResult(
                    file_id="dummy-file-2",
                    filename="研究資料.docx",
                    chunk_text="機械学習アルゴリズムの改良により、予測精度が向上しました。",
                    score=0.78,
                    page_number=2,
                    chunk_index=1
                )
            ]
            
        except Exception as e:
            logger.error(f"チャンク検索エラー: {e}")
            return []
    
    async def _search_files(
        self,
        query: str,
        embedding_config: Dict,
        limit: int,
        min_score: float,
        timeout: int
    ) -> List[SearchResult]:
        """ファイル単位検索"""
        try:
            # TODO: ファイル単位のベクトル検索実装
            
            # ダミー実装
            await asyncio.sleep(0.1)
            
            return [
                SearchResult(
                    file_id="dummy-file-1",
                    filename="技術報告書.pdf",
                    chunk_text="技術報告書の要約：最新のAI技術動向と将来展望について詳細に解説しています。",
                    score=0.92,
                    page_number=None,
                    chunk_index=None,
                    summary="最新AI技術の動向と展望に関する包括的な報告書"
                ),
                SearchResult(
                    file_id="dummy-file-2",
                    filename="研究資料.docx",
                    chunk_text="研究資料の要約：機械学習アルゴリズムの改良とその効果について実証研究の結果を報告。",
                    score=0.88,
                    page_number=None,
                    chunk_index=None,
                    summary="機械学習アルゴリズム改良の実証研究"
                )
            ]
            
        except Exception as e:
            logger.error(f"ファイル検索エラー: {e}")
            return []
    
    def _build_context(self, search_results: List[SearchResult]) -> str:
        """検索結果からコンテキスト構築"""
        if not search_results:
            return "関連する文書が見つかりませんでした。"
        
        context_parts = []
        for i, result in enumerate(search_results[:5], 1):  # 上位5件
            context_part = f"【文書{i}】{result.filename}\n"
            if result.summary:
                context_part += f"要約: {result.summary}\n"
            context_part += f"内容: {result.chunk_text}\n"
            if result.score:
                context_part += f"関連度: {result.score:.2f}\n"
            context_parts.append(context_part)
        
        return "\n".join(context_parts)
    
    def _build_chat_prompt(
        self,
        query: str,
        context: str,
        chat_history: Optional[List[Dict]] = None
    ) -> str:
        """チャットプロンプト構築"""
        prompt_parts = [
            "あなたは専門的な文書を分析し、ユーザーの質問に正確に答えるAIアシスタントです。",
            "",
            "以下の文書情報を参考にして、ユーザーの質問に答えてください：",
            "",
            context,
            "",
            "回答の際は以下の点にご注意ください：",
            "- 提供された文書情報に基づいて回答してください",
            "- 不明な点は推測せず、「文書に記載がありません」と述べてください",
            "- 具体的で実用的な回答を心がけてください",
            "- 必要に応じて文書名を引用してください",
            "",
            f"ユーザーの質問: {query}",
            "",
            "回答:"
        ]
        
        return "\n".join(prompt_parts)
    
    async def _call_llm_streaming(self, prompt: str) -> AsyncGenerator[str, None]:
        """LLM呼び出し（ストリーミング）"""
        try:
            # TODO: Ollama連携の実装
            # 現在はダミー応答を生成
            
            sample_response = """
AI技術の動向について、提供された文書を基にお答えします。

【技術報告書.pdf】によると、AI技術は急速に発展しており、特に自然言語処理の分野で大幅な精度向上が見られています。

【研究資料.docx】では、機械学習アルゴリズムの改良により予測精度が向上したことが実証研究で確認されています。

主なトレンド：
1. 自然言語処理の高精度化
2. 機械学習アルゴリズムの改良
3. 実用的なAIシステムの普及

これらの技術進歩により、より実用的なAIソリューションが期待されます。
"""
            
            # ストリーミング風にチャンクに分けて送信
            words = sample_response.strip().split()
            for i in range(0, len(words), 3):
                chunk = " ".join(words[i:i+3]) + " "
                yield chunk
                await asyncio.sleep(0.05)  # ストリーミング効果
                
        except Exception as e:
            logger.error(f"LLM呼び出しエラー: {e}")
            yield f"LLMの呼び出し中にエラーが発生しました: {str(e)}"


# 依存性注入用ファクトリ
async def get_chat_service(db = None):
    """チャットサービス取得"""
    if db is None:
        db = next(get_db())
    return ChatService(db)