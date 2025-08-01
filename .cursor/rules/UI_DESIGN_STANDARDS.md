# UI Design Standards

本システムにおけるUI設計の統一基準を定義します。

## 基本設計原則

### 1. レイアウト統一
- **高さ**: `height: calc(100vh - 95px)` - ヘッダー60px + マージン35pxを除いた画面全体
- **パディング**: `padding: 8px` - 全ページ共通の外側余白
- **ギャップ**: `gap: 6px` - ペイン間の統一間隔
- **overflow**: `overflow: hidden` - 全体スクロール禁止、個別ペインでスクロール制御

### 2. ペイン設計
#### 共通スタイル
```css
.panel {
    background: white;
    border: 1px solid #ddd;
    border-radius: 8px;
    display: flex;
    flex-direction: column;
    overflow: hidden;
    height: 100%;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}
```

#### ヘッダー統一
```css
.panel-header {
    background: #f8f9fa;
    padding: 8px 12px;
    border-bottom: 1px solid #ddd;
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-shrink: 0;
}

.panel-header h3 {
    margin: 0;
    font-size: 16px;
    font-weight: 600;
}
```

#### コンテンツエリア
```css
.panel-content {
    flex: 1;
    padding: 8px;
    overflow-y: auto;
    min-height: 0;
}
```

### 3. フォーム要素統一

#### 基本入力
```css
.form-control {
    width: 100%;
    padding: 6px 10px;
    border: 1px solid #ddd;
    border-radius: 4px;
    font-size: 13px;
}

.form-select {
    padding: 6px 12px;
    border: 1px solid #ced4da;
    border-radius: 4px;
    font-size: 0.9rem;
    min-width: 180px;
}
```

#### コンパクト要素
```css
.compact-select {
    height: 32px;
    font-size: 12px;
    min-width: 180px;
}

.compact-input {
    height: 32px;
    font-size: 12px;
}
```

### 4. ドラッグ可能境界線

#### 実装パターン
```css
.splitter {
    background: #dee2e6;
    cursor: col-resize; /* または row-resize */
}

.splitter:hover {
    background: #007bff;
}
```

#### Grid配置での注意点
- 縦分割: `grid-column: 2; grid-row: 1 / span;`
- 横分割: `grid-row: 2; grid-column: 1;`

### 5. スクロールバー制御

#### 不要なスクロールバー防止
```css
.container {
    overflow: hidden; /* 全体レベル */
}

.scrollable-content {
    overflow-y: auto; /* 必要な部分のみ */
    overflow-x: hidden; /* 横スクロール防止 */
}
```

## ページ別適用例

### ファイル管理ページ
- 左右2分割レイアウト
- リサイズ可能境界線
- 左: ファイル一覧、右: プレビュー

### データ登録ページ
- 3列×2行グリッドレイアウト
- 設定（左上）、ログ（中央全体）、ファイル選択（右全体）

### OCR検証ページ
- 2×2グリッドレイアウト + ドラッグ可能境界線
- 左右独立の上下分割制御

## 実装時の注意点

1. **CSS詳細度**: ページ固有CSSは `!important` を最小限に抑制
2. **レスポンシブ**: モバイル対応時は `gap` を `4px` に縮小
3. **ブラウザ互換性**: Grid + Flexbox の組み合わせでIE11対応は考慮しない
4. **パフォーマンス**: `transform` や `opacity` でアニメーション実装
5. **アクセシビリティ**: フォーカス可能要素にはキーボードナビゲーション対応

## 品質チェックリスト

- [ ] ペイン間ギャップが6pxで統一されているか
- [ ] 角丸が8pxで統一されているか
- [ ] 不要な横スクロールバーが出現していないか
- [ ] ドラッグ境界線が正常に動作するか
- [ ] レスポンシブ時に要素が重複していないか