// app/static/js/try_ocr_pdf.js

class TryOcrPdf {
  constructor() {
    this.selectedFile = null;
    this.totalPages = 0;
  }

  // PDFの総ページ数を取得する関数（PDF.js使用）
  async getPdfPageCount(file) {
    return new Promise((resolve) => {
      try {
        if (window.pdfjsLib) {
          const reader = new FileReader();
          reader.onload = async (e) => {
            try {
              const typedarray = new Uint8Array(e.target.result);
              const pdf = await pdfjsLib.getDocument(typedarray).promise;
              resolve(pdf.numPages);
            } catch (error) {
              console.error('PDF読み込みエラー:', error);
              resolve(1);
            }
          };
          reader.readAsArrayBuffer(file);
        } else {
          console.warn('PDF.jsが利用できません');
          resolve(1);
        }
      } catch (error) {
        console.error('PDFページ数取得エラー:', error);
        resolve(1);
      }
    });
  }

  // PDF表示の切り替え
  async updatePdfDisplay() {
    const pdfPane = document.getElementById("pdf-pane");
    const pdfViewer = document.getElementById("pdf-viewer");
    const pdfMode = document.querySelector('input[name="pdf_mode"]:checked').value;

    if (pdfMode === "hide") {
      pdfPane.style.display = "none";
      return;
    }

    pdfPane.style.display = "block";

    if (this.selectedFile) {
      const pageNum = parseInt(document.getElementById("page-num").value) || 1;
      const fileUrl = URL.createObjectURL(this.selectedFile);
      
      if (pageNum === 0) {
        pdfViewer.src = `${fileUrl}#view=FitH`;
      } else {
        pdfViewer.src = `${fileUrl}#page=${pageNum}&view=FitH`;
      }
    }
  }

  // ページ番号の検証と修正
  validateAndCorrectPageNumber() {
    const pageNumInput = document.getElementById("page-num");
    let pageNum = parseInt(pageNumInput.value) || 1;

    if (pageNum < 0) {
      pageNum = 0;
    } else if (pageNum > this.totalPages && this.totalPages > 0) {
      pageNum = this.totalPages;
    }

    if (parseInt(pageNumInput.value) !== pageNum) {
      pageNumInput.value = pageNum;
    }

    return pageNum;
  }

  // PDFページの更新（ページ番号検証付き）
  updatePdfPage() {
    if (this.selectedFile && document.getElementById("pdf-pane").style.display !== "none") {
      this.validateAndCorrectPageNumber();
      this.updatePdfDisplay();
    }
  }

  // ファイル選択処理
  async handleFileSelection(file) {
    this.selectedFile = file;
    
    if (file) {
      // ファイル名をテキストボックスに表示（OCR機能比較は単一ファイル用）
      const fileInput = document.getElementById("file-input");
      if (fileInput) {
        fileInput.value = file.name;
      }

      // PDFの場合、総ページ数を取得
      if (file.type === 'application/pdf') {
        this.totalPages = await this.getPdfPageCount(file);
        console.log(`PDFファイル: ${file.name}, 総ページ数: ${this.totalPages}`);
      } else {
        this.totalPages = 1;
      }

      // ページ番号の検証と修正
      this.validateAndCorrectPageNumber();
      
      // PDF表示を更新
      await this.updatePdfDisplay();
    }
  }

  // 選択されたファイルを取得
  getSelectedFile() {
    return this.selectedFile;
  }

  // 総ページ数を取得
  getTotalPages() {
    return this.totalPages;
  }
}

// グローバルに公開
window.TryOcrPdf = TryOcrPdf;