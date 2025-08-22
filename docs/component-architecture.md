# 共通コンポーネント設計原則

## ファイル構成戦略
```
prototypes/ui/
├── components/
│   ├── base/          # 継承可能なベースクラス
│   │   ├── styles.py  # StyleBuilder
│   │   ├── panel.py   # BasePanel, InheritablePanel, FormPanel
│   │   ├── form.py    # BaseFormRow, FormBuilder
│   │   ├── card.py    # BaseCard, InteractiveCard
│   │   └── button.py  # BaseButton, FloatingActionButton
│   ├── common/        # 汎用コンポーネント
│   │   ├── layout.py  # CommonSplitter, CommonTabs
│   │   └── display.py # CommonTable, CommonFormElements
│   ├── chat/          # 具体的な機能コンポーネント
│   │   ├── settings_panel.py    # ChatSettingsPanel (FormPanel継承)
│   │   ├── search_result_card.py # ChatSearchResultCard (InteractiveCard継承)
│   │   └── layout_button.py     # ChatLayoutButton (FloatingActionButton継承)
│   └── elements.py    # 互換性維持用（151行に削減済み）
├── pages/
│   ├── arrangement_test.py  # 【重要】UI実験・練習専用ページ
│   └── (その他本番ページ)
└── styles/
    └── common.py      # CSS定数・クラス定義
```

## コンポーネント階層
- **Level 1**: 継承可能なベースクラス（base/）
- **Level 2**: 汎用コンポーネント（common/）  
- **Level 3**: 機能別具体コンポーネント（chat/, rag/, etc.）
- **Level 4**: スタイル定数（styles/common.py）

## UI開発フロー - arrangement_test.py実験駆動開発

### 基本方針
**「本番コードを壊さずに、新機能・新コンポーネントの実験を安全に行う」**

### arrangement_test.py の役割
1. **新コンポーネント開発の実験場**
   - 新しいUI要素の作り込み・テスト
   - レイアウトパターンの試行錯誤
   - デザインバリエーションの比較検討

2. **共通コンポーネント化の練習場**
   - 既存コードから共通パターンを抽出
   - 再利用可能な形への変換練習
   - パラメータ設計の最適化

3. **配置・組み合わせテスト**
   - 複数コンポーネントの組み合わせ確認
   - レスポンシブ動作の検証
   - アクセシビリティテスト

### 安全な開発フロー

#### ステップ1: 実験・練習フェーズ
```
arrangement_test.py（タブ機能活用）
├── タブ1: リサイズ4分割（基本レイアウト）
├── タブ2: 新レイアウト実験①（自由改変可）
├── タブ3: 新レイアウト実験②（自由改変可）  
└── タブ4: コンポーネント単体練習（自由改変可）
```

**実験ルール:**
- `arrangement_test.py`内で自由に書き換え・破壊OK
- `# === 実験エリア開始/終了 ===` でマーク
- 失敗してもロールバック簡単

#### ステップ2: 共通化・本番投入フェーズ
```
実験完了 → 共通コンポーネント化 → 本番配置
    ↓              ↓               ↓
arrangement_test.py → components/ → 本番ページ
```

**投入ルール:**
- 実験で安定したコンポーネントのみ移植
- `base/` → `common/` → `機能別/` の順で段階投入
- 本番ページは最小限の変更に留める

### 禁止事項
- **components/内での直接実験・練習は厳禁**
- **本番ページでの場当たり的UI調整は厳禁**
- **arrangement_test.pyを本番環境で使用禁止**

### メンテナンス指針
- arrangement_test.pyは定期的にクリーンアップ
- 成功パターンはコメント付きで保存
- 失敗パターンも学習のため一時保存

## 共通コンポーネント実装ガイド（2025年実証済み）

### MainContentArea - FixedHeaderFooterContainer（NiceGUI準拠版）
```python
# prototypes/ui/components/layout.py
class MainContentArea:
    """
    NiceGUI公式ガイドライン + simple_test.py成功実装の統合版
    
    機能:
    1. ui.query().style()でNiceGUIフレームワーク要素を完全制御
    2. calc(100vh - 48px - 24px)による正確な高さ計算
    3. position:fixedヘッダー・フッター対応の完全レイアウト
    4. NiceGUI公式コンポーネント活用でメンテナンス性向上
    
    NiceGUI公式準拠要素:
    - ui.element()をベースとした構築
    - context managerパターン準拠
    - classes()とstyle()の使い分け
    
    Usage:
        RAGHeader()
        with MainContentArea():
            # NiceGUI公式コンポーネント配置推奨
            with ui.card():
                ui.label('コンテンツ')
        RAGFooter()
    """
```

### コンポーネント化の成功手順（NiceGUI準拠版）
1. **実験フェーズ**: arrangement_test.pyで公式コンポーネントベース実装作成
2. **公式コンポーネント検証**: NiceGUIドキュメントで最適な公式要素を確認
3. **バックアップ作成**: 既存コンポーネントを `_back` でリネーム
4. **NiceGUI準拠実装**: 公式推奨パターン + 成功パターンの融合
5. **実動確認**: `nicegui-query` 出力数と DOM構造で動作確認
6. **本番投入**: 他のページでの利用可能性確認

### 実装時の注意点（NiceGUI準拠）
- **公式ドキュメント優先**: 新機能実装前に[公式ドキュメント](https://nicegui.io/documentation/)を確認
- **カスタムCSS最小化**: 公式コンポーネントで解決できる場合はCSS直書き回避
- **classes()とstyle()使い分け**: Tailwindクラスは`classes()`、カスタムCSSは`style()`
- **simple_test.pyとの一致性確認**: `nicegui-query` 出力数で正確性検証
- **段階的移行**: 全ページ一括変更ではなく、1ページずつ確実に移行
- **バックアップ保持**: 既存実装は必ず `_back` として保持
- **DOM実測**: ブラウザ開発者ツールで実際の出力を常に確認

### カスタムCSS vs 公式コンポーネント判断基準
```python
# ✅ 公式コンポーネントで実現可能 → 優先
ui.table(columns=columns, rows=rows, pagination=True)

# ✅ 公式 + 軽微なスタイル調整 → 許可
ui.card().style('border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.1);')

# ⚠️ 複雑なカスタムレイアウト → arrangement_test.pyで実験後判断
with ui.element('div').style('display: grid; grid-template-columns: ...'):
    # 複雑なカスタム実装
```

これらの原則に従い、**安全性と革新性を両立したUI開発**を実現する。