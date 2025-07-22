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

### ペイン分割構造
```css
/* 上下分割レイアウト */
#ingest-container {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 2em);
}

/* 上ペイン: 設定・操作 */
#pane-top {
  flex: 0 0 auto;
  background: rgba(255, 255, 255, 0.3);
  backdrop-filter: blur(15px);
}

/* 下ペイン: ログ・編集 */
#pane-bottom {
  flex: 1 1 auto;
  display: flex;
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

### SSE（Server-Sent Events）活用
```javascript
// 進捗更新の効率的処理
if (d.is_progress_update && d.page_id) {
  const existingProgress = section.querySelector(`[data-page-id="${d.page_id}"]`);
  if (existingProgress) {
    // 既存行を更新（新規作成を避ける）
    existingProgress.textContent = step;
  } else {
    // 新規進捗行作成
    const progressLine = createLine(step);
    progressLine.setAttribute('data-page-id', d.page_id);
    section.appendChild(progressLine);
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