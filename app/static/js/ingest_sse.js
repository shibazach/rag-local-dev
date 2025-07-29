// app/static/js/ingest_sse.js

class IngestSSE {
  constructor(layoutManager) {
    this.layoutManager = layoutManager;
    this.logContent = document.getElementById('log-content');
    this.eventSource = null;
    this.fileContainers = {};
  }

  startIngestStream() {
    console.log('🔄 SSE接続を開始...');
    
    // 既存の接続があればクローズ
    if (this.eventSource) {
      console.log('🔄 既存のSSE接続をクローズ');
      this.eventSource.close();
      this.eventSource = null;
    }
    // ファイルコンテナを初期化
    this.fileContainers = {};

    console.log('🔄 EventSourceを作成: /ingest/stream');
    this.eventSource = new EventSource('/ingest/stream');

    this.eventSource.onopen = evt => {
      console.log('✅ SSE接続が開かれました');
    };

    this.eventSource.onmessage = evt => this.handleSSEMessage(evt);

    this.eventSource.onerror = evt => {
      console.error('SSE接続エラー:', evt);
      this.addLogMessage('❌ 接続エラーが発生しました');
      this.eventSource.close();
      // 処理完了コールバックを呼び出し
      if (this.onComplete) this.onComplete();
    };
  }

  handleSSEMessage(event) {
    try {
      const data = JSON.parse(event.data);

      // キャンセルメッセージを即座に処理
      if (data.cancelling) {
        this.addLogMessage('🛑 処理をキャンセルしています...');
        if (data.message) {
          this.addLogMessage(data.message);
        }
        return;
      }

      if (data.stopped) {
        this.addLogMessage('⏹️ 処理がキャンセルされました');
        if (data.message) {
          this.addLogMessage(data.message);
        }
        return;
      }

      // 通常の処理メッセージ
      if (data.file && data.step) {
        const fileName = data.file;
        const step = data.step;
        const detail = data.detail;
        const pageId = data.page_id;
        const isProgressUpdate = data.is_progress_update;
        
        // 進捗更新メッセージの処理
        if (isProgressUpdate && pageId) {
          this.updateProgressMessage(fileName, step, detail, pageId);
        } else if (step === "ファイル登録完了" || step === "テキスト抽出完了" || step.includes("OCR完了")) {
          // 完了メッセージ（クリック可能）
          this.addClickableFileMessage(fileName, step, detail);
        } else if (step.includes("ページ") && step.includes("処理中")) {
          // ページ処理中の進捗表示
          this.addProgressMessage(fileName, step, detail, pageId);
        } else {
          // 通常のメッセージ表示
          this.addLogMessage(`${fileName}: ${step}`);
          
          // 詳細情報がある場合は追加表示
          if (detail) {
            this.addLogMessage(`  → ${detail}`);
          }
        }
      }

      // 開始・完了メッセージ
      if (data.start) {
        this.addLogMessage(`🚀 全 ${data.total_files} 件の処理を開始`);
      }
      
      if (data.done) {
        this.addLogMessage('✅ 全処理が完了しました');
      }
      
    } catch (error) {
      console.error('SSEメッセージ解析エラー:', error);
    }
  }

  addLogMessage(message) {
    if (!this.logContent) return;
    const timestamp = new Date().toLocaleTimeString();
    const line = document.createElement('div');
    line.innerHTML = '<span style="color: #666; font-size: 11px;">[' + timestamp + ']</span> ' + message;
    this.logContent.appendChild(line);
    this.logContent.scrollTop = this.logContent.scrollHeight;
    
    // フロントエンドの更新を強制
    this.forceUpdate();
  }

  forceUpdate() {
    // フロントエンドの更新を強制する
    if (this.logContent) {
      // スクロール位置を更新
      this.logContent.scrollTop = this.logContent.scrollHeight;
      
      // ブラウザの再描画を強制
      this.logContent.style.display = 'none';
      this.logContent.offsetHeight; // リフローを強制
      this.logContent.style.display = 'block';
    }
  }



