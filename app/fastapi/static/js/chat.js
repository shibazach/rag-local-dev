// /workspace/app/fastapi/static/js/chat.js  # REM: 最終更新 2025-07-10 17:20
// REM: チャット検索 UI と再ベクトル化オーバーレイ制御

document.addEventListener("DOMContentLoaded", () => {
  const searchBtn = document.getElementById("search-btn");
  const cancelBtn = document.getElementById("cancel-btn");
  const loading   = document.getElementById("loading");
  const resultsDiv= document.getElementById("results");
  const answerDiv = document.getElementById("answer");
  const overlay   = document.getElementById("processing-overlay");
  const overlayMsg= document.getElementById("overlay-message");
  const overlayOk = document.getElementById("overlay-ok-btn");
  let controller  = null;

  // REM: 初期表示時にオーバーレイを確実に隠す
  hideOverlay();

  // REM: 検索実行ボタン
  searchBtn.addEventListener("click", async () => {
    searchBtn.disabled = true;
    cancelBtn.disabled = false;
    loading.style.display = "inline";
    resultsDiv.innerHTML = "";
    answerDiv.innerHTML  = "";
    hideOverlay();

    const query     = document.getElementById("query").value;
    const mode      = document.getElementById("mode").value;
    const model_key = document.getElementById("model_key").value;

    controller = new AbortController();
    const signal = controller.signal;

    try {
      const form = new FormData();
      form.append("query", query);
      form.append("mode", mode);
      form.append("model_key", model_key);

      const res  = await fetch("/query", { method: "POST", body: form, signal });
      const json = await res.json();

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
    }
  });

  // REM: キャンセルボタン
  cancelBtn.addEventListener("click", () => {
    if (controller) controller.abort();
  });

  // REM: 結果描画
  function renderResults(json) {
    resultsDiv.innerHTML = "";
    // チャンク統合モード
    if (json.mode === "チャンク統合") {
      answerDiv.innerHTML = `<h2>統合回答</h2><pre>${json.answer}</pre>`;
      answerDiv.style.display = "block";
      resultsDiv.innerHTML = `<h3>ソースファイル</h3>`;
      json.sources.forEach((src, i) => {
        resultsDiv.innerHTML +=
          `<p>${i+1}. <a href="/viewer/${src.file_id}" target="_blank">${src.filename}</a></p>`;
      });
    } else {
      answerDiv.style.display = "none";
    }

    json.results.forEach((item, idx) => {
      const card = document.createElement("div");
      card.className = "card";

      // タイトル
      const h3 = document.createElement("h3");
      if (item.file_id) {
        h3.innerHTML = `${idx+1}. <a href="/viewer/${item.file_id}" target="_blank">${item.filename}</a>`;
      } else {
        h3.textContent = `${idx+1}. ${item.filename}`;
      }
      card.appendChild(h3);

      // スニペット or 要約
      const pre = document.createElement("pre");
      pre.textContent = item.snippet || item.summary || "";
      card.appendChild(pre);

      // 一致度表示（ファイル別モードのみ）
      if (item.score !== undefined) {
        const p = document.createElement("p");
        p.textContent = `一致度: ${item.score.toFixed(2)}`;
        card.appendChild(p);
      }

      // 編集機能
      if (item.file_id) {
        addEditor(item.file_id, card);
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
              // 既存リスナをクリアして新しく設定
              overlayOk.replaceWith(overlayOk.cloneNode(true));
              const newOk = document.getElementById("overlay-ok-btn");
              newOk.addEventListener("click", () => {
                // 1) オーバーレイを非表示
                overlay.style.display    = "none";
                newOk.style.display      = "none";
                // 2) 編集画面を閉じる
                editorDiv.style.display  = "none";
                toggleBtn.textContent    = "✏️ 編集";
                // 3) プレビュー(<pre>)を更新
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
});
