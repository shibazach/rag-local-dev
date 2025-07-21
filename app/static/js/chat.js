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

    // ナビゲーション制御を開始
    if (window.chatSearchStart) window.chatSearchStart();

    // 経過時間タイマーを開始
    if (window.startSearchTimer) window.startSearchTimer();

    // REM: 検索中は入力フィールドをグレーアウト
    document.getElementById("query").disabled = true;
    document.getElementById("mode").disabled = true;
    document.getElementById("model_key").disabled = true;
    if (document.getElementById("search_limit")) document.getElementById("search_limit").disabled = true;
    if (document.getElementById("min_score")) document.getElementById("min_score").disabled = true;

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

      // 新しいパラメータを追加
      const searchLimit = document.getElementById("search_limit")?.value || 10;
      const minScore = document.getElementById("min_score")?.value || 0.0;
      form.append("search_limit", searchLimit);
      form.append("min_score", minScore);

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
      if (document.getElementById("search_limit")) document.getElementById("search_limit").disabled = false;
      if (document.getElementById("min_score")) document.getElementById("min_score").disabled = false;

      // ナビゲーション制御を終了
      if (window.chatSearchEnd) window.chatSearchEnd();

      // 経過時間タイマーを停止
      if (window.stopSearchTimer) window.stopSearchTimer();
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

  // 履歴ダイアログのイベントリスナー
  document.getElementById('history-btn').addEventListener('click', showHistoryModal);
  document.getElementById('history-modal-close').addEventListener('click', hideHistoryModal);
  document.getElementById('history-modal-overlay').addEventListener('click', hideHistoryModal);

  // 展開ボタン
  document.getElementById('history-expand-btn').addEventListener('click', () => {
    if (selectedHistoryItem) {
      const selectedElement = document.querySelector(`[data-history-id="${selectedHistoryItem.id}"]`);
      if (selectedElement) {
        toggleHistoryExpansion(selectedElement);
      }
    }
  });

  // 復元ボタン
  document.getElementById('history-restore-btn').addEventListener('click', () => {
    if (selectedHistoryItem) {
      restoreFromHistory(selectedHistoryItem);
    }
  });

  // 削除ボタン
  document.getElementById('history-delete-btn').addEventListener('click', async () => {
    if (selectedHistoryItem && confirm('選択した履歴を削除しますか？')) {
      try {
        await fetch(`/history/${selectedHistoryItem.id}`, { method: 'DELETE' });
        loadHistoryList();
        selectedHistoryItem = null;
        updateHistoryButtons();
      } catch (error) {
        console.error('履歴削除エラー:', error);
        alert('履歴の削除に失敗しました');
      }
    }
  });

  // ダウンロードボタン
  document.getElementById('history-download-btn').addEventListener('click', async () => {
    const format = document.getElementById('history-download-format').value;
    try {
      const response = await fetch(`/history/download/${format}`);
      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = response.headers.get('Content-Disposition')?.split('filename=')[1] || `history.${format}`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
      } else {
        throw new Error('ダウンロードに失敗しました');
      }
    } catch (error) {
      console.error('ダウンロードエラー:', error);
      alert('ダウンロードに失敗しました');
    }
  });

  // 全削除ボタン
  document.getElementById('history-clear-btn').addEventListener('click', async () => {
    if (confirm('全ての履歴を削除しますか？この操作は取り消せません。')) {
      try {
        await fetch('/history', { method: 'DELETE' });
        loadHistoryList();
        selectedHistoryItem = null;
        updateHistoryButtons();
      } catch (error) {
        console.error('履歴全削除エラー:', error);
        alert('履歴の削除に失敗しました');
      }
    }
  });
});

// REM: 履歴機能
let selectedHistoryItem = null;

// 履歴ダイアログの表示/非表示
function showHistoryModal() {
  document.getElementById('history-modal').style.display = 'block';
  loadHistoryList();
}

function hideHistoryModal() {
  document.getElementById('history-modal').style.display = 'none';
  selectedHistoryItem = null;
  updateHistoryButtons();
}

