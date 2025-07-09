# /workspace/app/routes/file.py
"""
PDF バイナリ / テキスト取得 / 保存 API
"""

from urllib.parse import quote
from fastapi import APIRouter, Form, HTTPException
from fastapi.responses import Response, JSONResponse
from sqlalchemy import text

from src.config import DB_ENGINE
from fileio.file_embedder import embed_and_insert

router = APIRouter()

# REM: PDFバイナリを inline で返却（RFC5987 方式で UTF-8 エンコード）
@router.get("/api/pdf/{file_id}")
def get_pdf(file_id: int):
    # REM: DB からファイル BLOB と元ファイル名を取得
    row = DB_ENGINE.connect().execute(
        text("SELECT file_blob, filename FROM files WHERE file_id=:id"),
        {"id": file_id}
    ).fetchone()
    if not row:
        raise HTTPException(404, "PDF not found")

    blob, filename = row
    # REM: 日本語等を含むファイル名を URL エンコード
    quoted_fname = quote(filename)
    content_disposition = f"inline; filename*=UTF-8''{quoted_fname}"

    return Response(
        content=blob,
        media_type="application/pdf",
        headers={"Content-Disposition": content_disposition}
    )

@router.get("/api/content/{file_id}")
def get_content(file_id: int):
    cont = DB_ENGINE.connect().execute(
        text("SELECT content FROM files WHERE file_id=:id"),
        {"id": file_id}
    ).scalar()
    if cont is None:
        raise HTTPException(404, "Content not found")
    return {"content": cont}

@router.post("/api/save/{file_id}")
def save_content(file_id: int, content: str = Form(...)):
    # REM: ファイル名を取得
    fname = DB_ENGINE.connect().execute(
        text("SELECT filename FROM files WHERE file_id=:id"),
        {"id": file_id}
    ).scalar()
    if not fname:
        raise HTTPException(404, "File not found")
    # REM: content を更新
    with DB_ENGINE.begin() as tx:
        tx.execute(
            text("UPDATE files SET content=:c WHERE file_id=:id"),
            {"c": content, "id": file_id}
        )
    # REM: 保存後に再ベクトル化
    embed_and_insert([content], fname, None, 0.0)
    return {"status": "started"}
