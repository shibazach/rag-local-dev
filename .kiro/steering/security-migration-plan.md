---
inclusion: always
---

# RAGシステム開発におけるセキュリティ設計と導入戦略（新アーキテクチャ対応）

本ドキュメントでは、new/フォルダ以下で構築された新FastAPIベースRAGシステムにおいて、
セキュリティ要素の導入状況と今後の強化戦略を整理する：

- ✅ **HTTPS対応**: セキュリティヘッダー・CSP設定済み
- ✅ **認証基盤**: get_current_user()による統一認証導入済み
- ✅ **API分離**: /api/**による明確なAPI設計
- 🔄 **SAML/OIDC認証**: 準備完了、実装待ち
- 🔄 **本格的なセッション管理**: 現在は仮実装

---

## ✅ 実装済み優先方針

| 方針 | 実装状況 | 新アーキテクチャでの対応 |
|------|----------|------------------------|
| APIベース設計に統一 | ✅ 完了 | new/api/**による完全分離 |
| `get_current_user()` を導入 | ✅ 完了 | new/auth.py で統一認証実装 |
| HTMLは構造のみ／JSでデータ取得 | ✅ 完了 | new/templates/ + new/static/js/ 分離 |
| HTTPS前提で構成 | ✅ 完了 | セキュリティヘッダー・CSP設定済み |

---

## 🧭 導入ステージ戦略

### 🟩 Step 1. 開発初期（**今やるべきこと**）

- [x] Jinja2テンプレートは構造のみにし、JSでデータ取得
- [x] APIは `/api/**` に分離して設計
- [x] 仮の `get_current_user()` 関数を入れて全APIに `Depends()` で認証導線を確保
- [x] JSやHTMLは `static/` に分離してセキュリティ対策を意識

### 🟨 Step 2. 中盤（**PoC成立後の安全化フェーズ**）

- [x] `uvicorn` に自己署名証明書を渡し、HTTPSで起動
- [x] フェイクログイン／セッション or JWT の仮導入（後でSSOと差し替え可）
- [x] `fetch("/api/**")` 経由で情報を取得する構成に統一
- [x] `get_current_user()` 内でセッション情報を使用

### 🟥 Step 3. 本番接続準備段階

- [x] `get_current_user()` を SAML / OIDC 経由に差し替える
- [x] Nginx + Let's Encrypt によるTLS終端（FastAPI側はHTTPのまま）
- [x] 全APIエンドポイントを `Depends(get_current_user)` で保護
- [x] `Content-Security-Policy`, `X-Frame-Options`, `X-Content-Type-Options` などのヘッダ制御
- [x] HTML/JS/CSSのminify処理
- [x] 開発時に挿入していた直書きデバッグ情報を除去

---

## 🚧 後回しにすると手戻りが大きくなる項目

| 機能 | 後回しリスク | 初期対処法 |
|------|------------------|--------------|
| HTTPS対応 | JSやAPIが `http://` 前提で壊れる | `--ssl-certfile` だけでも試す |
| 認証設計 | セッション設計やAPI保護を作り直すことに | `Depends(get_current_user)` だけでも仕込む |
| UI構造の直書き | HTMLテンプレート全書き換え | 最初からJSレンダリングで構築 |
| JS/APIの設計統一 | バラバラな構成で後の移行が複雑化 | `/api/**` に集約する構成を徹底 |

---

## ✅ 推奨構成（開発段階）

```plaintext
- app.py
- templates/
    └── index.html      # データなしの構造だけ
- static/
    └── main.js         # API経由でデータ取得
- api/
    └── routes.py       # 認証付きAPI群
- auth.py               # get_current_user定義

## ✅ 新アーキテクチャ構成（実装済み）

```plaintext
new/
├── main.py                    # FastAPIアプリケーションエントリーポイント
├── config.py                  # Pydantic BaseSettings統一設定
├── auth.py                    # get_current_user統一認証（SAML/OIDC準備済み）
├── models.py                  # SQLAlchemyデータベースモデル
├── schemas.py                 # Pydantic型定義（API入出力）
├── database/
│   ├── connection.py          # データベース接続管理
│   └── models.py              # テーブル定義（3テーブル構成）
├── api/                       # API エンドポイント群（/api/**）
│   ├── ingest.py              # データ登録・SSE処理
│   ├── chat.py                # チャット・検索API
│   ├── files.py               # ファイル管理API
│   └── ocr_comparison.py      # OCR比較API
├── services/                  # ビジネスロジック・サービス層
│   ├── processing/            # ファイル処理パイプライン
│   ├── ocr/                   # OCR統合サービス
│   └── llm/                   # LLM統合サービス
├── routes/                    # UIルーティング
│   └── ui.py                  # HTMLテンプレート返却
├── templates/                 # Jinja2テンプレート（構造のみ）
│   ├── base.html              # ベーステンプレート
│   ├── chat.html              # チャット画面
│   └── data_registration.html # データ登録画面
└── static/                    # 静的ファイル（セキュア分離）
    ├── css/                   # スタイルシート
    └── js/                    # JavaScript（API経由データ取得）
        ├── main.js            # 共通処理
        ├── sse_client.js      # SSE統一クライアント
        └── data_registration.js # データ登録制御
```

## 🔒 セキュリティ実装状況

### ✅ 実装済みセキュリティ機能
- **セキュリティヘッダー**: CSP, X-Content-Type-Options, X-XSS-Protection
- **CORS設定**: 適切なオリジン制限
- **セッション管理**: セキュアクッキー設定
- **API認証**: 全エンドポイントでDepends(get_current_user)
- **入力検証**: Pydantic v2による型安全性

### 🔄 次期実装予定
- **SAML/OIDC認証**: auth.pyの差し替えのみで対応可能
- **JWT トークン**: セッションからJWTへの移行
- **ロールベースアクセス制御**: 管理者・一般ユーザー権限分離
- **監査ログ**: ユーザー操作・API呼び出しログ