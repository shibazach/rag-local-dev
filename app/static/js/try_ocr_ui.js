// app/static/js/try_ocr_ui.js

class TryOcrUI {
  constructor() {
    this.isResizing = false;
    this.processingStartTime = null;
    this.processingTimerInterval = null;
    
    // 新規追加: ログ関連要素
    this.processingStatus = document.getElementById('processing-status');
    this.statusMessage = document.querySelector('.status-message');
    this.statusTimer = document.querySelector('.status-timer');
    this.logContent = document.getElementById('log-content');
    this.startTime = null;
  }

  // 処理中オーバーレイの表示/非表示
  showProcessing() {
    const processingOverlay = document.getElementById("processing-overlay");
    processingOverlay.classList.add("show");
    this.startProcessingTimer();
  }

  hideProcessing() {
    const processingOverlay = document.getElementById("processing-overlay");
    processingOverlay.classList.remove("show");
    this.stopProcessingTimer();
  }

  // 処理中オーバーレイを強制的に隠す
  forceHideOverlay() {
    const overlay = document.getElementById('processing-overlay');
    if (overlay) {
      overlay.classList.remove('show');
      overlay.style.display = 'none';
      overlay.style.visibility = 'hidden';
      overlay.style.opacity = '0';
    }
  }

  // 処理進捗の更新
  updateProcessingProgress(message) {
    console.log('🔄 進捗更新:', message);
    
    // 既存のオーバーレイ更新
    const processingMessage = document.getElementById('processing-message');
    if (processingMessage) {
      if (this.processingStartTime) {
        const elapsed = Math.floor((Date.now() - this.processingStartTime) / 1000);
        processingMessage.textContent = `${message} (${elapsed}秒経過)`;
      } else {
        processingMessage.textContent = message;
      }
    }
    
    // 新規追加: ステータス表示とログ更新
    if (this.statusMessage) {
      this.statusMessage.textContent = message;
    }
    this.addLogMessage(`🔄 ${message}`, 'progress');
  }

  // 処理ログにメッセージを追加
  addLogMessage(message, type = 'info') {
    if (!this.logContent) return;
    
    const timestamp = new Date().toLocaleTimeString();
    const logEntry = document.createElement('div');
    logEntry.className = `log-entry log-${type}`;
    logEntry.innerHTML = `<span class="log-time">[${timestamp}]</span> ${message}`;
    
    this.logContent.appendChild(logEntry);
    this.logContent.scrollTop = this.logContent.scrollHeight;
  }

  // 処理開始時の表示
  showProcessingStatus() {
    this.startTime = Date.now();
    if (this.processingStatus) {
      this.processingStatus.style.display = 'flex';
    }
    this.addLogMessage('🚀 OCR処理を開始しました', 'info');
    this.startStatusTimer();
  }

  // 処理完了時の非表示
  hideProcessingStatus() {
    if (this.processingTimerInterval) {
      clearInterval(this.processingTimerInterval);
      this.processingTimerInterval = null;
    }
    
    const totalTime = this.startTime ? Math.floor((Date.now() - this.startTime) / 1000) : 0;
    const timeStr = totalTime >= 60 ? `${Math.floor(totalTime/60)}分${totalTime%60}秒` : `${totalTime}秒`;
    this.addLogMessage(`🏁 全処理完了 (総処理時間: ${timeStr})`, 'complete');
    
    if (this.processingStatus) {
      this.processingStatus.style.display = 'none';
    }
    this.startTime = null;
  }

  // ステータスタイマー開始
  startStatusTimer() {
    this.processingTimerInterval = setInterval(() => {
      if (this.startTime && this.statusTimer) {
        const elapsed = Math.floor((Date.now() - this.startTime) / 1000);
        const timeStr = elapsed >= 60 ? `${Math.floor(elapsed/60)}分${elapsed%60}秒` : `${elapsed}秒`;
        this.statusTimer.textContent = `処理時間: ${timeStr}`;
      }
    }, 1000);
  }

  // 処理タイマーの開始
  startProcessingTimer() {
    this.processingStartTime = Date.now();
    this.updateProcessingProgress('OCR処理中…');
    
    // 1秒間隔で経過時間を更新
    this.processingTimerInterval = setInterval(() => {
      this.updateProcessingProgress('OCR処理中…');
    }, 1000);
  }

  // 処理タイマーの停止
  stopProcessingTimer() {
    this.processingStartTime = null;
    if (this.processingTimerInterval) {
      clearInterval(this.processingTimerInterval);
      this.processingTimerInterval = null;
    }
  }

