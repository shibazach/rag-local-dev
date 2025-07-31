// app/static/js/common/ocr_settings.js
// OCR設定の共通モジュール

class CommonOCRSettings {
  constructor() {
    this.availableEngines = {};
    this.currentSettings = {};
    this.onSaveCallback = null;
  }

  // 設定保存コールバックを設定
  setOnSave(callback) {
    this.onSaveCallback = callback;
  }

  // OCRエンジン一覧を読み込み
  async loadOCREngines() {
    try {
      // ingestとtry_ocr両方のエンドポイントを試行
      let response;
      try {
        response = await fetch('/ingest/ocr/engines');
      } catch (error) {
        response = await fetch('/api/try_ocr/engines');
      }
      
      const engines = await response.json();
      this.availableEngines = engines;
      return engines;
    } catch (error) {
      console.error('OCRエンジン一覧の読み込みに失敗:', error);
      return {};
    }
  }

  // エンジン設定を読み込み
  async loadEngineSettings(engineId) {
    try {
      // ingestとtry_ocr両方のエンドポイントを試行
      let response;
      try {
        response = await fetch(`/ingest/ocr/settings/${encodeURIComponent(engineId)}`);
      } catch (error) {
        response = await fetch(`/api/try_ocr/engine_parameters/${encodeURIComponent(engineId)}`);
      }
      
      const data = await response.json();
      const settings = data.settings || data.parameters || {};
      this.currentSettings = settings;
      return settings;
    } catch (error) {
      console.error('エンジン設定の読み込みに失敗:', error);
      this.currentSettings = {};
      return {};
    }
  }

  // 設定ダイアログを表示
  async showSettingsDialog(engineId, containerId = 'ocr-settings-content') {
    const engines = await this.loadEngineSettings(engineId);
    
    if (!engines || Object.keys(engines).length === 0) {
      document.getElementById(containerId).innerHTML = 
        '<p style="color:#888; text-align:center; padding:2em;">このエンジンには調整項目がありません</p>';
      return;
    }

    this.renderEngineParameters(engines, containerId);
  }

  // エンジンパラメータをレンダリング
  renderEngineParameters(parameters, containerId) {
    const contentDiv = document.getElementById(containerId);
    if (!contentDiv) return;
    
    contentDiv.innerHTML = '';
    this.currentSettings = {};

    // パラメータをカテゴリ別にグループ化
    const categorizedParams = {};
    parameters.forEach(param => {
      const category = param.category || '基本設定';
      if (!categorizedParams[category]) {
        categorizedParams[category] = [];
      }
      categorizedParams[category].push(param);
    });

    // カテゴリ別にUI生成
    Object.keys(categorizedParams).forEach((categoryName, index) => {
      const categoryDiv = document.createElement('div');
      categoryDiv.className = 'parameter-category';
      categoryDiv.style.marginBottom = '8px';

      // カテゴリヘッダー
      const headerDiv = document.createElement('div');
      headerDiv.style.cssText = `
        background: #f8f9fa;
        padding: 4px 8px;
        border-radius: 3px;
        font-weight: bold;
        margin-bottom: 4px;
        border-left: 3px solid #007bff;
        font-size: 12px;
      `;
      headerDiv.textContent = categoryName;
      categoryDiv.appendChild(headerDiv);

      // パラメータ項目を生成
      categorizedParams[categoryName].forEach(param => {
        const itemDiv = this.createParameterItem(param);
        categoryDiv.appendChild(itemDiv);
      });

      contentDiv.appendChild(categoryDiv);
    });
  }

  // パラメータ項目を作成
  createParameterItem(param) {
    const itemDiv = document.createElement('div');
    itemDiv.style.cssText = `
      display: flex;
      align-items: center;
      margin-bottom: 4px;
      padding: 2px 0;
    `;

    // 1. ラベル（固定幅）
    const labelDiv = document.createElement('div');
    labelDiv.style.cssText = `
      min-width: 120px;
      flex-shrink: 0;
      font-size: 12px;
      font-weight: normal;
      color: #495057;
    `;
    labelDiv.textContent = param.label;

    // 2. コントロール
    const controlDiv = document.createElement('div');
    controlDiv.style.cssText = `
      flex-shrink: 0;
      margin-right: 12px;
    `;

    let input;
    const inputId = `param-${param.name}`;

    switch (param.type) {
      case 'checkbox':
        input = document.createElement('input');
        input.type = 'checkbox';
        input.checked = param.default;
        input.id = inputId;
        input.style.cssText = 'transform: scale(1.2);';
        break;

      case 'number':
        input = document.createElement('input');
        input.type = 'number';
        input.value = param.default;
        input.min = param.min || '';
        input.max = param.max || '';
        input.step = param.step || '';
        input.id = inputId;
        input.style.cssText = 'width: 60px; padding: 2px 4px; border: 1px solid #ccc; border-radius: 2px; font-size: 12px; text-align: right; font-family: monospace;';
        break;

      case 'select':
        input = document.createElement('select');
        input.id = inputId;
        input.style.cssText = 'width: 100px; padding: 2px 4px; border: 1px solid #ccc; border-radius: 2px; font-size: 12px;';
        
        if (param.options) {
          param.options.forEach(option => {
            const optionEl = document.createElement('option');
            optionEl.value = option.value;
            optionEl.textContent = option.label;
            if (option.value === param.default) {
              optionEl.selected = true;
            }
            input.appendChild(optionEl);
          });
        }
        break;

      case 'text':
        input = document.createElement('input');
        input.type = 'text';
        input.value = param.default || '';
        input.id = inputId;
        input.style.cssText = 'width: 100px; padding: 2px 4px; border: 1px solid #ccc; border-radius: 2px; font-family: monospace; font-size: 12px;';
        break;

      default:
        input = document.createElement('input');
        input.type = 'text';
        input.value = param.default || '';
        input.id = inputId;
        input.style.cssText = 'width: 100px; padding: 2px 4px; border: 1px solid #ccc; border-radius: 2px; font-size: 12px;';
        break;
    }

    controlDiv.appendChild(input);

    // 3. 説明（薄字、若干小さく）
    const descDiv = document.createElement('div');
    descDiv.style.cssText = `
      flex: 1;
      margin-left: 12px;
      font-size: 11px;
      color: #6c757d;
      line-height: 1.2;
    `;
    descDiv.textContent = param.description || '';

    // 設定値を保存
    this.currentSettings[param.name] = param.default;
    
    // 変更イベント
    input.addEventListener('change', () => {
      if (param.type === 'checkbox') {
        this.currentSettings[param.name] = input.checked;
      } else if (param.type === 'number') {
        this.currentSettings[param.name] = parseFloat(input.value) || 0;
      } else {
        this.currentSettings[param.name] = input.value;
      }
    });

    itemDiv.appendChild(labelDiv);
    itemDiv.appendChild(controlDiv);
    itemDiv.appendChild(descDiv);

    return itemDiv;
  }

  // 設定を保存
  saveSettings(engineId) {
    if (this.onSaveCallback) {
      this.onSaveCallback(engineId, this.currentSettings);
    }
    console.log('OCR設定を保存しました:', engineId, this.currentSettings);
  }

  // 現在の設定を取得
  getCurrentSettings() {
    return this.currentSettings;
  }
}

// グローバルに公開
window.CommonOCRSettings = CommonOCRSettings; 