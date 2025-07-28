// app/static/js/try_ocr_main.js

class TryOcrMain {
  constructor() {
    this.pdfManager = new TryOcrPdf();
    this.engineManager = new TryOcrEngine();
    this.uiManager = new TryOcrUI();
    this.processingInProgress = false;
    this.controller = null;
  }

  // 初期化
  initialize() {
    // UI初期化
    this.uiManager.initialize();

    // DOM要素の取得
    this.processBtn = document.getElementById("process-btn");
    this.clearBtn = document.getElementById("clear-btn");
    this.compareAllBtn = document.getElementById("compare-all-btn");
    this.engineSelect = document.getElementById("engine-select");
    this.fileInput = document.getElementById("file-input");
    this.browseFileBtn = document.getElementById("browse-file");
    this.filePicker = document.getElementById("file-picker");
    this.pageNumInput = document.getElementById("page-num");

    // イベントリスナーの設定
    this.setupEventListeners();

    // OCRエンジンパラメータの初期読み込み
    this.engineManager.loadEngineParameters();

    // OCR設定ダイアログの初期化
    this.engineManager.initializeSettingsDialog();

    // 保存・プリセットボタンの初期化
    this.engineManager.initializeButtons();
  }

  // イベントリスナーの設定
  setupEventListeners() {
    // OCR実行ボタン
    if (this.processBtn) {
      this.processBtn.addEventListener("click", () => this.processOCR());
    }

    // キャンセルボタン
    this.cancelBtn = document.getElementById("cancel-btn");
    if (this.cancelBtn) {
      this.cancelBtn.addEventListener("click", () => this.cancelProcessing());
    }

    // 結果クリアボタン
    if (this.clearBtn) {
      this.clearBtn.addEventListener("click", () => this.uiManager.clearResults());
    }

    // ページ離脱警告
    window.addEventListener('beforeunload', (e) => {
      if (this.processingInProgress) {
        e.preventDefault();
        // 現代的なブラウザでは、カスタムメッセージは表示されないが、
        // preventDefault()により離脱確認ダイアログが表示される
        return 'OCR処理中です。ページを離れますか？';
      }
    });

    // 全エンジン比較ボタン
    if (this.compareAllBtn) {
      this.compareAllBtn.addEventListener("click", () => this.compareAllEngines());
    }

    // エンジン選択変更
    if (this.engineSelect) {
      this.engineSelect.addEventListener("change", () => {
        this.engineManager.loadEngineParameters();
      });
    }

    // ファイル選択
    if (this.browseFileBtn && this.filePicker) {
      this.browseFileBtn.addEventListener("click", () => {
        this.filePicker.click();
      });

      this.filePicker.addEventListener("change", (e) => {
        if (e.target.files.length > 0) {
          this.pdfManager.handleFileSelection(e.target.files[0]);
        }
      });
    }

    // ファイル入力フィールドの変更
    if (this.fileInput) {
      this.fileInput.addEventListener("change", () => {
        this.pdfManager.updatePdfPage();
      });
    }

    // ページ番号変更
    if (this.pageNumInput) {
      this.pageNumInput.addEventListener("change", () => {
        this.pdfManager.updatePdfPage();
      });
    }

    // PDF表示モード変更
    const pdfModeRadios = document.querySelectorAll('input[name="pdf_mode"]');
    pdfModeRadios.forEach(radio => {
      radio.addEventListener("change", () => {
        this.pdfManager.updatePdfDisplay();
      });
    });
  }

  // OCR処理実行
  async processOCR() {
    if (this.processingInProgress) {
      alert("既に処理が実行中です");
      return;
    }

    const selectedFile = this.pdfManager.getSelectedFile();
    const engineName = this.engineSelect.value;
    const pageNum = parseInt(this.pageNumInput.value) || 1;

    if (!selectedFile) {
      alert("ファイルを選択してください");
      return;
    }

    if (!engineName) {
      alert("OCRエンジンを選択してください");
      return;
    }

    this.processingInProgress = true;
    this.setFormDisabled(true);
    this.uiManager.showProcessing();
    this.uiManager.showProcessingStatus();

    try {
      this.controller = new AbortController();
      
      const formData = new FormData();
      formData.append("file", selectedFile);
      formData.append("engine_name", engineName);
      formData.append("page_num", pageNum);

      // 誤字修正チェックボックスの値を追加
      const useCorrectionCheckbox = document.getElementById("use-correction-dict");
      formData.append("use_correction", useCorrectionCheckbox ? useCorrectionCheckbox.checked : false);

      // エンジンパラメータを追加
      const engineParams = this.engineManager.getCurrentEngineParameters();
      Object.keys(engineParams).forEach(key => {
        formData.append(`param_${key}`, engineParams[key]);
      });

      const response = await fetch("/api/try_ocr/process", {
        method: "POST",
        body: formData,
        signal: this.controller.signal
      });

      const result = await response.json();

      if (result.success) {
        this.uiManager.displayResult(result);
      } else {
        this.uiManager.displayError(result.error || "OCR処理に失敗しました");
      }
    } catch (error) {
      if (error.name === 'AbortError') {
        this.uiManager.displayError("OCR処理がキャンセルされました");
      } else {
        console.error("OCR処理エラー:", error);
        this.uiManager.displayError(`処理エラー: ${error.message}`);
      }
    } finally {
      this.onProcessingComplete();
    }
  }

