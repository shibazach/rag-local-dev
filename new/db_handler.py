# new/db_handler.py
# 旧系db/handler.pyを移植したDBハンドラー（3テーブル構成）

from __future__ import annotations

import os
import hashlib
import mimetypes
import tempfile
from typing import Any, Sequence, Optional, List, Dict
from sqlalchemy.sql import text as sql_text
from uuid import UUID

from .database import engine
from .config import DEVELOPMENT_MODE

# ──────────────────────────────────────────────────────────
# 内部ユーティリティ
# ──────────────────────────────────────────────────────────
def _calc_sha256(file_data: bytes) -> str:
    """バイナリデータからSHA256を計算"""
    return hashlib.sha256(file_data).hexdigest()

DEFAULT_MIME = "application/octet-stream"

def _normalize_tags(tags: Optional[Sequence[str]]) -> list[str]:
    return list(dict.fromkeys([t.strip() for t in (tags or []) if t.strip()]))

# ──────────────────────────────────────────────────────────
# 開発モード専用 DB 初期化
# ──────────────────────────────────────────────────────────
def reset_dev_database() -> None:
    """開発モード時のデータベースリセット"""
    if not DEVELOPMENT_MODE:
        return
    
    with engine.begin() as db:
        db.execute(sql_text("TRUNCATE files_blob, files_meta, files_text CASCADE"))
        # 埋め込みテーブルもクリア
        rows = db.execute(
            sql_text("""SELECT tablename FROM pg_tables
                       WHERE schemaname='public'
                         AND tablename ~ '^[a-zA-Z0-9_]+_[0-9]+$'""")
        ).fetchall()
        for (tbl,) in rows:
            db.execute(sql_text(f'TRUNCATE "{tbl}"'))

# ──────────────────────────────────────────────────────────
# 重複チェック機能
# ──────────────────────────────────────────────────────────
def find_existing_by_checksum(checksum: str) -> Optional[str]:
    """checksumで既存ファイルを検索し、あればそのblob_idを返す"""
    with engine.connect() as db:
        row = db.execute(
            sql_text("SELECT id FROM files_blob WHERE checksum = :checksum"),
            {"checksum": checksum}
        ).first()
    return str(row[0]) if row else None

# ──────────────────────────────────────────────────────────
# ファイル一括 INSERT
# ──────────────────────────────────────────────────────────
def insert_file_blob_only(
    file_name: str,
    file_data: bytes,
    mime_type: str = None
) -> str:
    """
    ファイルのアップロード時：blobとmetaのみ保存
    1. checksum計算
    2. 既存blob検索（重複チェック）
    3. files_blob INSERT（新規の場合）
    4. files_meta INSERT/UPDATE
    """
    result = insert_file_blob_with_details(file_name, file_data, mime_type)
    return result["blob_id"]

