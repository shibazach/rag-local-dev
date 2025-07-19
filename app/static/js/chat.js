// /workspace/app/static/js/chat.js  # REM: 最終更新 2025-07-10 17:20
// REM: チャット検索 UI と再ベクトル化オーバーレイ制御

console.log("✅ chat.js loaded");

document.addEventListener("DOMContentLoaded", () => {
  const searchBtn = document.getElementById("search-btn");
  const cancelBtn = document.getElementById("cancel-btn");
  const loading = document.getElementById("loading");
  const resultsDiv = document.getElementById("results");
  const answerDiv = document.getElementById("answer");
  const overlay = document.getElementById("processing-overlay");
  const overlayMsg = document.getElementById("overlay-message");
  const overlayOk = document.getElementById("overlay-ok-btn");
  const searchOverlay = document.getElementById("search-overlay");
  const searchMessage = document.getElementById("search-message");
  let controller = null;

  // REM: 初期表示時にオーバーレイを確実に隠す
  hideOverlay();
  hideSearchOverlay();

  // REM: 検索実行ボタン
  searchBtn.addEventListener("click", async () => {
    searchBtn.disabled = true;
    cancelBtn.disabled = false;
    loading.style.display = "inline";
    resultsDiv.innerHTML = "";
    answerDiv.innerHTML = "";
    hideOverlay();
    showSearchOverlay();

    // REM: 検索中は入力フィールドをグレーアウト
    document.getElementById("query").disabled = true;
    document.getElementById("mode").disabled = true;
    document.getElementById("model_key").disabled = true;

    const query = document.getElementById("query").value;
    const mode = document.getElementById("mode").value;
    const model_key = document.getElementById("model_key").value;

    controller = new AbortController();
    const signal = controller.signal;

    try {
      const form = new FormData();
      form.append("query", query);
      form.append("mode", mode);
      form.append("model_key", model_key);

      const res = await fetch("/query", { method: "POST", body: form, signal });
      const json = await res.json();

      console.log("★ fetch /query →", json);  // デバッグ: まずここで JSON の中身を確認！

      if (json.error) {
        resultsDiv.innerHTML = `<p style="color:red;">エラー: ${json.error}</p>`;
      } else {
        renderResults(json);
      }
    } catch (err) {
      if (err.name === "AbortError") {
        resultsDiv.innerHTML = `<p style="color:#888;">検索をキャンセルしました。</p>`;
      } else {
        resultsDiv.innerHTML = `<p style="color:red;">通信エラー: ${err.message}</p>`;
      }
    } finally {
      searchBtn.disabled = false;
      cancelBtn.disabled = true;
      loading.style.display = "none";
      controller = null;
      hideSearchOverlay();

      // REM: 検索完了後は入力フィールドを有効に戻す
      document.getElementById("query").disabled = false;
      document.getElementById("mode").disabled = false;
      document.getElementById("model_key").disabled = false;
    }
  });

  // REM: キャンセルボタン
  cancelBtn.addEventListener("click", () => {
    if (controller) controller.abort();
  });

  // REM: 結果描画
  function renderResults(json) {
    resultsDiv.innerHTML = "";

    // REM: チャンク統合モード
    if (json.mode === "チャンク統合") {
      answerDiv.innerHTML = `<h2>統合回答</h2><pre>${json.answer}</pre>`;
      answerDiv.style.display = "block";
      resultsDiv.innerHTML = `<h3>ソースファイル</h3>`;
      json.sources.forEach((src, i) => {
        const file_id = src.file_id;
        const file_name = src.file_name;
        resultsDiv.innerHTML +=
          `<p>${i + 1}. <a href="#" onclick="openFile('${file_id}', '${file_name}')">${file_name}</a></p>`;
      });
    } else {
      answerDiv.style.display = "none";
    }

    json.results.forEach((item, idx) => {
      const card = document.createElement("div");
      card.className = "card";

      // REM: タイトル (ファイル別モード)
      const h3 = document.createElement("h3");
      const file_id = item.file_id;
      const file_name = item.file_name;
      if (file_id) {
        h3.innerHTML =
          `${idx + 1}. <a href="#" onclick="openFile('${file_id}', '${file_name}')">${file_name}</a>`;
      } else {
        h3.textContent = `${idx + 1}. ${file_name}`;
      }
      card.appendChild(h3);

      // REM: コンテンツ表示
      // REM: チャンク統合 → snippet（元データのまま）、ファイル別 → summary（要約）
      const pre = document.createElement("pre");
      const content = json.mode === "チャンク統合" ? item.snippet : item.summary;
      pre.textContent = content || "";
      card.appendChild(pre);

      // REM: 一致度表示（ファイル別モードのみ）
      if (item.score !== undefined) {
        const p = document.createElement("p");
        p.textContent = `一致度: ${item.score.toFixed(2)}`;
        card.appendChild(p);
      }

      // REM: 編集機能
      if (file_id) {
        addEditor(file_id, card);
      }

      resultsDiv.appendChild(card);
    });
  }

  // REM: 編集・再ベクトル化用
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
          console.log("★ fetch /api/content →", data);  // デバッグ
          editorDiv.innerHTML = `
            <textarea>${data.content}</textarea><br>
            <button class="save-btn">保存（再ベクトル化）</button>
          `;
          editorDiv.querySelector(".save-btn").addEventListener("click", async () => {
            const newContent = editorDiv.querySelector("textarea").value;
            overlayMsg.innerHTML = "再ベクトル化中…<br>閉じないでください";
            overlayOk.style.display = "none";
            showOverlay();

            try {
              const form2 = new FormData();
              form2.append("content", newContent);
              const resSave = await fetch(`/api/save/${file_id}`, {
                method: "POST",
                body: form2
              });
              if (!resSave.ok) {
                const txt = await resSave.text();
                overlayMsg.innerHTML = `❌ エラー: ${txt}`;
              } else {
                overlayMsg.innerHTML = "✅ 再ベクトル化完了";
              }
            } catch (err) {
              overlayMsg.innerHTML = `❌ 通信エラー: ${err.message}`;
            } finally {
              overlayOk.style.display = "block";
              overlayOk.replaceWith(overlayOk.cloneNode(true));
              const newOk = document.getElementById("overlay-ok-btn");
              newOk.addEventListener("click", () => {
                overlay.style.display = "none";
                newOk.style.display = "none";
                editorDiv.style.display = "none";
                toggleBtn.textContent = "✏️ 編集";
                const updated = editorDiv.querySelector("textarea").value;
                const pre = container.querySelector("pre");
                if (pre) pre.textContent = updated;
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

  // REM: オーバーレイ表示
  function showOverlay() {
    overlay.style.display = "flex";
  }
  // REM: オーバーレイ非表示
  function hideOverlay() {
    overlay.style.display = "none";
  }

  // REM: 検索中オーバーレイ表示
  function showSearchOverlay() {
    searchOverlay.style.display = "flex";
  }
  // REM: 検索中オーバーレイ非表示
  function hideSearchOverlay() {
    searchOverlay.style.display = "none";
  }

  // REM: スプリッター機能（ingestと同様）
  const splitter = document.getElementById("splitter");
  const rightPane = document.getElementById("right-pane");
  const resultsPane = document.getElementById("results-pane");
  let isResizing = false;

  splitter.addEventListener("mousedown", (e) => {
    isResizing = true;
    document.addEventListener("mousemove", handleMouseMove);
    document.addEventListener("mouseup", handleMouseUp);
  });

  function handleMouseMove(e) {
    if (!isResizing) return;
    const containerWidth = document.getElementById("pane-bottom").offsetWidth;
    const newRightWidth = containerWidth - e.clientX;
    const minWidth = 200;
    const maxWidth = containerWidth - 300;

    if (newRightWidth >= minWidth && newRightWidth <= maxWidth) {
      rightPane.style.flex = `0 0 ${newRightWidth}px`;
    }
  }

  function handleMouseUp() {
    isResizing = false;
    document.removeEventListener("mousemove", handleMouseMove);
    document.removeEventListener("mouseup", handleMouseUp);
  }
});

// REM: ファイル表示機能（グローバル関数として定義）
function openFile(fileId, fileName) {
  const pdfMode = document.querySelector('input[name="pdf_mode"]:checked').value;
  const rightPane = document.getElementById("right-pane");
  const pdfViewer = document.getElementById("pdf-viewer");
  const promptEditor = document.getElementById("prompt-editor-area");

  if (pdfMode === "newtab") {
    // 別タブで開く
    window.open(`/viewer/${fileId}`, '_blank');
  } else {
    // 同一タブ内表示（右ペインに表示）
    rightPane.style.display = "block";
    pdfViewer.style.display = "block";
    promptEditor.style.display = "none";
    pdfViewer.src = `/viewer/${fileId}`;

    console.log(`📄 PDF表示: ${fileName} (${fileId})`);
  }
}
