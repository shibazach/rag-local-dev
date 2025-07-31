// app/static/js/ingest_ocr.js

class IngestOCR {
  constructor(processingManager) {
    this.processingManager = processingManager;
    this.availableEngines = {};
    this.settingsDialog = new OCRSettingsDialog();
    
    // 設定保存コールバックを設定
    this.settingsDialog.setOnSave((engineId, settings) => {
      this.processingManager.setCurrentEngineSettings(settings);
      console.log('OCR設定を保存しました:', engineId, settings);
    });
    
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

  async showOCRSettings() {
    const ocrEngineSelect = document.getElementById('ocr-engine');
    const currentEngine = ocrEngineSelect ? ocrEngineSelect.value : null;
    
    if (!currentEngine) {
      alert('OCRエンジンを選択してください');
      return;
    }
    
    await this.settingsDialog.show(currentEngine, this.availableEngines);
  }

  async showOCRPresets() {
    const ocrEngineSelect = document.getElementById('ocr-engine');
    const currentEngine = ocrEngineSelect ? ocrEngineSelect.value : null;
    
    if (!currentEngine) {
      alert('OCRエンジンを選択してください');
      return;
    }
    
    await this.showPresetsDialog(currentEngine);
  }

  async showPresetsDialog(engineId) {
    // プリセット一覧を取得
    let presets = {};
    try {
      const response = await fetch(`/api/ocr/presets/${engineId}`);
      if (response.ok) {
        presets = await response.json();
      }
    } catch (error) {
      console.error('プリセット読み込みエラー:', error);
    }

    // モーダルHTML作成
    const modal = document.createElement('div');
    modal.className = 'modal';
    modal.style.display = 'block';
    modal.innerHTML = `
      <div class="modal-content" style="max-width: 600px;">
        <div class="modal-header">
          <h3>📋 OCRプリセット管理（${this.availableEngines[engineId]?.name || engineId}）</h3>
          <span class="close">&times;</span>
        </div>
        <div style="margin-bottom: 20px;">
          <div style="display: flex; gap: 10px; margin-bottom: 15px;">
            <input type="text" id="preset-name" placeholder="プリセット名" style="flex: 1; padding: 8px;">
            <button type="button" id="save-preset" class="btn-primary">現在の設定を保存</button>
          </div>
          <div id="presets-list" style="max-height: 300px; overflow-y: auto; border: 1px solid #ddd; border-radius: 4px;">
            <!-- プリセット一覧がここに表示される -->
          </div>
        </div>
        <div class="modal-actions">
          <button type="button" class="btn-secondary close-btn">閉じる</button>
        </div>
      </div>
    `;

    document.body.appendChild(modal);

    // プリセット一覧を表示
    this.renderPresetsList(presets, engineId);

    // イベントリスナー設定
    const closeBtn = modal.querySelector('.close');
    const closeBtnSecondary = modal.querySelector('.close-btn');
    const savePresetBtn = modal.querySelector('#save-preset');
    const presetNameInput = modal.querySelector('#preset-name');

    function closeModal() {
      modal.remove();
    }

    closeBtn.addEventListener('click', closeModal);
    closeBtnSecondary.addEventListener('click', closeModal);
    modal.addEventListener('click', (e) => {
      if (e.target === modal) closeModal();
    });

    // プリセット保存
    savePresetBtn.addEventListener('click', async () => {
      const presetName = presetNameInput.value.trim();
      if (!presetName) {
        alert('プリセット名を入力してください');
        return;
      }

      const currentSettings = this.settingsDialog.getCurrentSettings();
      if (Object.keys(currentSettings).length === 0) {
        alert('保存する設定がありません。先にOCR設定を開いて設定を変更してください。');
        return;
      }

      try {
        const response = await fetch(`/api/ocr/presets/${engineId}`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            name: presetName,
            settings: currentSettings
          })
        });

        if (response.ok) {
          presetNameInput.value = '';
          // プリセット一覧を再読み込み
          const updatedResponse = await fetch(`/api/ocr/presets/${engineId}`);
          const updatedPresets = updatedResponse.ok ? await updatedResponse.json() : {};
          this.renderPresetsList(updatedPresets, engineId);
        } else {
          alert('プリセットの保存に失敗しました');
        }
      } catch (error) {
        console.error('プリセット保存エラー:', error);
        alert('プリセットの保存に失敗しました');
      }
    });
  }

  renderPresetsList(presets, engineId) {
    const listDiv = document.getElementById('presets-list');
    if (!listDiv) return;

    if (Object.keys(presets).length === 0) {
      listDiv.innerHTML = '<p style="text-align: center; color: #888; padding: 20px;">保存されたプリセットはありません</p>';
      return;
    }

    listDiv.innerHTML = '';

    Object.keys(presets).forEach(presetName => {
      const presetDiv = document.createElement('div');
      presetDiv.style.cssText = `
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 10px 15px;
        border-bottom: 1px solid #eee;
        background: #f9f9f9;
      `;

      const nameSpan = document.createElement('span');
      nameSpan.textContent = presetName;
      nameSpan.style.fontWeight = 'bold';

      const actionsDiv = document.createElement('div');
      actionsDiv.style.display = 'flex';
      actionsDiv.style.gap = '8px';

      // 適用ボタン
      const applyBtn = document.createElement('button');
      applyBtn.textContent = '適用';
      applyBtn.className = 'btn-primary';
      applyBtn.style.fontSize = '12px';
      applyBtn.style.padding = '4px 8px';
      applyBtn.addEventListener('click', async () => {
        try {
          const settings = presets[presetName];
          this.processingManager.setCurrentEngineSettings(settings);
          
          // 設定ダイアログが開いている場合は更新
          if (this.settingsDialog.currentSettings) {
            Object.assign(this.settingsDialog.currentSettings, settings);
          }
          
          alert(`プリセット「${presetName}」を適用しました`);
        } catch (error) {
          console.error('プリセット適用エラー:', error);
          alert('プリセットの適用に失敗しました');
        }
      });

      // 削除ボタン
      const deleteBtn = document.createElement('button');
      deleteBtn.textContent = '削除';
      deleteBtn.className = 'btn-danger';
      deleteBtn.style.fontSize = '12px';
      deleteBtn.style.padding = '4px 8px';
      deleteBtn.addEventListener('click', async () => {
        if (!confirm(`プリセット「${presetName}」を削除しますか？`)) return;

        try {
          const response = await fetch(`/api/ocr/presets/${engineId}/${encodeURIComponent(presetName)}`, {
            method: 'DELETE'
          });

          if (response.ok) {
            // プリセット一覧を再読み込み
            const updatedResponse = await fetch(`/api/ocr/presets/${engineId}`);
            const updatedPresets = updatedResponse.ok ? await updatedResponse.json() : {};
            this.renderPresetsList(updatedPresets, engineId);
          } else {
            alert('プリセットの削除に失敗しました');
          }
        } catch (error) {
          console.error('プリセット削除エラー:', error);
          alert('プリセットの削除に失敗しました');
        }
      });

      actionsDiv.appendChild(applyBtn);
      actionsDiv.appendChild(deleteBtn);

      presetDiv.appendChild(nameSpan);
      presetDiv.appendChild(actionsDiv);

      listDiv.appendChild(presetDiv);
    });
  }
}

// グローバルに公開
window.IngestOCR = IngestOCR;