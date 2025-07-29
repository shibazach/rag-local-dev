# UI設計統一ルール

## 基本方針

### デザイン哲学
- **一貫性**: 全ページで統一されたUI/UX
- **可読性**: 適切なフォントサイズと行間
- **操作性**: 統一されたコントロールサイズ
- **保守性**: CSS変数による集中管理

## フォントサイズ階層

### 統一ルール
```css
:root {
  /* フォントサイズ階層 - 統一ルール */
  --font-size-xs: 12px;      /* 補助情報、キャプション */
  --font-size-sm: 13px;      /* 小さなラベル */
  --font-size-base: 14px;    /* 基本テキスト、フォーム */
  --font-size-lg: 16px;      /* セクション見出し */
  --font-size-xl: 18px;      /* 大見出し */
  --font-size-xxl: 20px;     /* ページタイトル */
}
```

### 使用例
- **ページタイトル**: `--font-size-xxl` (20px)
- **セクション見出し**: `--font-size-lg` (16px)
- **フォーム要素**: `--font-size-base` (14px)
- **補助テキスト**: `--font-size-xs` (12px)

## コントロール統一ルール

### 基本設定
```css
:root {
  /* コントロール統一ルール */
  --control-font-size: 14px;
  --control-height: 28px;
  --control-line-height: 1.1;
  --control-padding: 4px 8px;
}
```

### 適用対象
- `input[type="text"]`
- `input[type="number"]`
- `select`
- `textarea`
- `button`

### 実装例
```css
.form-section input,
.form-section select,
.form-section textarea {
  font-size: var(--control-font-size) !important;
  height: var(--control-height) !important;
  line-height: var(--control-line-height);
  padding: var(--control-padding);
}
```

## 行間・余白統一

### 基本設定
```css
:root {
  /* 行間・余白 - 統一ルール */
  --line-height-tight: 1.1;    /* 密な行間（フォーム） */
  --line-height-base: 1.2;     /* 標準行間 */
  --line-height-relaxed: 1.4;  /* ゆったり行間（本文） */
  
  --spacing-xs: 4px;           /* 最小余白 */
  --spacing-sm: 8px;           /* 小余白 */
  --spacing-base: 12px;        /* 標準余白 */
  --spacing-lg: 16px;          /* 大余白 */
  --spacing-xl: 24px;          /* 最大余白 */
}
```

## 見出し階層

### H1要素（ページタイトル）
```css
.page-title {
  font-size: var(--font-size-xxl);  /* 20px */
  font-weight: bold;
  margin: 0 0 var(--spacing-base) 0;
  color: var(--gray-800);
  line-height: var(--line-height-tight);
}
```

### セクション見出し
```css
.section-title {
  font-size: var(--font-size-lg);   /* 16px */
  font-weight: normal;
  margin: 0 0 var(--spacing-sm) 0;
  color: var(--gray-700);
  line-height: var(--line-height-tight);
}
```

## 色彩統一ルール

### 基本カラーパレット
```css
:root {
  /* カラーパレット - 調和の取れた色調 */
  --primary-color: #5a6c7d;      /* メインカラー */
  --secondary-color: #6c757d;    /* セカンダリカラー */
  --success-color: #4a7c59;      /* 成功・実行 */
  --danger-color: #c85450;       /* 危険・削除 */
  --warning-color: #d4a843;      /* 警告 */
  --info-color: #5a9aa8;         /* 情報 */
  
  /* グレースケール */
  --gray-100: #f8f9fa;
  --gray-200: #e9ecef;
  --gray-300: #dee2e6;
  --gray-400: #ced4da;
  --gray-500: #adb5bd;
  --gray-600: #6c757d;
  --gray-700: #495057;
  --gray-800: #343a40;
  --gray-900: #212529;
}
```

### 使用ガイドライン
- **青色系の禁止**: `#007bff`, `#3498db` などの青色は使用禁止
- **統一された色調**: `--primary-color` ベースの落ち着いた色調
- **アクセシビリティ**: 十分なコントラスト比を確保

## フォーム設計

### 基本構造
```html
<div class="form-section">
  <label for="input-id">ラベル:</label>
  <input type="text" id="input-id" />
</div>
```

### スタイル適用
```css
.form-section {
  display: flex;
  align-items: center;
  margin-bottom: var(--spacing-xs);  /* 4px */
  line-height: var(--line-height-tight);
}

.form-section label {
  min-width: 120px;
  flex-shrink: 0;
  font-weight: normal;
  font-size: var(--font-size-base);
}
```

## レイアウト統一

### コンテナ高さ
```css
#app-container,
#try-ocr-container {
  height: 100vh;  /* 余白なし */
  display: flex;
  flex-direction: column;
}
```

### パネル構造
```css
.panel {
  background: rgba(255, 255, 255, 0.3);
  backdrop-filter: blur(15px);
  border: 1px solid rgba(255, 255, 255, 0.4);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
}
```

## 実装ガイドライン

### CSS変数の優先使用
❌ **悪い例**
```css
.my-input {
  font-size: 14px;
  height: 28px;
}
```

✅ **良い例**
```css
.my-input {
  font-size: var(--control-font-size);
  height: var(--control-height);
}
```

### !important の適切な使用
- 個別CSSファイルでの上書き防止に限定使用
- CSS変数の値変更を優先

### メンテナンス性の確保
1. **集中管理**: common.cssのCSS変数で統一
2. **一貫性**: 全ページで同じ変数を使用
3. **拡張性**: 新しいコンポーネントも変数を使用

## ファイル構成

### CSS階層
```
app/static/css/
├── common.css      # 統一ルール・CSS変数
├── base.css        # 全体レイアウト
├── chat.css        # チャット固有
├── ingest.css      # データ整形固有
└── try_ocr.css     # OCR比較固有
```

### 優先順位
1. `common.css` - 最高優先度
2. `base.css` - 全体レイアウト
3. 個別CSS - ページ固有の調整

## 品質チェックリスト

### デザイン統一性
- [ ] フォントサイズがCSS変数を使用している
- [ ] コントロール高さが統一されている
- [ ] 色調が統一カラーパレットを使用している
- [ ] 行間・余白が統一ルールに従っている

### 機能性
- [ ] 全ブラウザで表示が統一されている
- [ ] レスポンシブ対応ができている
- [ ] アクセシビリティが確保されている

### 保守性
- [ ] CSS変数による集中管理ができている
- [ ] コードの重複がない
- [ ] 命名規則が統一されている