---
inclusion: always
---

# テスト・デプロイメントガイドライン（新アーキテクチャ対応）

## テスト戦略

### テスト分類
- **単体テスト**: 個別関数・クラスのテスト（new/services/配下）
- **統合テスト**: モジュール間連携のテスト（new/simple_integration_test.py）
- **システムテスト**: エンドツーエンドの動作確認（new/system_integration_test.py）
- **パフォーマンステスト**: 処理速度・メモリ使用量の検証

### pytest設定（新アーキテクチャ対応）
```python
# conftest.py - テスト共通設定
import pytest
import tempfile
import os
from unittest.mock import Mock, AsyncMock
from new.config import settings
from new.database.connection import get_db_connection

@pytest.fixture
def temp_pdf_file():
    """テスト用PDFファイルの作成"""
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
        # テスト用PDFデータを作成
        yield f.name
    os.unlink(f.name)

@pytest.fixture
def mock_file_processor():
    """FileProcessorのモック（新アーキテクチャ対応）"""
    mock = AsyncMock()
    mock.process_file.return_value = {
        "success": True,
        "file_id": "test-uuid",
        "status": "completed",
        "text_length": 1000,
        "processing_time": 2.5,
        "ocr_result": {"text": "テスト用OCRテキスト", "success": True},
        "llm_refined_text": "整形済みテキスト"
    }
    return mock

@pytest.fixture
def db_connection():
    """テスト用データベース接続"""
    with get_db_connection() as conn:
        yield conn
```

### OCR処理のテスト
```python
# test_ocr_processing.py
import pytest
from app.services.ingest.processor import IngestProcessor

class TestOCRProcessing:
    def test_pdf_extraction_success(self, temp_pdf_file, mock_ocr_factory):
        """PDF抽出の正常系テスト"""
        processor = IngestProcessor()
        processor.ocr_factory = mock_ocr_factory
        
        result = list(processor._extract_text_with_ocr_generator(
            temp_pdf_file, "test.pdf", "tesseract", {}
        ))
        
        # 最後の要素が結果リスト
        text_list = result[-1]
        assert isinstance(text_list, list)
        assert len(text_list) > 0
        assert "テスト用OCRテキスト" in text_list[0]

    def test_ocr_error_handling(self, temp_pdf_file):
        """OCRエラー時の処理テスト"""
        processor = IngestProcessor()
        mock_factory = Mock()
        mock_factory.process_with_settings.return_value = {
            "success": False,
            "error": "OCR処理エラー"
        }
        processor.ocr_factory = mock_factory
        
        result = list(processor._extract_text_with_ocr_generator(
            temp_pdf_file, "test.pdf", "tesseract", {}
        ))
        
        text_list = result[-1]
        assert "OCRエラー: OCR処理エラー" in text_list[0]
```

### API エンドポイントのテスト
```python
# test_api_endpoints.py
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

class TestIngestAPI:
    def test_ingest_page_loads(self):
        """Ingestページの表示テスト"""
        response = client.get("/ingest")
        assert response.status_code == 200
        assert "データ整形/登録" in response.text

    def test_ocr_engines_endpoint(self):
        """OCRエンジン一覧APIのテスト"""
        response = client.get("/ingest/ocr/engines")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)

    def test_invalid_file_upload(self):
        """不正ファイルアップロードのテスト"""
        files = {"input_files": ("test.xyz", b"invalid content", "application/octet-stream")}
        response = client.post("/ingest", files=files, data={
            "input_mode": "files",
            "refine_prompt_key": "japanese",
            "embed_models": ["sentence-transformers"]
        })
        assert response.status_code == 400
```

## Docker環境

### 開発環境設定
```dockerfile
# .devcontainer/Dockerfile
FROM python:3.11-slim

# 日本語環境設定
ENV LANG=ja_JP.UTF-8
ENV LANGUAGE=ja_JP:ja
ENV LC_ALL=ja_JP.UTF-8

# システムパッケージ
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-jpn \
    libreoffice \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Python依存関係
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

WORKDIR /workspace
```

