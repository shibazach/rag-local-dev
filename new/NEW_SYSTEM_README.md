# R&D RAGシステム

セキュリティ設計に基づく日本語文書処理RAGシステムの新しいアーキテクチャです。

## 🚀 特徴

### セキュリティ設計
- **HTTPS対応**: セキュアな通信を前提とした設計
- **認証システム**: セッション管理とJWTトークン対応
- **API分離**: `/api/**` エンドポイントによる明確な分離
- **セキュリティヘッダー**: CSP、XSS保護、CSRF対策
- **CORS制御**: 適切なオリジン制御

### アーキテクチャ
- **FastAPI**: 高速なPython Webフレームワーク
- **SQLAlchemy**: ORMによるデータベース操作
- **PostgreSQL**: リレーショナルデータベース
- **pgvector**: ベクトル検索対応
- **Jinja2**: テンプレートエンジン

### 機能
- **多形式文書対応**: PDF、Word、テキスト、CSV、JSON、EML
- **高精度OCR**: 複数エンジン対応
- **LLM整形**: Ollamaによるテキスト品質向上
- **ベクトル検索**: 複数埋め込みモデル対応
- **リアルタイム処理**: SSEによる進捗表示

## 📁 ディレクトリ構造

```
new/
├── __init__.py
├── main.py              # FastAPIアプリケーション
├── config.py            # 設定管理
├── auth.py              # 認証システム
├── database.py          # データベース接続
├── models.py            # データベースモデル
├── routes/              # ルーター
│   ├── __init__.py
│   ├── api.py           # APIルーター（認証付き）
│   └── ui.py            # UIルーター（認証不要）
├── services/            # ビジネスロジック
│   ├── __init__.py
│   ├── file_service.py  # ファイル処理
│   └── chat_service.py  # チャット処理
├── templates/           # HTMLテンプレート
│   ├── base.html
│   ├── index.html
│   ├── login.html
│   ├── 404.html
│   └── 500.html
└── static/              # 静的ファイル
    ├── css/
    │   └── main.css
    └── js/
        └── main.js
```

## 🛠️ セットアップ

### 1. 依存関係のインストール
```bash
pip install fastapi uvicorn sqlalchemy psycopg2-binary jinja2 python-multipart
```

### 2. 環境変数の設定
```bash
export DATABASE_URL="postgresql://raguser:ragpass@ragdb:5432/rag"
export SECRET_KEY="your-secret-key-change-in-production"
export DEBUG_MODE="true"
export DEVELOPMENT_MODE="true"
```

### 3. データベースの初期化
```bash
python -c "from new.database import init_db; init_db()"
```

### 4. アプリケーションの起動
```bash
# 新しいシステムを起動
python new/run_app.py --app new

# 既存システムを起動
python new/run_app.py --app main
```

## 🔐 認証

### 開発用アカウント
- **管理者**: admin / password
- **一般ユーザー**: user / password

### 認証フロー
1. ユーザーがログインページにアクセス
2. 認証情報を送信
3. セッションにユーザー情報を保存
4. APIエンドポイントで認証確認

## 📡 API エンドポイント

### 認証不要
- `GET /` - メインページ
- `GET /login` - ログインページ
- `GET /health` - ヘルスチェック

### 認証必要
- `GET /api/files` - ファイル一覧
- `POST /api/files/upload` - ファイルアップロード
- `DELETE /api/files/{id}` - ファイル削除
- `GET /api/chat/sessions` - チャットセッション一覧
- `POST /api/chat/sessions` - セッション作成
- `GET /api/user/profile` - ユーザープロフィール

## 🔧 開発

### 開発モード
```bash
export DEBUG_MODE="true"
export DEVELOPMENT_MODE="true"
```

### ログ
- ログレベル: DEBUG/INFO/WARNING/ERROR
- フォーマット: 構造化ログ
- 出力先: コンソール + ファイル

### テスト
```bash
# ユニットテスト
python -m pytest tests/

# 統合テスト
python -m pytest tests/integration/
```

## 🚀 デプロイ

### 本番環境設定
```bash
export DEBUG_MODE="false"
export SECURE_COOKIES="true"
export SECRET_KEY="production-secret-key"
```

### Docker
```bash
docker build -t new-rag-system .
docker run -p 8000:8000 new-rag-system
```

### HTTPS設定
```bash
uvicorn new.main:app --ssl-certfile cert.pem --ssl-keyfile key.pem
```

## 📊 監視

### メトリクス
- ファイル処理数
- チャットセッション数
- API応答時間
- エラー率

### ログ分析
- アクセスログ
- エラーログ
- パフォーマンスログ

## 🔒 セキュリティ

### 実装済み
- HTTPS対応
- セッション管理
- CSRF保護
- XSS保護
- SQLインジェクション対策

### 今後の予定
- SAML/OIDC認証
- JWTトークン
- レート制限
- 監査ログ

## 📝 ライセンス

MIT License

## 🤝 コントリビューション

1. フォークを作成
2. フィーチャーブランチを作成
3. 変更をコミット
4. プルリクエストを作成

## 📞 サポート

問題や質問がある場合は、GitHubのIssuesを作成してください。 