"""
シンプルで安定的なDB接続ヘルパー
NiceGUIとの相性を考慮した同期的実装
"""

import psycopg2
import psycopg2.extras
from contextlib import contextmanager
from typing import List, Dict, Any, Optional
import os
from app.config import logger, config

# データベース接続URL（config.pyから取得）
DATABASE_URL = config.DATABASE_URL
logger.info(f"DB接続URL: {DATABASE_URL}")

@contextmanager
def get_db_connection():
    """
    シンプルなDB接続コンテキストマネージャー
    自動的に接続を開いて閉じる
    """
    conn = None
    try:
        # デバッグ用に接続文字列を出力
        logger.debug(f"接続先DB: {DATABASE_URL}")
        conn = psycopg2.connect(DATABASE_URL)
        yield conn
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"DB接続エラー: {e}")
        logger.error(f"接続文字列: {DATABASE_URL}")
        raise
    finally:
        if conn:
            conn.close()

def fetch_all(query: str, params: tuple = None) -> List[Dict[str, Any]]:
    """
    SELECT文を実行して全結果を辞書のリストで返す
    """
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(query, params)
            return cur.fetchall()

def fetch_one(query: str, params: tuple = None) -> Optional[Dict[str, Any]]:
    """
    SELECT文を実行して1件の結果を辞書で返す
    """
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(query, params)
            return cur.fetchone()

def execute(query: str, params: tuple = None) -> int:
    """
    INSERT/UPDATE/DELETE文を実行
    """
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)
            conn.commit()
            return cur.rowcount

def get_file_list(limit: int = 1000, offset: int = 0) -> Dict[str, Any]:
    """
    ファイルリスト取得（安定版）
    """
    try:
        # 総数取得
        count_query = "SELECT COUNT(*) as total FROM files_blob"
        total_result = fetch_one(count_query)
        total = total_result['total'] if total_result else 0
        
        # ファイルリスト取得（blob_dataは除外）
        list_query = """
            SELECT 
                fb.id,
                fb.checksum,
                fb.stored_at,
                fm.file_name,
                fm.mime_type,
                fm.size,
                fm.created_at,
                ft.blob_id IS NOT NULL as has_text,
                CASE 
                    WHEN ft.refined_text IS NOT NULL THEN LENGTH(ft.refined_text)
                    WHEN ft.raw_text IS NOT NULL THEN LENGTH(ft.raw_text)
                    ELSE 0
                END as text_length,
                CASE
                    WHEN ft.refined_text IS NOT NULL THEN 'processed'
                    WHEN ft.raw_text IS NOT NULL THEN 'processing'
                    ELSE 'pending'
                END as status
            FROM files_blob fb
            LEFT JOIN files_meta fm ON fb.id = fm.blob_id
            LEFT JOIN files_text ft ON fb.id = ft.blob_id
            ORDER BY fb.stored_at DESC
            LIMIT %s OFFSET %s
        """
        
        rows = fetch_all(list_query, (limit, offset))
        
        # 結果を整形
        files = []
        for row in rows:
            files.append({
                "file_id": str(row['id']),
                "checksum": row['checksum'],
                "filename": row['file_name'] or "unknown",
                "file_size": row['size'] or 0,
                "content_type": row['mime_type'] or "application/octet-stream",
                "is_pdf": row['mime_type'] == 'application/pdf' if row['mime_type'] else False,
                "created_at": row['stored_at'].isoformat() if row['stored_at'] else "",
                "has_text": row['has_text'],
                "text_length": row['text_length'],
                "status": row['status']
            })
        
        return {
            "files": files,
            "total": total,
            "limit": limit,
            "offset": offset
        }
        
    except Exception as e:
        logger.error(f"ファイルリスト取得エラー: {e}")
        return {
            "files": [],
            "total": 0,
            "limit": limit,
            "offset": offset
        }

def get_file_with_blob(file_id: str) -> Optional[Dict[str, Any]]:
    """
    個別ファイル取得（blob含む）
    """
    try:
        query = """
            SELECT 
                fb.id,
                fb.checksum,
                fb.blob_data,
                fb.stored_at,
                fm.file_name,
                fm.mime_type,
                fm.size,
                fm.created_at,
                ft.raw_text,
                ft.refined_text,
                ft.quality_score,
                ft.tags,
                ft.updated_at
            FROM files_blob fb
            LEFT JOIN files_meta fm ON fb.id = fm.blob_id
            LEFT JOIN files_text ft ON fb.id = ft.blob_id
            WHERE fb.id = %s
        """
        
        row = fetch_one(query, (file_id,))
        
        if not row:
            return None
            
        return {
            "file_id": str(row['id']),
            "checksum": row['checksum'],
            "blob_data": row['blob_data'],
            "filename": row['file_name'] or "unknown",
            "file_size": row['size'] or 0,
            "content_type": row['mime_type'] or "application/octet-stream",
            "created_at": row['stored_at'].isoformat() if row['stored_at'] else "",
            "raw_text": row['raw_text'],
            "refined_text": row['refined_text'],
            "quality_score": row['quality_score'],
            "tags": row['tags'],
            "updated_at": row['updated_at'].isoformat() if row['updated_at'] else None
        }
        
    except Exception as e:
        logger.error(f"ファイル取得エラー（ID: {file_id}）: {e}")
        return None

def check_file_exists(checksum: str) -> Optional[str]:
    """
    チェックサムでファイルの存在確認
    """
    try:
        query = "SELECT id FROM files_blob WHERE checksum = %s LIMIT 1"
        result = fetch_one(query, (checksum,))
        return str(result['id']) if result else None
    except Exception as e:
        logger.error(f"ファイル存在確認エラー: {e}")
        return None

