---
inclusion: always
---

# UI/UX設計ガイドライン

## デザイン哲学

### 基本方針
- **日本語ユーザー最優先**: 日本語UI、直感的な操作性
- **リアルタイム性**: 処理進捗の即座な可視化
- **エラー耐性**: 処理中断・復旧への配慮
- **アクセシビリティ**: 視覚的・操作的配慮

### 視覚デザイン
- **グラスモーフィズム**: 半透明・ブラー効果による現代的UI
- **カラーパレット**: 落ち着いた色調、高コントラスト
- **タイポグラフィ**: 日本語フォント最適化
- **アイコン**: 絵文字活用による直感的表現

## レイアウト設計

### ペイン分割構造（3パターン対応）
```css
/* 基本コンテナ構造 */
#app-container {
  height: calc(100vh - 2em);
  display: flex;
  flex-direction: column;
}

/* パターン1: 上部設定、下部に処理ログとPDFの横分割 */
.layout-pattern1 #top-container {
  flex: 0 0 200px;
  display: flex;
}

.layout-pattern1 #bottom-container {
  flex: 1;
  display: flex;
}

/* パターン2: 左側に設定と処理ログの縦分割、右側にPDF */
.layout-pattern2 #left-container {
  flex: 0 0 200px;
  display: flex;
}

.layout-pattern2 #pdf-panel {
  flex: 1;
  display: flex;
}

/* PDFプレビューなし: 縦2分割（設定+ログ） */
.layout-no-preview #top-container {
  flex: 0 0 220px;
}

.layout-no-preview #pdf-panel {
  display: none;
}
```

### レスポンシブ対応
- モバイル端末での縦画面最適化
- タブレット端末での横画面活用
- デスクトップでの大画面活用

## インタラクション設計

### 処理状態管理
```javascript
// 処理中のナビゲーション制御
function startProcessing() {
  processingInProgress = true;
  document.body.classList.add('processing-in-progress');
  
  // ページ離脱警告
  window.addEventListener('beforeunload', handleBeforeUnload);
}

function endProcessing() {
  processingInProgress = false;
  document.body.classList.remove('processing-in-progress');
  
  // イベントリスナー削除
  window.removeEventListener('beforeunload', handleBeforeUnload);
}
```

### モーダル設計
- **OCR設定モーダル**: 動的設定項目生成
- **プリセット管理モーダル**: CRUD操作対応
- **確認ダイアログ**: 重要操作の確認

## リアルタイム更新

### JavaScript モジュール構成
現在のIngestシステムは以下の機能別モジュールで構成されています：

- **ingest_main.js**: メイン統合・初期化処理
- **ingest_layout.js**: レイアウト切り替え機能（3パターン対応）
- **ingest_resize.js**: パネルリサイズ機能
- **ingest_sse.js**: SSE（Server-Sent Events）処理
- **ingest_processing.js**: 処理実行・フォーム制御
- **ingest_ocr.js**: OCR設定・プリセット管理

### SSE（Server-Sent Events）活用
```javascript
// IngestSSE クラスによる進捗更新の効率的処理
class IngestSSE {
  handleMessage(evt) {
    const d = JSON.parse(evt.data);
    
    // 進捗更新の場合は既存行を上書き
    if (d.is_progress_update && d.page_id) {
      const existingProgress = section.querySelector(`[data-page-id="${d.page_id}"]`);
      if (existingProgress) {
        existingProgress.textContent = step;
      } else {
        const progressLine = this.createLine(step);
        progressLine.setAttribute('data-page-id', d.page_id);
        section.appendChild(progressLine);
      }
    }
  }
}
```

### 自動スクロール制御
```javascript
function scrollBottom(el) {
  const threshold = 32;
  const distance = el.scrollHeight - el.scrollTop - el.clientHeight;
  // ユーザーが手動スクロール中は自動スクロールを停止
  if (distance <= threshold) el.scrollTop = el.scrollHeight;
}
```

## フォーム設計

### 設定項目の構造化
```html
<!-- 論理的なグループ化 -->
<div class="form-section">
  <label for="refine-prompt">📝 整形プロンプト：</label>
  <select id="refine-prompt" name="refine_prompt_key">
    <!-- 動的オプション生成 -->
  </select>
  <button type="button" id="prompt-edit-btn">確認</button>
</div>
```

### バリデーション
- **リアルタイム検証**: 入力時即座チェック
- **視覚的フィードバック**: エラー状態の明確表示
- **日本語エラーメッセージ**: 分かりやすい説明

## アクセシビリティ

### キーボード操作
- Tab順序の論理的設定
- Enterキーでの操作実行
- Escapeキーでのモーダル閉じ

### スクリーンリーダー対応
- 適切なaria-label設定
- role属性の活用
- 構造的なHTML記述

### 視覚的配慮
- 高コントラスト対応
- フォントサイズ調整可能
- カラーブラインド対応

## エラーハンドリング

### ユーザーフレンドリーなエラー表示
```javascript
// 処理エラー時の適切な通知
window.onIngestError = function(errorInfo) {
  showNotification({
    type: 'error',
    title: '処理エラーが発生しました',
    message: errorInfo.userMessage,
    actions: ['再試行', 'キャンセル']
  });
};
```

### 復旧支援
- 処理中断からの復旧ガイド
- 設定保存・復元機能
- ログ出力による問題特定支援