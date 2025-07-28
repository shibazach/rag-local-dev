---
inclusion: always
---

# RAGシステム開発におけるセキュリティ設計と導入戦略

本ドキュメントでは、開発中のFastAPIベースRAGシステムにおいて、
後々導入すべき以下の要素をどのタイミングで組み込むべきかを整理する：

- HTTPS対応
- SAML認証（またはOIDC連携）
- API経由のフロントエンドデータ取得

---

## ✅ 優先方針（先にやるべきこと）

| 方針 | 理由 | 影響 |
|------|------|------|
| APIベース設計に統一 | HTML埋め込みデータを排除 | UIとロジックの分離が明確化 |
| `get_current_user()` を導入 | 認証を後で差し替えしやすくする | 認証導入が1関数で済む |
| HTMLは構造のみ／JSでデータ取得 | 「ソースの可視化」を防ぐ | 後でSSO認証やセキュアAPIへ移行しやすい |
| HTTPS前提で構成 | Cookie/SameSite/CORS制御に影響 | 後からHTTPS化するのは面倒 |

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
