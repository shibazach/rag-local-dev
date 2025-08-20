-- アップロードログテーブル作成
CREATE TABLE IF NOT EXISTS upload_logs (
    id VARCHAR(36) PRIMARY KEY,
    session_id VARCHAR(36) NOT NULL,
    file_name VARCHAR(255) NOT NULL,
    file_size INTEGER NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    progress INTEGER DEFAULT 0,
    message TEXT,
    error_detail TEXT,
    metadata JSON DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- インデックス作成
CREATE INDEX idx_upload_logs_session_id ON upload_logs(session_id);
CREATE INDEX idx_upload_logs_status ON upload_logs(status);
CREATE INDEX idx_upload_logs_created_at ON upload_logs(created_at DESC);

-- updated_atの自動更新トリガー（PostgreSQL用）
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


