// /workspace/app/fastapi/static/js/ingest.js 2025-07-11 13:16 JST
// REM: フォルダ/ファイル選択切り替えとフォーム制御
document.addEventListener("DOMContentLoaded", () => {
  const overlay = document.getElementById("folder-overlay");
  const dlg     = document.getElementById("folder-dialog");
  const listEl  = document.getElementById("folder-list");
  const bcEl    = document.getElementById("folder-breadcrumbs");
  const inputFolderEl      = document.getElementById("input-folder");
  const inputFilesEl       = document.getElementById("input-files");
  const selectedFilesDisplay = document.getElementById("selected-files-display");

  // 初期パスを保持
  const basePath = inputFolderEl.value || "";
  let currentPath = basePath;

  // REM: モード切替（フォルダ or ファイル）
  document.getElementsByName("input_mode").forEach(radio => {
    radio.addEventListener("change", () => {
      const folderMode = document.getElementById("folder-mode");
      const filesMode  = document.getElementById("files-mode");
      if (radio.value === "folder" && radio.checked) {
        folderMode.style.display = "block";
        filesMode.style.display  = "none";
      } else if (radio.value === "files" && radio.checked) {
        folderMode.style.display = "none";
        filesMode.style.display  = "block";
      }
    });
  });

  // REM: フォルダモーダル読み込み
  async function loadFolders(path) {
    currentPath = path;
    bcEl.textContent = "/" + path;
    const res = await fetch(`/api/list-folders?path=${encodeURIComponent(path)}`);
    const { folders } = await res.json();
    listEl.innerHTML = "";

    // 「🔙 上へ」は basePath を超えない範囲で表示
    if (currentPath !== basePath) {
      const up = document.createElement("li");
      up.textContent = "🔙 上へ";
      up.onclick = () => {
        const parts = currentPath.split("/");
        parts.pop();
        loadFolders(parts.join("/"));
      };
      listEl.appendChild(up);
    }

    folders.forEach(name => {
      const li = document.createElement("li");
      li.textContent = name;
      li.onclick = () => loadFolders(path ? `${path}/${name}` : name);
      li.ondblclick = () => {
        inputFolderEl.value = path ? `${path}/${name}` : name;
        closeDialog();
      };
      listEl.appendChild(li);
    });
  }

  function openDialog() {
    overlay.style.display = dlg.style.display = 'block';
    loadFolders(basePath);
  }
  function closeDialog() {
    overlay.style.display = dlg.style.display = 'none';
  }

  document.getElementById("browse-folder").onclick       = openDialog;
  document.getElementById("close-folder-dialog").onclick = closeDialog;
  document.getElementById("confirm-folder").onclick      = () => {
    inputFolderEl.value = currentPath;
    closeDialog();
  };
  overlay.onclick = closeDialog;

  // REM: ファイル選択表示
  inputFilesEl.addEventListener("change", () => {
    const files = Array.from(inputFilesEl.files).map(f => f.name);
    selectedFilesDisplay.value = files.join("\n");
    // 高さ自動調整
    selectedFilesDisplay.style.height = "auto";
    selectedFilesDisplay.style.height = selectedFilesDisplay.scrollHeight + "px";
  });
});
