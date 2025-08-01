// app/static/js/chat_resize.js

class ChatResize {
  constructor() {
    this.appContainer = document.getElementById('app-container');
    this.isResizing = false;
    this.currentResizer = null;
    
    this.initializeResizers();
  }

  initializeResizers() {
    // リサイザー要素
    const topResizer = document.getElementById('top-resizer');
    const leftResizer = document.getElementById('left-resizer');
    const verticalResizer = document.getElementById('vertical-resizer');

    // マウスイベント
    document.addEventListener('mousemove', (e) => this.handleMouseMove(e));
    document.addEventListener('mouseup', () => this.handleMouseUp());

    // リサイザーのイベント
    if (topResizer) {
      topResizer.addEventListener('mousedown', (e) => this.startResize('top', 'row-resize', e));
    }
    if (leftResizer) {
      leftResizer.addEventListener('mousedown', (e) => this.startResize('left', 'row-resize', e));
    }
    if (verticalResizer) {
      verticalResizer.addEventListener('mousedown', (e) => this.startResize('vertical', 'col-resize', e));
    }
  }

  startResize(resizer, cursor, e) {
    this.isResizing = true;
    this.currentResizer = resizer;
    document.body.style.cursor = cursor;
    document.body.style.userSelect = 'none';
    
    // オーバーレイ追加
    this.addResizeOverlay();
    e.preventDefault();
  }

  addResizeOverlay() {
    if (document.getElementById('resize-overlay')) return;
    const overlay = document.createElement('div');
    overlay.id = 'resize-overlay';
    overlay.style.position = 'fixed';
    overlay.style.top = '0';
    overlay.style.left = '0';
    overlay.style.right = '0';
    overlay.style.bottom = '0';
    overlay.style.zIndex = '9999';
    overlay.style.background = 'transparent';
    overlay.style.cursor = 'inherit';
    document.body.appendChild(overlay);
  }

  removeResizeOverlay() {
    const overlay = document.getElementById('resize-overlay');
    if (overlay) overlay.remove();
  }

  handleMouseMove(e) {
    if (!this.isResizing) return;

    if (this.currentResizer === 'top') {
      // 第1パターン：上部設定の高さ調整
      const container = this.appContainer.getBoundingClientRect();
      const relativeY = e.clientY - container.top;
      const minHeight = 150; // 最小150px（固定値）
      const maxHeight = container.height * 0.7; // 最大70%に拡大
      
      if (relativeY >= minHeight && relativeY <= maxHeight) {
        const topEl = document.getElementById('top-container');
        if (topEl) {
          topEl.style.flex = '0 0 ' + (relativeY - 5) + 'px';
        }
      }
    } else if (this.currentResizer === 'left') {
      // 第2パターン：左側検索の高さ調整
      const leftPane = document.getElementById('left-pane');
      if (leftPane) {
        const leftRect = leftPane.getBoundingClientRect();
        const relativeY = e.clientY - leftRect.top;
        const minHeight = leftRect.height * 0.2;
        const maxHeight = leftRect.height * 0.8;
        
        if (relativeY >= minHeight && relativeY <= maxHeight) {
          const leftEl = document.getElementById('left-container');
          if (leftEl) {
            leftEl.style.flex = '0 0 ' + (relativeY - 5) + 'px';
          }
        }
      }
    } else if (this.currentResizer === 'vertical') {
      // 左ペインとPDFの幅調整
      const bottomContainer = document.getElementById('bottom-container');
      if (bottomContainer) {
        const bottomRect = bottomContainer.getBoundingClientRect();
        const relativeX = e.clientX - bottomRect.left;
        const minWidth = bottomRect.width * 0.2;
        const maxWidth = bottomRect.width * 0.8;
        
        if (relativeX >= minWidth && relativeX <= maxWidth) {
          const leftPercent = (relativeX / bottomRect.width) * 100;
          const rightPercent = 100 - leftPercent;
          
          const leftPane = document.getElementById('left-pane');
          const pdfPanel = document.getElementById('pdf-panel');
          if (leftPane) leftPane.style.flex = '0 0 ' + (leftPercent - 0.5) + '%';
          if (pdfPanel) pdfPanel.style.flex = '0 0 ' + (rightPercent - 0.5) + '%';
        }
      }
    }
  }

  handleMouseUp() {
    if (this.isResizing) {
      this.isResizing = false;
      this.currentResizer = null;
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
      this.removeResizeOverlay();
    }
  }

  adjustTextareaHeight(containerHeight) {
    // テキストエリアは固定高さ（80px）に設定済みのため、動的調整は無効化
    return;
  }
}

// グローバルに公開
window.ChatResize = ChatResize;