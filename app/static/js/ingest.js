// REM: app/fastapi/static/js/ingest.js（更新日時: 2025-07-16 14:00 JST）
// フォルダ/ファイル選択切り替え＋フォーム送信＆SSEトリガ

document.addEventListener("DOMContentLoaded", () => {
  // --- モード切替（フォルダ vs ファイル） ---
  const folderMode = document.getElementById("folder-mode");
  const filesMode  = document.getElementById("files-mode");
  document.getElementsByName("input_mode").forEach(radio => {
    radio.addEventListener("change", () => {
      if (radio.value === "folder" && radio.checked) {
        folderMode.style.display = "block";
        filesMode.style.display  = "none";
      }
      if (radio.value === "files" && radio.checked) {
        folderMode.style.display = "none";
        filesMode.style.display  = "block";
      }
    });
  });

  // --- フォルダブラウズモーダル ---
  const overlay = document.getElementById("folder-overlay");
  const dlg     = document.getElementById("folder-dialog");
  const listEl  = document.getElementById("folder-list");
  const bcEl    = document.getElementById("folder-breadcrumbs");
  const inputEl = document.getElementById("input-folder");
  let basePath  = inputEl.value || "";
  let currentPath = basePath;

  async function loadFolders(path) {
    currentPath      = path;
    bcEl.textContent = "/" + (path || "");
    const res        = await fetch(`/api/list-folders?path=${encodeURIComponent(path||"")}`);
    const { folders = [] } = await res.json();
    listEl.innerHTML = "";

    if (currentPath !== basePath) {
      const up = document.createElement("li");
      up.textContent = "🔙 上へ";
      up.onclick     = () => loadFolders(currentPath.split("/").slice(0, -1).join("/"));
      listEl.appendChild(up);
    }
    folders.forEach(name => {
      const li = document.createElement("li");
      li.textContent = name;
      li.onclick     = () => loadFolders(path ? `${path}/${name}` : name);
      li.ondblclick  = () => {
        inputEl.value = path ? `${path}/${name}` : name;
        closeDialog();
      };
      listEl.appendChild(li);
    });
  }
  function openDialog()  { overlay.style.display = dlg.style.display = "block"; loadFolders(basePath); }
  function closeDialog() { overlay.style.display = dlg.style.display = "none"; }

  document.getElementById("browse-folder").onclick       = openDialog;
  document.getElementById("close-folder-dialog").onclick = closeDialog;
  document.getElementById("confirm-folder").onclick      = () => { inputEl.value = currentPath; closeDialog(); };
  overlay.onclick = closeDialog;

  // --- ファイル選択プレビュー ---
  const inputFilesEl         = document.getElementById("input-files");
  const selectedFilesDisplay = document.getElementById("selected-files-display");
  if (inputFilesEl) {
    inputFilesEl.addEventListener("change", () => {
      const files = Array.from(inputFilesEl.files).map(f => f.name);
      selectedFilesDisplay.value = files.join("\n");
      selectedFilesDisplay.style.height = "auto";
      selectedFilesDisplay.style.height = selectedFilesDisplay.scrollHeight + "px";
    });
  }

  // --- ボタンハンドリング ---
  const startBtn  = document.getElementById("start-btn");
  const cancelBtn = document.getElementById("cancel-btn");

  startBtn.addEventListener("click", async () => {
    startBtn.disabled  = true;
    cancelBtn.disabled = false;
    // ログクリア
    document.getElementById("pane-bottom").innerHTML = "";

    // フォーム送信
    const form = new FormData(document.getElementById("ingest-form"));
    form.append("include_subdirs",
      document.getElementById("include-subdirs").checked ? "true" : "false");
    try {
      await fetch("/ingest", { method: "POST", body: form });
      // SSE 開始
      startIngestStream();
    } catch (err) {
      console.error("ingest POST error:", err);
    }
  });

  cancelBtn.addEventListener("click", () => {
    cancelIngestStream();
    startBtn.disabled  = false;
    cancelBtn.disabled = true;
  });
});