// 履歴一覧の読み込み
async function loadHistoryList() {
  try {
    const response = await fetch('/history');
    const history = await response.json();

    const historyList = document.getElementById('history-list');
    historyList.innerHTML = '';

    if (history.length === 0) {
      historyList.innerHTML = '<p style="text-align:center; color:#666; margin:2em;">履歴がありません</p>';
      return;
    }

    history.forEach(item => {
      const historyItem = createHistoryItem(item);
      historyList.appendChild(historyItem);
    });

  } catch (error) {
    console.error('履歴読み込みエラー:', error);
    document.getElementById('history-list').innerHTML = '<p style="text-align:center; color:#d32f2f; margin:2em;">履歴の読み込みに失敗しました</p>';
  }
}

// 履歴アイテムのHTML要素を作成
function createHistoryItem(item) {
  const div = document.createElement('div');
  div.className = 'history-item';
  div.dataset.historyId = item.id;

  const timestamp = new Date(item.timestamp).toLocaleString('ja-JP');
  const result = item.result || {};

  // プレビューテキストを生成
  let previewText = '';
  if (result.mode === 'チャンク統合') {
    previewText = result.answer ? result.answer.substring(0, 100) + '...' : '';
  } else {
    const results = result.results || [];
    if (results.length > 0) {
      previewText = `${results.length}件のファイルが見つかりました: ${results[0].file_name}など`;
    }
  }

  div.innerHTML = `
    <div class="history-item-header">
      <div class="history-item-query">${item.query}</div>
      <div class="history-item-meta">
        <span>モード: ${item.mode}</span>
        <span>処理時間: ${item.processing_time}秒</span>
        <span>${timestamp}</span>
      </div>
    </div>
    <div class="history-item-preview">${previewText}</div>
    <div class="history-item-expanded">
      <div class="history-item-result">${formatHistoryResult(result)}</div>
    </div>
  `;

  // クリックイベント
  div.addEventListener('click', () => selectHistoryItem(div, item));

  // ダブルクリックで展開
  div.addEventListener('dblclick', () => toggleHistoryExpansion(div));

  return div;
}

// 履歴結果をフォーマット
function formatHistoryResult(result) {
  if (result.mode === 'チャンク統合') {
    let formatted = `統合回答:\n${result.answer || ''}\n\n`;
    if (result.sources && result.sources.length > 0) {
      formatted += '参照ファイル:\n';
      result.sources.forEach(src => {
        formatted += `- ${src.file_name}\n`;
      });
    }
    return formatted;
  } else {
    let formatted = 'ファイル別結果:\n\n';
    const results = result.results || [];
    results.forEach((res, index) => {
      formatted += `${index + 1}. ${res.file_name} (一致度: ${res.score?.toFixed(2) || 'N/A'})\n`;
      formatted += `要約: ${res.summary || ''}\n\n`;
    });
    return formatted;
  }
}

// 履歴アイテムの選択
function selectHistoryItem(element, item) {
  // 既存の選択を解除
  document.querySelectorAll('.history-item.selected').forEach(el => {
    el.classList.remove('selected');
  });

  // 新しい選択を設定
  element.classList.add('selected');
  selectedHistoryItem = item;
  updateHistoryButtons();
}

// 履歴アイテムの展開/折りたたみ
function toggleHistoryExpansion(element) {
  const expanded = element.querySelector('.history-item-expanded');
  expanded.classList.toggle('show');
}

// 履歴ボタンの状態更新
function updateHistoryButtons() {
  const expandBtn = document.getElementById('history-expand-btn');
  const restoreBtn = document.getElementById('history-restore-btn');
  const deleteBtn = document.getElementById('history-delete-btn');

  const hasSelection = selectedHistoryItem !== null;
  expandBtn.disabled = !hasSelection;
  restoreBtn.disabled = !hasSelection;
  deleteBtn.disabled = !hasSelection;
}

// 履歴から検索条件を復元
function restoreFromHistory(historyItem) {
  document.getElementById('query').value = historyItem.query;
  document.getElementById('mode').value = historyItem.mode;
  document.getElementById('model_key').value = historyItem.model_key;

  // 結果を表示
  renderResults(historyItem.result);

  // ダイアログを閉じる
  hideHistoryModal();
}

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
