-- .devcontainer/init_schema.sql  最終更新 2025-07-18 15:00
-- 拡張
CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS vector;

-- files_blob (主テーブル - checksum が真の一意性)
CREATE TABLE files_blob (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    checksum    TEXT UNIQUE NOT NULL,
    blob_data   BYTEA NOT NULL,
    stored_at   TIMESTAMPTZ DEFAULT NOW()
);

-- files_meta (1:1対応)
CREATE TABLE files_meta (
    blob_id     UUID PRIMARY KEY
                REFERENCES files_blob(id)
                ON DELETE CASCADE DEFERRABLE INITIALLY DEFERRED,
    file_name   TEXT NOT NULL,
    mime_type   TEXT NOT NULL,
    size        BIGINT NOT NULL,
    created_at  TIMESTAMPTZ DEFAULT NOW()
    -- 後日追加予定: image_pages INT[] DEFAULT '{}', chart_pages INT[] DEFAULT '{}'
);

-- files_text (1:1対応)
CREATE TABLE files_text (
    blob_id        UUID PRIMARY KEY
                   REFERENCES files_blob(id)
                   ON DELETE CASCADE DEFERRABLE INITIALLY DEFERRED,
    raw_text       TEXT,
    refined_text   TEXT,
    quality_score  FLOAT,
    tags           TEXT[] DEFAULT '{}',
    updated_at     TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_files_text_tags ON files_text USING GIN (tags);

/* 任意: ベクトル専用インデックス
CREATE INDEX idx_embeddings_vector
  ON embeddings USING ivfflat (vector) WITH (lists = 100);
*/
