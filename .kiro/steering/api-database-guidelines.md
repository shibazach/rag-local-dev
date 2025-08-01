---
inclusion: always
---

# API・データベース設計ガイドライン

## FastAPI設計原則（新アーキテクチャ対応）

### ルーター構造
```python
# new/api/ 配下のルーター定義標準形式
from fastapi import APIRouter, Depends, HTTPException
from new.auth import get_current_user
from new.schemas import SuccessResponse, ErrorResponse

router = APIRouter(prefix="/api/ingest", tags=["ingest"])

@router.post("/start", response_model=SuccessResponse)
async def start_processing(
    request_data: ProcessingRequest,
    current_user = Depends(get_current_user)
):
    """データ登録処理を開始"""
    try:
        # 処理ロジック
        result = await processing_service.start(request_data)
        return SuccessResponse(
            message="処理を開始しました",
            data=result
        )
    except Exception as e:
        raise HTTPException(500, f"処理開始エラー: {str(e)}")
```

### 新アーキテクチャでのAPI分離
- **UI Routes** (`new/routes/ui.py`): HTMLテンプレート返却
- **API Routes** (`new/api/*.py`): JSON API エンドポイント
- **認証統合**: 全APIで `Depends(get_current_user)` による統一認証

### エンドポイント命名規則
- **GET /resource**: 一覧・詳細取得
- **POST /resource**: 新規作成・処理実行
- **PUT /resource/{id}**: 全体更新
- **PATCH /resource/{id}**: 部分更新
- **DELETE /resource/{id}**: 削除

### レスポンス形式
```python
# 成功レスポンス
return JSONResponse({
    "status": "success",
    "data": result_data,
    "message": "処理が完了しました"
})

# エラーレスポンス
raise HTTPException(
    status_code=400,
    detail="ユーザー向けエラーメッセージ"
)
```

## SSE（Server-Sent Events）設計

### ストリーミング処理
```python
async def event_generator():
    # 全体開始イベント
    yield f"data: {json.dumps({'start': True, 'total_files': total_files})}\n\n"
    
    # 進捗イベント
    for event in process_events:
        yield f"data: {json.dumps(event)}\n\n"
    
    # 完了イベント
    yield "data: {\"done\": true}\n\n"

return StreamingResponse(event_generator(), media_type="text/event-stream")
```

### イベント形式標準化
```python
# 進捗イベント
{
    "file": "filename.pdf",
    "step": "ページ 1/10 処理中...",
    "page_id": "page_1_10",
    "is_progress_update": True
}

# 完了イベント
{
    "file": "filename.pdf",
    "step": "file_done",
    "elapsed": 45.2
}
```

## データベース設計（新3テーブル構成）

### テーブル設計原則
```sql
-- ファイルバイナリ格納テーブル（主テーブル）
CREATE TABLE files_blob (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    checksum VARCHAR(64) NOT NULL UNIQUE,
    blob_data BYTEA NOT NULL,
    stored_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ファイルメタ情報テーブル（1:1対応）
CREATE TABLE files_meta (
    blob_id UUID PRIMARY KEY REFERENCES files_blob(id) ON DELETE CASCADE,
    file_name VARCHAR(255) NOT NULL,
    mime_type VARCHAR(100) NOT NULL,
    size INTEGER NOT NULL,
    page_count INTEGER,
    status VARCHAR(50) DEFAULT 'uploaded',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ファイルテキスト格納テーブル（1:1対応）
CREATE TABLE files_text (
    blob_id UUID PRIMARY KEY REFERENCES files_blob(id) ON DELETE CASCADE,
    raw_text TEXT,
    refined_text TEXT,
    quality_score REAL,
    tags TEXT[],
    processing_log TEXT,
    ocr_engine VARCHAR(50),
    llm_model VARCHAR(100),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### インデックス戦略
```sql
-- 検索性能最適化
CREATE INDEX idx_files_status ON files(status);
CREATE INDEX idx_files_created_at ON files(created_at);
CREATE INDEX idx_file_texts_quality_score ON file_texts(quality_score);

-- pgvector用インデックス
CREATE INDEX ON embeddings USING ivfflat (embedding vector_cosine_ops);
```

### トランザクション管理
```python
# データベース操作の標準パターン
def update_file_with_transaction(file_id: int, **updates):
    """トランザクション内でファイル情報を更新"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # 複数テーブルの更新
                cur.execute("UPDATE files SET status = %s WHERE id = %s", 
                           (updates.get('status'), file_id))
                cur.execute("UPDATE file_texts SET refined_text = %s WHERE file_id = %s",
                           (updates.get('refined_text'), file_id))
                conn.commit()
    except Exception as exc:
        conn.rollback()
        raise DatabaseError(f"ファイル更新失敗: {exc}")
```

## 設定管理

### 環境変数活用
```python
# 設定値の標準的な取得方法
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1:8b")
LLM_TIMEOUT_SEC = int(os.getenv("LLM_TIMEOUT_SEC", "300"))
DEVELOPMENT_MODE = os.getenv("DEVELOPMENT_MODE", "false").lower() == "true"
```

### 設定ファイル管理
```python
# JSON設定ファイルの読み書き
class SettingsManager:
    def __init__(self, settings_path: str):
        self.settings_path = settings_path
        self.settings = self.load_settings()
    
    def load_settings(self) -> Dict:
        """設定ファイルを読み込み"""
        try:
            with open(self.settings_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
    
    def save_settings(self, settings: Dict):
        """設定ファイルに保存"""
        os.makedirs(os.path.dirname(self.settings_path), exist_ok=True)
        with open(self.settings_path, 'w', encoding='utf-8') as f:
            json.dump(settings, f, ensure_ascii=False, indent=2)
```

## エラーハンドリング・ログ

### 構造化ログ
```python
# ログ出力の標準形式
LOGGER = logging.getLogger("module_name")

def process_with_logging(file_path: str):
    """ログ付き処理実行"""
    LOGGER.info(f"処理開始: file={file_path}")
    try:
        result = do_processing(file_path)
        LOGGER.info(f"処理完了: file={file_path}, result={result}")
        return result
    except Exception as exc:
        LOGGER.exception(f"処理失敗: file={file_path}")
        raise ProcessingError(f"ファイル処理エラー: {exc}")
```

### 非同期処理でのエラー管理
```python
async def async_process_with_error_handling():
    """非同期処理のエラーハンドリング"""
    try:
        async with asyncio.timeout(300):  # 5分タイムアウト
            result = await long_running_task()
            return result
    except asyncio.TimeoutError:
        LOGGER.warning("処理タイムアウト")
        raise HTTPException(408, "処理がタイムアウトしました")
    except Exception as exc:
        LOGGER.exception("非同期処理エラー")
        raise HTTPException(500, f"内部エラー: {exc}")
```

## パフォーマンス最適化

### データベースクエリ最適化
- N+1問題の回避
- 適切なJOIN使用
- インデックス活用
- バッチ処理の活用

### メモリ管理
- 大容量ファイル処理時のストリーミング
- 適切なガベージコレクション
- メモリリーク防止

### 並行処理
```python
# 適切な並行処理設計
async def process_multiple_files(files: List[str]):
    """複数ファイルの並行処理"""
    semaphore = asyncio.Semaphore(3)  # 同時実行数制限
    
    async def process_single_file(file_path: str):
        async with semaphore:
            return await process_file(file_path)
    
    tasks = [process_single_file(f) for f in files]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return results
```