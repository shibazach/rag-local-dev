---
inclusion: always
---

# プロジェクト概要

## システム概要
このプロジェクトは、日本語文書処理に特化したRAG（Retrieval-Augmented Generation）システムです。OCR機能を活用して様々な形式の文書からテキストを抽出し、LLMによる整形・埋め込みベクトル化を行い、効率的な文書検索・質問応答を実現します。

## 主要機能
- **多形式文書対応**: PDF、Word、テキスト、CSV、JSON、EMLファイルの処理
- **高精度OCR**: 複数のOCRエンジン（OCRmyPDF、PaddleOCR、EasyOCR、Tesseract）をサポート
- **LLM整形**: Ollamaを使用した日本語テキストの品質向上
- **ベクトル検索**: 複数の埋め込みモデルによる高精度検索
- **リアルタイム処理**: SSE（Server-Sent Events）による進捗表示
- **チャット機能**: RAG検索による質問応答システム
- **OCR比較**: 複数エンジンによる精度比較・検証機能

## 技術スタック
- **バックエンド**: FastAPI + Pydantic v2 + SQLAlchemy
- **フロントエンド**: HTML/CSS/JavaScript（バニラJS）
- **データベース**: PostgreSQL + pgvector
- **LLM**: Ollama（ローカル実行）
- **OCR**: 複数エンジン対応
- **埋め込み**: sentence-transformers, Ollama embeddings

## 新アーキテクチャ（new/フォルダ構成）
- `new/main.py`: FastAPIアプリケーションエントリーポイント
- `new/config.py`: Pydantic BaseSettingsによる統一設定管理
- `new/models.py`: SQLAlchemyデータベースモデル定義
- `new/schemas.py`: Pydantic型定義（API入出力）
- `new/auth.py`: 認証システム（SAML/OIDC対応準備済み）
- `new/database/`: データベース接続・モデル管理
- `new/api/`: API エンドポイント群
- `new/services/`: ビジネスロジック・サービス層
- `new/routes/`: UIルーティング
- `new/static/`: 静的ファイル（CSS/JS）
- `new/templates/`: Jinja2テンプレート
- `new/utils/`: ユーティリティ関数

## データベース設計（3テーブル構成）
- **files_blob**: ファイルバイナリ格納（主テーブル）
- **files_meta**: ファイルメタ情報（1:1対応）
- **files_text**: テキスト・処理結果（1:1対応）

## 開発方針
- **セキュリティファースト**: 認証基盤・API分離による安全な設計
- **モジュラー構造**: サービス層分離による保守性重視
- **リアルタイム処理**: SSEによる進捗表示とユーザビリティの両立
- **日本語最適化**: OCR・LLM処理の日本語特化
- **スケーラビリティ**: 非同期処理・パイプライン設計による拡張性確保