  addClickableFileMessage(fileName, step, detail = null) {
    if (!this.logContent) return;
    
    const timestamp = new Date().toLocaleTimeString();
    const line = document.createElement('div');
    
    // ファイル名をクリック可能にする
    const fileLink = document.createElement('span');
    fileLink.textContent = fileName;
    fileLink.style.color = '#007bff';
    fileLink.style.cursor = 'pointer';
    fileLink.style.textDecoration = 'underline';
    fileLink.style.fontWeight = 'bold';
    fileLink.title = 'クリックしてPDFプレビューを表示';
    fileLink.onclick = () => {
      console.log('ファイル名クリック:', fileName);
      this.showPDFPreview(fileName);
    };
    
    // メッセージを構築
    line.innerHTML = `<span style="color: #666; font-size: 11px;">[${timestamp}]</span> `;
    line.appendChild(fileLink);
    line.innerHTML += `: ${step}`;
    if (detail) {
      line.innerHTML += ` - ${detail}`;
    }
    
    this.logContent.appendChild(line);
    this.logContent.scrollTop = this.logContent.scrollHeight;
  }

  addProgressMessage(fileName, step, detail = null, pageId = null) {
    if (!this.logContent) return;
    
    const timestamp = new Date().toLocaleTimeString();
    const line = document.createElement('div');
    
    // 進捗メッセージのスタイル
    line.style.color = '#28a745';
    line.style.fontWeight = 'bold';
    
    // ファイル名をクリック可能にする
    const fileLink = document.createElement('span');
    fileLink.textContent = fileName;
    fileLink.style.color = '#007bff';
    fileLink.style.cursor = 'pointer';
    fileLink.style.textDecoration = 'underline';
    fileLink.title = 'クリックしてPDFプレビューを表示';
    fileLink.onclick = () => {
      console.log('ファイル名クリック:', fileName);
      this.showPDFPreview(fileName);
    };
    
    // メッセージを構築
    line.innerHTML = `<span style="color: #666; font-size: 11px;">[${timestamp}]</span> `;
    line.appendChild(fileLink);
    line.innerHTML += `: ${step}`;
    if (detail) {
      line.innerHTML += ` - ${detail}`;
    }
    
    // ページIDがある場合は進捗更新として扱う
    if (pageId) {
      line.setAttribute('data-page-id', pageId);
      line.className = 'progress-update';
    }
    
    this.logContent.appendChild(line);
    this.logContent.scrollTop = this.logContent.scrollHeight;
  }

  updateProgressMessage(fileName, step, detail = null, pageId = null) {
    if (!this.logContent) return;
    
    // 既存の進捗メッセージを探す
    const existingLine = this.logContent.querySelector(`[data-page-id="${pageId}"]`);
    
    if (existingLine) {
      // 既存の進捗メッセージを更新
      const timestamp = new Date().toLocaleTimeString();
      const fileLink = document.createElement('span');
      fileLink.textContent = fileName;
      fileLink.style.color = '#007bff';
      fileLink.style.cursor = 'pointer';
      fileLink.style.textDecoration = 'underline';
      fileLink.onclick = () => this.showPDFPreview(fileName);
      
      existingLine.innerHTML = `<span style="color: #666; font-size: 11px;">[${timestamp}]</span> `;
      existingLine.appendChild(fileLink);
      existingLine.innerHTML += `: ${step}`;
      if (detail) {
        existingLine.innerHTML += ` - ${detail}`;
      }
      
      // 進捗更新のスタイルを適用
      existingLine.style.color = '#28a745';
      existingLine.style.fontWeight = 'bold';
    } else {
      // 新しい進捗メッセージを追加
      this.addProgressMessage(fileName, step, detail, pageId);
    }
  }

  showPDFPreview(fileName) {
    console.log('📄 PDFプレビューを表示:', fileName);
    
    // PDFプレビューを右ペインに表示
    if (this.layoutManager && this.layoutManager.showPDFPreview) {
      this.layoutManager.showPDFPreview(fileName, fileName);
    } else {
      // フォールバック: 新しいタブでPDFを開く
      const pdfUrl = `/api/pdf/${encodeURIComponent(fileName)}`;
      console.log('📄 PDF URL:', pdfUrl);
      window.open(pdfUrl, '_blank');
    }
  }

  createLine(text, cls) {
    const div = document.createElement("div");
    if (cls) div.className = cls;
    div.textContent = text;
    return div;
  }

  scrollBottom(el) {
    const threshold = 32;
    const distance = el.scrollHeight - el.scrollTop - el.clientHeight;
    if (distance <= threshold) el.scrollTop = el.scrollHeight;
  }

  clearLog() {
    if (this.logContent) {
      this.logContent.innerHTML = '';
    }
    this.fileContainers = {};
  }

  setOnCompleteCallback(callback) {
    this.onComplete = callback;
  }

  close() {
    if (this.eventSource) {
      this.eventSource.close();
      this.eventSource = null;
    }
  }
}

// グローバルに公開
window.IngestSSE = IngestSSE;