  // キャンセル処理
  async cancelProcessing() {
    if (!this.processingInProgress) return;
    
    if (!confirm('OCR処理をキャンセルしますか？')) return;

    try {
      if (this.controller) {
        this.controller.abort();
      }
      this.uiManager.updateProcessingProgress('キャンセル中...');
    } catch (error) {
      console.error('キャンセルエラー:', error);
    }
  }

  // 処理完了時の処理
  onProcessingComplete() {
    this.processingInProgress = false;
    this.controller = null;
    this.setFormDisabled(false);
    this.uiManager.hideProcessing();
    this.uiManager.hideProcessingStatus();
  }

  // フォーム要素の有効/無効切り替え
  setFormDisabled(disabled) {
    if (this.processBtn) this.processBtn.disabled = disabled;
    if (this.compareAllBtn) this.compareAllBtn.disabled = disabled;
    if (this.engineSelect) this.engineSelect.disabled = disabled;
    if (this.pageNumInput) this.pageNumInput.disabled = disabled;
    if (this.browseFileBtn) this.browseFileBtn.disabled = disabled;
    if (this.cancelBtn) this.cancelBtn.disabled = !disabled;
  }



  // 全エンジン比較
  async compareAllEngines() {
    if (this.processingInProgress) {
      alert("既に処理が実行中です");
      return;
    }

    const selectedFile = this.pdfManager.getSelectedFile();
    const pageNum = parseInt(this.pageNumInput.value) || 1;

    if (!selectedFile) {
      alert("ファイルを選択してください");
      return;
    }

    // 利用可能なエンジンを取得
    const engines = [];
    for (let i = 0; i < this.engineSelect.options.length; i++) {
      const option = this.engineSelect.options[i];
      if (option.value) {
        engines.push(option.value);
      }
    }

    if (engines.length === 0) {
      alert("利用可能なOCRエンジンがありません");
      return;
    }

    this.processingInProgress = true;
    this.setFormDisabled(true);
    this.uiManager.showProcessing();
    this.uiManager.showProcessingStatus();

    try {
      this.controller = new AbortController();
      
      // 各エンジンで順次処理
      for (const engineName of engines) {
        // キャンセルチェック
        if (this.controller.signal.aborted) {
          break;
        }

        this.uiManager.updateProcessingProgress(`${engineName} で処理中...`);

        const formData = new FormData();
        formData.append("file", selectedFile);
        formData.append("engine_name", engineName);
        formData.append("page_num", pageNum);

        // 誤字修正チェックボックスの値を追加
        const useCorrectionCheckbox = document.getElementById("use-correction-dict");
        formData.append("use_correction", useCorrectionCheckbox ? useCorrectionCheckbox.checked : false);

        try {
          const response = await fetch("/api/try_ocr/process", {
            method: "POST",
            body: formData,
            signal: this.controller.signal
          });

          const result = await response.json();

          if (result.success) {
            this.uiManager.displayResult(result);
          } else {
            this.uiManager.displayError(`${engineName}: ${result.error || "処理に失敗しました"}`);
          }
        } catch (error) {
          if (error.name === 'AbortError') {
            this.uiManager.displayError(`${engineName}: 処理がキャンセルされました`);
            break;
          } else {
            console.error(`${engineName} エラー:`, error);
            this.uiManager.displayError(`${engineName}: ${error.message}`);
          }
        }

        // 次のエンジン処理前に少し待機（キャンセルチェック付き）
        if (!this.controller.signal.aborted) {
          await new Promise(resolve => setTimeout(resolve, 500));
        }
      }
    } finally {
      this.onProcessingComplete();
    }
  }
}

// ページ読み込み時の初期化
document.addEventListener("DOMContentLoaded", () => {
  const tryOcrMain = new TryOcrMain();
  tryOcrMain.initialize();
  
  // グローバルに公開（デバッグ用）
  window.tryOcrMain = tryOcrMain;
});