  // リサイズ機能の初期化
  initializeResize() {
    const splitter = document.getElementById("splitter");
    const topSplitter = document.getElementById("top-splitter");
    const verticalSplitter = document.getElementById("vertical-splitter");

    // 横分割リサイズ（下ペイン）
    if (splitter) {
      splitter.addEventListener("mousedown", (e) => {
        this.isResizing = true;
        this.handleMouseMove = this.handleMouseMove.bind(this);
        this.handleMouseUp = this.handleMouseUp.bind(this);
        document.addEventListener("mousemove", this.handleMouseMove);
        document.addEventListener("mouseup", this.handleMouseUp);
        e.preventDefault();
      });
    }

    // 上ペインの横分割リサイズ
    if (topSplitter) {
      topSplitter.addEventListener("mousedown", (e) => {
        this.isTopResizing = true;
        this.handleTopMouseMove = this.handleTopMouseMove.bind(this);
        this.handleTopMouseUp = this.handleTopMouseUp.bind(this);
        document.addEventListener("mousemove", this.handleTopMouseMove);
        document.addEventListener("mouseup", this.handleTopMouseUp);
        e.preventDefault();
      });
    }

    // 上下分割リサイズ
    if (verticalSplitter) {
      verticalSplitter.addEventListener("mousedown", (e) => {
        this.isVerticalResizing = true;
        this.handleVerticalMouseMove = this.handleVerticalMouseMove.bind(this);
        this.handleVerticalMouseUp = this.handleVerticalMouseUp.bind(this);
        document.addEventListener("mousemove", this.handleVerticalMouseMove);
        document.addEventListener("mouseup", this.handleVerticalMouseUp);
        e.preventDefault();
      });
    }
  }

  // 横分割リサイズのマウス移動処理
  handleMouseMove(e) {
    if (!this.isResizing) return;
    
    const container = document.getElementById("pane-bottom");
    const containerRect = container.getBoundingClientRect();
    const containerWidth = containerRect.width;
    const relativeX = e.clientX - containerRect.left;
    
    const newWidth = Math.max(200, Math.min(containerWidth - 200, relativeX));
    const percentage = (newWidth / containerWidth) * 100;
    
    const resultsPane = document.getElementById("results-pane");
    const pdfPane = document.getElementById("pdf-pane");
    
    resultsPane.style.flex = `0 0 ${percentage}%`;
    pdfPane.style.flex = `1 1 auto`;
    
    e.preventDefault();
  }

  // 横分割リサイズのマウスアップ処理
  handleMouseUp(e) {
    this.isResizing = false;
    document.removeEventListener("mousemove", this.handleMouseMove);
    document.removeEventListener("mouseup", this.handleMouseUp);
    e.preventDefault();
  }

  // 上ペインの横分割リサイズ処理
  handleTopMouseMove(e) {
    if (!this.isTopResizing) return;
    
    const container = document.getElementById("pane-top");
    const containerRect = container.getBoundingClientRect();
    const containerWidth = containerRect.width;
    const relativeX = e.clientX - containerRect.left;
    
    const newWidth = Math.max(200, Math.min(containerWidth - 200, relativeX));
    const percentage = (newWidth / containerWidth) * 100;
    
    const topLeft = document.getElementById("top-left");
    const topRight = document.getElementById("top-right");
    
    topLeft.style.flex = `0 0 ${percentage}%`;
    topRight.style.flex = `1 1 auto`;
    
    e.preventDefault();
  }

  // 上ペインの横分割リサイズのマウスアップ処理
  handleTopMouseUp(e) {
    this.isTopResizing = false;
    document.removeEventListener("mousemove", this.handleTopMouseMove);
    document.removeEventListener("mouseup", this.handleTopMouseUp);
    e.preventDefault();
  }

  // 上下分割リサイズ処理
  handleVerticalMouseMove(e) {
    if (!this.isVerticalResizing) return;
    
    const container = document.getElementById("try-ocr-container");
    const containerRect = container.getBoundingClientRect();
    const containerHeight = containerRect.height;
    const relativeY = e.clientY - containerRect.top;
    
    const newHeight = Math.max(150, Math.min(containerHeight - 150, relativeY));
    const percentage = (newHeight / containerHeight) * 100;
    
    const paneTop = document.getElementById("pane-top");
    const paneBottom = document.getElementById("pane-bottom");
    
    paneTop.style.flex = `0 0 ${percentage}%`;
    paneBottom.style.flex = `1 1 auto`;
    
    e.preventDefault();
  }

  // 上下分割リサイズのマウスアップ処理
  handleVerticalMouseUp(e) {
    this.isVerticalResizing = false;
    document.removeEventListener("mousemove", this.handleVerticalMouseMove);
    document.removeEventListener("mouseup", this.handleVerticalMouseUp);
    e.preventDefault();
  }

