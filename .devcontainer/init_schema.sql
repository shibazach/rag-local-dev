-- .devcontainer/init_schema.sql  最終更新 2025-01-08 04:45
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

-- files_image (画像データ保存用 - PDFから抽出した画像等)
CREATE TABLE files_image (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    blob_id         UUID NOT NULL REFERENCES files_blob(id) ON DELETE CASCADE,
    page_number     INTEGER NOT NULL,
    image_index     INTEGER NOT NULL,
    image_type      VARCHAR(50) NOT NULL DEFAULT 'image',
    image_data      BYTEA NOT NULL,
    image_format    VARCHAR(10),
    width           INTEGER,
    height          INTEGER,
    caption         TEXT,
    extracted_text  TEXT,
    created_at      TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_files_image_blob_id ON files_image(blob_id);
CREATE INDEX idx_files_image_page ON files_image(blob_id, page_number);

-- embeddings (テキストチャンクの埋め込みベクトル保存用)
CREATE TABLE embeddings (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    blob_id             UUID NOT NULL REFERENCES files_blob(id) ON DELETE CASCADE,
    chunk_index         INTEGER NOT NULL,
    chunk_text          TEXT NOT NULL,
    chunk_start         INTEGER,
    chunk_end           INTEGER,
    vector_json         TEXT,  -- 実装予定: vector型への移行
    embedding_model     VARCHAR(100),
    embedding_dimension INTEGER,
    created_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_embeddings_blob_id ON embeddings(blob_id);
CREATE INDEX idx_embeddings_chunk ON embeddings(blob_id, chunk_index);

/* 将来実装予定: ベクトル専用インデックス
CREATE INDEX idx_embeddings_vector
  ON embeddings USING ivfflat (vector) WITH (lists = 100);
*/

-- chat_sessions (チャットセッション管理 - 未実装)
-- REM: ユーザーごとのチャットセッションを管理。会話の履歴を論理的にグループ化
CREATE TABLE chat_sessions (
    id          SERIAL PRIMARY KEY,
    session_id  VARCHAR NOT NULL UNIQUE,
    user_id     INTEGER NOT NULL,  -- REM: 将来的にusersテーブルと連携予定
    title       VARCHAR,
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    updated_at  TIMESTAMPTZ DEFAULT NOW(),
    is_active   BOOLEAN DEFAULT TRUE
);

CREATE INDEX idx_chat_sessions_user ON chat_sessions(user_id);
CREATE INDEX idx_chat_sessions_session ON chat_sessions(session_id);

-- chat_messages (チャットメッセージ履歴 - 未実装)
-- REM: ユーザーとAIの会話履歴を保存。RAGシステムで参照したファイル情報も記録
CREATE TABLE chat_messages (
    id               SERIAL PRIMARY KEY,
    session_id       VARCHAR NOT NULL,  -- chat_sessions.session_idへの参照
    role             VARCHAR NOT NULL,  -- 'user', 'assistant', 'system'
    content          TEXT NOT NULL,
    created_at       TIMESTAMPTZ DEFAULT NOW(),
    tokens_used      INTEGER,           -- REM: トークン消費量の追跡用
    referenced_files JSON               -- REM: RAG検索で使用したファイル情報
);

CREATE INDEX idx_chat_messages_session ON chat_messages(session_id);
CREATE INDEX idx_chat_messages_created ON chat_messages(created_at);

-- processing_queue (非同期処理キュー - 未実装)
-- REM: OCRやベクトル化などの重い処理をキューイングして管理
CREATE TABLE processing_queue (
    id            SERIAL PRIMARY KEY,
    file_id       UUID NOT NULL,       -- files_blob.idへの参照
    task_type     VARCHAR NOT NULL,    -- 'ocr', 'vectorize', 'image_extract' など
    priority      INTEGER DEFAULT 5,    -- 1-10 (1が最高優先度)
    status        VARCHAR DEFAULT 'pending',  -- 'pending', 'processing', 'completed', 'failed'
    retry_count   INTEGER DEFAULT 0,
    max_retries   INTEGER DEFAULT 3,
    created_at    TIMESTAMPTZ DEFAULT NOW(),
    started_at    TIMESTAMPTZ,
    completed_at  TIMESTAMPTZ,
    error_message TEXT
);

CREATE INDEX idx_processing_queue_status ON processing_queue(status);
CREATE INDEX idx_processing_queue_priority ON processing_queue(priority, created_at);
CREATE INDEX idx_processing_queue_file ON processing_queue(file_id);

-- system_config (システム設定 - 未実装)
-- REM: アプリケーション全体の設定値を保存（APIキー、モデル設定など）
CREATE TABLE system_config (
    id          SERIAL PRIMARY KEY,
    key         VARCHAR NOT NULL UNIQUE,
    value       TEXT,
    description TEXT,
    updated_at  TIMESTAMPTZ DEFAULT NOW()
);

-- REM: 初期設定値の例（将来実装時に使用）
-- INSERT INTO system_config (key, value, description) VALUES
-- ('openai_api_key', '', 'OpenAI APIキー'),
-- ('default_embedding_model', 'text-embedding-ada-002', 'デフォルトの埋め込みモデル'),
-- ('chunk_size', '1000', 'テキストチャンクのデフォルトサイズ'),
-- ('chunk_overlap', '200', 'チャンクのオーバーラップサイズ');

-- upload_logs (アップロードログ管理)
-- REM: ファイルアップロードのリアルタイム進捗追跡
CREATE TABLE upload_logs (
    id              VARCHAR(36) PRIMARY KEY,
    session_id      VARCHAR(36) NOT NULL,      -- アップロードセッションID
    file_name       VARCHAR(255) NOT NULL,
    file_size       INTEGER NOT NULL,
    status          VARCHAR(20) NOT NULL DEFAULT 'pending',  -- pending, uploading, processing, completed, failed, duplicate
    progress        INTEGER DEFAULT 0,          -- アップロード進捗（0-100）
    message         TEXT,                       -- 詳細メッセージ
    error_detail    TEXT,                       -- エラー詳細
    metadata        JSON DEFAULT '{}',          -- 追加メタデータ
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_upload_logs_session_id ON upload_logs(session_id);
CREATE INDEX idx_upload_logs_status ON upload_logs(status);
CREATE INDEX idx_upload_logs_created_at ON upload_logs(created_at DESC);

-- updated_atの自動更新トリガー
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_upload_logs_updated_at 
BEFORE UPDATE ON upload_logs 
FOR EACH ROW 
EXECUTE FUNCTION update_updated_at_column();
