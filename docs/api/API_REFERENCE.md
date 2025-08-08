# R&D RAGシステム API リファレンス

## 概要

R&D RAGシステムは、RESTful APIとWebSocket APIを提供します。全てのAPIエンドポイントは`/api/v1`プレフィックスを持ちます。

## 認証

### セッション認証
```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "username": "user@example.com",
  "password": "password123"
}
```

レスポンス:
```json
{
  "status": "success",
  "user": {
    "id": "uuid",
    "username": "user@example.com",
    "role": "user"
  }
}
```

## ファイル管理API

### ファイルアップロード

#### 単一ファイルアップロード
```http
POST /api/v1/upload/single
Content-Type: multipart/form-data
Authorization: Session

file: (binary)
```

レスポンス:
```json
{
  "status": "success",
  "file_id": "uuid",
  "filename": "document.pdf",
  "size": 1024000,
  "checksum": "sha256hash"
}
```

#### バッチアップロード
```http
POST /api/v1/upload/batch
Content-Type: multipart/form-data
Authorization: Session

files: (multiple binaries)
```

### ファイル一覧取得
```http
GET /api/v1/files?limit=10&offset=0&status=processed
Authorization: Session
```

レスポンス:
```json
{
  "files": [
    {
      "file_id": "uuid",
      "filename": "document.pdf",
      "size": 1024000,
      "status": "processed",
      "created_at": "2025-01-01T00:00:00Z",
      "has_text": true,
      "text_length": 5000
    }
  ],
  "total": 100,
  "limit": 10,
  "offset": 0
}
```

### ファイル詳細取得
```http
GET /api/v1/files/{file_id}
Authorization: Session
```

### ファイル削除
```http
DELETE /api/v1/files/{file_id}
Authorization: Session
```

## 処理API

### 処理ジョブ開始
```http
POST /api/v1/processing/start
Content-Type: application/json
Authorization: Session

{
  "file_ids": ["uuid1", "uuid2"],
  "config": {
    "enable_ocr": true,
    "enable_llm_refine": true,
    "enable_embedding": true,
    "ocr_engine": "ocrmypdf",
    "llm_model": "phi4-mini",
    "embedding_option": "1"
  }
}
```

レスポンス:
```json
{
  "job_id": "job-uuid",
  "status": "started",
  "total_files": 2
}
```

### 処理状況取得
```http
GET /api/v1/processing/status/{job_id}
Authorization: Session
```

### 処理キャンセル
```http
POST /api/v1/processing/cancel/{job_id}
Authorization: Session
```

## 検索・チャットAPI

### 文書検索
```http
POST /api/v1/search
Content-Type: application/json
Authorization: Session

{
  "query": "検索キーワード",
  "mode": "file_separate",
  "embedding_option": "1",
  "limit": 10,
  "min_score": 0.7
}
```

レスポンス:
```json
{
  "results": [
    {
      "file_id": "uuid",
      "filename": "document.pdf",
      "content": "関連するテキスト内容...",
      "score": 0.95,
      "page": 5,
      "chunk_id": "chunk-uuid"
    }
  ],
  "total": 25,
  "query_time": 0.123
}
```

### チャット送信
```http
POST /api/v1/chat
Content-Type: application/json
Authorization: Session

{
  "message": "質問内容",
  "use_rag": true,
  "temperature": 0.7,
  "max_tokens": 2000
}
```

### チャット履歴取得
```http
GET /api/v1/chat/history?limit=50
Authorization: Session
```

## WebSocket API

### リアルタイム処理進捗

接続:
```javascript
ws://localhost:8000/ws/processing/{job_id}
```

メッセージフォーマット:
```json
{
  "type": "progress",
  "job_id": "job-uuid",
  "message": "処理中: file1.pdf",
  "progress": 0.5,
  "completed_files": 1,
  "total_files": 2
}
```

### チャットストリーミング

接続:
```javascript
ws://localhost:8000/ws/chat
```

送信:
```json
{
  "type": "message",
  "content": "質問内容",
  "use_rag": true
}
```

受信:
```json
{
  "type": "chunk",
  "content": "応答テキストの一部"
}
```

## エラーレスポンス

### エラーフォーマット
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "入力データが無効です",
    "details": {
      "field": "email",
      "reason": "有効なメールアドレスではありません"
    }
  }
}
```

### HTTPステータスコード
- `200 OK`: 成功
- `201 Created`: リソース作成成功
- `400 Bad Request`: 不正なリクエスト
- `401 Unauthorized`: 認証エラー
- `403 Forbidden`: 権限エラー
- `404 Not Found`: リソースが見つからない
- `422 Unprocessable Entity`: バリデーションエラー
- `500 Internal Server Error`: サーバーエラー

## レート制限

- 認証済みユーザー: 1000リクエスト/時間
- 非認証ユーザー: 100リクエスト/時間

レート制限情報はレスポンスヘッダーに含まれます:
```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 950
X-RateLimit-Reset: 1640995200
```

## バージョニング

APIバージョンはURLパスに含まれます:
- 現在のバージョン: `/api/v1`
- 将来のバージョン: `/api/v2`

古いバージョンは最低6ヶ月間サポートされます。

## SDKとツール

### Python SDK
```python
from rag_client import RAGClient

client = RAGClient(
    base_url="http://localhost:8000",
    api_key="your-api-key"
)

# ファイルアップロード
response = client.upload_file("document.pdf")

# 検索実行
results = client.search("検索キーワード")
```

### cURL例
```bash
# ログイン
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"user@example.com","password":"password123"}'

# ファイル一覧取得
curl -X GET http://localhost:8000/api/v1/files \
  -H "Cookie: session=..."
```

### Postmanコレクション
[RAG_API.postman_collection.json](./postman/RAG_API.postman_collection.json)をインポートしてください。

---
*最終更新: 2025年1月*