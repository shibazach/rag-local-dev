// app/static/js/try_ocr_resize.js

class TryOcrResize {
  constructor() {
    this.isResizing = false;
    this.currentSplitter = null;
    this.startX = 0;
    this.startY = 0;
    this.startWidth = 0;
    this.startHeight = 0;
  }

  // 初期化
  initialize() {
    this.setupSplitters();
  }

  // スプリッターの設定
  setupSplitters() {
    // 上ペイン用横分割スプリッター
    const topSplitter = document.getElementById('top-splitter');
    if (topSplitter) {
      topSplitter.addEventListener('mousedown', (e) => this.startResize(e, 'horizontal-top'));
    }

    // 上下分割用縦スプリッター
    const verticalSplitter = document.getElementById('vertical-splitter');
    if (verticalSplitter) {
      verticalSplitter.addEventListener('mousedown', (e) => this.startResize(e, 'vertical'));
    }

    // 下ペイン用横分割スプリッター
    const splitter = document.getElementById('splitter');
    if (splitter) {
      splitter.addEventListener('mousedown', (e) => this.startResize(e, 'horizontal-bottom'));
    }

    // グローバルイベントリスナー
    document.addEventListener('mousemove', (e) => this.handleResize(e));
    document.addEventListener('mouseup', () => this.stopResize());
  }

  // リサイズ開始
  startResize(e, type) {
    e.preventDefault();
    this.isResizing = true;
    this.currentSplitter = type;
    this.startX = e.clientX;
    this.startY = e.clientY;

    // カーソルスタイルを設定
    document.body.style.cursor = type.includes('horizontal') ? 'col-resize' : 'row-resize';
    document.body.style.userSelect = 'none';

    // リサイズ中のオーバーレイを作成（iframe問題対策）
    this.createResizeOverlay();

    // 初期サイズを記録
    if (type === 'horizontal-top') {
      const topLeft = document.getElementById('top-left');
      this.startWidth = topLeft.offsetWidth;
    } else if (type === 'vertical') {
      const paneTop = document.getElementById('pane-top');
      this.startHeight = paneTop.offsetHeight;
    } else if (type === 'horizontal-bottom') {
      const resultsPane = document.getElementById('results-pane');
      this.startWidth = resultsPane.offsetWidth;
    }
  }

  // リサイズ処理
  handleResize(e) {
    if (!this.isResizing) return;

    const deltaX = e.clientX - this.startX;
    const deltaY = e.clientY - this.startY;

    if (this.currentSplitter === 'horizontal-top') {
      // 上ペインの左右分割
      const container = document.getElementById('pane-top');
      const topLeft = document.getElementById('top-left');
      const topRight = document.getElementById('top-right');
      
      const containerWidth = container.offsetWidth;
      const splitterWidth = 5;
      const newLeftWidth = Math.max(200, Math.min(containerWidth - 200 - splitterWidth, this.startWidth + deltaX));
      const newRightWidth = containerWidth - newLeftWidth - splitterWidth;
      
      topLeft.style.flex = `0 0 ${newLeftWidth}px`;
      topRight.style.flex = `0 0 ${newRightWidth}px`;
      
    } else if (this.currentSplitter === 'vertical') {
      // 上下分割
      const container = document.getElementById('try-ocr-container');
      const paneTop = document.getElementById('pane-top');
      const paneBottom = document.getElementById('pane-bottom');
      
      const containerHeight = container.offsetHeight;
      const splitterHeight = 5;
      const newTopHeight = Math.max(200, Math.min(containerHeight - 200 - splitterHeight, this.startHeight + deltaY));
      const newBottomHeight = containerHeight - newTopHeight - splitterHeight;
      
      paneTop.style.flex = `0 0 ${newTopHeight}px`;
      paneBottom.style.flex = `0 0 ${newBottomHeight}px`;
      
    } else if (this.currentSplitter === 'horizontal-bottom') {
      // 下ペインの左右分割
      const container = document.getElementById('pane-bottom');
      const resultsPane = document.getElementById('results-pane');
      const pdfPane = document.getElementById('pdf-pane');
      
      if (!container || !resultsPane || !pdfPane) {
        console.error('下段スプリッター: 必要な要素が見つかりません', {
          container: !!container,
          resultsPane: !!resultsPane,
          pdfPane: !!pdfPane
        });
        return;
      }
      
      const containerWidth = container.offsetWidth;
      const splitterWidth = 5;
      const newLeftWidth = Math.max(200, Math.min(containerWidth - 200 - splitterWidth, this.startWidth + deltaX));
      const newRightWidth = containerWidth - newLeftWidth - splitterWidth;
      
      console.log('下段リサイズ:', { containerWidth, newLeftWidth, newRightWidth });
      
      resultsPane.style.flex = `0 0 ${newLeftWidth}px`;
      pdfPane.style.flex = `0 0 ${newRightWidth}px`;
    }
  }

  // リサイズ終了
  stopResize() {
    if (!this.isResizing) return;
    
    this.isResizing = false;
    this.currentSplitter = null;
    
    // カーソルスタイルをリセット
    document.body.style.cursor = '';
    document.body.style.userSelect = '';
    
    // オーバーレイを削除
    this.removeResizeOverlay();
  }

  // リサイズ中のオーバーレイを作成（iframe問題対策）
  createResizeOverlay() {
    // 既存のオーバーレイがあれば削除
    this.removeResizeOverlay();
    
    const overlay = document.createElement('div');
    overlay.id = 'resize-overlay';
    overlay.style.cssText = `
      position: fixed;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      z-index: 9999;
      cursor: ${this.currentSplitter.includes('horizontal') ? 'col-resize' : 'row-resize'};
      background: transparent;
      pointer-events: all;
    `;
    
    document.body.appendChild(overlay);
    
    // オーバーレイ上でのマウスイベントを処理
    overlay.addEventListener('mousemove', (e) => this.handleResize(e));
    overlay.addEventListener('mouseup', () => this.stopResize());
  }

  // リサイズオーバーレイを削除
  removeResizeOverlay() {
    const overlay = document.getElementById('resize-overlay');
    if (overlay) {
      overlay.remove();
    }
  }
}

// グローバルに公開
window.TryOcrResize = TryOcrResize;