# 📊 RAGシステム 現在の状況

**最終更新**: 2025年8月19日

## システム概要

現在のRAGシステムは、NiceGUIベースのWebアプリケーションとして実装されており、以下の主要機能を提供しています。

## 🎯 主要機能

### 1. ファイル管理・OCR処理
- **ファイルアップロード**: PDF、画像ファイルの取り込み
- **OCR処理**: テキスト抽出とデータベース保存
- **プレビュー**: PDF・テキスト表示

### 2. チャット・検索機能
- **RAG検索**: アップロードファイルを対象とした意味検索
- **チャット**: 自然言語でのファイル内容に関する質問応答

### 3. 管理機能
- **辞書編集**: OCR補正用辞書管理
- **ファイル管理**: アップロードファイルの管理・削除

## 🏗️ 技術構成

### バックエンド
- **Framework**: FastAPI + NiceGUI
- **Database**: PostgreSQL
- **OCR**: Tesseract + 日本語対応
- **LLM**: OpenAI API (GPT-4)
- **Embedding**: OpenAI text-embedding-ada-002

### フロントエンド
- **Framework**: NiceGUI (Python-based)
- **UI Components**: Quasar Framework base
- **PDF Display**: Browser native PDF.js

## 📁 ファイル構造

```
workspace/
├── app/                    # メインアプリケーション
│   ├── ui/                # NiceGUI UIコンポーネント
│   ├── services/          # ビジネスロジック
│   ├── core/             # データモデル・DB
│   └── config/           # 設定管理
├── database/             # DB関連スクリプト
├── logs/                 # システムログ
├── data/                 # アプリケーションデータ
├── docs/                 # ドキュメント
└── archive/              # 非推奨・実験ファイル
```

## 🚀 起動方法

```bash
# 開発環境起動
cd /workspace
timeout 15 python3 main.py
```

アクセス: http://localhost:8081

## 🔧 現在の主要課題

### UI制御の制約
- NiceGUIのダイアログサイズ制御（Quasar制約）
- テキストエリアのVB.NET風Anchor/Dock機能

### 解決策検討中
- Fletへの部分/完全移行検討
- NiceGUI内での技術的解決策実装

## 📈 今後の方針

1. **短期**: 現在のUI問題の技術的解決
2. **中期**: Flet PoC による代替UI検証
3. **長期**: 最適フレームワークでの安定運用

---

**メンテナー**: AI Assistant  
**問い合わせ**: プロジェクト管理者まで