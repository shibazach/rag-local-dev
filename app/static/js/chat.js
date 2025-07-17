// REM: app/static/js/chat.js @2025-07-18 20:00 日本時間（UTC +9）
// REM: チャット検索 UI 制御 + 検索結果ペイン限定オーバーレイ + 再ベクトル化オーバーレイ制御

console.log("✅ chat.js loaded");

document.addEventListener("DOMContentLoaded", () => {
  // REM: 要素取得
  const searchBtn      = document.getElementById("search-btn");
  const cancelBtn      = document.getElementById("cancel-btn");
  const loading        = document.getElementById("loading");
  const resultsDiv     = document.getElementById("results");
  const resultsOverlay = document.getElementById("results-overlay");
  const answerDiv      = document.getElementById("answer");
  // REM: 再ベクトル化オーバーレイ関連
  const overlay        = document.getElementById("processing-overlay");
  const overlayMsg     = document.getElementById("overlay-message");
  const overlayOkBtn   = document.getElementById("overlay-ok-btn");
  let controller       = null;

  // REM: 再ベクトル化オーバーレイ制御
  function showOverlay() { overlay.style.display = "flex"; }
  function hideOverlay() { overlay.style.display = "none"; }
  hideOverlay(); // 初期非表示

  // REM: 検索中オーバーレイ制御（結果ペイン限定）
  function showResultsOverlay() { resultsOverlay.style.display = "flex"; }
  function hideResultsOverlay() { resultsOverlay.style.display = "none"; }
  hideResultsOverlay(); // 初期非表示

  // REM: 検索実行ボタン
  searchBtn.addEventListener("click", async () => {
    showResultsOverlay();
    searchBtn.disabled = true;
    cancelBtn.disabled = false;
    loading.style.display = "inline";
    resultsDiv.innerHTML = "";
    answerDiv.innerHTML  = "";

    controller = new AbortController();
    const signal = controller.signal;

    try {
      const form = new FormData();
      form.append("query", document.getElementById("query").value);
      form.append("mode", document.getElementById("mode").value);
      form.append("model_key", document.getElementById("model_key").value);

      const res = await fetch("/query", { method: "POST", body: form, signal });
      const json = await res.json();

      if (json.error) {
        resultsDiv.innerHTML = `<p style=\"color:red;\">エラー: ${json.error}</p>`;
      } else {
        renderResults(json);
      }
    } catch (err) {
      if (err.name === "AbortError") {
        resultsDiv.innerHTML = `<p style=\"color:#888;\">検索をキャンセルしました。</p>`;
      } else {
        resultsDiv.innerHTML = `<p style=\"color:red;\">通信エラー: ${err.message}</p>`;
      }
    } finally {
      hideResultsOverlay();
      searchBtn.disabled = false;
      cancelBtn.disabled = true;
      loading.style.display = "none";
      controller = null;
    }
  });

  // REM: キャンセルボタン
  cancelBtn.addEventListener("click", () => {
    if (controller) controller.abort();
    hideResultsOverlay();
  });

  // REM: 結果描画関数
  function renderResults(json) {
    resultsDiv.innerHTML = "";

    // REM: チャンク統合モード
    if (json.mode === "チャンク統合") {
      answerDiv.innerHTML = `<h2>統合回答</h2><pre>${json.answer}</pre>`;
      answerDiv.style.display = "block";
      resultsDiv.innerHTML = `<h3>ソースファイル</h3>`;
      json.sources.forEach((src, i) => {
        const file_id   = src.file_id || src.id || "UNKNOWN_ID";
        const file_name = src.file_name || src.filename || src.name || "[no name]";
        resultsDiv.innerHTML +=
          `<p>${i+1}. <a href=\"/viewer/${file_id}\" target=\"_blank\">${file_name}</a></p>`;
      });
    } else {
      answerDiv.style.display = "none";
    }

    // REM: ファイル別モード
    json.results.forEach((item, idx) => {
      const card = document.createElement("div");
      card.className = "card";

      // REM: タイトル
      const h3 = document.createElement("h3");
      const file_id   = item.file_id || item.id || "UNKNOWN_ID";
      const file_name = item.file_name || item.filename || item.name || "[no name]";
      if (file_id !== "UNKNOWN_ID") {
        h3.innerHTML = `${idx+1}. <a href=\"/viewer/${file_id}\" class=\"result-link\">${file_name}</a>`;
      } else {
        h3.textContent = `${idx+1}. ${file_name}`;
      }
      card.appendChild(h3);

      // REM: スニペット/要約
      const pre = document.createElement("pre");
      pre.textContent = item.snippet || item.summary || "";
      card.appendChild(pre);

      // REM: 一致度表示
      if (item.score !== undefined) {
        const p = document.createElement("p");
        p.textContent = `一致度: ${item.score.toFixed(2)}`;
        card.appendChild(p);
      }

      // REM: 編集機能
      if (item.file_id) {
        addEditor(item.file_id, card);
      }

      resultsDiv.appendChild(card);
    });
  }

  // REM: 編集・再ベクトル化機能
  function addEditor(file_id, container) {
    const toggleBtn = document.createElement("button");
    toggleBtn.textContent = "✏️ 編集";
    container.appendChild(toggleBtn);

    const editorDiv = document.createElement("div");
    editorDiv.className = "editor";
    editorDiv.style.display = "none";
    container.appendChild(editorDiv);

    toggleBtn.addEventListener("click", async () => {
      if (editorDiv.style.display === "none") {
        toggleBtn.textContent = "✖️ 閉じる";
        if (!editorDiv.innerHTML) {
          const resp = await fetch(`/api/content/${file_id}`);
          const data = await resp.json();
          editorDiv.innerHTML = `
            <textarea>${data.content}</textarea><br>
            <button class=\"save-btn\">保存（再ベクトル化）</button>
          `;
          editorDiv.querySelector(".save-btn").addEventListener("click", async () => {
            showOverlay();
            overlayMsg.innerHTML = "再ベクトル化中…<br>閉じないでください";
            overlayOkBtn.style.display = "none";

            try {
              const form2 = new FormData();
              form2.append("content", editorDiv.querySelector("textarea").value);
              const resSave = await fetch(`/api/save/${file_id}`, { method: "POST", body: form2 });
              if (!resSave.ok) {
                const txt = await resSave.text();
                overlayMsg.innerHTML = `❌ エラー: ${txt}`;
              } else {
                overlayMsg.innerHTML = "✅ 再ベクトル化完了";
              }
            } catch (err) {
              overlayMsg.innerHTML = `❌ 通信エラー: ${err.message}`;
            } finally {
              overlayOkBtn.style.display = "block";
              overlayOkBtn.replaceWith(overlayOkBtn.cloneNode(true));
              const newOk = document.getElementById("overlay-ok-btn");
              newOk.addEventListener("click", () => {
                hideOverlay();
                editorDiv.style.display = "none";
                toggleBtn.textContent = "✏️ 編集";
                const updated = editorDiv.querySelector("textarea").value;
                const preElem = container.querySelector("pre");
                if (preElem) preElem.textContent = updated;
              });
            }
          });
        }
        editorDiv.style.display = "block";
      } else {
        toggleBtn.textContent = "✏️ 編集";
        editorDiv.style.display = "none";
      }
    });
  }

  // REM: 再ベクトル化オーバーレイ OKボタン
  overlayOkBtn.addEventListener("click", () => {
    hideOverlay();
  });
});
