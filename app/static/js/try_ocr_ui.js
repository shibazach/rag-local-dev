// app/static/js/try_ocr_ui.js

class TryOcrUI {
  constructor() {
    this.isResizing = false;
    
    // タイマー管理の統一
    this.processingStartTime = null;
    this.overlayTimerInterval = null;  // オーバーレイ用タイマー
    this.statusTimerInterval = null;   // ステータス表示用タイマー
    
    // DOM要素は初期化時に取得（遅延初期化）
    this.processingStatus = null;
    this.statusMessage = null;
    this.statusTimer = null;
  }

  // DOM要素の遅延初期化
  initializeDOMElements() {
    if (!this.processingStatus) {
      this.processingStatus = document.getElementById('processing-status');
    }
    if (!this.statusMessage) {
      this.statusMessage = document.querySelector('.status-message');
    }
    if (!this.statusTimer) {
      this.statusTimer = document.querySelector('.status-timer');
    }
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
    
    // DOM要素の初期化を確実に行う
    this.initializeDOMElements();
    
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
    
    // ステータス表示の更新
    if (this.statusMessage) {
      this.statusMessage.textContent = message;
    }
  }



  // 処理開始時の表示
  showProcessingStatus() {
    console.log('🚀 処理ステータス表示開始');
    
    // DOM要素の初期化を確実に行う
    this.initializeDOMElements();
    
    this.processingStartTime = Date.now();
    
    // 結果エリアから初期メッセージを削除（処理中は表示しない）
    const resultsContainer = document.getElementById("results-container");
    if (resultsContainer) {
      const initialMessage = resultsContainer.querySelector('p');
      if (initialMessage && initialMessage.textContent.includes('OCR実行')) {
        initialMessage.remove();
      }
    }
    
    if (this.processingStatus) {
      this.processingStatus.style.display = 'flex';
    }
    this.startStatusTimer();
  }

  // 処理完了時の非表示
  hideProcessingStatus() {
    // DOM要素の初期化を確実に行う
    this.initializeDOMElements();
    
    // ステータス用タイマーを停止
    if (this.statusTimerInterval) {
      clearInterval(this.statusTimerInterval);
      this.statusTimerInterval = null;
    }
    
    if (this.processingStatus) {
      this.processingStatus.style.display = 'none';
    }
    this.processingStartTime = null;
  }

