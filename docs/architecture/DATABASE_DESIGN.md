# データベース設計書

## 概要

R&D RAGシステムのデータベースは、PostgreSQL + pgvectorを使用し、効率的なファイル管理とベクトル検索を実現します。

## 設計思想

### checksum主導設計
- ファイルの重複を防ぐため、SHA256チェックサムで一意性を保証
- 同一ファイルの重複アップロードを自動的に検出・防止
- ストレージ効率の最大化

### 3テーブル分割設計（Files3兄弟）
OLD/db/構想.txt の設計思想に基づく：

1. **files_blob** - バイナリデータ（主テーブル）
   - 実ファイルのバイナリデータを格納
   - checksumによる一意制約
   - 将来的には外部ストレージ（S3等）への移行も考慮

2. **files_meta** - メタデータ
   - ファイル名、MIMEタイプ、サイズ等の不変情報
   - 検索UIの高速化のため軽量に保持
   - 将来的にimage_pages, chart_pagesを追加予定

3. **files_text** - テキストデータ
   - OCR抽出テキスト、LLM整形テキスト
   - 品質スコア、タグ情報
   - 更新が頻繁な情報を分離してロック競合を最小化

### 設計のメリット
- **性能**: メタ情報のみの検索が高速
- **柔軟性**: テキスト編集がfiles_textのみに閉じる
- **拡張性**: バイナリの外部ストレージ移行が容易
- **保守性**: 用途別にテーブルが分離され管理しやすい

## テーブル定義

### files_blob
```sql
CREATE TABLE files_blob (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    checksum     VARCHAR(64) NOT NULL UNIQUE,
    blob_data    BYTEA NOT NULL,
    stored_at    TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_files_blob_checksum ON files_blob(checksum);
CREATE INDEX idx_files_blob_stored_at ON files_blob(stored_at);
```

### files_meta
```sql
CREATE TABLE files_meta (
    blob_id      UUID PRIMARY KEY REFERENCES files_blob(id) ON DELETE CASCADE,
    file_name    VARCHAR(255) NOT NULL,
    mime_type    VARCHAR(100) NOT NULL,
    size         INTEGER NOT NULL,
    created_at   TIMESTAMPTZ DEFAULT NOW()
    -- 将来追加:
    -- image_pages INT[] DEFAULT '{}',
    -- chart_pages INT[] DEFAULT '{}'
);
CREATE INDEX idx_files_meta_file_name ON files_meta(file_name);
CREATE INDEX idx_files_meta_created_at ON files_meta(created_at);
```

### files_text
```sql
CREATE TABLE files_text (
    blob_id       UUID PRIMARY KEY REFERENCES files_blob(id) ON DELETE CASCADE,
    raw_text      TEXT,
    refined_text  TEXT,
    quality_score FLOAT,
    tags          TEXT[] DEFAULT '{}',
    updated_at    TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_files_text_tags ON files_text USING GIN (tags);
CREATE INDEX idx_files_text_updated_at ON files_text(updated_at);
```

### embeddings
```sql
CREATE TABLE embeddings (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    blob_id           UUID REFERENCES files_blob(id) ON DELETE CASCADE,
    chunk_index       INTEGER NOT NULL,
    chunk_text        TEXT NOT NULL,
    chunk_start       INTEGER,
    chunk_end         INTEGER,
    vector_json       TEXT,  -- 一時的、将来的にはvector型
    embedding_model   VARCHAR(100),
    embedding_dimension INTEGER,
    created_at        TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_embeddings_blob_id ON embeddings(blob_id);
CREATE INDEX idx_embeddings_chunk_index ON embeddings(blob_id, chunk_index);
```

### file_images
```sql
CREATE TABLE file_images (
    id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    blob_id        UUID REFERENCES files_blob(id) ON DELETE CASCADE,
    page_number    INTEGER,
    image_index    INTEGER,
    image_type     VARCHAR(50),  -- image, chart, diagram
    image_data     BYTEA,
    image_format   VARCHAR(20),
    width          INTEGER,
    height         INTEGER,
    caption        TEXT,
    extracted_text TEXT,
    created_at     TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_file_images_blob_id ON file_images(blob_id);
CREATE INDEX idx_file_images_page ON file_images(blob_id, page_number);
```

## 参照整合性

- **CASCADE削除**: files_blob削除時、関連する全テーブルのレコードも削除
- **単方向依存**: embeddings削除はfiles_blobに影響しない
- **DEFERRABLE**: 複合トランザクションでの整合性確保（将来実装）

## 画像・グラフ検出（将来拡張）

PDFに含まれる画像やグラフを検出し、マルチモーダルLLMでの優先処理に使用：

```python
# ページごとの画像・グラフ検出
image_pages = [1, 3, 5]  # 画像があるページ
chart_pages = [2, 4]     # グラフがあるページ

# files_metaに保存（ALTER TABLEで追加）
UPDATE files_meta 
SET image_pages = '{1,3,5}', 
    chart_pages = '{2,4}'
WHERE blob_id = :blob_id;
```

詳細な実装は `app/core/image_detection_concept.py` を参照。

## 移行・アップグレード

### SQLiteからの移行
プロジェクトではPostgreSQLを使用。SQLiteは開発時のみ。

### pgvector拡張
```sql
CREATE EXTENSION IF NOT EXISTS vector;
-- 将来的にembeddings.vector_jsonをvector型に移行
```

### タグのテーブル分離（将来）
タグが肥大化した場合：
```sql
CREATE TABLE file_tags (
    id      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    blob_id UUID REFERENCES files_blob(id) ON DELETE CASCADE,
    tag     TEXT NOT NULL,
    UNIQUE (blob_id, tag)
);
```

## ベストプラクティス

1. **トランザクション管理**
   - ファイル登録は3テーブルへの挿入を1トランザクションで
   - エラー時は全体をロールバック

2. **インデックス戦略**
   - 検索頻度の高いカラムには必ずインデックス
   - 配列型（tags）にはGINインデックス
   - ベクトル検索にはivfflatまたはhnsw

3. **パフォーマンス最適化**
   - files_metaのみで完結する処理は積極的に活用
   - 大きなバイナリアクセスは必要時のみ
   - バッチ処理での一括更新

## 参考資料

- [OLD/db/構想.txt](../../OLD/db/構想.txt) - 初期設計の議論
- [OLD/db/schema.py](../../OLD/db/schema.py) - 元の実装
- [app/core/models.py](../../app/core/models.py) - 現在の実装
- [app/core/image_detection_concept.py](../../app/core/image_detection_concept.py) - 画像検出の設計思想