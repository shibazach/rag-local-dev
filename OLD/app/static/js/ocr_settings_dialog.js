// app/static/js/ocr_settings_dialog.js

class OCRSettingsDialog {
  constructor() {
    this.currentEngine = null;
    this.currentSettings = {};
    this.availableEngines = {};
    
    this.initializeModal();
  }

  initializeModal() {
    // モーダルが既に存在する場合は削除
    const existingModal = document.getElementById('ocr-settings-modal');
    if (existingModal) {
      existingModal.remove();
    }

    // モーダルHTML作成
    const modalHTML = `
      <div id="ocr-settings-modal" class="modal" style="display: none;">
        <div class="modal-content" style="max-width: 900px; max-height: 85vh;">
          <div class="modal-header" style="display: flex; justify-content: space-between; align-items: center; padding: 15px 20px; border-bottom: 1px solid #e9ecef;">
            <h3 id="ocr-settings-title" style="margin: 0; font-size: 18px;">🔍 OCRエンジン設定</h3>
            <div style="display: flex; gap: 8px;">
              <button type="button" class="btn-primary" id="ocr-settings-save" style="padding: 4px 12px; font-size: 12px; height: auto;">保存</button>
              <button type="button" class="btn-secondary" id="ocr-settings-close" style="padding: 4px 12px; font-size: 12px; height: auto;">閉じる</button>
            </div>
          </div>
          <div id="ocr-settings-content" style="max-height: 65vh; overflow-y: auto; padding: 10px 20px;">
            <!-- 動的に生成される設定項目 -->
          </div>
        </div>
      </div>
    `;

    document.body.insertAdjacentHTML('beforeend', modalHTML);

    // イベントリスナー設定
    document.getElementById('ocr-settings-close').addEventListener('click', () => this.hide());
    document.getElementById('ocr-settings-save').addEventListener('click', () => this.save());
    
    // モーダル外クリックで閉じる
    document.getElementById('ocr-settings-modal').addEventListener('click', (e) => {
      if (e.target.id === 'ocr-settings-modal') {
        this.hide();
      }
    });
  }

  async show(engineId, availableEngines = {}) {
    this.currentEngine = engineId;
    this.availableEngines = availableEngines;
    
    // タイトル更新
    const engineName = availableEngines[engineId]?.name || engineId;
    document.getElementById('ocr-settings-title').textContent = `🔍 OCRエンジン設定（${engineName}）`;
    
    // 設定項目を読み込み
    await this.loadEngineParameters(engineId);
    
    // モーダル表示
    document.getElementById('ocr-settings-modal').style.display = 'block';
  }

  hide() {
    document.getElementById('ocr-settings-modal').style.display = 'none';
  }

  async loadEngineParameters(engineId) {
    try {
      // ingestとtry_ocr両方に対応するため、両方のエンドポイントを試行
      let response;
      let data;
      
      try {
        // まずingest用のAPIを試行
        response = await fetch(`/api/ocr/engine_parameters/${encodeURIComponent(engineId)}`);
        data = await response.json();
      } catch (error) {
        // ingest用が失敗した場合、try_ocr用のAPIを試行
        response = await fetch(`/api/try_ocr/engine_parameters/${encodeURIComponent(engineId)}`);
        data = await response.json();
      }

      if (data.parameters && data.parameters.length > 0) {
        this.renderEngineParameters(data.parameters);
      } else {
        document.getElementById('ocr-settings-content').innerHTML = 
          '<p style="color:#888; text-align:center; padding:2em;">このエンジンには調整項目がありません</p>';
      }
    } catch (error) {
      document.getElementById('ocr-settings-content').innerHTML = 
        '<p style="color:#d32f2f; text-align:center; padding:2em;">パラメータの読み込みに失敗しました</p>';
      console.error('パラメータ読み込みエラー:', error);
    }
  }

  renderEngineParameters(parameters) {
    const contentDiv = document.getElementById('ocr-settings-content');
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

  createParameterItem(param) {
    const itemDiv = document.createElement('div');
    itemDiv.style.cssText = `
      display: flex;
      align-items: center;
      padding: 0;
      margin-bottom: 1px;
      background: transparent;
      border: none;
      min-height: 24px;
    `;

    // 1. 項目名（通常の太さ、左揃え）
    const labelDiv = document.createElement('div');
    labelDiv.style.cssText = `
      font-weight: normal;
      min-width: 120px;
      flex-shrink: 0;
      text-align: left;
      font-size: 12px;
    `;
    labelDiv.textContent = param.label;

    // 2. コントロール（左位置を揃える）
    const controlDiv = document.createElement('div');
    controlDiv.style.cssText = `
      min-width: 80px;
      flex-shrink: 0;
      margin-left: 12px;
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

  save() {
    // 設定を保存（実装は呼び出し元で処理）
    if (this.onSave) {
      this.onSave(this.currentEngine, this.currentSettings);
    }
    this.hide();
  }

  // 保存コールバックを設定
  setOnSave(callback) {
    this.onSave = callback;
  }

  // 現在の設定を取得
  getCurrentSettings() {
    return { ...this.currentSettings };
  }
}

// グローバルに公開
window.OCRSettingsDialog = OCRSettingsDialog;