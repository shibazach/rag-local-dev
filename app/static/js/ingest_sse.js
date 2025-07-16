// REM: app/fastapi/static/js/ingest_sse.js （更新日時: 2025-07-16）
"use strict";

let es = null;
const fileContainers = {};

/**
 * SSE で /ingest/stream を受信し、
 * pane-bottom にログを追加していくロジック
 */
function startIngestStream() {
  const pane = document.getElementById("pane-bottom");
  es = new EventSource("/ingest/stream");

  es.onmessage = evt => {
    const d = JSON.parse(evt.data);

    // ── ジョブ開始イベント ────────────────────────────
    if (d.start) {
      pane.appendChild(createLine(`▶ 全 ${d.total_files} 件の処理を開始`));
      scrollBottom(pane);
      return;
    }

    // ── 全完了イベント ────────────────────────────────
    if (d.done) {
      pane.appendChild(createLine("✅ 全処理完了"));
      scrollBottom(pane);
      es.close();
      return;
    }

    // ── 各ファイル・ステップイベント ───────────────────
    const {
      file, step, file_id, index, total, part, content, duration
    } = d;

    // ファイルごとのセクションを初期化
    let section = fileContainers[file];
    if (!section) {
      pane.appendChild(document.createElement("br"));
      pane.appendChild(createLine(
        `${index}/${total} ${file} の処理中…`, "file-progress"
      ));
      scrollBottom(pane);

      const header = document.createElement("div");
      header.className = "file-header";
      const link = document.createElement("a");
      link.href       = `/viewer/${file_id}`;
      link.target     = "_blank";
      link.textContent = file;
      header.appendChild(link);
      pane.appendChild(header);
      scrollBottom(pane);

      section = document.createElement("div");
      section.className = "file-section";
      pane.appendChild(section);
      scrollBottom(pane);

      fileContainers[file] = section;
    }

    // ── ページ単位の見出し ────────────────────────────
    if (step && step.startsWith("Page ")) {
      section.appendChild(createLine(step, "page-header"));
      scrollBottom(pane);
      return;
    }

    // ── 「使用プロンプト全文」「LLM整形結果全文」見出し ───
    if (step.startsWith("使用プロンプト全文") || step.startsWith("LLM整形結果全文")) {
      const [title, raw] = step.split(" part:");
      const p = raw || "all";
      const key = `${file}__${title}__${p}`;
      if (!section.querySelector(`details[data-key="${key}"]`)) {
        const det = document.createElement("details");
        det.setAttribute("data-key", key);
        const sum = document.createElement("summary");
        sum.textContent = step;
        det.appendChild(sum);
        section.appendChild(det);
        scrollBottom(pane);
      }
      return;
    }

    // ── 本文挿入（プロンプト全文 / 整形結果全文）───────────
    if (step === "prompt_text" || step === "refined_text") {
      const title = step === "prompt_text"
        ? "使用プロンプト全文"
        : "LLM整形結果全文";
      const p   = part || "all";
      const key = `${file}__${title}__${p}`;
      const det = section.querySelector(`details[data-key="${key}"]`);
      if (det) {
        let pre = det.querySelector("pre");
        if (!pre) {
          pre = document.createElement("pre");
          det.appendChild(pre);
        }
        pre.textContent = (content || "").replace(/\n{3,}/g, "\n\n");
        scrollBottom(pane);
      }
      return;
    }

    // ── 通常ログ行 ───────────────────────────────────
    const label = duration ? `${step} (${duration}s)` : step;
    section.appendChild(createLine(label));
    scrollBottom(pane);
  };

  es.onerror = () => {
    if (es) {
      es.close();
      es = null;
    }
  };
}

/**
 * SSE をキャンセル
 */
function cancelIngestStream() {
  if (es) {
    es.close();
    es = null;
  }
}

/**
 * 単純なテキスト行を生成
 */
function createLine(text, cls) {
  const div = document.createElement("div");
  if (cls) div.className = cls;
  div.textContent = text;
  return div;
}

/**
 * pane を常に下端にスクロール
 */
function scrollBottom(el) {
  el.scrollTop = el.scrollHeight;
}

// グローバル公開
window.startIngestStream  = startIngestStream;
window.cancelIngestStream = cancelIngestStream;
