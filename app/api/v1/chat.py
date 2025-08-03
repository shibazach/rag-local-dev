"""
チャットAPI
Chat and search endpoints with streaming support
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
# from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
import json

from app.auth.dependencies import get_current_user_optional
from app.core.database import get_db
from app.core.schemas import ChatRequest, ChatResponse, SearchResult
from app.services.chat_service import get_chat_service, ChatService

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/search")
async def search_documents(
    request: ChatRequest,
    chat_service = Depends(get_chat_service),
    db = Depends(get_db),
    current_user = Depends(get_current_user_optional)
):
    """文書検索"""
    try:
        results = await chat_service.search_documents(
            query=request.query,
            mode=request.mode,
            embedding_option=request.embedding_option,
            limit=request.limit,
            min_score=request.min_score,
            timeout=request.timeout
        )
        
        return results
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"検索エラー: {str(e)}")


@router.post("/stream")
async def chat_stream(
    request: ChatRequest,
    chat_service = Depends(get_chat_service),
    db = Depends(get_db),
    current_user = Depends(get_current_user_optional)
):
    """チャットストリーミング"""
    try:
        # まず検索実行
        search_results = await chat_service.search_documents(
            query=request.query,
            mode=request.mode,
            embedding_option=request.embedding_option,
            limit=request.limit,
            min_score=request.min_score,
            timeout=request.timeout
        )
        
        # ストリーミング応答生成
        async def generate_response():
            try:
                # 検索結果を最初に送信
                yield f"data: {json.dumps({'type': 'search_results', 'results': [r.dict() for r in search_results]}, ensure_ascii=False)}\n\n"
                
                # チャット応答をストリーミング
                async for chunk in chat_service.generate_chat_response(
                    query=request.query,
                    search_results=search_results,
                    chat_history=request.chat_history
                ):
                    yield f"data: {json.dumps({'type': 'response_chunk', 'content': chunk}, ensure_ascii=False)}\n\n"
                
                # 完了通知
                yield f"data: {json.dumps({'type': 'response_complete'}, ensure_ascii=False)}\n\n"
                
                # 履歴保存
                if current_user:
                    full_response = "".join([chunk async for chunk in chat_service.generate_chat_response(request.query, search_results)])
                    await chat_service.save_chat_history(
                        user_id=current_user.get("id"),
                        query=request.query,
                        response=full_response,
                        search_results=search_results
                    )
                
            except Exception as e:
                yield f"data: {json.dumps({'type': 'error', 'message': str(e)}, ensure_ascii=False)}\n\n"
        
        return StreamingResponse(
            generate_response(),
            media_type="text/plain; charset=utf-8",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Content-Type": "text/event-stream; charset=utf-8"
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"チャットエラー: {str(e)}")


@router.get("/history")
async def get_chat_history(
    limit: int = Query(50, ge=1, le=100),
    chat_service = Depends(get_chat_service),
    current_user = Depends(get_current_user_optional)
):
    """チャット履歴取得"""
    try:
        if not current_user:
            return []
        
        history = await chat_service.get_chat_history(
            user_id=current_user.get("id"),
            limit=limit
        )
        
        return history
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"履歴取得エラー: {str(e)}")


@router.post("/feedback")
async def submit_feedback(
    chat_id: str,
    rating: int = Query(..., ge=1, le=5),
    comment: Optional[str] = None,
    current_user = Depends(get_current_user_optional)
):
    """フィードバック送信"""
    try:
        # TODO: フィードバック保存の実装
        return {"message": "フィードバックを受け付けました"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"フィードバックエラー: {str(e)}")


@router.get("/stats")
async def get_chat_stats(
    current_user = Depends(get_current_user_optional)
):
    """チャット統計取得"""
    try:
        if not current_user:
            return {"total_chats": 0, "avg_response_time": 0}
        
        # TODO: 統計情報の実装
        return {
            "total_chats": 42,
            "avg_response_time": 2.3,
            "most_searched_topics": ["AI技術", "機械学習", "データ分析"],
            "satisfaction_score": 4.2
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"統計取得エラー: {str(e)}")