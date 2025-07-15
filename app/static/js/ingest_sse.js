REM: app/fastapi/static/js/ingest_sse.js（新規: 2025-07-15 22:45 JST）
/*
  インジェスト SSE 受信＆ログ描画。
  「使用プロンプト」「LLM整形結果」をアコーディオンで開閉表示する。
*/

"use strict";

// REM: ── 定数 ─────────────────────────────────────────
const SSE_URL   = "/ingest/stream";
const LOG_AREA  = "logArea";    // <div id="logArea"> を想定
const ACC_HEAD  = "accord-head";
const ACC_BODY  = "accord-body";

// REM: ── 起動関数（別 JS から呼び出す） ───────────────
function startIngestStream() {
  const es = new EventSource(SSE_URL);

  es.addEventListener("message", ev => {
    const payload = JSON.parse(ev.data);
    handleEvent(payload);
  });

  es.addEventListener("error", () => es.close());
}

// REM: handleEvent ─ イベント分配
function handleEvent(ev) {
  switch (ev.step) {
    case "prompt_text":
      insertBody(ev, "使用プロンプト");
      break;

    case "refined_text":
      insertBody(ev, "LLM整形結果");
      break;

    default:
      // 見出し系は共通関数へ
      if (ev.step.startsWith("使用プロンプト")) createHeading(ev, "使用プロンプト");
      else if (ev.step.startsWith("LLM整形結果")) createHeading(ev, "LLM整形結果");
      else     logLine(ev.step);
  }
}

// REM: createHeading ─ 見出し行を生成
function createHeading(ev, title) {
  const box = ensureAccord(ev.file, ev.part || getPart(ev.step), title);
  // preview があれば先頭に表示（任意）
  const body = box.querySelector("." + ACC_BODY);
  if (!body.textContent && ev.preview) body.textContent = ev.preview;
}

// REM: insertBody ─ 本文を追加
function insertBody(ev, title) {
  const box = ensureAccord(ev.file, ev.part, title);
  box.querySelector("." + ACC_BODY).textContent = ev.content;
}

// REM: ensureAccord ─ 見出し＋本文コンテナを確保
function ensureAccord(file, part, title) {
  const rootId = `${file}_${part}_${title}`;
  let box      = document.getElementById(rootId);
  if (box) return box;

  box        = document.createElement("div");
  box.id     = rootId;

  const head = document.createElement("div");
  head.className = ACC_HEAD;
  head.textContent = `▶ ${title} part:${part}`;
  head.onclick = () => toggleAccord(head, body);

  const body = document.createElement("pre");
  body.className = ACC_BODY;
  body.style.display = "none";

  box.appendChild(head);
  box.appendChild(body);
  document.getElementById(LOG_AREA).appendChild(box);
  return box;
}

// REM: toggleAccord ─ 開閉トグル
function toggleAccord(h, b) {
  const open = b.style.display === "none";
  b.style.display = open ? "block" : "none";
  h.textContent = `${open ? "▼" : "▶"} ${h.textContent.slice(2)}`;
}

// REM: logLine ─ 単純ステータス行
function logLine(text) {
  const div = document.createElement("div");
  div.textContent = text;
  document.getElementById(LOG_AREA).appendChild(div);
}

// REM: getPart ─ 見出し文字列から part 抜粋
function getPart(stepStr) {
  const m = stepStr.match(/part:([^\s]+)/);
  return m ? m[1] : "all";
}

// グローバル公開（HTML から呼びやすく）
window.startIngestStream = startIngestStream;
