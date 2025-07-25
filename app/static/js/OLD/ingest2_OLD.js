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
      console.log('🚀 処理開始関数が呼び出されました');
      
      if (processingInProgress) {
        console.log('❌ 既に処理が実行中です');
        alert('既に処理が実行中です');
        return;
      }

      const form = document.getElementById('ingest-form');
      if (!form) {
        console.log('❌ フォーム要素が見つかりません');
        return;
      }

      console.log('📝 フォームデータを準備中...');

      // フォームデータの内容をデバッグ出力
      const inputMode = document.querySelector('input[name="input_mode"]:checked');
      console.log('入力モード:', inputMode ? inputMode.value : 'なし');
      
      const inputFolder = document.getElementById('input-folder');
      console.log('入力フォルダ:', inputFolder ? inputFolder.value : 'なし');
      
      const inputFiles = document.getElementById('input-files');
      console.log('入力ファイル:', inputFiles ? inputFiles.files.length : 'なし');

      // OCR設定をフォームに追加（ingest系と同じ処理）
      const engineId = document.getElementById('ocr-engine').value;
      console.log('OCRエンジン:', engineId);
      
      // 既存のOCR設定フィールドを削除
      const existingOCRSettings = form.querySelector('input[name="ocr_settings"]');
      const existingOCREngine = form.querySelector('input[name="ocr_engine_id"]');
      if (existingOCRSettings) existingOCRSettings.remove();
      if (existingOCREngine) existingOCREngine.remove();
      
      // OCR設定を追加
      if (engineId) {
        const ocrEngineInput = document.createElement('input');
        ocrEngineInput.type = 'hidden';
        ocrEngineInput.name = 'ocr_engine_id';
        ocrEngineInput.value = engineId;
        form.appendChild(ocrEngineInput);
        
        const ocrSettingsInput = document.createElement('input');
        ocrSettingsInput.type = 'hidden';
        ocrSettingsInput.name = 'ocr_settings';
        ocrSettingsInput.value = JSON.stringify(currentEngineSettings);
        form.appendChild(ocrSettingsInput);
        
        console.log('OCR設定を追加:', currentEngineSettings);
      }

      const formData = new FormData(form);
      
      // FormDataの内容をデバッグ出力
      console.log('📤 送信するフォームデータ:');
      for (let [key, value] of formData.entries()) {
        console.log(`  ${key}:`, value);
      }
      
      try {
        processingInProgress = true;
        setFormDisabled(true);
        
        if (startBtn) startBtn.textContent = '処理中...';
        
        if (logContent) logContent.innerHTML = '';
        addLogMessage('処理を開始しています...');

        console.log('📡 POST送信開始...');

        // ingest系と同じ処理方式：POST送信後にSSE開始
        const response = await fetch('/ingest', {
          method: 'POST',
          body: formData
        });

        console.log('📡 POST送信完了:', response.status, response.statusText);

        if (!response.ok) {
          const errorText = await response.text();
          console.error('POST /ingest error', response.status, errorText);
          throw new Error('HTTP ' + response.status + ': ' + response.statusText);
        }

        console.log('🔄 SSE処理を開始...');
        // ingest系と同じSSE処理を開始
        startIngestStream2();

      } catch (error) {
        console.error('❌ 処理エラー:', error);
        addLogMessage('エラー: ' + error.message);
        processingInProgress = false;
        setFormDisabled(false);
        if (startBtn) startBtn.textContent = '🚀 処理開始';
      }
    }

    // ===== SSE処理機能（ingest_sse.jsと同じ実装） =====
    let eventSource = null;
    let fileContainers = {};

    // ファイルコンテナを作成（元のingest_sse.jsと同じ形式）
    function createFileContainer(fileName) {
      if (fileContainers[fileName]) return;

      const container = document.createElement('div');
      container.className = 'file-container';
      
      // ファイルヘッダー（クリック可能）
      const header = document.createElement('div');
      header.className = 'file-header';
      header.style.cursor = 'pointer';
      header.style.userSelect = 'none';
      header.innerHTML = `📄 ${fileName}`;
      
      // PDFプレビュー機能
      header.addEventListener('click', () => {
        showPDFPreview(fileName);
      });
      
      // 進捗表示エリア
      const progress = document.createElement('div');
      progress.className = 'file-progress';
      progress.innerHTML = '処理中...';
      
      container.appendChild(header);
      container.appendChild(progress);
      
      logContent.appendChild(container);
      fileContainers[fileName] = { container, progress };
      
      logContent.scrollTop = logContent.scrollHeight;
    }

    // ファイル進捗を更新
    function updateFileProgress(fileName, message) {
      if (!fileContainers[fileName]) {
        createFileContainer(fileName);
      }
      
      const { progress } = fileContainers[fileName];
      progress.innerHTML = message;
      
      logContent.scrollTop = logContent.scrollHeight;
    }

    // PDFプレビュー表示（file_idとfileNameの両方に対応）
    function showPDFPreview(fileIdOrName, fileName) {
      console.log('PDFプレビュー:', fileIdOrName, fileName);
      
      // PDFのURLを構築（file_idがある場合はそれを使用、なければファイル名）
      const pdfUrl = `/api/pdf/${encodeURIComponent(fileIdOrName)}`;
      
      // 現在のレイアウトに応じてPDF表示
      if (currentLayout === 'no-preview') {
        // PDFプレビューなしモードの場合、第1パターンに切り替え
        switchLayout('pattern1');
      }
      
      // PDFフレームにURLを設定
      if (pdfFrame) {
        pdfFrame.src = pdfUrl;
        currentPdfUrl = pdfUrl;
      }
    }

    // 単純なテキスト行を生成（元のingest_sse.jsと同じ）
    function createLine(text, cls) {
      const div = document.createElement("div");
      if (cls) div.className = cls;
      div.textContent = text;
      return div;
    }

    // 自動スクロール（元のingest_sse.jsと同じ）
    function scrollBottom(el) {
      const threshold = 32;
      const distance = el.scrollHeight - el.scrollTop - el.clientHeight;
      if (distance <= threshold) el.scrollTop = el.scrollHeight;
    }

    function startIngestStream2() {
      console.log('🔄 SSE接続を開始...');
      
      // 既存の接続があればクローズ
      if (eventSource) {
        console.log('🔄 既存のSSE接続をクローズ');
        eventSource.close();
        eventSource = null;
      }
      // ファイルコンテナを初期化
      fileContainers = {};

      console.log('🔄 EventSourceを作成: /ingest/stream');
      eventSource = new EventSource('/ingest/stream');

      eventSource.onopen = evt => {
        console.log('✅ SSE接続が開かれました');
      };

      eventSource.onmessage = evt => {
        console.log('📨 SSEメッセージ受信:', evt.data);
        const d = JSON.parse(evt.data);
        console.log('📨 パース済みデータ:', d);

        // cancelling イベントはログ化しない（即時フィードバックのみ）
        if (d.cancelling) {
          return;
        }

        // 全体開始イベント
        if (d.start) {
          addLogMessage(`▶ 全 ${d.total_files} 件の処理を開始`);
          return;
        }

        // 停止完了通知
        if (d.stopped) {
          addLogMessage('⏹️ 処理が停止しました');
          eventSource.close();
          processingInProgress = false;
          setFormDisabled(false);
          if (startBtn) startBtn.textContent = '🚀 処理開始';
          return;
        }

        // 全完了イベント
        if (d.done) {
          addLogMessage('✅ 全処理完了');
          eventSource.close();
          processingInProgress = false;
          setFormDisabled(false);
          if (startBtn) startBtn.textContent = '🚀 処理開始';
          return;
        }

        // 各ファイル・ステップイベント（元のingest_sse.jsと同じ詳細処理）
        const { file, step, file_id, index, total, part, content, duration } = d;

        // ファイルセクション準備
        let section = fileContainers[file];
        if (!section) {
          if (logContent) {
            logContent.appendChild(document.createElement("br"));
            logContent.appendChild(createLine(`${index}/${total} ${file} の処理中…`, "file-progress"));
            scrollBottom(logContent);

            const header = document.createElement("div");
            header.className = "file-header";
            const link = document.createElement("a");
            link.href = file_id ? `/api/pdf/${file_id}` : '#';
            link.textContent = file;
            // PDFプレビュー機能
            link.addEventListener('click', (e) => {
              e.preventDefault();
              if (file_id) {
                showPDFPreview(file_id, file);
              }
            });
            header.appendChild(link);
            logContent.appendChild(header);
            scrollBottom(logContent);

            section = document.createElement("div");
            section.className = "file-section";
            logContent.appendChild(section);
            scrollBottom(logContent);

            fileContainers[file] = section;
          }
        }

        // ページ単位の見出し
        if (step && step.startsWith("Page ")) {
          section.appendChild(createLine(step, "page-header"));
          scrollBottom(logContent);
          return;
        }

        // プロンプト全文／整形結果全文の details 初期化
        if (step.startsWith("使用プロンプト全文") || step.startsWith("LLM整形結果全文")) {
          const [title, raw] = step.split(" part:");
          const key = `${file}__${title}__${raw||"all"}`;
          if (!section.querySelector(`details[data-key="${key}"]`)) {
            const det = document.createElement("details");
            det.setAttribute("data-key", key);
            const sum = document.createElement("summary");
            sum.textContent = step;
            det.appendChild(sum);
            section.appendChild(det);
            scrollBottom(logContent);
          }
          return;
        }

        // プロンプト／整形結果のテキスト挿入
        if (step === "prompt_text" || step === "refined_text") {
          const title = step === "prompt_text" ? "使用プロンプト全文" : "LLM整形結果全文";
          const key = `${file}__${title}__${part||"all"}`;
          const det = section.querySelector(`details[data-key="${key}"]`);
          if (det) {
            let pre = det.querySelector("pre");
            if (!pre) {
              pre = document.createElement("pre");
              det.appendChild(pre);
            }
            pre.textContent = (content || "").replace(/\n{3,}/g, "\n\n");
            scrollBottom(logContent);
          }
          return;
        }

        // 進捗更新の場合は同じ行を上書き
        if (d.is_progress_update && d.page_id) {
          // 既存の進捗行を検索
          const existingProgress = section.querySelector(`[data-page-id="${d.page_id}"]`);
          if (existingProgress) {
            // 既存の行を更新
            existingProgress.textContent = step;
          } else {
            // 新しい進捗行を作成
            const progressLine = createLine(step);
            progressLine.setAttribute('data-page-id', d.page_id);
            section.appendChild(progressLine);
          }
        } else if (step) {
          // 通常ログ行
          const label = duration ? `${step} (${duration}s)` : step;
          section.appendChild(createLine(label));
        }
        scrollBottom(logContent);
      };

      eventSource.onerror = evt => {
        console.error('SSE接続エラー:', evt);
        addLogMessage('❌ 接続エラーが発生しました');
        eventSource.close();
        processingInProgress = false;
        setFormDisabled(false);
        if (startBtn) startBtn.textContent = '🚀 処理開始';
      };
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
    
    // 初期化完了をページに表示
    if (logContent) {
      logContent.innerHTML = '<div style="color: green; font-weight: bold;">✅ ingest2.js 初期化完了</div>';
    }
    
    // 処理開始ボタンにテスト用のクリックイベントを追加
    if (startBtn) {
      console.log('✅ 処理開始ボタンが見つかりました');
      // ボタンクリック時の基本動作確認
      startBtn.addEventListener('click', () => {
        console.log('🔥 処理開始ボタンがクリックされました！');
        if (logContent) {
          logContent.innerHTML += '<div style="color: blue;">🔥 処理開始ボタンがクリックされました</div>';
        }
      });
    } else {
      console.log('❌ 処理開始ボタンが見つかりません');
    }
  });
})();