# UI設計標準 - R&D RAGシステム

## 基本方針

### 1. 統一されたレイアウト構造
- **Flexboxベースの設計**: 全てのレイアウトはFlexboxを基本とする
- **固定高さ設定**: `height: 100%`を使用してコンテナの高さを明確に定義
- **ブラウザ間互換性**: Chrome、Edge等での表示差異を防ぐ統一構造

### 2. 表（テーブル）設計標準

#### 共通CSS設定
```css
/* 表コンテナ */
.file-list-container {
    flex: 1;
    overflow: hidden;
    display: flex;
    flex-direction: column;
    height: 100%;
    margin: 0;
    padding: 0;
}

/* 表本体 */
.file-table {
    width: 100%;
    border-collapse: collapse;
    display: flex;
    flex-direction: column;
    flex: 1;
    margin: 0;
    border-spacing: 0;
}

/* 固定ヘッダー */
.file-table thead {
    background: #f8f9fa;
    display: table;
    width: 100%;
    table-layout: fixed;
}

/* スクロール可能な本体 */
.file-table tbody {
    overflow-y: auto;
    display: block;
    flex: 1;
}

/* 行レイアウト */
.file-table tbody tr {
    display: table;
    width: 100%;
    table-layout: fixed;
}
```

#### 統一クラス名
- `.file-table`: メイン表クラス（全ページ共通）
- `.files-table`: 代替表クラス（後方互換性）
- `.results-table`: 結果表示用クラス（アップロード結果等）

### 3. ページネーション設計

#### 配置原則
- **表の直下に配置**: `.file-list-container`内の最下部
- **固定高さ**: `min-height: 32px`
- **余白なし**: `margin: 0`でギャップを排除

#### 標準構造
```html
<div class="file-list-container">
    <table class="file-table">
        <!-- 表内容 -->
    </table>
    <div class="pagination-container">
        <!-- ページネーション内容 -->
    </div>
</div>
```

### 4. CSS組織化方針

#### ファイル構成
- `main.css`: 共通スタイル・基本設定
- `[page].css`: ページ固有のスタイル
- `components.css`: 再利用可能コンポーネント

#### CSS優先順位
1. **!importantの回避**: 可能な限り使用しない
2. **詳細度による制御**: クラス名の組み合わせで優先度調整
3. **読み込み順序**: 共通CSS → ページ固有CSS

### 5. レスポンシブ対応

#### ブレークポイント
- デスクトップ: 1200px以上
- タブレット: 768px - 1199px
- モバイル: 767px以下

#### パネルレイアウト
- デスクトップ: 左右分割表示
- タブレット以下: 縦積み表示

### 6. 色彩・タイポグラフィ

#### 基本色
- プライマリ: `#007bff`
- 背景: `#f8f9fa`
- 境界線: `#e9ecef`、`#ddd`
- テキスト: `#333`、`#666`

#### フォント
- 基本: `-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif`
- サイズ: 12px（表内）、13-16px（一般UI）

### 7. 状態表示

#### ステータスバッジ
- 統一パディング: `2px 8px`
- 角丸: `border-radius: 12px`
- 最小幅: `60px`
- フォントサイズ: `11px`

#### ホバー効果
- 背景色変更: `#f8f9fa`
- トランジション: `all 0.2s ease`

### 8. アクセシビリティ

#### 基本要件
- キーボードナビゲーション対応
- 適切なコントラスト比確保
- スクリーンリーダー対応のラベル

#### フォーカス管理
- 可視的なフォーカスインジケーター
- 論理的なタブオーダー

### 9. パフォーマンス考慮

#### CSS最適化
- 不要なセレクターの削除
- 効率的なセレクター使用
- CSS Minificationの適用

#### 画像・アイコン
- SVGアイコンの使用
- 適切なサイズ設定
- 遅延読み込み対応

### 10. 実装時の注意点

#### 共通ルール
1. **データ登録ページとファイル管理ページの統一**: 同じ構造・スタイルを使用
2. **マージン・パディングの統一**: `0`を基本とし、必要な箇所のみ設定
3. **Flexboxの適切な使用**: `flex: 1`で可変領域、`flex-shrink: 0`で固定領域
4. **ブラウザテスト**: Chrome、Edge、Firefox での動作確認必須

#### 避けるべき事項
- `!important`の多用
- インラインスタイルの使用
- 固定ピクセル値での高さ指定（calc()は除く）
- ブラウザ固有のプレフィックス依存

---

## 更新履歴
- 2024/01/XX: 初版作成（表レイアウト標準化対応）
