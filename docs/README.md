# R&D RAGシステム ドキュメント

## 📁 ドキュメント構成

### 概要ドキュメント
- [プロジェクト概要](./PROJECT_OVERVIEW.md) - システムの全体像と目的
- [現在の状態](./CURRENT_STATUS.md) - 統合後の現在の状態
- [技術選択比較分析](./技術選択比較分析.md) - 技術スタックの選定理由
- [現在の課題と対応方針](./現在の課題と対応方針.md) - 既知の課題と解決方針

### アーキテクチャ
- [システムアーキテクチャ](./architecture/ARCHITECTURE.md) - 全体設計
- [設計原則](./architecture/DESIGN_PRINCIPLES.md) - 開発指針
- [マルチモーダルLLM統合計画](./architecture/MULTIMODAL_LLM_INTEGRATION_PLAN.md) - 将来拡張

### 統合プロセス
- [統合計画書](./integration/INTEGRATION_PLAN.md) - 4システム統合の全体計画
- [統合完了報告](./integration/INTEGRATION_COMPLETE.md) - 統合結果サマリー
- [Phase 1報告](./integration/PHASE1_COMPLETION_REPORT.md) - エンタープライズ基盤
- [Phase 2報告](./integration/PHASE2_COMPLETION_REPORT.md) - RAG機能
- [Phase 3報告](./integration/PHASE3_COMPLETION_REPORT.md) - セキュリティ強化
- [Phase 4報告](./integration/PHASE4_COMPLETION_REPORT.md) - 統合完成
- [Phase 5報告](./integration/PHASE5_COMPLETION_REPORT.md) - クリーンアップ

### コンポーネントガイド
- [BaseDataGridView マニュアル](./components/BaseDataGridView_Manual.md) - 高機能テーブルコンポーネント

### APIドキュメント
- [API リファレンス](./api/API_REFERENCE.md) - RESTful APIとWebSocket API仕様

### 開発ガイド
- [開発ガイド](./guides/DEVELOPMENT_GUIDE.md) - 環境構築、開発ルール、テスト方法

## 📚 関連資料

### 開発ルール
- `.cursor/rules` - カーソルエディタ用開発ルール
- `.kiro/steering` - プロジェクト方針

### システム構成
```
app/                        # メインアプリケーション
├── config/                 # 設定管理
├── core/                   # コア機能（DB、モデル）
├── auth/                   # 認証・セキュリティ
├── services/               # ビジネスロジック
│   ├── ocr/               # OCR処理
│   ├── llm/               # LLM処理
│   └── embedding/         # ベクトル検索
├── ui/                    # ユーザーインターフェース
│   ├── components/        # UIコンポーネント
│   └── pages/            # ページ定義
├── utils/                 # ユーティリティ
└── prompts/              # プロンプトテンプレート
```

## 🚀 クイックスタート

1. **環境設定**
   ```bash
   cp .env.example .env
   # 必要な環境変数を設定
   ```

2. **依存関係インストール**
   ```bash
   pip install -r requirements.txt
   ```

3. **データベース初期化**
   ```bash
   cd app
   python -c "from core.database import init_database; import asyncio; asyncio.run(init_database())"
   ```

4. **アプリケーション起動**
   ```bash
   python main.py
   ```

## 📖 詳細情報

各ドキュメントを参照して、システムの詳細を理解してください。

---
*最終更新: 2025年1月*