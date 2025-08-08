# 開発ガイド

## 🛠️ 開発環境のセットアップ

### 前提条件
- Python 3.10以上
- Git
- Docker（オプション、推奨）
- VSCode または Cursor（推奨エディタ）

### 初期セットアップ

1. **リポジトリのクローン**
   ```bash
   git clone https://github.com/your-org/rag-system.git
   cd rag-system
   ```

2. **仮想環境の作成**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Linux/Mac
   # または
   .venv\Scripts\activate  # Windows
   ```

3. **依存関係のインストール**
   ```bash
   pip install -r requirements.txt
   ```

4. **環境変数の設定**
   ```bash
   cp .env.example .env
   # .envファイルを編集して必要な値を設定
   ```

5. **データベースの初期化**
   ```bash
   cd app
   python -c "from core.database import init_database; import asyncio; asyncio.run(init_database())"
   ```

## 📁 プロジェクト構造

```
rag-system/
├── app/                    # メインアプリケーション
│   ├── __init__.py
│   ├── main.py            # エントリーポイント
│   ├── config/            # 設定管理
│   │   ├── __init__.py
│   │   └── settings.py    # Pydantic設定
│   ├── core/              # コア機能
│   │   ├── __init__.py
│   │   ├── database.py    # DB接続
│   │   └── models.py      # SQLAlchemyモデル
│   ├── auth/              # 認証
│   │   ├── __init__.py
│   │   ├── dependencies.py
│   │   └── session.py
│   ├── services/          # ビジネスロジック
│   │   ├── __init__.py
│   │   ├── file_service.py
│   │   ├── chat_service.py
│   │   ├── processing_service.py
│   │   ├── ocr/           # OCR処理
│   │   ├── llm/           # LLM処理
│   │   └── embedding/     # ベクトル処理
│   ├── ui/                # UI層
│   │   ├── components/    # UIコンポーネント
│   │   └── pages/         # ページ定義
│   ├── utils/             # ユーティリティ
│   └── prompts/           # プロンプト
├── docs/                  # ドキュメント
├── tests/                 # テスト
├── docker/                # Docker設定
└── .cursor/rules/         # 開発ルール
```

## 🔧 開発ルール

### コーディング規約

1. **Python Style Guide**
   - PEP 8に準拠
   - 型ヒントを必須とする
   - docstringは必須（Google Style）

2. **インポート順序**
   ```python
   # 1. 標準ライブラリ
   import os
   import sys
   
   # 2. サードパーティ
   from fastapi import FastAPI
   from nicegui import ui
   
   # 3. ローカルモジュール
   from app.config import config
   from app.services import FileService
   ```

3. **命名規則**
   - クラス名: PascalCase
   - 関数・変数: snake_case
   - 定数: UPPER_SNAKE_CASE

### UI開発ガイドライン

詳細は[.cursor/rules/](../../.cursor/rules/)を参照：

1. **UI設計ポリシー**
   - 情報密度最大化
   - 階層的CSS設計
   - 場当たり設計の排除

2. **NiceGUI ベストプラクティス**
   - 公式コンポーネント優先
   - context managerパターン
   - カスタムCSS最小化

3. **コンポーネントアーキテクチャ**
   - arrangement_test.pyでの実験駆動開発
   - 共通コンポーネント化
   - 継承ベース設計

## 🧪 テスト

### テストの実行

```bash
# 全テスト実行
pytest

# カバレッジ付き
pytest --cov=app

# 特定のテスト
pytest tests/test_file_service.py
```

### テストの書き方

```python
import pytest
from app.services import FileService

@pytest.mark.asyncio
async def test_file_upload():
    """ファイルアップロードのテスト"""
    service = FileService()
    
    # テストファイルの準備
    test_file = create_test_file()
    
    # アップロード実行
    result = await service.upload_file(test_file)
    
    # アサーション
    assert result["status"] == "success"
    assert result["file_id"] is not None
```

## 🚀 デプロイ

### 開発環境

```bash
cd app
python main.py
```

### Docker環境

```bash
docker-compose up -d
```

### 本番環境

1. 環境変数の設定
2. データベースマイグレーション
3. 静的ファイルの配置
4. リバースプロキシの設定

## 🐛 デバッグ

### ログの確認

```python
from app.config import logger

logger.debug("デバッグ情報")
logger.info("通常情報")
logger.warning("警告")
logger.error("エラー")
```

### ブラウザ開発者ツール
- F12でコンソールを開く
- Networkタブで通信を確認
- Elementsタブで DOM構造を確認

### Python デバッグ

```python
import pdb
pdb.set_trace()  # ブレークポイント

# または
breakpoint()  # Python 3.7+
```

## 📝 コミットメッセージ

### フォーマット

```
<type>(<scope>): <subject>

<body>

<footer>
```

### タイプ
- `feat`: 新機能
- `fix`: バグ修正
- `docs`: ドキュメント
- `style`: フォーマット
- `refactor`: リファクタリング
- `test`: テスト
- `chore`: その他

### 例

```
feat(auth): セッション管理機能を追加

- FastAPIセッション管理実装
- セキュアクッキー対応
- タイムアウト設定追加

Closes #123
```

## 🤝 プルリクエスト

### チェックリスト
- [ ] コードがスタイルガイドに準拠
- [ ] テストが追加/更新されている
- [ ] ドキュメントが更新されている
- [ ] 型ヒントが追加されている
- [ ] リンターが通っている

### レビューポイント
1. 機能要件を満たしているか
2. パフォーマンスへの影響
3. セキュリティの考慮
4. エラーハンドリング
5. テストカバレッジ

## 📚 参考資料

### 内部ドキュメント
- [プロジェクト概要](../PROJECT_OVERVIEW.md)
- [アーキテクチャ設計](../architecture/ARCHITECTURE.md)
- [API リファレンス](../api/API_REFERENCE.md)
- [UI開発ルール](../../.cursor/rules/)

### 外部リソース
- [FastAPI公式ドキュメント](https://fastapi.tiangolo.com/)
- [NiceGUI公式ドキュメント](https://nicegui.io/)
- [SQLAlchemy公式ドキュメント](https://www.sqlalchemy.org/)
- [Pydantic公式ドキュメント](https://docs.pydantic.dev/)

---
*最終更新: 2025年1月*