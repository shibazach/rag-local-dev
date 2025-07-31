// app/static/js/chat_layout.js

class ChatLayout {
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
    console.log('Chat DOM要素確認:');
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
    console.log('Chatレイアウト初期化: no-preview モードを設定');
    
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
    
    // 強制的にno-previewモードの要素を正しい状態に設定
    this.forceNoPreviewLayout();
    
    console.log('初期Chatレイアウト設定完了');
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
    console.log('Chatレイアウト切り替え:', this.currentLayout, '→', layout);
    
    // 既存クラスを削除
    this.appContainer.classList.remove('layout-no-preview', 'layout-pattern1', 'layout-pattern2');
    this.pattern1Btn.classList.remove('active');
    this.pattern2Btn.classList.remove('active');
    
    // インラインスタイルをクリア（CSSクラスによる制御を有効にする）
    const pdfPanel = document.getElementById('pdf-panel');
    const verticalResizer = document.getElementById('vertical-resizer');
    const layoutControls = document.getElementById('layout-controls');
    
    if (pdfPanel) pdfPanel.style.display = '';
    if (verticalResizer) verticalResizer.style.display = '';
    if (layoutControls) layoutControls.style.display = '';
    
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
    console.log('Chat PDFプレビュー:', fileIdOrName, fileName);
    
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
    console.log('Chat PDFプレビュー切り替え:', fileIdOrName, fileName);
    console.log('🔍 fileIdOrName type:', typeof fileIdOrName, 'value:', fileIdOrName);
    
    // ダミーPDFの場合の処理
    if (fileIdOrName && fileIdOrName.toString().startsWith('dummy_')) {
      console.log('🧪 ダミーPDFプレビューを表示します');
      this.showDummyPDF(fileName);
      return;
    }
    
    console.log('⚠️ 実際のPDF処理に進みます - これが404エラーの原因かもしれません');
    
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

  // ダミーPDFプレビューを表示
  showDummyPDF(fileName) {
    console.log('🎬 showDummyPDF開始:', fileName);
    
    // PDFフレームの存在確認
    this.pdfFrame = document.getElementById('pdf-frame');
    console.log('🔍 PDFフレーム検索結果:', this.pdfFrame);
    
    if (!this.pdfFrame) {
      console.error('❌ PDFフレームが見つかりません - DOM構造を確認します');
      const pdfPanel = document.getElementById('pdf-panel');
      console.log('pdf-panel:', pdfPanel);
      if (pdfPanel) {
        const iframe = pdfPanel.querySelector('iframe');
        console.log('pdf-panel内のiframe:', iframe);
      }
      return;
    }
    
    // レイアウトを第1パターンに切り替え
    console.log('📐 レイアウトをpattern1に切り替え');
    this.switchLayout('pattern1');
    
    // 少し待ってからPDFフレームを再取得
    setTimeout(() => {
      this.pdfFrame = document.getElementById('pdf-frame');
      console.log('🔄 レイアウト切り替え後のPDFフレーム:', this.pdfFrame);
      
      if (this.pdfFrame) {
        // ダミーPDFコンテンツを生成
        const dummyPdfContent = this.generateDummyPDFContent(fileName);
        
        // データURLでダミーHTMLを表示
        const dataUrl = `data:text/html;charset=utf-8,${encodeURIComponent(dummyPdfContent)}`;
        console.log('🔗 データURL生成:', dataUrl.substring(0, 100) + '...');
        
        this.pdfFrame.src = dataUrl;
        this.currentPdfUrl = dataUrl;
        
        console.log('📺 PDFフレームにダミーコンテンツを設定:', this.pdfFrame.src.substring(0, 50) + '...');
        
        // PDFパネルが表示されているか確認
        const pdfPanel = document.getElementById('pdf-panel');
        if (pdfPanel) {
          console.log('📦 PDFパネルの表示状態:', window.getComputedStyle(pdfPanel).display);
          console.log('📦 PDFパネルの可視性:', window.getComputedStyle(pdfPanel).visibility);
        }
      } else {
        console.error('❌ レイアウト切り替え後もPDFフレームが見つかりません');
      }
    }, 100);
  }

  // ダミーPDFコンテンツのHTML生成（シンプル版）
  generateDummyPDFContent(fileName) {
    return `
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <title>ダミーPDF</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 50px;
            text-align: center;
            background: white;
        }
        .dummy-content {
            font-size: 48px;
            color: #666;
            margin-top: 200px;
        }
    </style>
</head>
<body>
    <div class="dummy-content">
        ダミー
    </div>
</body>
</html>`;
  }

  getCurrentLayout() {
    return this.currentLayout;
  }

  getCurrentPdfUrl() {
    return this.currentPdfUrl;
  }

  // デバッグ用：現在の状態を表示
  debugCurrentState() {
    console.log('🔍 現在のレイアウト状態:');
    console.log('- currentLayout:', this.currentLayout);
    console.log('- currentPdfUrl:', this.currentPdfUrl);
    
    const appContainer = document.getElementById('app-container');
    console.log('- app-container classes:', appContainer?.className);
    
    const pdfPanel = document.getElementById('pdf-panel');
    const pdfFrame = document.getElementById('pdf-frame');
    const layoutControls = document.getElementById('layout-controls');
    
    console.log('- pdf-panel:', pdfPanel ? '存在' : '不存在');
    if (pdfPanel) {
      console.log('  - display:', window.getComputedStyle(pdfPanel).display);
      console.log('  - visibility:', window.getComputedStyle(pdfPanel).visibility);
    }
    
    console.log('- pdf-frame:', pdfFrame ? '存在' : '不存在');
    if (pdfFrame) {
      console.log('  - src:', pdfFrame.src);
    }
    
    console.log('- layout-controls:', layoutControls ? '存在' : '不存在');
    if (layoutControls) {
      console.log('  - display:', window.getComputedStyle(layoutControls).display);
    }
  }

  // 強制的にno-previewモードの要素を正しい状態に設定
  forceNoPreviewLayout() {
    console.log('強制的にno-previewレイアウトを適用');
    
    // PDFパネルとリサイザーを強制非表示
    const pdfPanel = document.getElementById('pdf-panel');
    const verticalResizer = document.getElementById('vertical-resizer');
    const layoutControls = document.getElementById('layout-controls');
    
    if (pdfPanel) {
      pdfPanel.style.display = 'none';
      console.log('PDFパネルを非表示にしました');
    }
    
    if (verticalResizer) {
      verticalResizer.style.display = 'none';
      console.log('縦リサイザーを非表示にしました');
    }
    
    if (layoutControls) {
      layoutControls.style.display = 'none';
      console.log('レイアウトボタンを非表示にしました');
    }
    
    // left-paneを100%幅に設定
    const leftPane = document.getElementById('left-pane');
    if (leftPane) {
      leftPane.style.flex = '1';
      console.log('左ペインを100%幅に設定しました');
    }
  }


}

// グローバルに公開
window.ChatLayout = ChatLayout;