// REM: app/static/js/ingest_sse.js @2025-07-18 00:00 UTC +9
// REM: SSE で /ingest/stream を受信し、ログを #log-pane に追加していくロジック

"use strict";

let es = null;
// REM: ファイルごとのログセクション管理
let fileContainers = {};

/**
 * REM: SSE を開始し、ログを #log-pane に追記
 */
function startIngestStream() {
  // REM: 既存の接続があればクローズ
  if (es) {
    es.close();
    es = null;
  }
  // REM: ファイルコンテナを初期化
  fileContainers = {};

  const logPane = document.getElementById("log-pane");
  es = new EventSource("/ingest/stream");

  es.onmessage = evt => {
    const d = JSON.parse(evt.data);

    // REM: cancelling イベントはログ化しない（即時フィードバックのみ）
    if (d.cancelling) {
      return;
    }

    // REM: 全体開始イベント
    if (d.start) {
      logPane.appendChild(createLine(`▶ 全 ${d.total_files} 件の処理を開始`));
      scrollBottom(logPane);
      return;
    }

    // REM: 停止完了通知
    if (d.stopped) {
      logPane.appendChild(createLine("⏹️ 処理が停止しました"));
      scrollBottom(logPane);
      es.close();
      if (window.onIngestComplete) window.onIngestComplete();
      return;
    }

    // REM: 全完了イベント
    if (d.done) {
      logPane.appendChild(createLine("✅ 全処理完了"));
      scrollBottom(logPane);
      es.close();
      if (window.onIngestComplete) window.onIngestComplete();
      return;
    }

    // REM: 各ファイル・ステップイベント
    const { file, step, file_id, index, total, part, content, duration } = d;

    // REM: ファイルセクション準備
    let section = fileContainers[file];
    if (!section) {
      logPane.appendChild(document.createElement("br"));
      logPane.appendChild(createLine(`${index}/${total} ${file} の処理中…`, "file-progress"));
      scrollBottom(logPane);

      const header = document.createElement("div");
      header.className = "file-header";
      const link = document.createElement("a");
      link.href       = `/viewer/${file_id}`;
      link.target     = "_blank";  // REM: 別タブ表示
      link.textContent = file;
      header.appendChild(link);
      logPane.appendChild(header);
      scrollBottom(logPane);

      section = document.createElement("div");
      section.className = "file-section";
      logPane.appendChild(section);
      scrollBottom(logPane);

      fileContainers[file] = section;
    }

    // REM: ページ単位の見出し
    if (step && step.startsWith("Page ")) {
      section.appendChild(createLine(step, "page-header"));
      scrollBottom(logPane);
      return;
    }

    // REM: プロンプト全文／整形結果全文の details 初期化
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
        scrollBottom(logPane);
      }
      return;
    }

    // REM: プロンプト／整形結果のテキスト挿入
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
        scrollBottom(logPane);
      }
      return;
    }

    // REM: 進捗更新の場合は同じ行を上書き
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
    } else {
      // REM: 通常ログ行
      const label = duration ? `${step} (${duration}s)` : step;
      section.appendChild(createLine(label));
    }
    scrollBottom(logPane);
  };

  es.onerror = () => {
    if (es) {
      es.close();
      es = null;
    }
  };
}

/**
 * REM: SSE をキャンセル（何もしない）
 */
function cancelIngestStream() {
  // noop
}

/**
 * REM: 単純なテキスト行を生成
 */
function createLine(text, cls) {
  const div = document.createElement("div");
  if (cls) div.className = cls;
  div.textContent = text;
  return div;
}

/**
 * REM: 自動スクロール
 */
function scrollBottom(el) {
  const threshold = 32;
  const distance = el.scrollHeight - el.scrollTop - el.clientHeight;
  if (distance <= threshold) el.scrollTop = el.scrollHeight;
}

// REM: グローバル公開
window.startIngestStream  = startIngestStream;
window.cancelIngestStream = cancelIngestStream;
