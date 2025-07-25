// app/static/js/ingest_layout.js @作成日時: 2025-07-25
// REM: レイアウト切り替え機能

class IngestLayout {
  constructor() {
    this.appContainer = document.getElementById('app-container');
    this.pattern1Btn = document.getElementById('pattern1-btn');
    this.pattern2Btn = document.getElementById('pattern2-btn');
    this.pdfFrame = document.getElementById('pdf-frame');
    this.settingsPanel = document.getElementById('settings-panel');
    this.topContainer = document.getElementById('top-container');
    this.leftContainer = document.getElementById('left-container');
    
    this.currentLayout = 'no-preview';
    this.currentPdfUrl = null;
    
    this.initializeEventListeners();
    
    // DOM要素の存在確認
    if (!this.appContainer || !this.settingsPanel || !this.topContainer) {
      console.error('レイアウト初期化失敗: 必要なDOM要素が見つかりません');
      return;
    }
    
    // 初期レイアウトを強制的に設定
    console.log('レイアウト初期化: no-preview モードを設定');
    this.switchLayout('no-preview');
  }

  initializeEventListeners() {
    if (this.pattern1Btn) {
      this.pattern1Btn.addEventListener('click', () => this.switchLayout('pattern1'));
    }
    if (this.pattern2Btn) {
      this.pattern2Btn.addEventListener('click', () => this.switchLayout('pattern2'));
    }
  }

  switchLayout(layout) {
    console.log('レイアウト切り替え:', this.currentLayout, '→', layout);
    
    // 既存クラスを削除
    this.appContainer.classList.remove('layout-no-preview', 'layout-pattern1', 'layout-pattern2');
    this.pattern1Btn.classList.remove('active');
    this.pattern2Btn.classList.remove('active');
    
    // 新しいクラスを追加と設定パネル移動
    switch (layout) {
      case 'pattern1':
        this.appContainer.classList.add('layout-pattern1');
        this.pattern1Btn.classList.add('active');
        // 設定パネルを上部に移動
        if (this.settingsPanel && this.topContainer) {
          this.topContainer.appendChild(this.settingsPanel);
        }
        break;
      case 'pattern2':
        this.appContainer.classList.add('layout-pattern2');
        this.pattern2Btn.classList.add('active');
        // 設定パネルを左側に移動
        if (this.settingsPanel && this.leftContainer) {
          this.leftContainer.appendChild(this.settingsPanel);
        }
        break;
      default:
        this.appContainer.classList.add('layout-no-preview');
        // 設定パネルを上部に移動（PDFプレビューなしでも上下分割）
        console.log('設定パネル移動:', this.settingsPanel, this.topContainer);
        if (this.settingsPanel && this.topContainer) {
          this.topContainer.appendChild(this.settingsPanel);
          console.log('設定パネルを上部に移動しました');
        } else {
          console.error('設定パネルまたは上部コンテナが見つかりません');
        }
        break;
    }
    
    this.currentLayout = layout;
    
    // PDFフレームの制御
    if (this.currentPdfUrl && (layout === 'pattern1' || layout === 'pattern2')) {
      if (this.pdfFrame) this.pdfFrame.src = this.currentPdfUrl;
    } else if (layout === 'no-preview') {
      if (this.pdfFrame) this.pdfFrame.src = '';
    }
  }

  showPDFPreview(fileIdOrName, fileName) {
    console.log('PDFプレビュー:', fileIdOrName, fileName);
    
    // PDFのURLを構築（file_idがある場合はそれを使用、なければファイル名）
    const pdfUrl = `/api/pdf/${encodeURIComponent(fileIdOrName)}`;
    
    // 現在のレイアウトに応じてPDF表示
    if (this.currentLayout === 'no-preview') {
      // PDFプレビューなしモードの場合、第1パターンに切り替え
      this.switchLayout('pattern1');
    }
    
    // PDFフレームにURLを設定
    if (this.pdfFrame) {
      this.pdfFrame.src = pdfUrl;
      this.currentPdfUrl = pdfUrl;
    }
  }

  togglePDFPreview(fileIdOrName, fileName) {
    console.log('PDFプレビュー切り替え:', fileIdOrName, fileName);
    
    // オルタネートスイッチ：現在の状態に応じて切り替え
    if (this.currentLayout === 'no-preview') {
      // プレビューなし → 第1パターン
      this.showPDFPreview(fileIdOrName, fileName);
    } else {
      // プレビューあり → プレビューなし
      this.switchLayout('no-preview');
      this.currentPdfUrl = null;
    }
  }

  getCurrentLayout() {
    return this.currentLayout;
  }

  getCurrentPdfUrl() {
    return this.currentPdfUrl;
  }
}

// グローバルに公開
window.IngestLayout = IngestLayout;