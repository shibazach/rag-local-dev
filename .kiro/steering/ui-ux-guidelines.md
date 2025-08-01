---
inclusion: always
---

# UI/UX設計ガイドライン（新アーキテクチャ対応）

## デザイン哲学

### 基本方針
- **日本語ユーザー最優先**: 日本語UI、直感的な操作性
- **リアルタイム性**: SSE（Server-Sent Events）による処理進捗の即座な可視化
- **エラー耐性**: 処理中断・復旧への配慮
- **アクセシビリティ**: 視覚的・操作的配慮
- **セキュリティ**: API分離による安全なデータ取得

### 視覚デザイン
- **モダンUI**: CSS Grid/Flexboxによるレスポンシブデザイン
- **カラーパレット**: 落ち着いた色調、高コントラスト
- **タイポグラフィ**: 日本語フォント最適化
- **アイコン**: 絵文字活用による直感的表現
- **コンポーネント化**: 再利用可能なUIコンポーネント設計

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

### JavaScript モジュール構成（new/static/js/対応）
新アーキテクチャでは以下の機能別モジュールで構成されています：

- **main.js**: 共通初期化・ユーティリティ関数
- **header.js**: ヘッダーナビゲーション制御
- **data_registration.js**: データ登録画面制御
- **files.js**: ファイル管理画面制御
- **chat_main.js**: チャット機能メイン処理
- **chat_layout.js**: チャットレイアウト制御
- **chat_resize.js**: チャットパネルリサイズ
- **chat_search.js**: チャット検索機能
- **chat_history.js**: チャット履歴管理
- **ocr_comparison.js**: OCR比較検証機能
- **sse_client.js**: SSE（Server-Sent Events）統一クライアント
- **file_selection.js**: ファイル選択・フィルタリング

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