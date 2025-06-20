# src/embedder.py
import os
import numpy as np
import hashlib
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings
from sentence_transformers import SentenceTransformer
from sqlalchemy import create_engine
from sqlalchemy.sql import text as sql_text

from src import bootstrap
from src.embedding_config import embedding_options

engine = create_engine("postgresql://raguser:ragpass@pgvector-db:5432/ragdb")

# REM: numpy配列をpgvector文字列リテラルに変換
def to_pgvector_literal(vec):
    if isinstance(vec, np.ndarray):
        vec = vec.tolist()
    return "[" + ",".join(f"{float(x):.6f}" for x in vec) + "]"

# REM: ファイル内容のハッシュ生成
def compute_hash(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

# REM: filesテーブルにファイルを登録しfile_idを返す
def insert_file_and_get_id(filepath, refined_ja, score):
    from src.config import DEVELOPMENT_MODE
    from sqlalchemy import text as sql_text

    with open(filepath, "rb") as f:
        file_blob = f.read()

    file_hash = hashlib.sha256(file_blob).hexdigest()

    with engine.begin() as conn:
        # REM: files テーブルを初期化前に必ず作成
        conn.execute(sql_text("""
            CREATE TABLE IF NOT EXISTS files (
                file_id SERIAL PRIMARY KEY,
                filename TEXT,
                content TEXT,
                file_blob BYTEA,
                quality_score FLOAT,
                file_hash TEXT UNIQUE
            )
        """))

        if DEVELOPMENT_MODE:
            print("🧨 DEVELOPMENT_MODE: files テーブルを TRUNCATE")
            conn.execute(sql_text("TRUNCATE TABLE files CASCADE"))

        existing = conn.execute(sql_text(
            "SELECT file_id FROM files WHERE file_hash = :hash"
        ), {"hash": file_hash}).fetchone()

        if existing:
            print(f"📎 file_id {existing[0]} を files テーブルより取得")
            return existing[0]

        result = conn.execute(sql_text("""
            INSERT INTO files (filename, content, file_blob, quality_score, file_hash)
            VALUES (:filename, :content, :file_blob, :score, :hash)
            RETURNING file_id
        """), {
            "filename": os.path.basename(filepath),
            "content": refined_ja,
            "file_blob": file_blob,
            "score": score,
            "hash": file_hash
        })
        file_id = result.scalar()
        print(f"📎 file_id {file_id} を新規登録")
        return file_id

# REM: ベクトル化とDB登録（モデル指定対応）
def embed_and_insert(texts, filename, model_keys=None, truncate_done_tables=None, return_data=False, quality_score=0.0):
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks = [splitter.split_text(t) for t in texts]
    flat_chunks = [s for c in chunks for s in c]
    full_text = "\n".join(flat_chunks)

    file_id = insert_file_and_get_id(filename, full_text, quality_score)

    if truncate_done_tables is None:
        truncate_done_tables = set()

    all_chunks = []
    all_embeddings = []

    for key, config in embedding_options.items():
        # REM: 指定モデル以外はスキップ
        if model_keys is not None and key not in model_keys:
            continue

        print(f"🔍 モデル {key}: {config['model_name']} による埋め込み中...")

        # REM: モデルに応じて埋め込みエンジンを切り替え
        if config["embedder"] == "OllamaEmbeddings":
            embedder = OllamaEmbeddings(
                model=config["model_name"],
                base_url="http://host.docker.internal:11434"
            )
            embeddings = embedder.embed_documents(flat_chunks)
        elif config["embedder"] == "SentenceTransformer":
            device = "cuda" if torch.cuda.is_available() else "cpu"
            embedder = SentenceTransformer(config["model_name"], device=device)
            embeddings = embedder.encode(flat_chunks, convert_to_numpy=True)
        else:
            print(f"⚠️ 未対応の埋め込み: {config['embedder']}")
            continue

        # REM: テーブル名をモデル名から生成
        table_name = config["model_name"].replace("/", "_").replace("-", "_") + f"_{config['dimension']}"

        # REM: テーブル作成と初期化
        with engine.begin() as conn:
            conn.execute(sql_text(f"""
                CREATE TABLE IF NOT EXISTS "{table_name}" (
                    id SERIAL PRIMARY KEY,
                    content TEXT,
                    embedding VECTOR({config['dimension']}),
                    file_id INTEGER REFERENCES files(file_id)
                )
            """))

            if table_name not in truncate_done_tables:
                conn.execute(sql_text(f'TRUNCATE TABLE "{table_name}" CASCADE'))
                print(f"🧹 テーブル {table_name} を初期化しました")
                truncate_done_tables.add(table_name)

            # REM: チャンク毎に挿入
            insert_sql = sql_text(f"""
                INSERT INTO "{table_name}" (content, embedding, file_id)
                VALUES (:content, :embedding, :file_id)
            """)
            records = [
                {"content": chunk, "embedding": to_pgvector_literal(vec), "file_id": file_id}
                for chunk, vec in zip(flat_chunks, embeddings)
            ]
            conn.execute(insert_sql, records)
            print(f"✅ {len(records)} 件を {table_name} に挿入完了")

        if return_data:
            all_chunks.extend(flat_chunks)
            all_embeddings.extend(embeddings)

    if return_data:
        return all_chunks, all_embeddings
