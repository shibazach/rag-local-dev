"""
チャットサービス - Prototype統合版
チャット・検索・RAG統合サービス
"""

import asyncio
import json
from datetime import datetime
from typing import List, Dict, Any, Optional, AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from langchain_community.chat_models import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage

from app.config import config, logger
from app.services.embedding.searcher import search_similar_chunks
from app.services.llm.prompt_loader import get_chat_prompt

class ChatService:
    """チャット・検索サービス"""
    
    def __init__(self, db_session: AsyncSession = None):
        """
        Args:
            db_session: データベースセッション（オプショナル）
        """
        self.db = db_session
        self.embedding_options = config.EMBEDDING_OPTIONS
        self.default_embedding = config.DEFAULT_EMBEDDING_OPTION
        self.chat_history: List[Dict[str, Any]] = []
    
    async def search_documents(
        self,
        query: str,
        mode: str = "file_separate",
        embedding_option: str = None,
        limit: int = 10,
        min_score: float = 0.0,
        timeout: int = 10
    ) -> List[Dict[str, Any]]:
        """
        文書検索
        
        Args:
            query: 検索クエリ
            mode: 検索モード（file_separate/chunk_merge）
            embedding_option: 埋め込みオプション
            limit: 結果数上限
            min_score: 最小スコア
            timeout: タイムアウト秒数
            
        Returns:
            検索結果リスト
        """
        try:
            # 埋め込みオプション決定
            if not embedding_option:
                embedding_option = self.default_embedding
            
            embedding_config = self.embedding_options.get(embedding_option, {})
            if not embedding_config:
                raise ValueError(f"無効な埋め込みオプション: {embedding_option}")
            
            logger.info(f"検索開始: query='{query}', mode={mode}, embedding={embedding_config['model_name']}")
            
            # 実際の検索を実行
            results = await search_similar_chunks(
                query_text=query,
                embedding_option=embedding_option,
                limit=limit,
                min_score=min_score,
                db_session=self.db_session
            )
            
            # 検索モードに応じて結果を整形
            if mode == "file_separate":
                # ファイル単位で分離（デフォルト）
                return results
            elif mode == "chunk_merge":
                # チャンクをマージ（同一ファイルのチャンクを結合）
                merged_results = {}
                for result in results:
                    file_id = result.get("file_id")
                    if file_id not in merged_results:
                        merged_results[file_id] = {
                            "file_id": file_id,
                            "filename": result.get("filename"),
                            "content": result.get("content", ""),
                            "score": result.get("score", 0),
                            "chunks": [result]
                        }
                    else:
                        merged_results[file_id]["content"] += "\n\n" + result.get("content", "")
                        merged_results[file_id]["chunks"].append(result)
                        # 最高スコアを保持
                        merged_results[file_id]["score"] = max(
                            merged_results[file_id]["score"],
                            result.get("score", 0)
                        )
                
                return list(merged_results.values())
            else:
                return results
            
        except Exception as e:
            logger.error(f"検索エラー: {e}")
            return []
    
    async def chat_completion(
        self,
        message: str,
        search_results: List[Dict[str, Any]] = None,
        system_prompt: str = None,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> AsyncGenerator[str, None]:
        """
        チャット応答生成（ストリーミング）
        
        Args:
            message: ユーザーメッセージ
            search_results: 検索結果（コンテキスト）
            system_prompt: システムプロンプト
            temperature: 生成温度
            max_tokens: 最大トークン数
            
        Yields:
            応答テキストのチャンク
        """
        try:
            # チャット履歴に追加
            self.chat_history.append({
                "role": "user",
                "content": message,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            # システムプロンプト設定
            if not system_prompt:
                system_prompt = get_chat_prompt()
            
            # コンテキスト構築
            context = ""
            if search_results:
                context = "\n\n関連文書:\n"
                for idx, result in enumerate(search_results[:5], 1):  # 上位5件まで
                    context += f"\n[文書{idx}] {result.get('filename', 'Unknown')}\n"
                    context += f"{result.get('content', '')[:500]}...\n"
            
            # プロンプト構築
            full_prompt = system_prompt
            if context:
                full_prompt += f"\n\n{context}"
            
            # LLMインスタンス作成
            llm = ChatOllama(
                model=config.OLLAMA_MODEL,
                base_url=config.OLLAMA_BASE_URL,
                temperature=temperature
            )
            
            # メッセージ構築
            messages = [
                SystemMessage(content=full_prompt),
                HumanMessage(content=message)
            ]
            
            # ストリーミング応答生成
            full_response = ""
            async for chunk in llm.astream(messages):
                content = chunk.content
                if content:
                    full_response += content
                    yield content
            
            # チャット履歴に応答を追加
            self.chat_history.append({
                "role": "assistant",
                "content": full_response,
                "timestamp": datetime.utcnow().isoformat()
            })
            
        except Exception as e:
            logger.error(f"チャット応答エラー: {e}")
            yield f"エラーが発生しました: {str(e)}"
    
    async def get_chat_response(
        self,
        message: str,
        use_rag: bool = True,
        **kwargs
    ) -> str:
        """
        チャット応答取得（非ストリーミング）
        
        Args:
            message: ユーザーメッセージ
            use_rag: RAG使用フラグ
            **kwargs: その他のパラメータ
            
        Returns:
            応答テキスト
        """
        search_results = None
        
        if use_rag:
            # RAG検索実行
            search_results = await self.search_documents(message)
        
        # 応答生成
        response_parts = []
        async for chunk in self.chat_completion(
            message,
            search_results=search_results,
            **kwargs
        ):
            response_parts.append(chunk)
        
        return "".join(response_parts)
    
    def get_chat_history(
        self,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        チャット履歴取得
        
        Args:
            limit: 取得数上限
            
        Returns:
            チャット履歴
        """
        return self.chat_history[-limit:]
    
    def clear_chat_history(self) -> None:
        """チャット履歴クリア"""
        self.chat_history.clear()
        logger.info("チャット履歴をクリアしました")
    
    async def export_chat_history(
        self,
        format: str = "json"
    ) -> str:
        """
        チャット履歴エクスポート
        
        Args:
            format: エクスポート形式（json/text）
            
        Returns:
            エクスポートデータ
        """
        if format == "json":
            return json.dumps(self.chat_history, ensure_ascii=False, indent=2)
        elif format == "text":
            lines = []
            for msg in self.chat_history:
                role = "ユーザー" if msg["role"] == "user" else "アシスタント"
                lines.append(f"[{msg['timestamp']}] {role}: {msg['content']}")
            return "\n".join(lines)
        else:
            raise ValueError(f"未対応の形式: {format}")

# サービスインスタンス作成ヘルパー
def get_chat_service(db_session: AsyncSession = None) -> ChatService:
    """チャットサービスインスタンス取得"""
    return ChatService(db_session)