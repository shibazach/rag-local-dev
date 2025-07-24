// app/static/js/ingest2.js @作成日時: 2025-07-24
// REM: 設定パネル動的移動方式による統合レイアウトシステム

(function() {
  document.addEventListener("DOMContentLoaded", () => {
    // ===== 基本要素の取得 =====
    const appContainer = document.getElementById('app-container');
    const pattern1Btn = document.getElementById('pattern1-btn');
    const pattern2Btn = document.getElementById('pattern2-btn');
    const pdfFrame = document.getElementById('pdf-frame');
    const logContent = document.getElementById('log-content');
    
    // 設定パネル関連
    const settingsPanel = document.getElementById('settings-panel');
    const topContainer = document.getElementById('top-container');
    const leftContainer = document.getElementById('left-container');
    
    // 現在の状態
    let currentLayout = 'no-preview';
    let currentPdfUrl = null;
    let processingInProgress = false;
    let availableEngines = {}; // OCRエンジン情報を保存

    // ===== レイアウト切り替え機能 =====
    function switchLayout(layout) {
      console.log('レイアウト切り替え:', currentLayout, '→', layout);
      
      // 既存クラスを削除
      appContainer.classList.remove('layout-no-preview', 'layout-pattern1', 'layout-pattern2');
      pattern1Btn.classList.remove('active');
      pattern2Btn.classList.remove('active');
      
      // 新しいクラスを追加と設定パネル移動
      switch (layout) {
        case 'pattern1':
          appContainer.classList.add('layout-pattern1');
          pattern1Btn.classList.add('active');
          // 設定パネルを上部に移動
          if (settingsPanel && topContainer) {
            topContainer.appendChild(settingsPanel);
          }
          break;
        case 'pattern2':
          appContainer.classList.add('layout-pattern2');
          pattern2Btn.classList.add('active');
          // 設定パネルを左側に移動
          if (settingsPanel && leftContainer) {
            leftContainer.appendChild(settingsPanel);
          }
          break;
        default:
          appContainer.classList.add('layout-no-preview');
          // 設定パネルを左側に移動（デフォルト位置）
          if (settingsPanel && leftContainer) {
            leftContainer.appendChild(settingsPanel);
          }
          break;
      }
      
      currentLayout = layout;
      
      // PDFフレームの制御
      if (currentPdfUrl && (layout === 'pattern1' || layout === 'pattern2')) {
        if (pdfFrame) pdfFrame.src = currentPdfUrl;
      } else if (layout === 'no-preview') {
        if (pdfFrame) pdfFrame.src = '';
      }
    }

    // ボタンイベント
    if (pattern1Btn) pattern1Btn.addEventListener('click', () => switchLayout('pattern1'));
    if (pattern2Btn) pattern2Btn.addEventListener('click', () => switchLayout('pattern2'));

    // ===== リサイズ機能 =====
    function initializeResizers() {
      let isResizing = false;
      let currentResizer = null;

      // リサイザー要素
      const topResizer = document.getElementById('top-resizer');
      const leftResizer = document.getElementById('left-resizer');
      const verticalResizer = document.getElementById('vertical-resizer');

      function startResize(resizer, cursor, e) {
        isResizing = true;
        currentResizer = resizer;
        document.body.style.cursor = cursor;
        document.body.style.userSelect = 'none';
        
        // オーバーレイ追加
        addResizeOverlay();
        e.preventDefault();
      }

      function addResizeOverlay() {
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

      function removeResizeOverlay() {
        const overlay = document.getElementById('resize-overlay');
        if (overlay) overlay.remove();
      }

      // マウスイベント
      document.addEventListener('mousemove', (e) => {
        if (!isResizing) return;

        if (currentResizer === 'top') {
          // 第1パターン：上部設定の高さ調整
          const container = appContainer.getBoundingClientRect();
          const relativeY = e.clientY - container.top;
          const minHeight = container.height * 0.2;
          const maxHeight = container.height * 0.6;
          
          if (relativeY >= minHeight && relativeY <= maxHeight) {
            const topEl = document.getElementById('top-container');
            if (topEl) {
              topEl.style.flex = '0 0 ' + (relativeY - 5) + 'px';
            }
          }
        } else if (currentResizer === 'left') {
          // 第2パターン：左側設定の高さ調整
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
        } else if (currentResizer === 'vertical') {
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
      });

      document.addEventListener('mouseup', () => {
        if (isResizing) {
          isResizing = false;
          currentResizer = null;
          document.body.style.cursor = '';
          document.body.style.userSelect = '';
          removeResizeOverlay();
        }
      });

      // リサイザーのイベント
      if (topResizer) {
        topResizer.addEventListener('mousedown', (e) => startResize('top', 'row-resize', e));
      }
      if (leftResizer) {
        leftResizer.addEventListener('mousedown', (e) => startResize('left', 'row-resize', e));
      }
      if (verticalResizer) {
        verticalResizer.addEventListener('mousedown', (e) => startResize('vertical', 'col-resize', e));
      }
    }

    // ===== 入力モード切り替え機能 =====
    function initializeInputModeToggle() {
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

    // ===== 処理機能 =====
    const startBtn = document.getElementById('start-btn');
    const cancelBtn = document.getElementById('cancel-btn');

    function setFormDisabled(disabled) {
      // フォーム要素の無効化/有効化
      const form = document.getElementById('ingest-form');
      if (form) {
        const elements = form.querySelectorAll('input, select, button');
        elements.forEach(el => {
          if (el.name !== 'pdf_mode') el.disabled = disabled;
        });
      }
      
      if (cancelBtn) cancelBtn.disabled = !disabled;
    }

    function addLogMessage(message) {
      if (!logContent) return;
      const timestamp = new Date().toLocaleTimeString();
      const line = document.createElement('div');
      line.innerHTML = '<span style="color: #666; font-size: 11px;">[' + timestamp + ']</span> ' + message;
      logContent.appendChild(line);
      logContent.scrollTop = logContent.scrollHeight;
    }

    // SSE処理を含む本格的な処理開始機能
    async function startProcessing() {
      if (processingInProgress) {
        alert('既に処理が実行中です');
        return;
      }

      const form = document.getElementById('ingest-form');
      if (!form) return;

      const formData = new FormData(form);
      
      try {
        processingInProgress = true;
        setFormDisabled(true);
        
        if (startBtn) startBtn.textContent = '処理中...';
        
        if (logContent) logContent.innerHTML = '';
        addLogMessage('処理を開始しています...');

        // SSEストリーミング処理
        const response = await fetch('/ingest', {
          method: 'POST',
          body: formData
        });

        if (!response.ok) {
          throw new Error('HTTP ' + response.status + ': ' + response.statusText);
        }

        // レスポンスがSSEの場合の処理
        if (response.headers.get('content-type')?.includes('text/event-stream')) {
          const reader = response.body.getReader();
          const decoder = new TextDecoder();

          while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            const chunk = decoder.decode(value);
            const lines = chunk.split('\n');

            for (const line of lines) {
              if (line.startsWith('data: ')) {
                try {
                  const data = JSON.parse(line.substring(6));
                  if (data.file && data.step) {
                    addLogMessage(data.file + ': ' + data.step);
                  } else if (data.done) {
                    addLogMessage('全ての処理が完了しました');
                  }
                } catch (e) {
                  // JSONパースエラーは無視
                }
              }
            }
          }
        } else {
          addLogMessage('処理が完了しました');
        }

      } catch (error) {
        console.error('処理エラー:', error);
        addLogMessage('エラー: ' + error.message);
      } finally {
        processingInProgress = false;
        setFormDisabled(false);
        
        if (startBtn) startBtn.textContent = '🚀 処理開始';
      }
    }

    async function cancelProcessing() {
      if (!processingInProgress) return;
      
      if (!confirm('処理をキャンセルしますか？')) return;

      try {
        await fetch('/ingest/cancel', { method: 'POST' });
        addLogMessage('処理をキャンセルしました');
      } catch (error) {
        console.error('キャンセルエラー:', error);
        addLogMessage('キャンセルエラー: ' + error.message);
      }

      processingInProgress = false;
      setFormDisabled(false);
      
      if (startBtn) startBtn.textContent = '🚀 処理開始';
    }

    // ===== プロンプト確認機能 =====
    const promptEditBtn = document.getElementById('prompt-edit-btn');

    async function showPromptModal() {
      const promptSelect = document.getElementById('refine-prompt');
      const promptKey = promptSelect ? promptSelect.value : '';
      
      if (!promptKey) {
        alert('プロンプトを選択してください');
        return;
      }

      try {
        // 元のingest.jsと同じAPIエンドポイントを使用
        const response = await fetch('/api/refine_prompt?key=' + encodeURIComponent(promptKey));
        const promptText = await response.text();
        
        // モーダルを動的作成
        const modal = document.createElement('div');
        modal.className = 'modal';
        modal.innerHTML = '<div class="modal-content">' +
          '<div class="modal-header">' +
          '<h3>📝 プロンプト確認: ' + promptKey + '</h3>' +
          '<span class="close">&times;</span>' +
          '</div>' +
          '<div style="margin-bottom: 20px;">' +
          '<textarea readonly style="width: 100%; height: 300px; font-family: monospace; font-size: 13px; padding: 10px; border: 1px solid #ddd; border-radius: 4px; resize: vertical;">' + promptText + '</textarea>' +
          '</div>' +
          '<div class="modal-actions">' +
          '<button type="button" class="btn-secondary">閉じる</button>' +
          '</div>' +
          '</div>';
        
        document.body.appendChild(modal);
        modal.style.display = 'block';
        
        // 閉じるイベント
        const closeBtn = modal.querySelector('.close');
        const cancelBtn = modal.querySelector('.btn-secondary');
        
        function closeModal() {
          modal.remove();
        }
        
        if (closeBtn) closeBtn.addEventListener('click', closeModal);
        if (cancelBtn) cancelBtn.addEventListener('click', closeModal);
        modal.addEventListener('click', (e) => {
          if (e.target === modal) closeModal();
        });
        
      } catch (error) {
        console.error('プロンプト取得エラー:', error);
        alert('プロンプトの取得に失敗しました');
      }
    }

    if (promptEditBtn) promptEditBtn.addEventListener('click', showPromptModal);

    // ===== OCR機能 =====
    async function loadOCREngines() {
      try {
        const response = await fetch('/ingest/ocr/engines');
        const engines = await response.json();
        
        // エンジン情報を保存
        availableEngines = engines;

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
            
            // EasyOCRを初期値に設定
            if (engineId === 'easyocr' && engineInfo.available) {
              option.selected = true;
              easyOCRFound = true;
            }
          }
          
          // EasyOCRが見つからない場合は最初の利用可能なエンジンを選択
          if (!easyOCRFound) {
            for (const engineId in engines) {
              const engineInfo = engines[engineId];
              if (engineInfo.available) {
                select.value = engineId;
                break;
              }
            }
          }
        }
      } catch (error) {
        console.error('OCRエンジン一覧の読み込みに失敗:', error);
      }
    }

    // OCR設定表示（ingest.htmlと同じ実装）
    let currentEngineSettings = {};

    async function loadEngineSettings(engineId) {
      try {
        const response = await fetch('/ingest/ocr/settings/' + engineId);
        const data = await response.json();
        currentEngineSettings = data.settings;
      } catch (error) {
        console.error('エンジン設定の読み込みに失敗:', error);
        currentEngineSettings = {};
      }
    }

    function showOCRSettings() {
      const engineSelect = document.getElementById('ocr-engine');
      const engineId = engineSelect ? engineSelect.value : '';
      if (!engineId) {
        alert('OCRエンジンを選択してください');
        return;
      }
      showOCRSettingsModal(engineId);
    }

    function showOCRSettingsModal(engineId) {
      const modal = document.getElementById('ocr-settings-modal');
      const content = document.getElementById('ocr-settings-content');

      if (!availableEngines[engineId]) {
        alert('エンジン情報が見つかりません');
        return;
      }

      const engineInfo = availableEngines[engineId];
      const parameters = engineInfo.parameters || [];

      // 設定項目を動的生成
      content.innerHTML = '';

      if (parameters.length === 0) {
        content.innerHTML = '<p>このエンジンには設定可能なパラメータがありません。</p>';
      } else {
        parameters.forEach(param => {
          const group = document.createElement('div');
          group.className = 'ocr-setting-group';

          const label = document.createElement('label');
          label.textContent = param.label;
          group.appendChild(label);

          let input;
          const currentValue = currentEngineSettings[param.name] !== undefined
            ? currentEngineSettings[param.name]
            : param.default;

          if (param.type === 'checkbox') {
            input = document.createElement('input');
            input.type = 'checkbox';
            input.checked = currentValue;
          } else if (param.type === 'number') {
            input = document.createElement('input');
            input.type = 'number';
            input.value = currentValue;
            if (param.min !== undefined) input.min = param.min;
            if (param.max !== undefined) input.max = param.max;
            if (param.step !== undefined) input.step = param.step;
          } else if (param.type === 'select') {
            input = document.createElement('select');
            param.options.forEach(option => {
              const opt = document.createElement('option');
              opt.value = option.value;
              opt.textContent = option.label;
              opt.selected = option.value === currentValue;
              input.appendChild(opt);
            });
          } else {
            input = document.createElement('input');
            input.type = 'text';
            input.value = currentValue;
          }

          input.dataset.paramName = param.name;
          group.appendChild(input);

          if (param.description) {
            const desc = document.createElement('div');
            desc.className = 'ocr-setting-description';
            desc.textContent = param.description;
            group.appendChild(desc);
          }

          content.appendChild(group);
        });
      }

      modal.style.display = 'block';
    }

    // OCR設定を保存
    async function saveOCRSettings() {
      const engineId = document.getElementById('ocr-engine').value;
      if (!engineId) return;

      const settings = {};
      const inputs = document.querySelectorAll('#ocr-settings-content input, #ocr-settings-content select');

      inputs.forEach(input => {
        const paramName = input.dataset.paramName;
        if (paramName) {
          if (input.type === 'checkbox') {
            settings[paramName] = input.checked;
          } else if (input.type === 'number') {
            settings[paramName] = parseFloat(input.value);
          } else {
            settings[paramName] = input.value;
          }
        }
      });

      try {
        const response = await fetch('/ingest/ocr/settings/' + engineId, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(settings)
        });

        if (response.ok) {
          currentEngineSettings = settings;
          alert('設定を保存しました');
          closeOCRSettingsModal();
        } else {
          alert('設定の保存に失敗しました');
        }
      } catch (error) {
        console.error('設定保存エラー:', error);
        alert('設定の保存に失敗しました');
      }
    }

    function closeOCRSettingsModal() {
      document.getElementById('ocr-settings-modal').style.display = 'none';
    }

    // OCRプリセット表示（簡略版）
    function showOCRPresets() {
      const modal = document.getElementById('ocr-presets-modal');
      const list = document.getElementById('ocr-presets-list');
      
      if (!modal || !list) return;
      
      list.innerHTML = '<p>プリセット機能は開発中です。</p>';
      modal.style.display = 'block';
    }

    // OCRエンジン変更時の設定読み込み
    const ocrEngineSelect = document.getElementById('ocr-engine');
    if (ocrEngineSelect) {
      ocrEngineSelect.addEventListener('change', async () => {
        const engineId = ocrEngineSelect.value;
        if (engineId) {
          await loadEngineSettings(engineId);
        }
      });
    }

    // OCRボタンのイベント
    const ocrSettingsBtn = document.getElementById('ocr-settings-btn');
    const ocrPresetsBtn = document.getElementById('ocr-presets-btn');

    if (ocrSettingsBtn) ocrSettingsBtn.addEventListener('click', showOCRSettings);
    if (ocrPresetsBtn) ocrPresetsBtn.addEventListener('click', showOCRPresets);

    // モーダルの閉じるボタン
    const ocrSettingsClose = document.getElementById('ocr-settings-close');
    const ocrSettingsCancel = document.getElementById('ocr-settings-cancel');
    const ocrSettingsSave = document.getElementById('ocr-settings-save');
    const ocrPresetsClose = document.getElementById('ocr-presets-close');
    const ocrPresetsCancel = document.getElementById('ocr-presets-cancel');

    if (ocrSettingsClose) ocrSettingsClose.addEventListener('click', closeOCRSettingsModal);
    if (ocrSettingsCancel) ocrSettingsCancel.addEventListener('click', closeOCRSettingsModal);
    if (ocrSettingsSave) ocrSettingsSave.addEventListener('click', saveOCRSettings);
    if (ocrPresetsClose) {
      ocrPresetsClose.addEventListener('click', () => {
        const modal = document.getElementById('ocr-presets-modal');
        if (modal) modal.style.display = 'none';
      });
    }
    if (ocrPresetsCancel) {
      ocrPresetsCancel.addEventListener('click', () => {
        const modal = document.getElementById('ocr-presets-modal');
        if (modal) modal.style.display = 'none';
      });
    }

    // ===== フォルダブラウズ機能（元のingest.jsから移植） =====
    function initializeFolderBrowse() {
      const inputEl = document.getElementById('input-folder');
      const overlay = document.getElementById('folder-overlay');
      const dlg = document.getElementById('folder-dialog');
      const listEl = document.getElementById('folder-list');
      const bcEl = document.getElementById('folder-breadcrumbs');
      
      if (!inputEl || !overlay || !dlg || !listEl || !bcEl) return;
      
      let basePath = inputEl.value || 'ignored/input_files';
      let currentPath = basePath;
      
      // 初期値を設定
      if (!inputEl.value) {
        inputEl.value = basePath;
      }

      async function loadFolders(path) {
        currentPath = path;
        bcEl.textContent = '/' + (path || '');
        try {
          const res = await fetch('/api/list-folders?path=' + encodeURIComponent(path || ''));
          if (!res.ok) throw new Error('フォルダ取得失敗');
          const { folders = [] } = await res.json();
          listEl.innerHTML = '';
          
          if (currentPath !== basePath) {
            const up = document.createElement('li');
            up.textContent = '🔙 上へ';
            up.onclick = () => loadFolders(currentPath.split('/').slice(0, -1).join('/'));
            listEl.appendChild(up);
          }
          
          folders.forEach(name => {
            const li = document.createElement('li');
            li.textContent = name;
            li.onclick = () => loadFolders(path ? path + '/' + name : name);
            li.ondblclick = () => { 
              inputEl.value = path ? path + '/' + name : name; 
              closeDialog(); 
            };
            listEl.appendChild(li);
          });
        } catch (error) {
          console.error('フォルダ読み込みエラー:', error);
        }
      }
      
      function openDialog() { 
        overlay.style.display = 'block';
        dlg.style.display = 'block';
        loadFolders(basePath); 
      }
      
      function closeDialog() { 
        overlay.style.display = 'none';
        dlg.style.display = 'none';
      }

      const browseBtn = document.getElementById('browse-folder');
      const closeBtn = document.getElementById('close-folder-dialog');
      const confirmBtn = document.getElementById('confirm-folder');
      
      if (browseBtn) browseBtn.onclick = openDialog;
      if (closeBtn) closeBtn.onclick = closeDialog;
      if (confirmBtn) {
        confirmBtn.onclick = () => { 
          inputEl.value = currentPath; 
          basePath = currentPath; // basePathも更新
          closeDialog(); 
        };
      }
      if (overlay) {
        overlay.onclick = (e) => {
          if (e.target === overlay) closeDialog();
        };
      }
    }

    // ===== ファイル選択表示機能 =====
    function initializeFileDisplay() {
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

    // ===== イベントリスナー設定 =====
    if (startBtn) startBtn.addEventListener('click', startProcessing);
    if (cancelBtn) cancelBtn.addEventListener('click', cancelProcessing);

    // ページ離脱警告
    window.addEventListener('beforeunload', (e) => {
      if (processingInProgress) {
        e.preventDefault();
        e.returnValue = 'データ処理中です。ページを離れると処理が中断されます。';
        return e.returnValue;
      }
    });

    // ===== 初期化 =====
    switchLayout('no-preview'); // 初期レイアウト
    initializeResizers(); // リサイズ機能初期化
    initializeInputModeToggle(); // 入力モード切り替え初期化
    initializeFolderBrowse(); // フォルダブラウズ初期化
    initializeFileDisplay(); // ファイル選択表示初期化
    loadOCREngines(); // OCRエンジン一覧を読み込み
    
    // 初期状態でキャンセルボタンを無効化
    if (cancelBtn) cancelBtn.disabled = true;
    
    console.log('ingest2.js 初期化完了');
  });
})();