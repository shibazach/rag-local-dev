// REM: app/static/js/ingest.js @2025-07-18 00:00 UTC +9
// REM: フォルダ/ファイル切替＋フォーム送信＆SSEトリガ＋UI制御＋プロンプト編集＋PDF埋め込み表示（トグル対応＋表示モード選択＋リンクテキスト判定）

(function() {
  // REM: DOMロード後に初期化
  document.addEventListener("DOMContentLoaded", () => {
    // REM: 要素取得
    const folderMode           = document.getElementById("folder-mode");
    const filesMode            = document.getElementById("files-mode");
    const overlay              = document.getElementById("folder-overlay");
    const dlg                  = document.getElementById("folder-dialog");
    const listEl               = document.getElementById("folder-list");
    const bcEl                 = document.getElementById("folder-breadcrumbs");
    const inputEl              = document.getElementById("input-folder");
    const inputFilesEl         = document.getElementById("input-files");
    const selectedFilesDisplay = document.getElementById("selected-files-display");
    const startBtn             = document.getElementById("start-btn");
    const cancelBtn            = document.getElementById("cancel-btn");
    const promptButton         = document.getElementById("prompt-edit-btn");
    const editorPane           = document.getElementById("editor-pane");
    const editorArea           = document.getElementById("prompt-editor");
    const logPane              = document.getElementById("log-pane");
    const splitter             = document.getElementById("splitter");

    // REM: PDF表示モード選択用ラジオ要素取得
    const pdfModeRadios        = document.getElementsByName("pdf_mode");
    let basePath    = inputEl.value || "";
    let currentPath = basePath;
    let currentPdf  = null; // REM: 現在表示中のPDF URLを保持

    // REM: PDF表示モード切替時の挙動
    Array.from(pdfModeRadios).forEach(radio => {
      radio.addEventListener("change", () => {
        const mode = radio.value;
        if (mode === "newtab" && editorPane.style.display === "block") {
          // 新規タブモード選択時に、すでに開いている右ペインを閉じる
          editorPane.style.display = "none";
          currentPdf = null;
        }
        // embed モード選択時は既存タブは放置、以降クリックは埋め込みへ
      });
    });

    // REM: 入力モードの切替制御
    Array.from(document.getElementsByName("input_mode")).forEach(radio => {
      radio.addEventListener("change", () => {
        if (radio.value === "folder" && radio.checked) {
          folderMode.style.display = "flex";
          filesMode.style.display  = "none";
        } else {
          folderMode.style.display = "none";
          filesMode.style.display  = "flex";
        }
      });
    });

    // REM: フォルダブラウズ機能
    async function loadFolders(path) {
      currentPath = path;
      bcEl.textContent = "/" + (path || "");
      const res = await fetch(`/api/list-folders?path=${encodeURIComponent(path || "")}`);
      if (!res.ok) throw new Error("フォルダ取得失敗");
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
        li.ondblclick  = () => { inputEl.value = path ? `${path}/${name}` : name; closeDialog(); };
        listEl.appendChild(li);
      });
    }
    function openDialog()  { overlay.style.display = dlg.style.display = "block"; loadFolders(basePath); }
    function closeDialog() { overlay.style.display = dlg.style.display = "none"; }

    document.getElementById("browse-folder").onclick       = openDialog;
    document.getElementById("close-folder-dialog").onclick = closeDialog;
    document.getElementById("confirm-folder").onclick      = () => { inputEl.value = currentPath; closeDialog(); };
    overlay.onclick = closeDialog;

    // REM: ファイルプレビュー表示
    if (inputFilesEl) {
      inputFilesEl.addEventListener("change", () => {
        const files = Array.from(inputFilesEl.files).map(f => f.name);
        selectedFilesDisplay.value         = files.join("\n");
        selectedFilesDisplay.style.display = "block";
        selectedFilesDisplay.style.height  = selectedFilesDisplay.scrollHeight + "px";
      });
    }

    // REM: フォーム要素一括無効化／有効化
    function setFormDisabled(disabled) {
      // REM: pdf_mode ラジオだけは対象外にして常に操作可能に
      document.querySelectorAll(
        "#ingest-form input:not([name=pdf_mode]), #ingest-form select, #ingest-form button"
      ).forEach(el => el.disabled = disabled);
      cancelBtn.disabled = !disabled;
    }

    // REM: 初期状態では編集ペインを閉じる
    editorPane.style.display = "none";

    // REM: プロンプト編集ペイン表示切替
    promptButton.addEventListener("click", async () => {
      if (!editorArea.value) {
        try {
          const res = await fetch("/api/refine_prompt");
          editorArea.value = await res.text();
        } catch (e) {
          console.error("プロンプト読み込みエラー", e);
          editorArea.value = "読み込み失敗";
        }
      }
      editorPane.style.display = (editorPane.style.display === "none") ? "block" : "none";
    });

    // REM: フォームsubmit時に隠しフィールドを追加
    document.getElementById("ingest-form").addEventListener("submit", e => {
      const hidden = document.createElement("input");
      hidden.type  = "hidden";
      hidden.name  = "refine_prompt_text";
      hidden.value = editorArea.value;
      e.target.appendChild(hidden);
    });

    // REM: 処理開始ボタン押下時の動作
    startBtn.addEventListener("click", async () => {
      // ↓ FormData は disabled される前に新規作成
      const form = new FormData();
      // REM: input_mode
      const mode = document.querySelector("input[name=input_mode]:checked").value;
      form.append("input_mode", mode);
      // REM: input_folder or input_files
      if (mode === "folder") {
        form.append("input_folder", inputEl.value);
      } else {
        Array.from(inputFilesEl.files).forEach(file => form.append("input_files", file));
      }
      // REM: include_subdirs
      form.append("include_subdirs", document.getElementById("include-subdirs").checked ? "true" : "false");
      // REM: refine_prompt_key
      form.append("refine_prompt_key", document.getElementById("refine-prompt").value);
      // REM: embed_models
      document.querySelectorAll("input[name=embed_models]:checked").forEach(cb => form.append("embed_models", cb.value));
      // REM: overwrite_existing
      form.append("overwrite_existing", document.getElementById("overwrite_existing").checked ? "true" : "false");
      // REM: quality_threshold
      form.append("quality_threshold", document.getElementById("quality_threshold").value);

      // REM: UI 無効化
      setFormDisabled(true);
      // REM: 処理開始と同時に編集ペインを閉じる
      editorPane.style.display = "none";
      // REM: logPane クリア
      logPane.innerHTML = "";

      // REM: POST & SSE開始
      try {
        const res = await fetch("/ingest", { method: "POST", body: form });
        if (!res.ok) {
          console.error("POST /ingest error", res.status, await res.text());
          setFormDisabled(false);
          return;
        }
        startIngestStream();
      } catch (err) {
        console.error("ingest POST exception:", err);
        setFormDisabled(false);
      }
    });

    // REM: キャンセルボタン押下時
    cancelBtn.addEventListener("click", async () => {
      // REM: ボタン二度押し防止
      cancelBtn.disabled = true;
      // REM: 即時フィードバック：キャンセル中メッセージ（重複防止）
      const last = logPane.lastElementChild;
      if (!(last && last.textContent === "⏳ キャンセル中…")) {
        const cancelDiv = document.createElement("div");
        cancelDiv.textContent = "⏳ キャンセル中…";
        // REM: ログペインに追加
        logPane.appendChild(cancelDiv);
        // REM: 强制スクロール
        logPane.scrollTop = logPane.scrollHeight;
      }

      // REM: バックエンドにキャンセル指示を送信
      try {
        await fetch("/ingest/cancel", { method: "POST" });
      } catch (e) {
        console.error("キャンセルAPIエラー", e);
      }
      // REM: SSE は切断せず、バックエンドからの 'stopped' イベントを待つ
    });

    // REM: SSE完了時のコールバック（UI再活性化）
    window.onIngestComplete = () => setFormDisabled(false);

    // REM: ログ内のPDFリンクをクリックした際のプレビュー表示
    logPane.addEventListener("click", e => {
      const a = e.target.closest("a");
      // REM: リンクテキストが.pdfで終わる場合にのみPDFリンクと判定
      if (!a || !a.textContent.trim().toLowerCase().endsWith('.pdf')) return;
      e.preventDefault();
      // REM: PDF表示モード取得
      let pdfMode;
      for (const r of pdfModeRadios) {
        if (r.checked) { pdfMode = r.value; break; }
      }
      
      if (pdfMode === "embed") {
        // REM: 同一PDF再クリックで閉じる
        if (currentPdf === a.href) {
          // 新しいPDFプレビューシステムで非表示
          if (window.hidePdfPreview) {
            window.hidePdfPreview();
          }
          currentPdf = null;
          return;
        }
        
        // REM: 新しいPDFプレビューシステムで表示
        if (window.showPdfPreview) {
          window.showPdfPreview(a.href);
          currentPdf = a.href;
        }
      } else {
        // REM: 従前の別タブ表示
        window.open(a.href, '_blank');
      }
    });

    // REM: スプリッターでペイン幅をドラッグ調整
    (function() {
      let dragging = false;
      let startX   = 0;
      let startW   = 0;

      function onMouseMove(e) {
        if (!dragging) return;
        const dx = e.clientX - startX;
        const newW = startW + dx
        const containerW = document.getElementById("pane-bottom").clientWidth;
        if (newW < 100 || newW > containerW * 0.8) return;
        // REM: flexBasis を用いて安定的に幅変更
        logPane.style.flexBasis   = `${newW}px`;
        editorPane.style.flexGrow = "1";
      }

      function onMouseUp() {
        if (!dragging) return;
        dragging = false;
        document.body.style.userSelect = "";
        document.removeEventListener("mousemove", onMouseMove);
        document.removeEventListener("mouseup", onMouseUp);
      }

      splitter.addEventListener("mousedown", e => {
        dragging = true;
        startX   = e.clientX;
        startW   = logPane.getBoundingClientRect().width;
        document.body.style.userSelect = "none";
        document.addEventListener("mousemove", onMouseMove);
        document.addEventListener("mouseup", onMouseUp);
      });
    })();    
  }); // REM: DOMContentLoaded end
})(); // REM: IIFE end
