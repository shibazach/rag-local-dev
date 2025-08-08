# Prototypes/系 アーキテクチャ設計書

## 📋 全体方針

### 設計思想
- **FastAPI+NiceGUI完全統合** - ミドルウェア含む本格統合
- **app/系準拠の構造** - 実績ある設計パターンを継承
- **段階的発展** - 最小動作版→機能拡張→本格運用の3段階
- **モジュラー設計** - 各機能の独立性と再利用性

### 時系列ポジション
```
OLD/系 → new/系 → app/系 → prototypes/系（最新）
未完成   未完成   未完成   完全統合目標
```

## 🏗️ ディレクトリ構造

```
prototypes/
├── main.py                     # エントリーポイント（NiceGUI統合）
├── __init__.py                 # パッケージ初期化
├── ARCHITECTURE.md             # 本文書
├── core/                       # コア機能層
│   ├── __init__.py
│   ├── database.py            # DB接続・セッション管理
│   ├── models.py              # SQLAlchemy ORMモデル
│   ├── schemas.py             # Pydantic データ検証
│   └── exceptions.py          # カスタム例外定義
├── auth/                       # 認証・認可層
│   ├── __init__.py
│   ├── dependencies.py        # FastAPI依存関係
│   ├── middleware.py          # セッション・認証ミドルウェア
│   ├── models.py              # 認証関連モデル
│   └── utils.py               # 認証ユーティリティ
├── ui/                         # NiceGUI UI層
│   ├── __init__.py
│   ├── app.py                 # UIアプリケーション統合
│   ├── components/            # 再利用可能UIコンポーネント
│   │   ├── __init__.py
│   │   ├── layout.py          # レイアウトコンポーネント
│   │   ├── forms.py           # フォームコンポーネント
│   │   ├── tables.py          # テーブルコンポーネント
│   │   └── auth.py            # 認証関連UI
│   ├── pages/                 # ページ定義
│   │   ├── __init__.py
│   │   ├── index.py           # メインページ
│   │   ├── login.py           # ログインページ
│   │   ├── dashboard.py       # ダッシュボード
│   │   ├── data_registration.py
│   │   ├── chat.py
│   │   ├── files.py
│   │   └── admin.py
│   └── themes/                # テーマ・スタイル管理
│       ├── __init__.py
│       ├── base.py            # 基本テーマ
│       └── rag.py             # RAG専用テーマ
├── services/                   # ビジネスロジック層
│   ├── __init__.py
│   ├── file_service.py        # ファイル処理サービス
│   ├── chat_service.py        # チャットサービス
│   ├── processing_service.py  # データ処理サービス
│   ├── stats_service.py       # 統計情報サービス
│   └── admin_service.py       # 管理機能サービス
├── utils/                      # ユーティリティ層
│   ├── __init__.py
│   ├── logging.py             # ログ設定
│   ├── security.py            # セキュリティ関数
│   ├── validators.py          # バリデーション
│   └── helpers.py             # 汎用ヘルパー
├── config/                     # 設定管理層
│   ├── __init__.py
│   ├── settings.py            # 設定クラス
│   ├── database.py            # DB設定
│   └── environments/          # 環境別設定
└── tests/                      # テスト層
    ├── __init__.py
    ├── test_nicegui.py        # NiceGUI統合テスト
    ├── test_auth.py           # 認証テスト
    ├── test_ui/               # UIテスト
    ├── test_services/         # サービステスト
    └── test_core/             # コアテスト
```

## 🎯 開発段階

### Phase 1: 基盤構築（現在）
- [x] ディレクトリ構造作成
- [x] 最小動作版完成（main.py）
- [ ] コア機能分離・モジュール化
- [ ] 認証システム統合

### Phase 2: 機能拡張
- [ ] データベース連携
- [ ] ファイル処理機能
- [ ] チャット機能
- [ ] 管理機能

### Phase 3: 本格運用
- [ ] セキュリティ強化
- [ ] パフォーマンス最適化
- [ ] テスト完備
- [ ] ドキュメント整備

## 🔧 技術スタック

### 統合フレームワーク
- **FastAPI** - API・バックエンド
- **NiceGUI** - フロントエンド・UI
- **SQLAlchemy** - ORM・データベース
- **Pydantic** - データ検証・設定

### 認証・セキュリティ
- **Starlette SessionMiddleware** - セッション管理
- **NiceGUI storage** - ユーザーストレージ
- **JWT** - トークン認証（オプション）

### データベース
- **SQLite** - 開発・テスト用
- **PostgreSQL** - 本番用（対応予定）

## 📊 設計原則

### 1. 関心の分離
- UI層、ビジネスロジック層、データ層の明確な分離
- 各層間の依存関係を最小化

### 2. 再利用性
- UIコンポーネントの共通化
- サービス層の独立性確保

### 3. 拡張性
- 新機能追加時のコード変更を最小化
- 設定による動作変更

### 4. 保守性
- 明確な命名規則
- 適切なコメント・ドキュメント
- テストコード充実

## 🚀 起動方法

```bash
# prototypes/システム起動
cd prototypes
python main.py

# または
python -m prototypes.main
```

## 📝 移行計画

### app/系からの移行
1. **コア機能**: `app/core/*` → `prototypes/core/*`
2. **認証システム**: `app/auth/*` → `prototypes/auth/*`
3. **サービス層**: `app/services/*` → `prototypes/services/*`
4. **UI層**: `app/ui/*` → `prototypes/ui/*` (NiceGUI化)

### new/系からの移行
1. **UIデザイン**: HTML/CSS → NiceGUIコンポーネント
2. **ページ構成**: Jinja2テンプレート → NiceGUIページ
3. **JavaScript機能**: JS → Pythonロジック

## 🔄 継続的改善

- 毎週アーキテクチャレビュー
- パフォーマンス測定・改善
- ユーザビリティテスト実施
- セキュリティ監査定期実行