// app/static/js/try_ocr_engine.js

class TryOcrEngine {
  constructor() {
    this.currentEngineParameters = {};
    this.ocrSettingsDialog = null;
  }

  // OCRエンジンのパラメータを読み込み
  async loadEngineParameters() {
    const engineSelect = document.getElementById("engine-select");
    const engineParametersDiv = document.getElementById("engine-parameters");
    const engineName = engineSelect.value;
    
    if (!engineName) {
      engineParametersDiv.innerHTML = '<p style="color:#888; font-size:0.9em;">OCRエンジンを選択すると、調整項目が表示されます</p>';
      return;
    }

    try {
      const response = await fetch(`/api/try_ocr/engine_parameters/${encodeURIComponent(engineName)}`);
      const data = await response.json();

      if (data.parameters && data.parameters.length > 0) {
        this.renderEngineParameters(data.parameters);
      } else {
        engineParametersDiv.innerHTML = '<p style="color:#888; font-size:0.9em;">このエンジンには調整項目がありません</p>';
      }
    } catch (error) {
      console.error('パラメータ読み込みエラー:', error);
      engineParametersDiv.innerHTML = '<p style="color:#d32f2f; font-size:0.9em;">パラメータの読み込みに失敗しました</p>';
    }
  }

  // エンジンパラメータのUI生成（カテゴリ別表示対応）
  renderEngineParameters(parameters) {
    const engineParametersDiv = document.getElementById("engine-parameters");
    engineParametersDiv.innerHTML = '';
    this.currentEngineParameters = {};

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

      // カテゴリヘッダー
      const headerDiv = document.createElement('div');
      headerDiv.className = 'category-header';
      headerDiv.innerHTML = `
        <span>${categoryName}</span>
        <span class="toggle-icon">▼</span>
      `;

      // カテゴリの折りたたみ機能
      const contentDiv = document.createElement('div');
      contentDiv.className = 'category-content';

      headerDiv.addEventListener('click', () => {
        const isCollapsed = contentDiv.classList.toggle('collapsed');
        headerDiv.classList.toggle('collapsed', isCollapsed);
      });

      categoryDiv.appendChild(headerDiv);
      categoryDiv.appendChild(contentDiv);

      // パラメータ項目を生成
      categorizedParams[categoryName].forEach(param => {
        const itemDiv = this.createParameterItem(param);
        contentDiv.appendChild(itemDiv);
      });

      engineParametersDiv.appendChild(categoryDiv);
    });
  }

  // パラメータ項目の作成
  createParameterItem(param) {
    const itemDiv = document.createElement('div');
    itemDiv.className = 'parameter-item';

    const rowDiv = document.createElement('div');
    rowDiv.className = 'parameter-row';

    // ラベル
    const labelDiv = document.createElement('div');
    labelDiv.className = 'parameter-label';
    labelDiv.textContent = param.label;

    // コントロール
    const controlDiv = document.createElement('div');
    controlDiv.className = 'parameter-control';

    let input;
    const inputId = `param-${param.name}`;

    switch (param.type) {
      case 'checkbox':
        input = document.createElement('input');
        input.type = 'checkbox';
        input.checked = param.default;
        input.id = inputId;
        input.className = 'parameter-input';
        break;

      case 'number':
        input = document.createElement('input');
        input.type = 'number';
        input.value = param.default;
        input.min = param.min || '';
        input.max = param.max || '';
        input.step = param.step || '';
        input.id = inputId;
        input.className = 'parameter-input';
        if (param.name.includes('canvas') || param.name.includes('size')) {
          input.classList.add('large-number');
        }
        break;

      case 'select':
        input = document.createElement('select');
        input.id = inputId;
        input.className = 'parameter-input';
        
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
        input.className = 'parameter-input';
        break;

      default:
        input = document.createElement('input');
        input.type = 'text';
        input.value = param.default || '';
        input.id = inputId;
        input.className = 'parameter-input';
        break;
    }

    controlDiv.appendChild(input);

    // 説明
    const descDiv = document.createElement('div');
    descDiv.className = 'parameter-description';
    descDiv.textContent = param.description || '';

    // 設定値を保存
    this.currentEngineParameters[param.name] = param.default;
    
    // 変更イベント
    input.addEventListener('change', () => {
      if (param.type === 'checkbox') {
        this.currentEngineParameters[param.name] = input.checked;
      } else if (param.type === 'number') {
        this.currentEngineParameters[param.name] = parseFloat(input.value) || 0;
      } else {
        this.currentEngineParameters[param.name] = input.value;
      }
    });

    rowDiv.appendChild(labelDiv);
    rowDiv.appendChild(controlDiv);
    rowDiv.appendChild(descDiv);
    itemDiv.appendChild(rowDiv);

    return itemDiv;
  }

  // OCR設定ダイアログの初期化
  initializeSettingsDialog() {
    this.ocrSettingsDialog = new OCRSettingsDialog();
    
    // 設定保存コールバックを設定
    this.ocrSettingsDialog.setOnSave((engineId, settings) => {
      this.currentEngineParameters = settings;
      console.log('OCR設定を保存しました:', engineId, settings);
      
      // エンジンパラメータ表示を更新
      this.loadEngineParameters();
    });
    
    // 設定ボタンのイベントリスナーを設定
    const settingsBtn = document.getElementById('ocr-settings-btn');
    if (settingsBtn) {
      settingsBtn.addEventListener('click', async () => {
        const engineSelect = document.getElementById("engine-select");
        const engineName = engineSelect.value;
        if (engineName) {
          await this.ocrSettingsDialog.show(engineName, {[engineName]: {name: engineName}});
        }
      });
    }
  }

  // 現在のエンジンパラメータを取得
  getCurrentEngineParameters() {
    // DOM要素から現在の値を取得
    const params = {};
    const paramInputs = document.querySelectorAll('.parameter-input');
    
    paramInputs.forEach(input => {
      const paramName = input.id.replace('param-', '');
      if (input.type === 'checkbox') {
        params[paramName] = input.checked;
      } else if (input.type === 'number') {
        params[paramName] = parseFloat(input.value) || 0;
      } else {
        params[paramName] = input.value;
      }
    });
    
    return params;
  }

  // 設定保存機能
  async saveSettings() {
    const engineSelect = document.getElementById("engine-select");
    const engineName = engineSelect.value;
    
    if (!engineName) {
      alert("OCRエンジンを選択してください");
      return;
    }

    const presetName = prompt("設定名を入力してください:", `${engineName}_設定`);
    if (!presetName) return;

    try {
      const response = await fetch('/api/ocr/presets/save', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          name: presetName,
          engine_id: engineName,
          settings: this.currentEngineParameters
        })
      });

      const result = await response.json();
      if (result.success) {
        alert(`設定「${presetName}」を保存しました`);
      } else {
        alert(`保存に失敗しました: ${result.error}`);
      }
    } catch (error) {
      console.error('設定保存エラー:', error);
      alert(`保存エラー: ${error.message}`);
    }
  }

  // プリセット管理機能
  async showPresets() {
    console.log('🔧 プリセットボタンがクリックされました');
    
    const engineSelect = document.getElementById("engine-select");
    const engineName = engineSelect.value;
    
    console.log('🔧 選択されたエンジン:', engineName);
    
    if (!engineName) {
      alert("OCRエンジンを選択してください");
      return;
    }

    try {
      const url = `/api/ocr/presets/list?engine_id=${encodeURIComponent(engineName)}`;
      console.log('🔧 リクエストURL:', url);
      
      const response = await fetch(url);
      console.log('🔧 レスポンスステータス:', response.status);
      
      const result = await response.json();
      console.log('🔧 レスポンス内容:', result);
      
      if (!result.success) {
        const errorMsg = `プリセット取得に失敗しました: ${result.error || 'サーバーエラー'}`;
        console.error('🔧 エラー:', errorMsg);
        alert(errorMsg);
        return;
      }

      const presets = result.presets || [];
      if (presets.length === 0) {
        alert("保存されたプリセットがありません");
        return;
      }

      // プリセット選択ダイアログを表示
      const presetNames = presets.map(p => p.name);
      const selectedPreset = prompt(`プリセットを選択してください:\n${presetNames.map((name, i) => `${i + 1}. ${name}`).join('\n')}\n\n番号を入力:`);
      
      if (!selectedPreset) return;
      
      const index = parseInt(selectedPreset) - 1;
      if (index < 0 || index >= presets.length) {
        alert("無効な番号です");
        return;
      }

      // プリセットを適用
      const preset = presets[index];
      this.currentEngineParameters = preset.settings || {};
      
      // UI を更新
      await this.loadEngineParameters();
      
      alert(`プリセット「${preset.name}」を適用しました`);
      
    } catch (error) {
      console.error('プリセット取得エラー:', error);
      alert(`プリセット取得エラー: ${error.message}`);
    }
  }

  // 不要になったメソッド（設定ダイアログ内で処理）
}

// グローバルに公開
window.TryOcrEngine = TryOcrEngine;