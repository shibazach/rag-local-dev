# app/routes/file.py
# REM: PDF バイナリ／テキスト取得／保存 API
from urllib.parse import quote
from fastapi import APIRouter, Form, HTTPException
from fastapi.responses import Response, JSONResponse

from db.handler import (
    get_file_meta,
    get_file_blob,
    get_file_text,
    update_file_text,
)
from fileio.file_embedder import embed_and_insert

router = APIRouter()


@router.get("/api/pdf/{file_id}")
def get_pdf(file_id: str):
    """
    files_blob から PDF バイナリを返却。
    ファイル名は files_meta.file_name を利用。
    """
    meta = get_file_meta(file_id)
    if not meta:
        raise HTTPException(status_code=404, detail="PDF not found")

    blob = get_file_blob(file_id)
    if blob is None:
        raise HTTPException(status_code=404, detail="PDF blob not found")

    file_name = meta["file_name"]
    quoted  = quote(file_name)
    return Response(
        content=blob,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"inline; file_name*=UTF-8''{quoted}"
        }
    )


@router.get("/api/content/{file_id}")
def get_content(file_id: str):
    """
    files_text.refined_text を返却。
    """
    textrec = get_file_text(file_id)
    if not textrec or textrec.get("refined_text") is None:
        raise HTTPException(status_code=404, detail="Content not found")
    return JSONResponse({"content": textrec["refined_text"]})


@router.post("/api/save/{file_id}")
def save_content(file_id: str, content: str = Form(...)):
    """
    編集後コンテンツを files_text にアップデートし、
    再ベクトル化を行う。
    """
    meta = get_file_meta(file_id)
    if not meta:
        raise HTTPException(status_code=404, detail="File not found")

    # 1) テキスト更新
    update_file_text(file_id, refined_text=content)

    # 2) 再ベクトル化
    embed_and_insert(
        texts=[content],
        file_name=meta["file_name"],
        model_keys=None,        # すべてのモデル or デフォルトモデルを渡す
        quality_score=0.0,
        overwrite=True,
        file_id=file_id
    )

    return JSONResponse({"status": "started"})
