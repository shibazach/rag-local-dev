// app/static/js/chat_search.js

class ChatSearch {
  constructor(layoutManager) {
    this.layoutManager = layoutManager;
    this.searchBtn = document.getElementById('search-btn');
    this.cancelBtn = document.getElementById('cancel-btn');
    this.queryInput = document.getElementById('query');
    this.resultsDiv = document.getElementById('results');
    this.answerDiv = document.getElementById('answer');
    this.loadingSpan = document.getElementById('loading');
    this.logContent = document.getElementById('log-content');
    
    // 検索中オーバーレイ
    this.searchOverlay = document.getElementById('search-overlay');
    this.searchMessage = document.getElementById('search-message');
    this.searchDetails = document.getElementById('search-details');
    this.searchCancelOverlayBtn = document.getElementById('search-cancel-overlay-btn');
    
    // 再ベクトル化オーバーレイ
    this.processingOverlay = document.getElementById('processing-overlay');
    this.overlayMsg = document.getElementById('overlay-message');
    this.overlayOk = document.getElementById('overlay-ok-btn');
    this.detailContent = document.getElementById('detail-content');
    
    this.searchInProgress = false;
    this.controller = null;
    this.searchStartTime = null;
    this.searchTimerInterval = null;
    
    this.initializeEventListeners();
    this.hideOverlay();
    this.hideSearchOverlay();
  }

  initializeEventListeners() {
    if (this.searchBtn) {
      this.searchBtn.addEventListener('click', () => this.startSearch());
    }
    if (this.cancelBtn) {
      this.cancelBtn.addEventListener('click', () => this.cancelSearch());
    }

    // 検索中オーバーレイのキャンセルボタン
    if (this.searchCancelOverlayBtn) {
      this.searchCancelOverlayBtn.addEventListener('click', () => this.cancelSearch());
    }

    // ページ離脱警告
    window.addEventListener('beforeunload', (e) => {
      if (this.searchInProgress) {
        e.preventDefault();
        e.returnValue = '検索処理中です。ページを離れますか？';
      }
    });
  }

  async startSearch() {
    console.log('🔍 検索開始');
    
    if (this.searchInProgress) {
      console.log('❌ 既に検索が実行中です');
      return;
    }
    
    // 前回のコントローラーが残っている場合は中断
    if (this.controller) {
      console.log('🚫 前回のリクエストを中断します');
      this.controller.abort();
      this.controller = null;
    }

    const query = this.queryInput ? this.queryInput.value.trim() : '';
    if (!query) {
      alert('質問を入力してください');
      return;
    }

    try {
      this.searchInProgress = true;
      this.setFormDisabled(true);
      
      if (this.searchBtn) this.searchBtn.textContent = '検索中...';
      if (this.loadingSpan) this.loadingSpan.style.display = 'inline';
      
      this.clearResults();
      this.hideOverlay();
      
      // 検索中オーバーレイを表示
      this.showSearchOverlay();

      // ナビゲーション制御を開始
      if (window.chatSearchStart) window.chatSearchStart();

      // 検索パラメータを収集
      const searchParams = this.collectSearchParams();
      
      // 検索実行
      let results;
      try {
        results = await this.performSearch(searchParams);
      } catch (searchError) {
        console.error('🚨 検索リクエストエラー:', searchError);
        // テスト用のダミーデータで動作確認
        results = {
          mode: "ファイル別（要約+一致度）",
          results: [
            {
              file_id: "dummy_test1", // ダミーPDFプレビュー用のID
              file_name: "テストファイル1.pdf（ダミーデータ）",
              summary: "これはテスト用の検索結果です。実際のサーバーとの通信でエラーが発生したため、ダミーデータを表示しています。ファイル名をクリックするとダミーPDFがプレビューされます。",
              score: 0.85
            }
          ]
        };
        console.log('🧪 テスト用ダミーデータを使用します');
      }
      
      // 結果表示
      this.renderResults(results);

    } catch (error) {
      console.error('❌ 検索エラー:', error);
      if (error.name === "AbortError") {
        this.showSearchMessage('検索をキャンセルしました。');
      } else {
        this.showSearchMessage('通信エラー: ' + error.message);
        // 詳細なエラー情報を表示
        alert(`検索エラーが発生しました:\n${error.message}\n\nコンソールで詳細を確認してください。`);
      }
    } finally {
      this.onSearchComplete();
    }
  }

  collectSearchParams() {
    return {
      query: this.queryInput.value.trim(),
      mode: document.getElementById('mode')?.value || 'ファイル別（要約+一致度）',
      model_key: document.getElementById('model_key')?.value || 'intfloat/e5-large-v2',
      search_limit: parseInt(document.getElementById('search_limit')?.value) || 10,
      min_score: parseFloat(document.getElementById('min_score')?.value) || 0.0
    };
  }