def insert_file_blob_with_details(
    file_name: str,
    file_data: bytes,
    mime_type: str = None
) -> dict:
    """
    ファイルのアップロード時：blobとmetaのみ保存（詳細情報付き）
    戻り値: {blob_id, is_existing, file_info}
    """
    file_hash = _calc_sha256(file_data)
    size = len(file_data)
    mime_type = mime_type or mimetypes.guess_type(file_name)[0] or DEFAULT_MIME
    
    with engine.begin() as db:
        # 1. 既存blob検索
        existing_blob_id = find_existing_by_checksum(file_hash)
        is_existing = existing_blob_id is not None
        
        if existing_blob_id:
            # 既存blobを使用
            blob_id = existing_blob_id
            print(f"[handler] Using existing blob: {blob_id}")
        else:
            # 新規blob作成
            blob_id = db.execute(
                sql_text("""
                    INSERT INTO files_blob (checksum, blob_data)
                    VALUES (:checksum, :data)
                    RETURNING id
                """),
                {"checksum": file_hash, "data": file_data}
            ).scalar_one()
            print(f"[handler] Created new blob: {blob_id}")

        # 2. files_meta INSERT/UPDATE
        db.execute(
            sql_text("""
                INSERT INTO files_meta (blob_id, file_name, mime_type, size)
                VALUES (:blob_id, :fn, :mt, :sz)
                ON CONFLICT (blob_id) DO UPDATE SET
                    file_name = EXCLUDED.file_name,
                    mime_type = EXCLUDED.mime_type,
                    size = EXCLUDED.size,
                    created_at = NOW()
            """),
            {"blob_id": blob_id, "fn": file_name, "mt": mime_type, "sz": size}
        )
        
        # 3. ファイル詳細情報を取得
        file_info = db.execute(
            sql_text("""
                SELECT 
                    m.file_name,
                    m.mime_type,
                    m.size,
                    m.created_at,
                    t.raw_text,
                    t.refined_text
                FROM files_meta m
                LEFT JOIN files_text t ON m.blob_id = t.blob_id
                WHERE m.blob_id = :blob_id
            """),
            {"blob_id": blob_id}
        ).mappings().first()
        
        # ステータス判定
        raw_text = file_info.get("raw_text", "") if file_info else ""
        refined_text = file_info.get("refined_text", "") if file_info else ""
        has_raw_text = raw_text and raw_text.strip()
        has_refined_text = refined_text and refined_text.strip()
        
        if not has_raw_text:
            status = "pending_processing"
        elif not has_refined_text:
            status = "text_extracted"
        else:
            status = "processed"
        
        # PDFページ数の計算（簡易版）
        page_count = 0
        if mime_type == "application/pdf" and raw_text:
            # テキストベースの簡易ページ数推定
            page_count = max(1, len(raw_text) // 2000)  # 2000文字/ページと仮定
    
    return {
        "blob_id": str(blob_id),
        "is_existing": is_existing,
        "file_info": {
            "file_name": file_info["file_name"] if file_info else file_name,
            "mime_type": file_info["mime_type"] if file_info else mime_type,
            "size": file_info["size"] if file_info else size,
            "created_at": file_info["created_at"] if file_info else None,
            "status": status,
            "page_count": page_count
        }
    }

def insert_file_full(
    file_name: str,
    file_data: bytes,
    raw_text: str,
    refined_text: str,
    quality_score: float,
    tags: Optional[Sequence[str]] = None,
    mime_type: str = None,
) -> str:
    """
    データ登録時：blob、meta、textを全て保存
    """
    file_hash = _calc_sha256(file_data)
    size = len(file_data)
    mime_type = mime_type or mimetypes.guess_type(file_name)[0] or DEFAULT_MIME
    tags_list = _normalize_tags(tags)
    
    with engine.begin() as db:
        # 1. 既存blob検索
        existing_blob_id = find_existing_by_checksum(file_hash)
        
        if existing_blob_id:
            # 既存blobを使用
            blob_id = existing_blob_id
            print(f"[handler] Using existing blob: {blob_id}")
        else:
            # 新規blob作成
            blob_id = db.execute(
                sql_text("""
                    INSERT INTO files_blob (checksum, blob_data)
                    VALUES (:checksum, :data)
                    RETURNING id
                """),
                {"checksum": file_hash, "data": file_data}
            ).scalar_one()
            print(f"[handler] Created new blob: {blob_id}")

        # 2. files_meta INSERT/UPDATE
        db.execute(
            sql_text("""
                INSERT INTO files_meta (blob_id, file_name, mime_type, size)
                VALUES (:blob_id, :fn, :mt, :sz)
                ON CONFLICT (blob_id) DO UPDATE SET
                    file_name = EXCLUDED.file_name,
                    mime_type = EXCLUDED.mime_type,
                    size = EXCLUDED.size,
                    created_at = NOW()
            """),
            {"blob_id": blob_id, "fn": file_name, "mt": mime_type, "sz": size}
        )

        # 3. files_text INSERT/UPDATE
        db.execute(
            sql_text("""
                INSERT INTO files_text (blob_id, raw_text, refined_text, quality_score, tags)
                VALUES (:blob_id, :raw, :ref, :qs, :tags)
                ON CONFLICT (blob_id) DO UPDATE SET
                    raw_text = EXCLUDED.raw_text,
                    refined_text = EXCLUDED.refined_text,
                    quality_score = EXCLUDED.quality_score,
                    tags = EXCLUDED.tags,
                    updated_at = NOW()
            """),
            {"blob_id": blob_id, "raw": raw_text, "ref": refined_text,
             "qs": quality_score, "tags": tags_list}
        )
    
    return str(blob_id)

# ──────────────────────────────────────────────────────────
# 取得系
# ──────────────────────────────────────────────────────────
def get_file_meta(blob_id: str) -> Optional[dict]:
    """files_meta から (file_name, mime_type, size, created_at) を取得"""
    with engine.connect() as db:
        row = db.execute(
            sql_text("""
                SELECT file_name, mime_type, size, created_at
                  FROM files_meta
                 WHERE blob_id = :blob_id
            """), {"blob_id": blob_id}
        ).mappings().first()
    return dict(row) if row else None

def get_file_blob(blob_id: str) -> Optional[bytes]:
    """files_blob からバイナリを取得"""
    with engine.connect() as db:
        row = db.execute(
            sql_text("SELECT blob_data FROM files_blob WHERE id = :blob_id"),
            {"blob_id": blob_id}
        ).first()
    return row[0] if row else None

def get_file_text(blob_id: str) -> Optional[dict]:
    """files_text から (raw_text, refined_text, quality_score, tags) を取得"""
    with engine.connect() as db:
        row = db.execute(
            sql_text("""
                SELECT raw_text, refined_text, quality_score, tags
                  FROM files_text
                 WHERE blob_id = :blob_id
            """), {"blob_id": blob_id}
        ).mappings().first()
    return dict(row) if row else None

def get_all_files() -> List[Dict[str, Any]]:
    """全ファイルの一覧を取得（正確なステータス判定付き）"""
    sql = """
        SELECT b.id as blob_id, m.file_name, m.mime_type, m.size, m.created_at,
               t.raw_text, t.refined_text
        FROM files_blob b
        JOIN files_meta m ON b.id = m.blob_id
        LEFT JOIN files_text t ON b.id = t.blob_id
        ORDER BY m.created_at DESC
    """
    with engine.connect() as db:
        rows = db.execute(sql_text(sql)).mappings().all()
    
    # 各ファイルに正確なステータスを設定
    result = []
    for row in rows:
        file_data = dict(row)
        
        # テキストデータの実態をチェック
        raw_text = file_data.get("raw_text", "")
        refined_text = file_data.get("refined_text", "")
        has_raw_text = raw_text and raw_text.strip()
        has_refined_text = refined_text and refined_text.strip()
        
        # ステータス判定
        if not has_raw_text:
            status = "pending_processing"  # 生テキストなし = 未処理
        elif not has_refined_text:
            status = "text_extracted"  # 生テキストあり、整形テキストなし = 未整形
        else:
            status = "processed"  # 両方あり = 処理完了
        
        file_data["status"] = status
        file_data["id"] = file_data["blob_id"]  # APIとの互換性のため
        result.append(file_data)
    
    return result

# ──────────────────────────────────────────────────────────
# 更新系
# ──────────────────────────────────────────────────────────
def update_file_text(
    blob_id: str,
    refined_text: str | None = None,
    raw_text: str | None = None,
    quality_score: float | None = None,
    tags: Optional[Sequence[str]] | None = None,
) -> None:
    """files_text を更新"""
    sets, params = [], {"blob_id": blob_id}
    if refined_text is not None: 
        sets.append("refined_text = :ref")
        params["ref"] = refined_text
    if raw_text is not None: 
        sets.append("raw_text = :raw")
        params["raw"] = raw_text
    if quality_score is not None: 
        sets.append("quality_score = :qs")
        params["qs"] = quality_score
    if tags is not None: 
        sets.append("tags = :tags")
        params["tags"] = _normalize_tags(tags)
    
    if not sets:
        return

    sets.append("updated_at = NOW()")
    sql = f"UPDATE files_text SET {', '.join(sets)} WHERE blob_id = :blob_id"
    with engine.begin() as db:
        db.execute(sql_text(sql), params)

# ──────────────────────────────────────────────────────────
# 削除系
# ──────────────────────────────────────────────────────────
def delete_file(blob_id: str) -> bool:
    """ファイルを削除（CASCADE削除）"""
    with engine.begin() as db:
        result = db.execute(
            sql_text("DELETE FROM files_blob WHERE id = :blob_id"),
            {"blob_id": blob_id}
        )
        return result.rowcount > 0

def drop_trial_tables() -> None:
    """trialで始まるテーブルを削除"""
    with engine.begin() as db:
        # trialで始まるテーブルを検索
        result = db.execute(sql_text("""
            SELECT tablename FROM pg_tables 
            WHERE tablename LIKE 'trial%'
        """))
        trial_tables = [row[0] for row in result]
        
        if trial_tables:
            print(f"🗑️ trialテーブルを削除中: {trial_tables}")
            for table in trial_tables:
                db.execute(sql_text(f'DROP TABLE IF EXISTS "{table}" CASCADE'))
            print(f"✅ {len(trial_tables)}個のtrialテーブルを削除しました")
        else:
            print("ℹ️ trialテーブルは見つかりませんでした")

def cleanup_obsolete_tables() -> None:
    """不要な旧系テーブルを削除"""
    obsolete_tables = [
        'file_images',  # 旧系画像テーブル
        'file_texts',   # 旧系テキストテーブル
        'files'         # 旧系ファイルテーブル
    ]
    
    with engine.begin() as db:
        dropped_tables = []
        for table in obsolete_tables:
            try:
                # テーブルが存在するかチェック
                result = db.execute(sql_text(f"""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = '{table}'
                    )
                """))
                exists = result.scalar()
                
                if exists:
                    db.execute(sql_text(f'DROP TABLE IF EXISTS "{table}" CASCADE'))
                    dropped_tables.append(table)
                    print(f"🗑️ 削除: {table}")
                else:
                    print(f"ℹ️ 存在しない: {table}")
            except Exception as e:
                print(f"⚠️ エラー ({table}): {e}")
        
        if dropped_tables:
            print(f"✅ {len(dropped_tables)}個の不要テーブルを削除しました: {dropped_tables}")
        else:
            print("ℹ️ 削除対象のテーブルはありませんでした")

def cleanup_embedder_tables() -> None:
    """embedder専用テーブルを削除（embeddingsテーブルに統合後）"""
    embedder_tables = [
        'intfloat_e5_large_v2_1024',
        'intfloat_e5_small_v2_384',
        'nomic_embed_text_768'
    ]
    
    with engine.begin() as db:
        dropped_tables = []
        for table in embedder_tables:
            try:
                # テーブルが存在するかチェック
                result = db.execute(sql_text(f"""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = '{table}'
                    )
                """))
                exists = result.scalar()
                
                if exists:
                    db.execute(sql_text(f'DROP TABLE IF EXISTS "{table}" CASCADE'))
                    dropped_tables.append(table)
                    print(f"🗑️ 削除: {table}")
                else:
                    print(f"ℹ️ 存在しない: {table}")
            except Exception as e:
                print(f"⚠️ エラー ({table}): {e}")
        
        if dropped_tables:
            print(f"✅ {len(dropped_tables)}個のembedder専用テーブルを削除しました: {dropped_tables}")
            print("📝 embeddingsテーブルに統合されました")
        else:
            print("ℹ️ 削除対象のembedderテーブルはありませんでした")

# ──────────────────────────────────────────────────────────
# 埋め込みテーブル操作
# ──────────────────────────────────────────────────────────
def ensure_embedding_table(table_name: str, dim: int) -> None:
    """埋め込みテーブルを作成（blob_id参照に変更）"""
    with engine.begin() as db:
        db.execute(sql_text(f"""
            CREATE TABLE IF NOT EXISTS "{table_name}" (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                content TEXT,
                embedding VECTOR({dim}),
                blob_id UUID REFERENCES files_blob(id) ON DELETE CASCADE
            )
        """))

def bulk_insert_embeddings(table_name: str, records: List[Dict[str, Any]]) -> None:
    """埋め込みレコードの一括INSERT（blob_id使用）"""
    if not records: 
        return
    with engine.begin() as db:
        db.execute(
            sql_text(f"""INSERT INTO "{table_name}"
                         (content, embedding, blob_id)
                         VALUES (:content, :embedding, :blob_id)"""),
            records
        )

def fetch_top_chunks(query_vec: str, table_name: str, limit: int = 5) -> list[dict]:
    """チャンク単位での近傍検索（新しいJOIN構造）"""
    sql = f"""
        SELECT e.content   AS snippet,
               b.id        AS blob_id,
               m.file_name AS file_name
          FROM "{table_name}" AS e
          JOIN files_blob AS b ON e.blob_id = b.id
          JOIN files_meta AS m ON b.id = m.blob_id
         ORDER BY e.embedding <-> '{query_vec}'::vector
         LIMIT :limit
    """
    with engine.connect() as db:
        rows = db.execute(sql_text(sql), {"limit": limit}).mappings().all()
    return [dict(r) for r in rows]

def fetch_top_files(query_vec: str, table_name: str, limit: int = 10) -> list[dict]:
    """ファイル単位での近傍検索（新しいJOIN構造）"""
    sql = f"""
        SELECT DISTINCT
               b.id            AS blob_id,
               m.file_name     AS file_name,
               t.refined_text  AS refined_text,
               MIN(e.embedding <-> '{query_vec}'::vector) AS distance
          FROM "{table_name}" AS e
          JOIN files_blob AS b ON e.blob_id = b.id
          JOIN files_meta AS m ON b.id = m.blob_id
          JOIN files_text AS t ON b.id = t.blob_id
         GROUP BY b.id, m.file_name, t.refined_text
         ORDER BY distance ASC
         LIMIT :limit
    """
    with engine.connect() as db:
        rows = db.execute(sql_text(sql), {"limit": limit}).mappings().all()
    return [dict(r) for r in rows]

def delete_embedding_for_file(table_name: str, blob_id: str) -> None:
    """指定blob_idの古い埋め込みレコードを削除（overwrite用）"""
    with engine.begin() as db:
        db.execute(sql_text(f'DELETE FROM "{table_name}" WHERE blob_id = :blob_id'),
                   {"blob_id": blob_id})

def migrate_embeddings_table() -> None:
    """embeddingsテーブルを新設計に移行"""
    with engine.begin() as db:
        # 旧テーブルを削除
        db.execute(sql_text("DROP TABLE IF EXISTS embeddings CASCADE"))
        
        # 新テーブルを作成
        db.execute(sql_text("""
            CREATE TABLE embeddings (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                content TEXT NOT NULL,
                embedding VECTOR(1536),  -- デフォルト次元（後で変更可能）
                blob_id UUID REFERENCES files_blob(id) ON DELETE CASCADE,
                embedding_model VARCHAR(100) NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            )
        """))
        
        print("✅ embeddingsテーブルを新設計に移行しました")
        print("  - content: テキストチャンク")
        print("  - embedding: ベクトル（次元は後で調整可能）")
        print("  - blob_id: ファイル参照")
        print("  - embedding_model: embedder名+次元（例: intfloat_e5_large_v2_1024）")

def insert_embedding(content: str, embedding: List[float], blob_id: str, embedding_model: str) -> None:
    """新設計embeddingsテーブルに埋め込みを挿入"""
    with engine.begin() as db:
        db.execute(sql_text("""
            INSERT INTO embeddings (content, embedding, blob_id, embedding_model)
            VALUES (:content, :embedding, :blob_id, :embedding_model)
        """), {
            "content": content,
            "embedding": embedding,
            "blob_id": blob_id,
            "embedding_model": embedding_model
        })

def get_embeddings_by_model(embedding_model: str) -> List[Dict[str, Any]]:
    """指定したembedding_modelの埋め込みを取得"""
    with engine.connect() as db:
        result = db.execute(sql_text("""
            SELECT e.content, e.embedding, e.blob_id, m.file_name
            FROM embeddings e
            JOIN files_meta m ON e.blob_id = m.blob_id
            WHERE e.embedding_model = :embedding_model
            ORDER BY e.created_at DESC
        """), {"embedding_model": embedding_model})
        return [dict(row) for row in result.mappings()]

def search_embeddings(query_embedding: List[float], embedding_model: str, limit: int = 5) -> List[Dict[str, Any]]:
    """指定したembedding_modelで類似検索"""
    with engine.connect() as db:
        result = db.execute(sql_text("""
            SELECT e.content AS snippet,
                   e.blob_id,
                   m.file_name,
                   e.embedding <-> :query_embedding::vector AS distance
            FROM embeddings e
            JOIN files_meta m ON e.blob_id = m.blob_id
            WHERE e.embedding_model = :embedding_model
            ORDER BY distance
            LIMIT :limit
        """), {
            "query_embedding": query_embedding,
            "embedding_model": embedding_model,
            "limit": limit
        })
        return [dict(row) for row in result.mappings()]

# ──────────────────────────────────────────────────────────
# 一時ファイル作成（プレビュー用）
# ──────────────────────────────────────────────────────────
def get_file_path(blob_id: str) -> Optional[str]:
    """ファイルIDからファイルパスを取得（一時的な実装）"""
    # バイナリデータを取得
    blob_data = get_file_blob(blob_id)
    if not blob_data:
        return None
    
    # メタデータを取得してファイル名を決定
    meta = get_file_meta(blob_id)
    if not meta:
        return None
    
    # 一時ファイルに書き出し
    suffix = os.path.splitext(meta['file_name'])[1] or '.pdf'
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
        temp_file.write(blob_data)
        return temp_file.name 