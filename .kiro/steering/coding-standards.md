---
inclusion: always
---

# コーディング規約・開発標準（新アーキテクチャ対応）

## Python コーディング規約

### 基本方針
- PEP 8に準拠した可読性重視のコード
- 日本語コメントを積極的に活用
- 型ヒントの必須使用（Pydantic v2対応）
- docstringによる関数・クラス説明
- 非同期処理（async/await）の積極活用

### ファイル構造（new/配下標準）
```python
# new/services/example_service.py
# サービス層の標準的な構造

# ── 標準ライブラリ ──
import asyncio
import logging
from typing import Dict, List, Optional, AsyncGenerator
from pathlib import Path

# ── サードパーティ ──
from fastapi import HTTPException
from pydantic import BaseModel, Field

# ── プロジェクト内 ──
from new.config import LOGGER, settings
from new.database.connection import get_db_connection
from new.schemas import SuccessResponse, ErrorResponse
```

### 命名規則
- **変数・関数**: snake_case
- **クラス**: PascalCase
- **定数**: UPPER_SNAKE_CASE
- **プライベート**: _leading_underscore

### エラーハンドリング
```python
try:
    result = risky_operation()
except SpecificException as exc:
    LOGGER.exception("具体的なエラー説明")
    raise HTTPException(400, f"ユーザー向けメッセージ: {str(exc)}")
```

## JavaScript 規約

### 基本方針
- ES6+の機能を積極活用
- バニラJSでの実装（フレームワーク不使用）
- 日本語コメントによる説明
- 関数型プログラミングの考え方を取り入れ

### 命名規則
- **変数・関数**: camelCase
- **定数**: UPPER_SNAKE_CASE
- **DOM要素**: kebab-case (HTML) → camelCase (JS)

### 非同期処理
```javascript
// async/awaitを優先使用
async function processData() {
  try {
    const result = await fetchData();
    return result;
  } catch (error) {
    console.error('データ処理エラー:', error);
    throw error;
  }
}
```

## データベース設計

### テーブル命名
- 複数形を使用（files, embeddings）
- snake_case
- 日本語カラムには適切な英語名を付与

### インデックス戦略
- 検索頻度の高いカラムには必ずインデックス
- 複合インデックスの適切な順序設定
- pgvectorの性能を考慮したベクトル検索最適化

## ログ出力規約

### ログレベル
- **DEBUG**: 開発時のデバッグ情報
- **INFO**: 正常な処理フロー
- **WARNING**: 注意が必要だが処理継続可能
- **ERROR**: エラーだが復旧可能
- **CRITICAL**: システム停止レベルのエラー

### ログフォーマット
```python
LOGGER = logging.getLogger("module_name")
LOGGER.info(f"処理開始: ファイル={file_name}, 件数={count}")
```