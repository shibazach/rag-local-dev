#!/usr/bin/env python3
# new/services/chat_service.py
# チャットサービス

import logging
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from ..models import ChatSession, ChatMessage, File, Embedding, FileImage
from ..config import LOGGER
from .search_service import SearchService

class ChatService:
    """チャットサービス"""
    
    def __init__(self):
        self.search_service = SearchService()
    
    def get_sessions(self, db: Session, user_id: int) -> List[Dict[str, Any]]:
        """ユーザーのチャットセッション一覧を取得"""
        try:
            sessions = db.query(ChatSession).filter(
                and_(
                    ChatSession.user_id == user_id,
                    ChatSession.is_active == True
                )
            ).order_by(ChatSession.updated_at.desc()).all()
            
            return [
                {
                    "session_id": session.session_id,
                    "title": session.title,
                    "created_at": session.created_at.isoformat() if session.created_at else None,
                    "updated_at": session.updated_at.isoformat() if session.updated_at else None
                }
                for session in sessions
            ]
        except Exception as e:
            LOGGER.error(f"チャットセッション取得エラー: {e}")
            return []
    
    def create_session(self, db: Session, user_id: int, title: str) -> Dict[str, Any]:
        """チャットセッションを作成"""
        try:
            session_id = str(uuid.uuid4())
            session = ChatSession(
                session_id=session_id,
                user_id=user_id,
                title=title
            )
            
            db.add(session)
            db.commit()
            db.refresh(session)
            
            return {
                "session_id": session.session_id,
                "title": session.title,
                "created_at": session.created_at.isoformat() if session.created_at else None
            }
        except Exception as e:
            LOGGER.error(f"チャットセッション作成エラー: {e}")
            db.rollback()
            raise
    
    def get_messages(self, db: Session, session_id: str) -> List[Dict[str, Any]]:
        """チャットメッセージを取得"""
        try:
            messages = db.query(ChatMessage).filter(
                ChatMessage.session_id == session_id
            ).order_by(ChatMessage.created_at).all()
            
            return [
                {
                    "id": message.id,
                    "role": message.role,
                    "content": message.content,
                    "created_at": message.created_at.isoformat() if message.created_at else None,
                    "tokens_used": message.tokens_used,
                    "referenced_files": message.referenced_files
                }
                for message in messages
            ]
        except Exception as e:
            LOGGER.error(f"チャットメッセージ取得エラー: {e}")
            return []
    
    def send_message(self, db: Session, session_id: str, user_id: int, message: str) -> Dict[str, Any]:
        """チャットメッセージを送信"""
        try:
            # ユーザーメッセージを保存
            user_message = ChatMessage(
                session_id=session_id,
                role="user",
                content=message,
                tokens_used=len(message.split())  # 簡易的なトークン数計算
            )
            db.add(user_message)
            db.commit()
            
            # RAG検索を実行
            search_results = self._perform_rag_search(db, message)
            
            # アシスタントの応答を生成
            assistant_response = self._generate_assistant_response(message, search_results)
            
            # アシスタントメッセージを保存
            assistant_message = ChatMessage(
                session_id=session_id,
                role="assistant",
                content=assistant_response["content"],
                tokens_used=assistant_response["tokens_used"],
                referenced_files=assistant_response["referenced_files"]
            )
            db.add(assistant_message)
            
            # セッションの更新日時を更新
            session = db.query(ChatSession).filter(ChatSession.session_id == session_id).first()
            if session:
                session.updated_at = datetime.now()
            
            db.commit()
            
            return {
                "message": assistant_response["content"],
                "search_results": search_results,
                "referenced_files": assistant_response["referenced_files"]
            }
            
        except Exception as e:
            LOGGER.error(f"チャットメッセージ送信エラー: {e}")
            db.rollback()
            raise
    
    def _perform_rag_search(self, db: Session, query: str) -> List[Dict[str, Any]]:
        """RAG検索を実行"""
        try:
            # ハイブリッド検索を実行
            search_results = self.search_service.hybrid_search(db, query, top_k=5)
            
            # 検索結果を整形
            formatted_results = []
            for result in search_results.get("results", []):
                if result["type"] == "text":
                    formatted_results.append({
                        "type": "text",
                        "content": result["text_chunk"],
                        "similarity": result["similarity"],
                        "file_id": result["file_id"],
                        "chunk_id": result["chunk_id"]
                    })
                elif result["type"] == "image":
                    formatted_results.append({
                        "type": "image",
                        "content": f"画像（ページ{result['page_number']}, 画像{result['image_number']}）",
                        "ocr_text": result["ocr_text"],
                        "llm_description": result["llm_description"],
                        "similarity": result["similarity"],
                        "file_id": result["file_id"]
                    })
            
            return formatted_results
            
        except Exception as e:
            LOGGER.error(f"RAG検索エラー: {e}")
            return []
    
    def _generate_assistant_response(self, user_message: str, search_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """アシスタントの応答を生成"""
        try:
            # 検索結果に基づいて応答を構築
            if not search_results:
                response_content = f"申し訳ございませんが、'{user_message}'に関する情報が見つかりませんでした。別のキーワードで検索してみてください。"
                return {
                    "content": response_content,
                    "tokens_used": len(response_content.split()),
                    "referenced_files": []
                }
            
            # 検索結果を整理
            text_results = [r for r in search_results if r["type"] == "text"]
            image_results = [r for r in search_results if r["type"] == "image"]
            
            # 応答を構築
            response_parts = []
            referenced_files = []
            
            if text_results:
                response_parts.append("テキスト検索結果:")
                for i, result in enumerate(text_results[:3], 1):
                    response_parts.append(f"{i}. {result['content'][:200]}...")
                    if result["file_id"] not in referenced_files:
                        referenced_files.append(result["file_id"])
            
            if image_results:
                response_parts.append("\n画像検索結果:")
                for i, result in enumerate(image_results[:2], 1):
                    response_parts.append(f"{i}. {result['content']}")
                    if result.get("ocr_text"):
                        response_parts.append(f"   OCRテキスト: {result['ocr_text'][:100]}...")
                    if result["file_id"] not in referenced_files:
                        referenced_files.append(result["file_id"])
            
            response_parts.append(f"\nこれらの情報に基づいて、'{user_message}'について回答いたします。")
            
            response_content = "\n".join(response_parts)
            
            return {
                "content": response_content,
                "tokens_used": len(response_content.split()),
                "referenced_files": referenced_files
            }
            
        except Exception as e:
            LOGGER.error(f"アシスタント応答生成エラー: {e}")
            return {
                "content": "申し訳ございませんが、応答の生成中にエラーが発生しました。",
                "tokens_used": 0,
                "referenced_files": []
            }
    
    def delete_session(self, db: Session, session_id: str, user_id: int) -> bool:
        """チャットセッションを削除"""
        try:
            session = db.query(ChatSession).filter(
                and_(
                    ChatSession.session_id == session_id,
                    ChatSession.user_id == user_id
                )
            ).first()
            
            if not session:
                return False
            
            # セッションを非アクティブにする
            session.is_active = False
            db.commit()
            
            return True
            
        except Exception as e:
            LOGGER.error(f"チャットセッション削除エラー: {e}")
            db.rollback()
            return False
    
    def get_session_stats(self, db: Session, session_id: str) -> Dict[str, Any]:
        """セッション統計を取得"""
        try:
            messages = db.query(ChatMessage).filter(
                ChatMessage.session_id == session_id
            ).all()
            
            user_messages = [m for m in messages if m.role == "user"]
            assistant_messages = [m for m in messages if m.role == "assistant"]
            
            total_tokens = sum(m.tokens_used for m in messages)
            referenced_files = set()
            for message in messages:
                if message.referenced_files:
                    referenced_files.update(message.referenced_files)
            
            return {
                "total_messages": len(messages),
                "user_messages": len(user_messages),
                "assistant_messages": len(assistant_messages),
                "total_tokens": total_tokens,
                "referenced_files": len(referenced_files),
                "created_at": messages[0].created_at.isoformat() if messages else None,
                "last_activity": messages[-1].created_at.isoformat() if messages else None
            }
            
        except Exception as e:
            LOGGER.error(f"セッション統計取得エラー: {e}")
            return {} 