// app/static/js/ingest_layout.js

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
    
    // DOM要素の詳細確認
    console.log('DOM要素確認:');
    console.log('- appContainer:', this.appContainer);
    console.log('- settingsPanel:', this.settingsPanel);
    console.log('- topContainer:', this.topContainer);
    console.log('- leftContainer:', this.leftContainer);
    
    this.initializeEventListeners();
    
    // DOM要素の存在確認
    if (!this.appContainer) {
      console.error('app-container が見つかりません');
      return;
    }
    if (!this.settingsPanel) {
      console.error('settings-panel が見つかりません');
      return;
    }
    if (!this.topContainer) {
      console.error('top-container が見つかりません');
      return;
    }
    
    // 初期レイアウトを設定（設定パネルは移動させない）
    console.log('レイアウト初期化: no-preview モードを設定');
    
    // HTMLで既に正しい位置にあるので、クラスのみ設定
    this.appContainer.classList.remove('layout-pattern1', 'layout-pattern2');
    this.appContainer.classList.add('layout-no-preview');
    this.currentLayout = 'no-preview';
    
    // 設定パネルが正しい位置にあることを確認
    if (this.settingsPanel && this.topContainer) {
      if (!this.topContainer.contains(this.settingsPanel)) {
        console.log('設定パネルを正しい位置に移動');
        this.topContainer.appendChild(this.settingsPanel);
      } else {
        console.log('設定パネルは既に正しい位置にあります');
      }
    }
    
    console.log('初期レイアウト設定完了');
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
    
    // PDFのURLを構築
    const pdfUrl = `/api/pdf/${encodeURIComponent(fileIdOrName)}`;
    
    // オルタネートスイッチ：現在の状態に応じて切り替え
    if (this.currentLayout === 'no-preview') {
      // プレビューなし → 第1パターン（初回表示は必ず第1パターン）
      this.switchLayout('pattern1');
      if (this.pdfFrame) {
        this.pdfFrame.src = pdfUrl;
        this.currentPdfUrl = pdfUrl;
      }
    } else if (this.currentPdfUrl === pdfUrl) {
      // 同じPDFを再クリック → プレビューなし
      this.switchLayout('no-preview');
      if (this.pdfFrame) {
        this.pdfFrame.src = '';
      }
      this.currentPdfUrl = null;
    } else {
      // 別のPDFをクリック → 現在のレイアウトを維持してPDFを切り替え
      if (this.pdfFrame) {
        this.pdfFrame.src = pdfUrl;
        this.currentPdfUrl = pdfUrl;
      }
      // レイアウトがno-previewの場合は第1パターンに切り替え
      if (this.currentLayout === 'no-preview') {
        this.switchLayout('pattern1');
      }
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