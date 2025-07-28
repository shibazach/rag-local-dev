// app/static/js/ingest_processing.js

class IngestProcessing {
  constructor(sseManager) {
    this.sseManager = sseManager;
    this.startBtn = document.getElementById('start-btn');
    this.cancelBtn = document.getElementById('cancel-btn');
    this.processingInProgress = false;
    this.currentEngineSettings = {};
    
    this.initializeEventListeners();
    this.initializeInputModeToggle();
    this.initializeFolderBrowse();
    this.initializeFileDisplay();
  }

  initializeEventListeners() {
    if (this.startBtn) {
      this.startBtn.addEventListener('click', () => this.startProcessing());
    }
    if (this.cancelBtn) {
      this.cancelBtn.addEventListener('click', () => this.cancelProcessing());
    }

    // ページ離脱警告
    window.addEventListener('beforeunload', (e) => {
      if (this.processingInProgress) {
        e.preventDefault();
        e.returnValue = 'データ処理中です。ページを離れますか？';
      }
    });
  }

  initializeInputModeToggle() {
    const inputModeRadios = document.querySelectorAll('input[name="input_mode"]');
    
    inputModeRadios.forEach(radio => {
      radio.addEventListener('change', () => {
        const folderMode = document.getElementById('folder-mode');
        const filesMode = document.getElementById('files-mode');
        
        if (radio.value === 'folder' && radio.checked) {
          if (folderMode) folderMode.style.display = 'flex';
          if (filesMode) filesMode.style.display = 'none';
        } else if (radio.value === 'files' && radio.checked) {
          if (folderMode) folderMode.style.display = 'none';
          if (filesMode) filesMode.style.display = 'flex';
        }
      });
    });
  }

  initializeFolderBrowse() {
    // フォルダブラウズ機能の初期化（簡略版）
    const browseBtn = document.getElementById('browse-folder');
    if (browseBtn) {
      browseBtn.addEventListener('click', () => {
        console.log('フォルダブラウズ機能');
      });
    }
  }

  initializeFileDisplay() {
    const inputFilesEl = document.getElementById('input-files');
    const selectedFilesDisplay = document.getElementById('selected-files-display');
    
    if (inputFilesEl && selectedFilesDisplay) {
      inputFilesEl.addEventListener('change', () => {
        const files = Array.from(inputFilesEl.files).map(f => f.name);
        selectedFilesDisplay.value = files.join('\n');
        selectedFilesDisplay.style.display = files.length > 0 ? 'block' : 'none';
        selectedFilesDisplay.style.height = selectedFilesDisplay.scrollHeight + 'px';
      });
    }
  }

  async startProcessing() {
    console.log('🚀 処理開始関数が呼び出されました');
    
    if (this.processingInProgress) {
      console.log('❌ 既に処理が実行中です');
      alert('既に処理が実行中です');
      return;
    }

    const form = document.getElementById('ingest-form');
    if (!form) {
      console.log('❌ フォーム要素が見つかりません');
      return;
    }

    const formData = new FormData(form);
    
    try {
      this.processingInProgress = true;
      this.setFormDisabled(true);
      
      if (this.startBtn) this.startBtn.textContent = '処理中...';
      
      this.sseManager.clearLog();
      this.sseManager.addLogMessage('処理を開始しています...');

      const response = await fetch('/ingest', {
        method: 'POST',
        body: formData
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error('HTTP ' + response.status + ': ' + response.statusText);
      }

      this.sseManager.setOnCompleteCallback(() => this.onProcessingComplete());
      this.sseManager.startIngestStream();

    } catch (error) {
      console.error('❌ 処理エラー:', error);
      this.sseManager.addLogMessage('エラー: ' + error.message);
      this.onProcessingComplete();
    }
  }

  async cancelProcessing() {
    if (!this.processingInProgress) return;
    
    if (!confirm('処理をキャンセルしますか？\n\n注意: OCR処理中の場合、完全に停止するまで時間がかかる場合があります。')) return;

    try {
      // キャンセル要求を送信
      await fetch('/ingest/cancel', { method: 'POST' });
      
      // UI状態を即座に更新
      this.sseManager.addLogMessage('⏹️ キャンセル要求を送信しました...');
      this.sseManager.addLogMessage('⚠️ OCR処理中の場合、完全停止まで時間がかかります');
      
      // ボタン状態を更新
      if (this.startBtn) this.startBtn.textContent = 'キャンセル中...';
      if (this.cancelBtn) {
        this.cancelBtn.textContent = 'キャンセル中...';
        this.cancelBtn.disabled = true;
      }
      
    } catch (error) {
      console.error('キャンセルエラー:', error);
      this.sseManager.addLogMessage('❌ キャンセルエラー: ' + error.message);
      this.onProcessingComplete();
    }
  }

  onProcessingComplete() {
    this.processingInProgress = false;
    this.setFormDisabled(false);
    
    if (this.startBtn) this.startBtn.textContent = '🚀 処理開始';
  }

  setFormDisabled(disabled) {
    const form = document.getElementById('ingest-form');
    if (form) {
      const elements = form.querySelectorAll('input, select, button');
      elements.forEach(el => {
        if (el.name !== 'pdf_mode') el.disabled = disabled;
      });
    }
    
    if (this.cancelBtn) this.cancelBtn.disabled = !disabled;
  }

  setCurrentEngineSettings(settings) {
    this.currentEngineSettings = settings;
  }

  getCurrentEngineSettings() {
    return this.currentEngineSettings;
  }
}

// グローバルに公開
window.IngestProcessing = IngestProcessing;