  async performSearch(params) {
    this.controller = new AbortController();
    const signal = this.controller.signal;

    const form = new FormData();
    form.append("query", params.query);
    form.append("mode", params.mode);
    form.append("model_key", params.model_key);
    form.append("search_limit", params.search_limit);
    form.append("min_score", params.min_score);

    console.log("🚀 検索リクエスト送信:", params);

    // ユーザー設定のタイムアウトを取得（デフォルト5秒）
    const timeoutSeconds = parseInt(document.getElementById('search_timeout')?.value) || 5;
    const timeoutMs = timeoutSeconds > 0 ? timeoutSeconds * 1000 : 0; // 0の場合はタイムアウトなし
    
    let timeoutId = null;
    if (timeoutMs > 0) {
      timeoutId = setTimeout(() => {
        this.controller.abort();
      }, timeoutMs);
    }

    try {
      const res = await fetch("/query", { method: "POST", body: form, signal });
      clearTimeout(timeoutId);
      
      console.log("📡 サーバー応答受信:", res.status, res.statusText);
      
      if (!res.ok) {
        throw new Error(`サーバーエラー: ${res.status} ${res.statusText}`);
      }
      
      const json = await res.json();
      console.log("★ fetch /query →", json);

      if (json.error) {
        throw new Error(json.error);
      }

      return json;
    } catch (error) {
      if (timeoutId) clearTimeout(timeoutId);
      if (error.name === 'AbortError') {
        // タイムアウト時は非同期処理の停止を試行
        await this.stopBackgroundProcesses();
        const timeoutMsg = timeoutMs > 0 ? `検索がタイムアウトしました（${timeoutSeconds}秒）` : '検索がキャンセルされました';
        throw new Error(timeoutMsg);
      }
      throw error;
    }
  }

  renderResults(json) {
    console.log('🎯 renderResults開始:', json);
    console.log('🎯 resultsDiv:', this.resultsDiv);
    
    if (!this.resultsDiv) {
      console.error('❌ resultsDiv が見つかりません');
      alert('エラー: 検索結果表示エリアが見つかりません');
      return;
    }
    
    // 結果が空の場合の処理
    if (!json.results || json.results.length === 0) {
      this.resultsDiv.innerHTML = '<p style="text-align: center; color: #666; margin: 2em;">検索結果が見つかりませんでした。</p>';
      console.log('📝 検索結果が空です');
      return;
    }
    
    this.resultsDiv.innerHTML = "";
    console.log(`📊 ${json.results.length}件の結果を表示します`);

    // チャンク統合モード
    if (json.mode === "チャンク統合") {
      if (this.answerDiv) {
        this.answerDiv.innerHTML = `<h2>統合回答</h2><pre>${json.answer}</pre>`;
        this.answerDiv.style.display = "block";
      }
      this.resultsDiv.innerHTML = `<h3>ソースファイル</h3>`;
      json.sources.forEach((src, i) => {
        const file_id = src.file_id;
        const file_name = src.file_name;
        this.resultsDiv.innerHTML +=
          `<p>${i + 1}. <a href="#" onclick="window.chatManagers.search.openFile('${file_id}', '${file_name}')">${file_name}</a></p>`;
      });
    } else {
      if (this.answerDiv) {
        this.answerDiv.style.display = "none";
      }
    }

    json.results.forEach((item, idx) => {
      const card = document.createElement("div");
      card.className = "card";

      // タイトル (ファイル別モード)
      const h3 = document.createElement("h3");
      const file_id = item.file_id;
      const file_name = item.file_name;
      if (file_id) {
        h3.innerHTML =
          `${idx + 1}. <a href="#" onclick="window.chatManagers.search.openFile('${file_id}', '${file_name}')">${file_name}</a>`;
      } else {
        h3.textContent = `${idx + 1}. ${file_name}`;
      }
      card.appendChild(h3);

      // コンテンツ表示
      const pre = document.createElement("pre");
      const content = json.mode === "チャンク統合" ? item.snippet : item.summary;
      pre.textContent = content || "";
      card.appendChild(pre);

      // 一致度表示（ファイル別モードのみ）
      if (item.score !== undefined) {
        const p = document.createElement("p");
        p.textContent = `一致度: ${item.score.toFixed(2)}`;
        card.appendChild(p);
      }

      // 編集機能
      if (file_id) {
        this.addEditor(file_id, card);
      }

      // 詳細表示機能
      card.addEventListener('click', (e) => {
        // 編集ボタンやリンクのクリックは除外
        if (e.target.tagName === 'BUTTON' || e.target.tagName === 'A') {
          return;
        }
        this.showDetailView(item, file_name);
      });

      card.style.cursor = 'pointer';
      card.title = 'クリックで詳細表示';

      this.resultsDiv.appendChild(card);
    });
  }

