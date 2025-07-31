// app/static/js/ingest_main.js

(function() {
  document.addEventListener("DOMContentLoaded", () => {
    console.log('🚀 Ingestシステム初期化開始');

    // DOM要素の存在確認
    const requiredElements = [
      'app-container', 'settings-panel', 'top-container', 
      'left-container', 'log-content'
    ];
    
    const missingElements = requiredElements.filter(id => !document.getElementById(id));
    if (missingElements.length > 0) {
      console.error('必要なDOM要素が見つかりません:', missingElements);
      return;
    }

    // 少し遅延させてから初期化
    setTimeout(() => {
      console.log('🚀 遅延初期化開始');
      
      // 各機能モジュールのインスタンス化
      const layoutManager = new IngestLayout();
      const resizeManager = new IngestResize();
      const sseManager = new IngestSSE(layoutManager);
      const processingManager = new IngestProcessing(sseManager);
      const ocrManager = new IngestOCR(processingManager);
      
      // グローバルに公開（デバッグ用）
      window.ingestManagers = {
        layout: layoutManager,
        resize: resizeManager,
        sse: sseManager,
        processing: processingManager,
        ocr: ocrManager
      };
      
      console.log('✅ Ingestシステム初期化完了');
    }, 100); // 100ms遅延

    // プロンプト確認機能
    const promptEditBtn = document.getElementById('prompt-edit-btn');
    if (promptEditBtn) {
      promptEditBtn.addEventListener('click', showPromptModal);
    }

    // ファイル選択機能
    const browseFilesBtn = document.getElementById('browse-files');
    const inputFiles = document.getElementById('input-files');
    const selectedFilesDisplay = document.getElementById('selected-files-display');
    
    if (browseFilesBtn && inputFiles && selectedFilesDisplay) {
      browseFilesBtn.addEventListener('click', () => {
        inputFiles.click();
      });
      
      inputFiles.addEventListener('change', (e) => {
        const files = Array.from(e.target.files);
        if (files.length > 0) {
          const fileNames = files.map(f => f.name).join('\n');
          selectedFilesDisplay.value = fileNames;
        } else {
          selectedFilesDisplay.value = '';
        }
      });
    }

    async function showPromptModal() {
      const promptSelect = document.getElementById('refine-prompt');
      const promptKey = promptSelect ? promptSelect.value : '';
      
      if (!promptKey) {
        alert('プロンプトを選択してください');
        return;
      }

      try {
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


  });
})();