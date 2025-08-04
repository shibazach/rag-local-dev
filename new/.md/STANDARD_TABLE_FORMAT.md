# 標準表フォーマット仕様 (Standard Table Format)

## 概要

RAGシステム全体で統一された表（テーブル）の標準仕様です。データ登録、ファイル管理、OCR比較等すべての表でこの仕様を適用し、一貫性のある美しいUIを実現します。

## 基本構造

### HTMLテンプレート
```html
<div class="file-list-container">
    <table class="file-table">
        <thead>
            <tr>
                <th>カラム1</th>
                <th>カラム2</th>
                <th>カラム3</th>
                <th>カラム4</th>
            </tr>
        </thead>
        <tbody id="table-body">
            <!-- 動的コンテンツ -->
        </tbody>
    </table>
    <!-- ページネーション -->
    <div class="pagination-container">
        <div class="pagination-info">
            <span id="file-count-info">0件のファイル</span>
            <select id="page-size" class="form-control pagination-select">
                <option value="50">50件/ページ</option>
                <option value="100" selected>100件/ページ</option>
                <option value="200">200件/ページ</option>
                <option value="500">500件/ページ</option>
            </select>
        </div>
        <div class="pagination-nav">
            <button id="prev-page" class="btn btn-sm btn-outline" disabled>◀</button>
            <span id="page-info">1 / 1</span>
            <button id="next-page" class="btn btn-sm btn-outline" disabled>▶</button>
        </div>
    </div>
</div>
```

## スクロールバー完璧設定法

### 核心となる設定思想
**値行のみをスクロール対象とし、ヘッダーとページネーションは固定表示する**

#### 1. ダイアログ全体のスクロール無効化
```css
.modal-large .modal-body {
    overflow: hidden; /* ダイアログ全体のスクロールを無効化 */
    padding: 12px;
}
```

#### 2. テーブルコンテナの固定高さ設定
```css
.file-list-container {
    height: 500px; /* 固定高さでダイアログ内スクロール制御 */
    display: flex;
    flex-direction: column;
    flex: 1;
}
```

#### 3. tbodyのスクロール制御（★最重要★）
```css
.file-table tbody {
    display: block;
    overflow-y: scroll; /* 強制的にスクロールバーを表示 */
    overflow-x: hidden;
    flex: 1;
    width: calc(100% - 2px); /* スクロールバー分の調整 */
    height: 400px; /* または適切な固定高さ */
    position: relative;
    /* スクロールバーを表の右端に固定 */
    scrollbar-width: thin;
    scrollbar-color: #c1c1c1 #f1f1f1;
}
```

#### 4. ヘッダーとデータ行の幅完全一致
```css
.file-table thead {
    display: table;
    width: 100%;
    table-layout: fixed;
}

.file-table tbody tr {
    display: table;
    width: 100%; /* ヘッダーと完全一致 */
    table-layout: fixed;
    box-sizing: border-box;
}
```

### 成功のポイント
- **overflow-y: scroll**（autoではなくscroll）で常にスクロールバー表示
- **width: calc(100% - 2px)**でスクロールバー分を考慮
- **固定高さ**でコンテナを制御
- **table-layout: fixed**で正確な列幅制御

## CSS仕様

### 1. テーブル基本構造
```css
.file-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 12px;
    table-layout: fixed;
    display: flex;
    flex-direction: column;
    height: 100%;
    background: white;
}
```

### 2. ヘッダー仕様（最重要）
```css
.file-table thead {
    display: table;
    width: 100%;
    table-layout: fixed;
    background: #f8f9fa;
    position: sticky;
    top: 0;
    z-index: 10;
}

.file-table thead th {
    background: #f8f9fa;
    padding: 6px 8px;           /* 標準パディング */
    text-align: center;         /* センタリング統一 */
    border-bottom: 1px solid #ddd;
    font-weight: 600;
    position: sticky;
    top: 0;
    z-index: 10;
    font-size: 10px;           /* 標準フォントサイズ */
    box-shadow: 0 1px 2px rgba(0,0,0,0.1);
    border-right: 1px solid #ddd;
    user-select: none;
    color: #495057;            /* 標準色 */
}
```

### 3. データ行仕様
```css
.file-table tbody {
    display: block;
    overflow-y: auto;
    flex: 1;
    width: 100%;
}

.file-table tbody tr {
    display: table;
    width: 100%;
    table-layout: fixed;
    border-bottom: 1px solid #eee;
    cursor: pointer;           /* 行選択可能な場合 */
}

.file-table tbody td {
    padding: 4px 8px;          /* 標準パディング */
    border-bottom: 1px solid #eee;
    vertical-align: top;       /* 上揃え統一 */
    line-height: 1.3;          /* 標準行高 */
    font-size: 11px;           /* 標準フォントサイズ */
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}
```

### 4. 標準カラム幅パターン

#### パターンA: ファイル管理（4カラム）
```css
/* ファイル名 | 頁数 | ステータス | 操作 */
.file-table th:nth-child(1) { width: calc(100% - 220px); }  /* ファイル名: 残り全幅 */
.file-table th:nth-child(2) { width: 50px; }                /* 頁数: 固定 */
.file-table th:nth-child(3) { width: 90px; }                /* ステータス: 拡張 */
.file-table th:nth-child(4) { width: 80px; }                /* 操作: 縮小 */
```