  addEditor(file_id, container) {
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
          console.log("★ fetch /api/content →", data);
          editorDiv.innerHTML = `
            <textarea style="width: 100%; box-sizing: border-box; resize: vertical; height: 200px;">${data.content}</textarea><br>
            <button class="save-btn" style="margin-right: 8px;">保存（再ベクトル化）</button>
          `;
          editorDiv.querySelector(".save-btn").addEventListener("click", async () => {
            const newContent = editorDiv.querySelector("textarea").value;
            if (this.overlayMsg) this.overlayMsg.innerHTML = "再ベクトル化中…<br>閉じないでください";
            if (this.overlayOk) this.overlayOk.style.display = "none";
            this.showOverlay();

            try {
              const form2 = new FormData();
              form2.append("content", newContent);
              const resSave = await fetch(`/api/save/${file_id}`, {
                method: "POST",
                body: form2
              });
              if (!resSave.ok) {
                const txt = await resSave.text();
                if (this.overlayMsg) this.overlayMsg.innerHTML = `❌ エラー: ${txt}`;
              } else {
                if (this.overlayMsg) this.overlayMsg.innerHTML = "✅ 再ベクトル化完了";
              }
            } catch (err) {
              if (this.overlayMsg) this.overlayMsg.innerHTML = `❌ 通信エラー: ${err.message}`;
            } finally {
              if (this.overlayOk) {
                this.overlayOk.style.display = "block";
                this.overlayOk.replaceWith(this.overlayOk.cloneNode(true));
                const newOk = document.getElementById("overlay-ok-btn");
                if (newOk) {
                  newOk.addEventListener("click", () => {
                    this.hideOverlay();
                    newOk.style.display = "none";
                    editorDiv.style.display = "none";
                    toggleBtn.textContent = "✏️ 編集";
                    const updated = editorDiv.querySelector("textarea").value;
                    const pre = container.querySelector("pre");
                    if (pre) pre.textContent = updated;
                  });
                }
              }
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

  openFile(fileId, fileName) {
    console.log(`🔍 openFile呼び出し: fileId=${fileId}, fileName=${fileName}`);
    
    const pdfMode = document.querySelector('input[name="pdf_mode"]:checked')?.value || 'embed';
    
    if (pdfMode === "newtab") {
      // 別タブで開く
      window.open(`/viewer/${fileId}`, '_blank');
    } else {
      // 同一タブ内表示（レイアウトマネージャーを使用）
      if (this.layoutManager) {
        console.log(`📄 レイアウトマネージャーでPDF表示: ${fileName} (${fileId})`);
        
        // デバッグ情報を表示
        this.layoutManager.debugCurrentState();
        
        this.layoutManager.togglePDFPreview(fileId, fileName);
        
        // 処理後の状態も確認
        setTimeout(() => {
          console.log('📊 PDF表示処理後の状態:');
          this.layoutManager.debugCurrentState();
        }, 200);
      } else {
        console.error('❌ レイアウトマネージャーが見つかりません');
      }
    }
  }

  async cancelSearch() {
    if (this.controller) {
      this.controller.abort();
    }
  }

  onSearchComplete() {
    this.searchInProgress = false;
    this.setFormDisabled(false);
    this.controller = null;
    
    if (this.searchBtn) this.searchBtn.textContent = '🔍 検索実行';
    if (this.loadingSpan) this.loadingSpan.style.display = 'none';
    
    // 検索中オーバーレイを非表示
    this.hideSearchOverlay();

    // ナビゲーション制御を終了
    if (window.chatSearchEnd) window.chatSearchEnd();
  }

  setFormDisabled(disabled) {
    // 検索中は入力フィールドをグレーアウト
    const elements = ['query', 'mode', 'model_key', 'search_limit', 'min_score'];
    elements.forEach(id => {
      const el = document.getElementById(id);
      if (el) el.disabled = disabled;
    });
    
    if (this.searchBtn) this.searchBtn.disabled = disabled;
    if (this.cancelBtn) this.cancelBtn.disabled = !disabled;
  }

  clearResults() {
    if (this.resultsDiv) this.resultsDiv.innerHTML = '';
    if (this.answerDiv) this.answerDiv.style.display = 'none';
  }

  showSearchMessage(message) {
    if (this.resultsDiv) {
      this.resultsDiv.innerHTML = `<p style="color: #666; font-style: italic; text-align: center; margin-top: 2em;">${message}</p>`;
    }
  }

  // オーバーレイ表示
  showOverlay() {
    if (this.processingOverlay) this.processingOverlay.style.display = "flex";
  }

  // オーバーレイ非表示
  hideOverlay() {
    if (this.processingOverlay) this.processingOverlay.style.display = "none";
  }

  // 検索中オーバーレイ表示
  showSearchOverlay() {
    if (this.searchOverlay) {
      this.searchOverlay.style.display = "flex";
      this.startSearchTimer();
    }
  }

  // 検索中オーバーレイ非表示
  hideSearchOverlay() {
    if (this.searchOverlay) {
      this.searchOverlay.style.display = "none";
      this.stopSearchTimer();
    }
  }

  // 検索タイマー開始
  startSearchTimer() {
    this.searchStartTime = Date.now();
    console.log('🕐 検索タイマー開始:', new Date().toLocaleTimeString());
    
    // 初期メッセージ設定
    if (this.searchMessage) {
      this.searchMessage.textContent = '検索中…';
    }
    if (this.searchDetails) {
      this.searchDetails.textContent = '0秒経過';
    }
    
    // 1秒間隔で経過時間を更新
    this.searchTimerInterval = setInterval(() => {
      if (this.searchStartTime) {
        const elapsed = Math.floor((Date.now() - this.searchStartTime) / 1000);
        const minutes = Math.floor(elapsed / 60);
        const seconds = elapsed % 60;
        const timeStr = minutes > 0 ? `${minutes}分${seconds}秒` : `${seconds}秒`;
        
        if (this.searchDetails) {
          this.searchDetails.textContent = `${timeStr}経過`;
        }
      }
    }, 1000);
  }

  // 検索タイマー停止
  stopSearchTimer() {
    console.log('🛑 検索タイマー停止:', new Date().toLocaleTimeString());
    if (this.searchTimerInterval) {
      clearInterval(this.searchTimerInterval);
      this.searchTimerInterval = null;
      console.log('✅ タイマーをクリアしました');
    }
    this.searchStartTime = null;
  }



  // タイムアウト時の非同期処理停止
  async stopBackgroundProcesses() {
    console.log('🛑 バックグラウンド処理の停止を試行中...');
    
    try {
      // 1. クライアント側のリクエストをキャンセル
      if (this.controller) {
        console.log('🚫 現在のリクエストをキャンセルします');
        this.controller.abort();
      }
      
      // 2. サーバー側の処理停止を要求
      console.log('🔄 サーバー側の処理停止を要求中...');
      try {
        const stopResponse = await fetch('/stop_search', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          }
        });
        
        if (stopResponse.ok) {
          const result = await stopResponse.json();
          console.log('✅ サーバー側処理停止成功:', result.message);
        } else {
          console.warn('⚠️ サーバー側処理停止失敗:', stopResponse.status);
        }
      } catch (stopError) {
        console.warn('⚠️ サーバー側処理停止リクエストエラー:', stopError);
      }
      
      console.log('✅ バックグラウンド処理の停止を完了しました');
      
    } catch (error) {
      console.warn('⚠️ バックグラウンド処理停止中にエラー:', error);
    }
  }

  // 詳細表示機能
  showDetailView(item, fileName) {
    if (!this.detailContent) return;

    const detailHTML = `
      <div class="detail-header">
        <h2 class="detail-title">${fileName}</h2>
        <div class="detail-meta">
          ${item.score !== undefined ? `一致度: ${item.score.toFixed(3)}` : ''}
          ${item.file_id ? ` | ファイルID: ${item.file_id}` : ''}
        </div>
      </div>
      <div class="detail-text">
        ${item.summary || item.snippet || item.content || 'コンテンツがありません'}
      </div>
      ${item.file_id ? `
        <div style="margin-top: 1em; padding-top: 1em; border-top: 1px solid #eee;">
          <button onclick="window.chatManagers.search.openFile('${item.file_id}', '${fileName}')" 
                  style="padding: 0.5em 1em; background: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer;">
            📄 ファイルを開く
          </button>
        </div>
      ` : ''}
    `;

    this.detailContent.innerHTML = detailHTML;
    
    // 詳細表示ペインをハイライト
    const detailPanel = document.getElementById('detail-panel');
    if (detailPanel) {
      detailPanel.style.border = '2px solid #007bff';
      setTimeout(() => {
        detailPanel.style.border = '';
      }, 1000);
    }
  }
}

// グローバルに公開
window.ChatSearch = ChatSearch;