### 本番環境設定
```yaml
# docker-compose.yml
version: '3.8'
services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - OLLAMA_MODEL=llama3.1:8b
      - DATABASE_URL=postgresql://user:pass@db:5432/ragdb
      - DEVELOPMENT_MODE=false
    volumes:
      - ./logs:/workspace/logs
      - ./data:/workspace/data
    depends_on:
      - db
      - ollama

  db:
    image: pgvector/pgvector:pg16
    environment:
      - POSTGRES_DB=ragdb
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./db/init_schema.sql:/docker-entrypoint-initdb.d/init.sql

  ollama:
    image: ollama/ollama:latest
    volumes:
      - ollama_data:/root/.ollama
    ports:
      - "11434:11434"

volumes:
  postgres_data:
  ollama_data:
```

## CI/CD パイプライン

### GitHub Actions設定
```yaml
# .github/workflows/test.yml
name: Test and Deploy

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: pgvector/pgvector:pg16
        env:
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: test_db
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install system dependencies
      run: |
        sudo apt-get update
        sudo apt-get install -y tesseract-ocr tesseract-ocr-jpn
    
    - name: Install Python dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest pytest-cov
    
    - name: Run tests
      run: |
        pytest --cov=app --cov-report=xml
      env:
        DATABASE_URL: postgresql://postgres:postgres@localhost:5432/test_db
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
```

## 監視・ログ

### アプリケーション監視
```python
# app/middleware/monitoring.py
import time
import logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

class MonitoringMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        response = await call_next(request)
        
        process_time = time.time() - start_time
        
        # パフォーマンスログ
        if process_time > 5.0:  # 5秒以上の処理
            logging.warning(f"Slow request: {request.url.path} took {process_time:.2f}s")
        
        response.headers["X-Process-Time"] = str(process_time)
        return response
```

### ヘルスチェックエンドポイント
```python
# app/routes/health.py
from fastapi import APIRouter
from app.services.ocr import OCREngineFactory

router = APIRouter()

@router.get("/health")
async def health_check():
    """システムヘルスチェック"""
    checks = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {}
    }
    
    # データベース接続確認
    try:
        with get_db_connection() as conn:
            conn.execute("SELECT 1")
        checks["services"]["database"] = "healthy"
    except Exception as e:
        checks["services"]["database"] = f"unhealthy: {e}"
        checks["status"] = "degraded"
    
    # OCRエンジン確認
    try:
        ocr_factory = OCREngineFactory()
        engines = ocr_factory.get_available_engines()
        available_count = sum(1 for e in engines.values() if e.get("available"))
        checks["services"]["ocr"] = f"healthy ({available_count} engines available)"
    except Exception as e:
        checks["services"]["ocr"] = f"unhealthy: {e}"
        checks["status"] = "degraded"
    
    return checks
```

## セキュリティ

### 入力検証
```python
# セキュリティ関連の検証
def validate_file_upload(file: UploadFile):
    """アップロードファイルの安全性検証"""
    # ファイルサイズ制限
    if file.size > 100 * 1024 * 1024:  # 100MB
        raise HTTPException(400, "ファイルサイズが大きすぎます")
    
    # 拡張子チェック
    allowed_extensions = {'.pdf', '.docx', '.txt', '.csv', '.json', '.eml'}
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in allowed_extensions:
        raise HTTPException(400, f"未対応のファイル形式: {ext}")
    
    # MIMEタイプ検証
    import magic
    file_type = magic.from_buffer(file.file.read(1024), mime=True)
    file.file.seek(0)  # ファイルポインタをリセット
    
    if not is_safe_mime_type(file_type):
        raise HTTPException(400, "安全でないファイル形式です")
```

### 環境変数管理
```python
# セキュアな設定管理
import os
from typing import Optional

class SecureConfig:
    def __init__(self):
        self.database_url = self._get_required_env("DATABASE_URL")
        self.secret_key = self._get_required_env("SECRET_KEY")
        self.ollama_endpoint = os.getenv("OLLAMA_ENDPOINT", "http://localhost:11434")
    
    def _get_required_env(self, key: str) -> str:
        value = os.getenv(key)
        if not value:
            raise ValueError(f"Required environment variable {key} is not set")
        return value
```