#### パターンB: データ選択（5カラム）
```css
/* チェック | ファイル名 | 頁数 | ステータス | サイズ */
.file-table th:nth-child(1) { width: 40px; }                    /* チェック: 固定 */
.file-table th:nth-child(2) { width: calc(100% - 270px); }      /* ファイル名: 残り全幅 */
.file-table th:nth-child(3) { width: 50px; }                    /* 頁数: 固定 */
.file-table th:nth-child(4) { width: 90px; }                    /* ステータス: 拡張 */
.file-table th:nth-child(5) { width: 90px; }                    /* サイズ: 統一 */
```

### 5. テキスト配置規則
```css
/* ヘッダー: 全センタリング */
.file-table th { text-align: center; }

/* データ: カラムの種類により分類 */
.file-table td:nth-child(1) { text-align: left; }    /* ファイル名: 左寄せ */
.file-table td:nth-child(2) { text-align: center; }  /* 頁数: センタリング */
.file-table td:nth-child(3) { text-align: center; }  /* ステータス: センタリング */
.file-table td:nth-child(4) { text-align: right; }   /* サイズ: 右寄せ */
.file-table td:nth-child(4) { text-align: center; }  /* 操作: センタリング */
```

### 6. ページネーション仕様
```css
.pagination-container {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 2px 6px;
    border-top: 1px solid #e9ecef;
    background: #f8f9fa;
    flex-shrink: 0;
    margin-top: 0;
    border-radius: 0 0 4px 4px;
    min-height: 32px;
}

.pagination-info {
    display: flex;
    align-items: center;
    gap: 4px;
    font-size: 12px;
    color: #666;
    margin-left: 2px;
}

.pagination-nav button {
    min-width: 32px !important;
    height: 32px !important;
    padding: 0 !important;
    font-size: 12px !important;
    border: 1px solid #ddd !important;
    background: white !important;
    cursor: pointer;
    border-radius: 4px !important;
    transition: all 0.2s ease;
}
```

### 7. スクロールバー調整
```css
.file-table tbody {
    width: calc(100% - 8px);  /* スクロールバー分のマージン */
    margin-right: 8px;        /* スクロールバーを右端に固定 */
}

.file-table tbody::-webkit-scrollbar {
    width: 8px;
}

.file-table tbody::-webkit-scrollbar-track {
    background: #f1f1f1;
    border-radius: 4px;
}

.file-table tbody::-webkit-scrollbar-thumb {
    background: #c1c1c1;
    border-radius: 4px;
}
```

## ステータスバッジ統一仕様

### 基本スタイル
```css
.status-badge {
    padding: 2px 8px;
    border-radius: 12px;
    font-size: 10px;
    font-weight: 500;
    text-align: center;
    display: inline-block;
    min-width: 60px;
}
```

### ステータス別色分け
```css
.status-未処理, .status-pending_processing { 
    background: #e3f2fd; color: #1976d2; border: 1px solid #bbdefb; 
}

.status-処理中, .status-processing { 
    background: #fff3e0; color: #f57c00; border: 1px solid #ffcc02; 
}

.status-未整形, .status-text_extracted { 
    background: #f3e5f5; color: #7b1fa2; border: 1px solid #ce93d8; 
}

.status-未ベクトル化, .status-text_refined { 
    background: #e8f5e8; color: #388e3c; border: 1px solid #a5d6a7; 
}

.status-処理完了, .status-processed { 
    background: #e8f5e8; color: #2e7d32; border: 1px solid #81c784; 
}

.status-エラー, .status-error { 
    background: #ffebee; color: #d32f2f; border: 1px solid #ef9a9a; 
}
```

## 使用例・実装手順

### 1. 新しい表を作成する場合
1. 上記HTMLテンプレートをコピー
2. カラム数に応じて`th`要素を調整
3. 標準カラム幅パターンを適用
4. ページネーションHTMLを追加

### 2. 既存の表を標準化する場合
1. ヘッダー仕様（`font-size: 10px`等）を適用
2. データ行仕様（`font-size: 11px`等）を適用
3. カラム幅を標準パターンに調整
4. テキスト配置を規則に従って設定

### 3. JavaScript連携
- ページネーション機能の実装
- フィルタリング機能の実装
- 行選択・ダブルクリック処理
- データの動的表示

## 品質チェックリスト

- [ ] ヘッダーフォントサイズ: `10px`
- [ ] データフォントサイズ: `11px`
- [ ] ヘッダーパディング: `6px 8px`
- [ ] データパディング: `4px 8px`
- [ ] ヘッダー配置: 全て`center`
- [ ] データ配置: カラム種類に応じた適切な配置
- [ ] スクロールバー位置: 表の右端に固定
- [ ] ページネーション: データ登録仕様と統一
- [ ] ステータスバッジ: 統一色分け適用
- [ ] カラム幅: 標準パターンに準拠

## 今後の拡張

この標準仕様は今後のシステム拡張時にも適用し、全ての表で一貫性を保つことを目的としています。新しい要件が発生した場合は、この仕様を更新し、既存の表にも反映させてください。

---

**更新日**: 2024-12-27  
**適用範囲**: RAGシステム全体（データ登録、ファイル管理、OCR比較、チャット等）  
**標準化レベル**: 100% 完全統一