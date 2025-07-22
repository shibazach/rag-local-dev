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

## 技術スタック
- **バックエンド**: FastAPI + Python
- **フロントエンド**: HTML/CSS/JavaScript（バニラJS）
- **データベース**: PostgreSQL + pgvector
- **LLM**: Ollama（ローカル実行）
- **OCR**: 複数エンジン対応
- **埋め込み**: sentence-transformers

## アーキテクチャ
- `app/`: FastAPIアプリケーション本体
- `db/`: データベース操作・スキーマ定義
- `ocr/`: OCR処理サービス
- `llm/`: LLM関連処理（チャンク分割、テキスト整形）
- `fileio/`: ファイル処理・埋め込み処理
- `src/`: 設定・共通ユーティリティ

## 開発方針
- 日本語処理に最適化された設計
- モジュラー構造による保守性重視
- リアルタイム処理とユーザビリティの両立
- 複数のOCRエンジンによる柔軟性確保