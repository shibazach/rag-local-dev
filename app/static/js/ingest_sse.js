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

    this.eventSource.onmessage = evt => this.handleMessage(evt);

    this.eventSource.onerror = evt => {
      console.error('SSE接続エラー:', evt);
      this.addLogMessage('❌ 接続エラーが発生しました');
      this.eventSource.close();
      // 処理完了コールバックを呼び出し
      if (this.onComplete) this.onComplete();
    };
  }

  handleMessage(evt) {
    console.log('📨 SSEメッセージ受信:', evt.data);
    const d = JSON.parse(evt.data);
    console.log('📨 パース済みデータ:', d);

    // cancelling イベントはログ化しない（即時フィードバックのみ）
    if (d.cancelling) {
      return;
    }

    // 全体開始イベント
    if (d.start) {
      this.addLogMessage(`全 ${d.total_files} 件の処理を開始`);
      return;
    }

    // 停止完了通知
    if (d.stopped) {
      this.addLogMessage('⏹️ 処理が停止しました');
      this.eventSource.close();
      if (this.onComplete) this.onComplete();
      return;
    }

    // 全完了イベント
    if (d.done) {
      this.addLogMessage('✅ 全処理完了');
      this.eventSource.close();
      if (this.onComplete) this.onComplete();
      return;
    }

    // 各ファイル・ステップイベント（元のingest_sse.jsと同じ詳細処理）
    const { file, step, file_id, index, total, part, content, duration } = d;

    // ファイルセクション準備
    let section = this.fileContainers[file];
    if (!section) {
      if (this.logContent) {
        this.logContent.appendChild(document.createElement("br"));
        this.logContent.appendChild(this.createLine(`${index}/${total} ${file} の処理中…`, "file-progress"));
        this.scrollBottom(this.logContent);

        const header = document.createElement("div");
        header.className = "file-header";
        const link = document.createElement("a");
        link.href = file_id ? `/api/pdf/${file_id}` : '#';
        link.textContent = file;
        // PDFプレビュー機能（オルタネートスイッチ）
        link.addEventListener('click', (e) => {
          e.preventDefault();
          if (file_id && this.layoutManager) {
            this.layoutManager.togglePDFPreview(file_id, file);
          }
        });
        header.appendChild(link);
        this.logContent.appendChild(header);
        this.scrollBottom(this.logContent);

        section = document.createElement("div");
        section.className = "file-section";
        this.logContent.appendChild(section);
        this.scrollBottom(this.logContent);

        this.fileContainers[file] = section;
      }
    }

    // ページ単位の見出し
    if (step && step.startsWith("Page ")) {
      section.appendChild(this.createLine(step, "page-header"));
      this.scrollBottom(this.logContent);
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
        this.scrollBottom(this.logContent);
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
        this.scrollBottom(this.logContent);
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
        const progressLine = this.createLine(step);
        progressLine.setAttribute('data-page-id', d.page_id);
        section.appendChild(progressLine);
      }
    } else if (step) {
      // 通常ログ行
      const label = duration ? `${step} (${duration}s)` : step;
      section.appendChild(this.createLine(label));
    }
    this.scrollBottom(this.logContent);
  }

  addLogMessage(message) {
    if (!this.logContent) return;
    const timestamp = new Date().toLocaleTimeString();
    const line = document.createElement('div');
    line.innerHTML = '<span style="color: #666; font-size: 11px;">[' + timestamp + ']</span> ' + message;
    this.logContent.appendChild(line);
    this.logContent.scrollTop = this.logContent.scrollHeight;
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