  // ステータスタイマー開始
  startStatusTimer() {
    this.statusTimerInterval = setInterval(() => {
      if (this.processingStartTime && this.statusTimer) {
        const elapsed = Math.floor((Date.now() - this.processingStartTime) / 1000);
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
    this.overlayTimerInterval = setInterval(() => {
      this.updateProcessingProgress('OCR処理中…');
    }, 1000);
  }

  // 処理タイマーの停止
  stopProcessingTimer() {
    if (this.overlayTimerInterval) {
      clearInterval(this.overlayTimerInterval);
      this.overlayTimerInterval = null;
    }
  }

  // リサイズ機能の初期化
  initializeResize() {
    // 既存のイベントリスナーをクリア
    this.cleanupResizeListeners();
    
    const splitter = document.getElementById("splitter");
    const topSplitter = document.getElementById("top-splitter");
    const verticalSplitter = document.getElementById("vertical-splitter");

    // 横分割リサイズ（下ペイン）
    if (splitter) {
      this.splitterMouseDown = (e) => {
        if (this.isResizing || this.isTopResizing || this.isVerticalResizing) return;
        
        this.isResizing = true;
        this.startX = e.clientX;
        this.startY = e.clientY;
        
        // イベントリスナーを追加
        document.addEventListener("mousemove", this.handleMouseMove, { passive: false });
        document.addEventListener("mouseup", this.handleMouseUp, { passive: false });
        document.body.style.cursor = "col-resize";
        document.body.style.userSelect = "none";
        
        e.preventDefault();
        e.stopPropagation();
      };
      splitter.addEventListener("mousedown", this.splitterMouseDown);
    }

    // 上ペインの横分割リサイズ
    if (topSplitter) {
      this.topSplitterMouseDown = (e) => {
        if (this.isResizing || this.isTopResizing || this.isVerticalResizing) return;
        
        this.isTopResizing = true;
        this.startX = e.clientX;
        this.startY = e.clientY;
        
        document.addEventListener("mousemove", this.handleTopMouseMove, { passive: false });
        document.addEventListener("mouseup", this.handleTopMouseUp, { passive: false });
        document.body.style.cursor = "col-resize";
        document.body.style.userSelect = "none";
        
        e.preventDefault();
        e.stopPropagation();
      };
      topSplitter.addEventListener("mousedown", this.topSplitterMouseDown);
    }

    // 上下分割リサイズ
    if (verticalSplitter) {
      this.verticalSplitterMouseDown = (e) => {
        if (this.isResizing || this.isTopResizing || this.isVerticalResizing) return;
        
        this.isVerticalResizing = true;
        this.startX = e.clientX;
        this.startY = e.clientY;
        
        document.addEventListener("mousemove", this.handleVerticalMouseMove, { passive: false });
        document.addEventListener("mouseup", this.handleVerticalMouseUp, { passive: false });
        document.body.style.cursor = "row-resize";
        document.body.style.userSelect = "none";
        
        e.preventDefault();
        e.stopPropagation();
      };
      verticalSplitter.addEventListener("mousedown", this.verticalSplitterMouseDown);
    }
  }

  // リサイズリスナーのクリーンアップ
  cleanupResizeListeners() {
    // 既存のイベントリスナーを削除
    if (this.handleMouseMove) {
      document.removeEventListener("mousemove", this.handleMouseMove);
    }
    if (this.handleMouseUp) {
      document.removeEventListener("mouseup", this.handleMouseUp);
    }
    if (this.handleTopMouseMove) {
      document.removeEventListener("mousemove", this.handleTopMouseMove);
    }
    if (this.handleTopMouseUp) {
      document.removeEventListener("mouseup", this.handleTopMouseUp);
    }
    if (this.handleVerticalMouseMove) {
      document.removeEventListener("mousemove", this.handleVerticalMouseMove);
    }
    if (this.handleVerticalMouseUp) {
      document.removeEventListener("mouseup", this.handleVerticalMouseUp);
    }
    
    // カーソルとユーザー選択をリセット
    document.body.style.cursor = "";
    document.body.style.userSelect = "";
    
    // フラグをリセット
    this.isResizing = false;
    this.isTopResizing = false;
    this.isVerticalResizing = false;
  }

  // 横分割リサイズのマウス移動処理
  handleMouseMove = (e) => {
    if (!this.isResizing) return;
    
    try {
      const container = document.getElementById("pane-bottom");
      if (!container) return;
      
      const containerRect = container.getBoundingClientRect();
      const containerWidth = containerRect.width;
      const relativeX = e.clientX - containerRect.left;
      
      const newWidth = Math.max(200, Math.min(containerWidth - 200, relativeX));
      const percentage = (newWidth / containerWidth) * 100;
      
      const resultsPane = document.getElementById("results-pane");
      const pdfPane = document.getElementById("pdf-pane");
      
      if (resultsPane && pdfPane) {
        resultsPane.style.flex = `0 0 ${percentage}%`;
        pdfPane.style.flex = `1 1 auto`;
      }
    } catch (error) {
      console.error('リサイズエラー:', error);
    }
    
    e.preventDefault();
  }

  // 横分割リサイズのマウスアップ処理
  handleMouseUp = (e) => {
    this.isResizing = false;
    document.removeEventListener("mousemove", this.handleMouseMove);
    document.removeEventListener("mouseup", this.handleMouseUp);
    document.body.style.cursor = "";
    document.body.style.userSelect = "";
    e.preventDefault();
  }

  // 上ペインの横分割リサイズ処理
  handleTopMouseMove = (e) => {
    if (!this.isTopResizing) return;
    
    try {
      const container = document.getElementById("pane-top");
      if (!container) return;
      
      const containerRect = container.getBoundingClientRect();
      const containerWidth = containerRect.width;
      const relativeX = e.clientX - containerRect.left;
      
      const newWidth = Math.max(200, Math.min(containerWidth - 200, relativeX));
      const percentage = (newWidth / containerWidth) * 100;
      
      const topLeft = document.getElementById("top-left");
      const topRight = document.getElementById("top-right");
      
      if (topLeft && topRight) {
        topLeft.style.flex = `0 0 ${percentage}%`;
        topRight.style.flex = `1 1 auto`;
      }
    } catch (error) {
      console.error('上ペインリサイズエラー:', error);
    }
    
    e.preventDefault();
  }

  // 上ペインの横分割リサイズのマウスアップ処理
  handleTopMouseUp = (e) => {
    this.isTopResizing = false;
    document.removeEventListener("mousemove", this.handleTopMouseMove);
    document.removeEventListener("mouseup", this.handleTopMouseUp);
    document.body.style.cursor = "";
    document.body.style.userSelect = "";
    e.preventDefault();
  }

  // 上下分割リサイズ処理
  handleVerticalMouseMove = (e) => {
    if (!this.isVerticalResizing) return;
    
    try {
      const container = document.getElementById("try-ocr-container");
      if (!container) return;
      
      const containerRect = container.getBoundingClientRect();
      const containerHeight = containerRect.height;
      const relativeY = e.clientY - containerRect.top;
      
      const newHeight = Math.max(150, Math.min(containerHeight - 150, relativeY));
      const percentage = (newHeight / containerHeight) * 100;
      
      const paneTop = document.getElementById("pane-top");
      const paneBottom = document.getElementById("pane-bottom");
      
      if (paneTop && paneBottom) {
        paneTop.style.flex = `0 0 ${percentage}%`;
        paneBottom.style.flex = `1 1 auto`;
      }
    } catch (error) {
      console.error('上下分割リサイズエラー:', error);
    }
    
    e.preventDefault();
  }

  // 上下分割リサイズのマウスアップ処理
  handleVerticalMouseUp = (e) => {
    this.isVerticalResizing = false;
    document.removeEventListener("mousemove", this.handleVerticalMouseMove);
    document.removeEventListener("mouseup", this.handleVerticalMouseUp);
    document.body.style.cursor = "";
    document.body.style.userSelect = "";
    e.preventDefault();
  }

  // 結果表示
  displayResult(result) {
    console.log('📊 OCR結果を表示:', result);
    
    // 結果表示処理
    this.showResults(result);
  }



  // 既存の結果表示処理（結果セクション用）
  showResults(result) {
    const resultsContainer = document.getElementById("results-container");
    const card = document.createElement("div");
    card.className = "result-card";

    const header = document.createElement("div");
    header.className = "result-header";
    header.style.display = "flex";
    header.style.justifyContent = "space-between";
    header.style.alignItems = "center";
    
    // ページ番号の表示を追加（0は全ページ、-1は全ページ処理中）
    const pageDisplay = result.page_num === -1 ? '（全ページ）' :
      result.page_num === 0 ? '（1ページ目）' :
      `（${result.page_num}ページ目）`;
    
    const titleDiv = document.createElement("div");
    titleDiv.textContent = `${result.engine_name || 'Unknown'} ${pageDisplay}`;
    
    const statsDiv = document.createElement("div");
    statsDiv.className = "result-stats";
    statsDiv.style.fontSize = "0.8em";
    statsDiv.style.color = "#666";
    
    // 修正箇所数の表示を追加
    let correctionStats = '';
    if (result.correction_count && result.correction_count > 0) {
      correctionStats = ` | 修正箇所: ${result.correction_count}箇所`;
    }
    
    statsDiv.innerHTML = `
      処理時間: ${result.processing_time?.toFixed(2) || 'N/A'}秒 | 
      文字数: ${(result.text || '').length}文字${correctionStats}
    `;
    
    header.appendChild(titleDiv);
    header.appendChild(statsDiv);

    const content = document.createElement("div");
    content.className = "result-content";

    const textDiv = document.createElement("div");
    textDiv.className = "result-text";
    
    // HTMLテキストがある場合は修正文字を赤字で表示
    if (result.html_text) {
      textDiv.innerHTML = result.html_text;
    } else {
      textDiv.textContent = result.text || "テキストが抽出されませんでした";
    }

    content.appendChild(textDiv);
    card.appendChild(header);
    card.appendChild(content);

    resultsContainer.appendChild(card);
    resultsContainer.scrollTop = resultsContainer.scrollHeight;
  }

  // エラー表示
  displayError(message) {
    console.log('❌ エラーを表示:', message);
    
    // エラー表示処理
    this.showResults({
      engine_name: "エラー",
      text: message,
      processing_time: 0,
      page_num: -1
    });
  }

  // 結果クリア
  clearResults() {
    console.log('🗑️ 結果をクリア中... 処理中:', !!this.processingStartTime);
    
    // DOM要素の初期化を確実に行う
    this.initializeDOMElements();
    
    const resultsContainer = document.getElementById("results-container");
    
    // 常に結果をクリア
    resultsContainer.innerHTML = '';
    
    // 処理中でない場合のみ初期メッセージを表示
    if (!this.processingStartTime) {
      console.log('🗑️ 初期メッセージを表示');
      resultsContainer.innerHTML = '<p style="color:#888; text-align:center; margin-top:2em;">OCRエンジンとファイルを選択して「OCR実行」ボタンを押してください</p>';
      
      // 処理ステータスを隠す
      if (this.processingStatus) {
        this.processingStatus.style.display = 'none';
      }
      
      // 全てのタイマーをクリア
      if (this.overlayTimerInterval) {
        clearInterval(this.overlayTimerInterval);
        this.overlayTimerInterval = null;
      }
      if (this.statusTimerInterval) {
        clearInterval(this.statusTimerInterval);
        this.statusTimerInterval = null;
      }
    } else {
      console.log('🗑️ 処理中のため初期メッセージは表示しない');
    }
  }

  // 初期化処理
  initialize() {
    // リサイズ機能の初期化
    this.initializeResize();

    // 初期状態の設定
    this.setInitialMessage();

    // 複数のタイミングでオーバーレイを確実に隠す
    this.forceHideOverlay();
    setTimeout(() => this.forceHideOverlay(), 100);
    setTimeout(() => this.forceHideOverlay(), 500);

    // ウィンドウ読み込み完了時にも隠す
    window.addEventListener('load', () => this.forceHideOverlay());

    // ページ表示時にも隠す
    document.addEventListener('visibilitychange', () => {
      if (!document.hidden) {
        this.forceHideOverlay();
      }
    });
  }

  // 初期メッセージを設定
  setInitialMessage() {
    const resultsContainer = document.getElementById("results-container");
    if (resultsContainer && !resultsContainer.innerHTML.trim()) {
      resultsContainer.innerHTML = '<p style="color:#888; text-align:center; margin-top:2em;">OCRエンジンとファイルを選択して「OCR実行」ボタンを押してください</p>';
    }
  }
}

// グローバルに公開
window.TryOcrUI = TryOcrUI;