  // 結果表示
  displayResult(result) {
    console.log('📊 OCR結果を表示:', result);
    
    // 処理時間の表示用文字列を作成
    const processingTime = result.processing_time ? `${Math.floor(result.processing_time)}秒` : '不明';
    const engineName = result.engine_name || 'Unknown';
    
    // ログに成功メッセージを追加
    this.addLogMessage(`✅ ${engineName}: 処理完了 (${processingTime})`, 'success');
    
    // 展開可能な詳細結果をログに追加
    const details = this.createExpandableResult(result);
    this.logContent.appendChild(details);
    this.logContent.scrollTop = this.logContent.scrollHeight;
    
    // 既存の結果表示処理
    this.showResults(result);
  }

  // 展開可能な結果詳細を作成
  createExpandableResult(result) {
    const details = document.createElement('details');
    details.className = 'result-details';
    
    const summary = document.createElement('summary');
    summary.innerHTML = `▶ ${result.engine_name || 'Unknown'} 詳細結果`;
    details.appendChild(summary);
    
    const content = document.createElement('div');
    content.className = 'result-content';
    
    // 信頼度の表示（存在する場合）
    const confidenceStr = result.confidence ? `${result.confidence}%` : '不明';
    const processingTimeStr = result.processing_time ? `${result.processing_time.toFixed(2)}秒` : '不明';
    const textLength = (result.text || '').length;
    
    content.innerHTML = `
      <div><strong>信頼度:</strong> ${confidenceStr}</div>
      <div><strong>処理時間:</strong> ${processingTimeStr}</div>
      <div><strong>文字数:</strong> ${textLength}文字</div>
      <div><strong>認識テキスト:</strong></div>
      <pre class="ocr-text">${result.text || 'テキストが抽出されませんでした'}</pre>
    `;
    details.appendChild(content);
    
    // 展開状態の切り替えアイコン更新
    details.addEventListener('toggle', () => {
      summary.innerHTML = details.open ? 
        `▼ ${result.engine_name || 'Unknown'} 詳細結果` : 
        `▶ ${result.engine_name || 'Unknown'} 詳細結果`;
    });
    
    return details;
  }

  // 既存の結果表示処理（結果セクション用）
  showResults(result) {
    const resultsContainer = document.getElementById("results-container");
    const card = document.createElement("div");
    card.className = "result-card";

    const header = document.createElement("div");
    header.className = "result-header";
    
    // ページ番号の表示を追加（0は全ページ、-1は全ページ処理中）
    const pageDisplay = result.page_num === -1 ? '（全ページ）' :
      result.page_num === 0 ? '（1ページ目）' :
      `（${result.page_num}ページ目）`;
    
    header.textContent = `${result.engine_name || 'Unknown'} ${pageDisplay}`;

    const content = document.createElement("div");
    content.className = "result-content";

    const textDiv = document.createElement("div");
    textDiv.className = "result-text";
    textDiv.textContent = result.text || "テキストが抽出されませんでした";

    const statsDiv = document.createElement("div");
    statsDiv.className = "result-stats";
    statsDiv.innerHTML = `
      処理時間: ${result.processing_time?.toFixed(2) || 'N/A'}秒 | 
      文字数: ${(result.text || '').length}文字
    `;

    content.appendChild(textDiv);
    content.appendChild(statsDiv);
    card.appendChild(header);
    card.appendChild(content);

    resultsContainer.appendChild(card);
    resultsContainer.scrollTop = resultsContainer.scrollHeight;
  }

  // エラー表示
  displayError(message) {
    console.log('❌ エラーを表示:', message);
    
    // ログにエラーメッセージを追加
    this.addLogMessage(`❌ ${message}`, 'error');
    
    // 既存のエラー表示処理
    this.showResults({
      engine_name: "エラー",
      text: message,
      processing_time: 0,
      page_num: -1
    });
  }

  // 結果クリア
  clearResults() {
    const resultsContainer = document.getElementById("results-container");
    resultsContainer.innerHTML = '<p style="color:#888; text-align:center; margin-top:2em;">OCRエンジンとファイルを選択して「OCR実行」ボタンを押してください</p>';
  }

  // 初期化処理
  initialize() {
    // リサイズ機能の初期化
    this.initializeResize();

    // 複数のタイミングでオーバーレイを確実に隠す
    this.forceHideOverlay();
    setTimeout(() => this.forceHideOverlay(), 1);
    setTimeout(() => this.forceHideOverlay(), 10);
    setTimeout(() => this.forceHideOverlay(), 50);
    setTimeout(() => this.forceHideOverlay(), 100);
    setTimeout(() => this.forceHideOverlay(), 200);
    setTimeout(() => this.forceHideOverlay(), 500);
    setTimeout(() => this.forceHideOverlay(), 1000);

    // ウィンドウ読み込み完了時にも隠す
    window.addEventListener('load', () => this.forceHideOverlay());

    // ページ表示時にも隠す
    document.addEventListener('visibilitychange', () => {
      if (!document.hidden) {
        this.forceHideOverlay();
      }
    });
  }
}

// グローバルに公開
window.TryOcrUI = TryOcrUI;