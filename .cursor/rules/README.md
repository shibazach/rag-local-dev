# Cursor Rules - UI開発ガイドライン

このディレクトリには、RAGシステムのUI開発における設計ポリシーとガイドラインが含まれています。

## ドキュメント構成

### 📋 [ui-design-policy.md](./ui-design-policy.md)
- UI設計の基本原則
- 情報密度最大化の方針
- 階層的CSS設計
- 実装チェックリスト
- 禁止事項

### 🎯 [nicegui-best-practices.md](./nicegui-best-practices.md)
- NiceGUI特有のベストプラクティス
- DOM構造の理解
- 公式ドキュメント準拠のルール
- コンポーネント階層構造
- 技術仕様とデフォルト値

### 🎨 [css-guidelines.md](./css-guidelines.md)
- CSS責任分離の原則
- ファイル構成戦略
- 共通設定の管理方法
- paddingゼロ実現のノウハウ
- デバッグ手順

### 🏗️ [component-architecture.md](./component-architecture.md)
- コンポーネント設計原則
- ディレクトリ構造
- 実験駆動開発のフロー
- 継承ベースのアーキテクチャ
- arrangement_test.pyの活用方法

### 🔧 [troubleshooting.md](./troubleshooting.md)
- よくあるエラーと解決法
- 白画面問題の診断
- JavaScriptエラーの対処
- 高さ制御の問題解決
- デバッグテクニック

## 使用方法

1. **新機能開発時**: まず[component-architecture.md](./component-architecture.md)を参照し、arrangement_test.pyで実験
2. **CSS実装時**: [css-guidelines.md](./css-guidelines.md)のルールに従う
3. **NiceGUI使用時**: [nicegui-best-practices.md](./nicegui-best-practices.md)の公式推奨パターンを確認
4. **問題発生時**: [troubleshooting.md](./troubleshooting.md)で解決方法を探す
5. **全体方針確認**: [ui-design-policy.md](./ui-design-policy.md)で基本原則を確認

## 重要な原則

### 🚫 絶対禁止
- `!important`の使用
- 複数ファイルでのCSS重複定義
- 推測によるデフォルト値設定
- 本番ページでの場当たり的調整

### ✅ 必須事項
- ブラウザ開発者ツールでの実測
- arrangement_test.pyでの事前実験
- 公式ドキュメントの確認
- バックアップの作成

## メンテナンス

これらのドキュメントは実際の開発経験に基づいて作成されており、新しい知見が得られた場合は随時更新してください。

更新時は以下を心がけてください：
- 実証済みの内容のみ記載
- 具体的なコード例を含める
- エラーメッセージは正確に記載
- 日付を含めて記録する

---

*最終更新: 2025年8月6日*