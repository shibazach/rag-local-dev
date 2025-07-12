-- .devcontainer/init_schema.sql  最終更新 2025-07-12 22:45
-- 拡張
CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS vector;

-- files_meta
CREATE TABLE files_meta (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    file_name   TEXT        NOT NULL,
    mime_type   TEXT        NOT NULL,
    size        BIGINT      NOT NULL,
    created_at  TIMESTAMPTZ DEFAULT NOW()
    -- 後日追加予定: image_pages INT[] DEFAULT '{}', chart_pages INT[] DEFAULT '{}'
);

-- files_blob
CREATE TABLE files_blob (
    file_id    UUID PRIMARY KEY
               REFERENCES files_meta(id)
               ON DELETE CASCADE DEFERRABLE INITIALLY DEFERRED,
    blob_data  BYTEA NOT NULL,
    checksum   TEXT,
    stored_at  TIMESTAMPTZ DEFAULT NOW()
);

-- files_text
CREATE TABLE files_text (
    file_id        UUID PRIMARY KEY
                   REFERENCES files_meta(id)
                   ON DELETE CASCADE DEFERRABLE INITIALLY DEFERRED,
    raw_text       TEXT,
    refined_text   TEXT,
    quality_score  FLOAT,
    tags           TEXT[] DEFAULT '{}',
    updated_at     TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_files_text_tags ON files_text USING GIN (tags);

-- embeddings
CREATE TABLE embeddings (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    file_id     UUID REFERENCES files_meta(id) ON DELETE CASCADE,
    chunk_index INT   NOT NULL,
    vector      VECTOR,
    model_name  TEXT  NOT NULL
);

/* 任意: ベクトル専用インデックス
CREATE INDEX idx_embeddings_vector
  ON embeddings USING ivfflat (vector) WITH (lists = 100);
*/
