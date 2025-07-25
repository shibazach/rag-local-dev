// app/static/js/ingest_ocr.js @作成日時: 2025-07-25
// REM: OCR設定機能

class IngestOCR {
  constructor(processingManager) {
    this.processingManager = processingManager;
    this.availableEngines = {};
    
    this.initializeEventListeners();
    this.loadOCREngines();
  }

  initializeEventListeners() {
    // OCRボタンのイベント
    const ocrSettingsBtn = document.getElementById('ocr-settings-btn');
    const ocrPresetsBtn = document.getElementById('ocr-presets-btn');

    if (ocrSettingsBtn) ocrSettingsBtn.addEventListener('click', () => this.showOCRSettings());
    if (ocrPresetsBtn) ocrPresetsBtn.addEventListener('click', () => this.showOCRPresets());

    // OCRエンジン変更時の設定読み込み
    const ocrEngineSelect = document.getElementById('ocr-engine');
    if (ocrEngineSelect) {
      ocrEngineSelect.addEventListener('change', async () => {
        const engineId = ocrEngineSelect.value;
        if (engineId) {
          await this.loadEngineSettings(engineId);
        }
      });
    }
  }

  async loadOCREngines() {
    try {
      const response = await fetch('/ingest/ocr/engines');
      const engines = await response.json();
      
      this.availableEngines = engines;

      const select = document.getElementById('ocr-engine');
      if (select) {
        select.innerHTML = '';
        let easyOCRFound = false;
        
        for (const engineId in engines) {
          const engineInfo = engines[engineId];
          const option = document.createElement('option');
          option.value = engineId;
          option.textContent = engineInfo.name + ' ' + (engineInfo.available ? '✓' : '✗');
          option.disabled = !engineInfo.available;
          select.appendChild(option);
          
          if (engineId === 'easyocr' && engineInfo.available) {
            option.selected = true;
            easyOCRFound = true;
          }
        }
        
        if (!easyOCRFound) {
          for (const engineId in engines) {
            const engineInfo = engines[engineId];
            if (engineInfo.available) {
              select.value = engineId;
              break;
            }
          }
        }

        if (select.value) {
          await this.loadEngineSettings(select.value);
        }
      }
    } catch (error) {
      console.error('OCRエンジン一覧の読み込みに失敗:', error);
    }
  }

  async loadEngineSettings(engineId) {
    try {
      const response = await fetch('/ingest/ocr/settings/' + engineId);
      const data = await response.json();
      const settings = data.settings;
      this.processingManager.setCurrentEngineSettings(settings);
    } catch (error) {
      console.error('エンジン設定の読み込みに失敗:', error);
      this.processingManager.setCurrentEngineSettings({});
    }
  }

  showOCRSettings() {
    console.log('OCR設定表示');
    alert('OCR設定機能は開発中です');
  }

  showOCRPresets() {
    console.log('OCRプリセット表示');
    alert('OCRプリセット機能は開発中です');
  }
}

// グローバルに公開
window.IngestOCR = IngestOCR;