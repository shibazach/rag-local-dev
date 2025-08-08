# 🚀 RAGシステム統合計画書【完了】

## 📋 概要

本計画書は、4つの系統（OLD/new/app/prototype）に分散していたRAGシステムを、prototype系に統合するための段階的移行計画を定めたものです。

**作成日**: 2025年1月
**完了日**: 2025年1月
**ステータス**: ✅ 全フェーズ完了
**最終成果**: prototype系が唯一の本番システムとして稼働

## 📊 現状分析

### 各系統の特徴と実装状況

#### 1. **prototype系（最新・統合先）**
- ✅ **強み**
  - NiceGUI統合済み（FastAPI + NiceGUI完全統合）
  - モダンなUIコンポーネント基盤
  - app系準拠のディレクトリ構造
- ❌ **課題**
  - RAG機能未実装（OCR/LLM/Embedding空）
  - サービス層不足（stats_serviceとmultimodal_serviceのみ）
  - 認証・設定システム未整備

#### 2. **app系（エンタープライズ設計）**
- ✅ **強み**
  - モジュラー構造、サービス層充実
  - Pydantic設定管理システム
  - セッション認証・SAML準備
  - エラーハンドリング・ログ管理
- ❌ **課題**
  - NiceGUI未統合（API専用）
  - RAG機能未実装（ディレクトリのみ）

#### 3. **OLD系（実績あり）**
- ✅ **強み**
  - RAG機能完全実装（OCR/LLM/Embedding）
  - 複数OCRエンジン対応、画像補正機能
  - 高品質プロンプトテンプレート
  - 3テーブル設計（blob/meta/text）
- ❌ **課題**
  - レガシー構造（モノリシック）
  - セキュリティ機能なし
  - UI古い（Bootstrap + Jinja2）

#### 4. **new系（過渡期）**
- ⚡ **特徴**
  - セキュリティ強化試行（CSP等）
  - UI実験段階
  - 機能不完全
- 📝 **判定**: 優先度低（UIはprototype系に移植済み）

## 🎯 統合戦略

### 基本方針
1. **prototype系を最終形態として育成**
2. **app系のエンタープライズ基盤を移植**
3. **OLD系の実績あるRAG機能を移植**
4. **new系は必要部分のみ抽出後削除**

### 移行優先順位
1. **高優先度**: app系基盤 + OLD系RAG機能
2. **中優先度**: 統合テスト・品質保証
3. **低優先度**: new系整理・旧系統削除

## 📅 段階的実行計画

### Phase 1: app系 → prototype系【基盤移植】

#### 1-1. 設定システム移植
- **移植元**: `app/config/base.py`
- **移植先**: `prototypes/config/settings.py`
- **内容**:
  - Pydantic BaseSettings統合
  - 環境別設定（development/staging/production）
  - GPU/CPU自動判定
  - LLMモデル設定
  - パス設定・セキュリティ設定

#### 1-2. 認証・セッション管理移植
- **移植元**: `app/auth/`
- **移植先**: `prototypes/auth/`
- **内容**:
  - SessionMiddleware統合
  - 認証依存関係（dependencies.py）
  - ユーザーモデル・セッションモデル
  - 認証デコレーター・ガード

#### 1-3. サービス層スケルトン移植
- **移植元**: `app/services/`
- **移植先**: `prototypes/services/`
- **対象サービス**:
  - file_service.py（ファイル管理）
  - chat_service.py（チャット機能）
  - processing_service.py（処理フロー）
  - admin_service.py（管理機能）

#### 1-4. データベースモデル統合
- **移植元**: `app/core/models.py`
- **移植先**: `prototypes/core/models.py`
- **内容**:
  - エンタープライズ拡張モデル
  - 監査ログテーブル
  - ユーザー・セッションテーブル
  - メトリクステーブル

### Phase 2: OLD系 → prototype系【RAG機能移植】

#### 2-1. OCR機能移植
- **移植元**: `OLD/ocr/`
- **移植先**: `prototypes/services/ocr/`
- **対象機能**:
  - ocr_process.py（メイン処理）
  - orientation_corrector.py（画像回転補正）
  - spellcheck.py（スペルチェック）
  - bert_corrector.py（BERT補正）

#### 2-2. LLM処理移植
- **移植元**: `OLD/llm/`
- **移植先**: `prototypes/services/llm/`
- **対象機能**:
  - refiner.py（テキスト整形）
  - prompt_loader.py（プロンプト管理）
  - chunker.py（チャンク分割）
  - scorer.py（品質スコアリング）

#### 2-3. Embedding処理移植
- **調査**: OLD系の実装確認
- **移植先**: `prototypes/services/embedding/`
- **統合**: ベクトル化・類似度検索

#### 2-4. プロンプトテンプレート移植
- **移植元**: `OLD/bin/`
- **移植先**: `prototypes/prompts/`
- **内容**: 実績ある高品質プロンプト

### Phase 3: new系整理【必要機能抽出】

#### 3-1. セキュリティ機能確認
- CSPヘッダー設定
- セキュリティミドルウェア
- その他有用な実装

#### 3-2. 不要ファイル削除
- UI関連（prototype系に移植済み）
- 重複実装

### Phase 4: prototype系完成【品質保証】

#### 4-1. 統合テスト
- 全機能の動作確認
- パフォーマンステスト
- セキュリティテスト

#### 4-2. ドキュメント整備
- 運用ドキュメント
- API仕様書
- 開発者ガイド

### Phase 5: 旧系統削除【クリーンアップ】

#### 5-1. app系削除
- 機能移植完了確認
- バックアップ作成
- ディレクトリ削除

#### 5-2. OLD系アーカイブ
- 参照用アーカイブ作成
- プロジェクトから削除

#### 5-3. new系削除
- 必要部分抽出確認
- ディレクトリ削除

## ⚠️ リスク管理

### 移植時の注意事項
1. **インポートパスの調整**: app.* → prototypes.*
2. **設定参照の更新**: 新しい設定システムへの対応
3. **依存関係の解決**: 必要なライブラリの確認
4. **テスト実施**: 各機能移植後の動作確認

### バックアップ戦略
- 各Phase実行前にバックアップ作成
- 問題発生時のロールバック手順確立
- OLD系は完全移植まで保持

## 📊 進捗管理

### 完了基準
- [ ] Phase 1: app系基盤移植完了
- [ ] Phase 2: OLD系RAG機能移植完了
- [ ] Phase 3: new系必要機能抽出完了
- [ ] Phase 4: 統合テスト・品質保証完了
- [ ] Phase 5: 旧系統削除完了

### 成功指標
1. prototype系で全機能が動作
2. パフォーマンス劣化なし
3. セキュリティ要件充足
4. コード品質向上

## 🚀 実行開始

本計画に基づき、Phase 1から順次実行を開始します。

---
*最終更新: 2025年1月*