def insert_file_blob(file_id: str, checksum: str, blob_data: bytes) -> bool:
    """
    ファイルBLOBデータを挿入
    """
    try:
        query = """
            INSERT INTO files_blob (id, checksum, blob_data, stored_at)
            VALUES (%s, %s, %s, NOW())
        """
        execute(query, (file_id, checksum, blob_data))
        return True
    except Exception as e:
        logger.error(f"ファイルBLOB挿入エラー: {e}")
        return False

def insert_file_meta(blob_id: str, filename: str, mime_type: str, size: int) -> bool:
    """
    ファイルメタデータを挿入
    """
    try:
        query = """
            INSERT INTO files_meta (blob_id, file_name, mime_type, size, created_at)
            VALUES (%s, %s, %s, %s, NOW())
        """
        execute(query, (blob_id, filename, mime_type, size))
        return True
    except Exception as e:
        logger.error(f"ファイルメタデータ挿入エラー: {e}")
        return False

def insert_file_text(blob_id: str, raw_text: str = None, refined_text: str = None) -> bool:
    """
    ファイルテキストデータを挿入
    """
    try:
        query = """
            INSERT INTO files_text (blob_id, raw_text, refined_text, updated_at)
            VALUES (%s, %s, %s, NOW())
            ON CONFLICT (blob_id) DO UPDATE
            SET raw_text = EXCLUDED.raw_text,
                refined_text = EXCLUDED.refined_text,
                updated_at = NOW()
        """
        execute(query, (blob_id, raw_text, refined_text))
        return True
    except Exception as e:
        logger.error(f"ファイルテキスト挿入エラー: {e}")
        return False

def delete_file(file_id: str) -> bool:
    """
    ファイル削除（CASCADE削除でFiles4兄弟すべて削除）
    """
    try:
        query = "DELETE FROM files_blob WHERE id = %s"
        rows_affected = execute(query, (file_id,))
        return rows_affected > 0
    except Exception as e:
        logger.error(f"ファイル削除エラー: {e}")
        return False

def get_files_for_export(user_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    エクスポート用のファイルリスト取得（blobは除く）
    """
    try:
        query = """
            SELECT 
                fb.id,
                fb.checksum,
                fb.stored_at,
                fm.file_name,
                fm.mime_type,
                fm.size,
                ft.raw_text,
                ft.refined_text,
                ft.quality_score,
                ft.tags
            FROM files_blob fb
            LEFT JOIN files_meta fm ON fb.id = fm.blob_id
            LEFT JOIN files_text ft ON fb.id = ft.blob_id
            ORDER BY fb.stored_at DESC
        """
        return fetch_all(query)
    except Exception as e:
        logger.error(f"エクスポート用ファイルリスト取得エラー: {e}")
        return []

# ================== Embeddings関連 ==================

def get_embeddings_stats() -> Dict[str, int]:
    """
    埋め込み統計情報を取得
    """
    try:
        stats = {}
        
        # 総チャンク数
        total_chunks_query = "SELECT COUNT(*) as count FROM embeddings"
        result = fetch_one(total_chunks_query)
        stats['total_chunks'] = result['count'] if result else 0
        
        # ベクトル化済みファイル数
        vectorized_files_query = """
            SELECT COUNT(DISTINCT blob_id) as count 
            FROM embeddings 
            WHERE blob_id IS NOT NULL
        """
        result = fetch_one(vectorized_files_query)
        stats['vectorized_files'] = result['count'] if result else 0
        
        return stats
    except Exception as e:
        logger.error(f"埋め込み統計取得エラー: {e}")
        return {'total_chunks': 0, 'vectorized_files': 0}

def insert_embedding(blob_id: str, chunk_index: int, content: str, embedding: List[float]) -> bool:
    """
    埋め込みデータを挿入
    """
    try:
        query = """
            INSERT INTO embeddings (blob_id, chunk_index, content, embedding, created_at)
            VALUES (%s, %s, %s, %s, NOW())
        """
        # PostgreSQLのarray型として埋め込みを保存
        execute(query, (blob_id, chunk_index, content, embedding))
        return True
    except Exception as e:
        logger.error(f"埋め込み挿入エラー: {e}")
        return False

def search_embeddings(query_embedding: List[float], limit: int = 10) -> List[Dict[str, Any]]:
    """
    類似度検索（pgvector使用）
    """
    try:
        query = """
            SELECT 
                e.blob_id,
                e.chunk_index,
                e.content,
                1 - (e.embedding <=> %s::vector) as similarity,
                fm.file_name
            FROM embeddings e
            LEFT JOIN files_meta fm ON e.blob_id = fm.blob_id
            ORDER BY e.embedding <=> %s::vector
            LIMIT %s
        """
        # 同じ埋め込みベクトルを2回渡す（距離計算と並び替えのため）
        return fetch_all(query, (query_embedding, query_embedding, limit))
    except Exception as e:
        logger.error(f"埋め込み検索エラー: {e}")
        return []

# ================== システム管理関連 ==================

def check_pgvector_extension() -> bool:
    """
    pgvector拡張が有効か確認
    """
    try:
        query = "SELECT 1 FROM pg_extension WHERE extname = 'vector'"
        result = fetch_one(query)
        return result is not None
    except Exception as e:
        logger.error(f"pgvector確認エラー: {e}")
        return False

def get_table_counts() -> Dict[str, int]:
    """
    各テーブルのレコード数を取得
    """
    try:
        tables = ['files_blob', 'files_meta', 'files_text', 'files_image', 'embeddings']
        counts = {}
        
        for table in tables:
            query = f"SELECT COUNT(*) as count FROM {table}"
            result = fetch_one(query)
            counts[table] = result['count'] if result else 0
            
        return counts
    except Exception as e:
        logger.error(f"テーブル数取得エラー: {e}")
        return {}
