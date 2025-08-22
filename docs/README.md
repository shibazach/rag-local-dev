# RAGシステム - Flet UI開発ドキュメント

このディレクトリには、Flet UIフレームワークに基づくRAGシステム開発における設計ガイドライン、実装パターン、品質保証手順が含まれています。

## 🎯 Flet開発の基本方針

### Flet公式ドキュメント準拠 (MANDATORY)
- **[Flet Controls Reference](https://flet.dev/docs/controls)** - 基本コントロール仕様
- **[Flet API Reference](https://docs.flet.dev/controls/)** - 詳細API仕様  
- **[Flet Controls Gallery](https://flet-controls-gallery.fly.dev/)** - 実装パターン集
- **[Fletレイアウト基礎](https://qiita.com/Tadataka_Takahashi/items/ab0535d228225d3d7bf1)** - Container/Flex設計パターン

### UI設計三原則
1. **情報密度最大化**: 画面内情報量を最大化、無駄な余白排除
2. **Flet公式準拠**: 公式コントロール優先、カスタム実装最小化  
3. **デバッグ駆動設計**: 推測禁止、実測・検証必須

## 📚 ドキュメント構成

### 🎯 [ui-design-policy.md](./ui-design-policy.md)
**Flet UI設計の根幹となる方針書**
- 情報密度最大化の具体的実装方法
- Fletネイティブスタイリング手法
- 公式コントロール活用パターン
- レスポンシブレイアウト設計原則
- **必読**: 全UI実装前に確認必須

### 🎨 [css-guidelines.md](./css-guidelines.md)
**スタイル管理ガイドライン** (Flet環境での読み替え適用)
- 共通スタイル定数の管理方法
- カラーパレット・サイズ体系の統一
- コンポーネント間スタイル整合性確保

### 🏗️ [component-architecture.md](./component-architecture.md)
**Fletコンポーネント設計指針**
- 階層的コンポーネント構造設計
- 再利用可能コンポーネントパターン
- 状態管理とイベント処理方式
- テスト駆動コンポーネント開発

### 🔧 [troubleshooting.md](./troubleshooting.md)
**Flet開発時の問題解決集**
- よくあるFletエラーパターンと対処法
- レイアウト崩れの診断・修正手順
- パフォーマンス問題の特定・最適化
- デバッグ効率化テクニック

### 📊 [ui/flet-migration-analysis.md](./ui/flet-migration-analysis.md)
**Flet実装進捗管理**
- 機能別実装状況一覧
- コンポーネント対応表
- 残課題・優先度管理

### 🏛️ architecture/
- **[DATABASE_DESIGN.md](./architecture/DATABASE_DESIGN.md)**: データベース設計仕様
- **[MULTIMODAL_LLM_INTEGRATION_PLAN.md](./architecture/MULTIMODAL_LLM_INTEGRATION_PLAN.md)**: マルチモーダルLLM統合設計

## 🚀 Flet開発ワークフロー

### Phase 1: 設計・調査
```mermaid
graph LR
    A[要求分析] --> B[Flet公式確認]
    B --> C[Gallery実装例研究]  
    C --> D[API仕様詳細確認]
    D --> E[設計パターン決定]
```

1. **要求分析**: 実装すべき機能・UI の明確化
2. **[公式ドキュメント確認](https://flet.dev/docs/controls)**: 適切なコントロール選定
3. **[Gallery研究](https://flet-controls-gallery.fly.dev/)**: 実装パターン把握
4. **[API仕様確認](https://docs.flet.dev/controls/)**: プロパティ・メソッド詳細把握
5. **設計決定**: [ui-design-policy.md](./ui-design-policy.md) 準拠設計

### Phase 2: 実装・検証
```mermaid
graph LR
    A[実験実装] --> B[tests手順実行]
    B --> C[公式パターン比較]
    C --> D[品質チェック]  
    D --> E[統合・デプロイ]
```

1. **実験実装**: `flet_ui/arrangement_test/` での安全な実装
2. **検証**: [tests/README.md](../tests/README.md) 手順に従った動作確認
3. **公式パターン比較**: ギャラリー例との整合性確認
4. **品質チェック**: [ai-assistant-behavioral-standards.md](../.cursor/rules/ai-assistant-behavioral-standards.md) 準拠
5. **統合**: 本番コンポーネントへの統合・デプロイ

### Phase 3: 保守・改善
1. **継続的モニタリング**: パフォーマンス・UX指標監視
2. **フィードバック収集**: ユーザビリティ問題の特定
3. **段階的改善**: [component-architecture.md](./component-architecture.md) パターン適用
4. **ドキュメント更新**: 得られた知見の文書化

## ✅ 開発品質基準

### 実装前チェックリスト
- [ ] **公式ドキュメント確認**: [Controls Reference](https://flet.dev/docs/controls) での仕様確認
- [ ] **実装パターン研究**: [Gallery](https://flet-controls-gallery.fly.dev/) での類似例確認
- [ ] **API詳細確認**: [API Reference](https://docs.flet.dev/controls/) でのプロパティ確認
- [ ] **設計方針準拠**: [ui-design-policy.md](./ui-design-policy.md) 原則確認

### 実装中チェックリスト  
- [ ] **公式コントロール使用**: `ft.*` コンポーネント優先使用
- [ ] **プロパティ名正確性**: API Reference準拠の正確なプロパティ名
- [ ] **レイアウトパターン**: Container/Row/Column の適切な組み合わせ
- [ ] **共通コンポーネント活用**: 再利用可能コンポーネントの最大活用

### 実装後チェックリスト
- [ ] **tests/README.md準拠検証**: 必須テスト手順の完全実行
- [ ] **公式例との整合性**: Gallery実装パターンとの一致確認  
- [ ] **レスポンシブ動作**: 画面サイズ変更時の適切な表示
- [ ] **パフォーマンス**: レンダリング速度・メモリ使用量の最適性

## 🚫 品質保証・禁止事項

### 絶対禁止
- **CSS概念の持ち込み**: Fletには CSS なし、ネイティブプロパティのみ使用
- **推測実装**: 公式ドキュメント確認なしの実装
- **tests手順省略**: 動作確認手順の省略・簡略化
- **カスタム実装優先**: 公式コントロールより自作を優先すること

### 強く非推奨
- **ハードコーディング**: サイズ・色・文字列の直接埋め込み
- **パフォーマンス無視**: 大量データ処理時の最適化不足
- **ドキュメント不備**: 実装理由・設計意図の文書化不足

## 🔗 公式リソースクイックアクセス

| リソース | 用途 | 確認タイミング |
|---------|------|--------------|
| [Controls Reference](https://flet.dev/docs/controls) | コントロール選定 | 設計時・実装前 |
| [API Reference](https://docs.flet.dev/controls/) | プロパティ確認 | 実装中・デバッグ時 | 
| [Gallery](https://flet-controls-gallery.fly.dev/) | 実装パターン | 設計時・検証時 |
| [Layout Guide](https://qiita.com/Tadataka_Takahashi/items/ab0535d228225d3d7bf1) | レイアウト設計 | 構造設計時 |

## 📈 継続的改善

### 学習・スキルアップ
- **公式アップデート追跡**: Flet新機能・変更点の継続学習
- **ベストプラクティス収集**: 成功パターンのドキュメント化
- **課題パターン分析**: よくある問題の類型化・対策整理

### ドキュメントメンテナンス
- **実装知見の反映**: 新たに得られた知見の文書追加
- **品質基準の更新**: より効率的な手順の編み出し・適用
- **事例集の拡充**: 成功・失敗事例の蓄積・共有

---

**本ドキュメント群は [Flet公式ドキュメント](https://flet.dev/docs/controls) 準拠を大前提とし、実際の開発経験に基づく品質向上指針として継続的に更新されます。**

*最終更新: 2025年8月22日 - Flet公式準拠化対応*