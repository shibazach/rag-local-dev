// app/static/js/chat_main.js

(function() {
  document.addEventListener("DOMContentLoaded", () => {
    console.log('🚀 Chatシステム初期化開始');

    // DOM要素の存在確認
    const requiredElements = [
      'app-container', 'settings-panel', 'top-container', 
      'left-container', 'log-content'
    ];
    
    const missingElements = requiredElements.filter(id => !document.getElementById(id));
    if (missingElements.length > 0) {
      console.error('必要なDOM要素が見つかりません:', missingElements);
      return;
    }

    // 少し遅延させてから初期化
    setTimeout(() => {
      console.log('🚀 Chat遅延初期化開始');
      
      // 各機能モジュールのインスタンス化
      const layoutManager = new ChatLayout();
      const resizeManager = new ChatResize();
      const searchManager = new ChatSearch(layoutManager);
      const historyManager = new ChatHistory(searchManager);
      
      // グローバルに公開（デバッグ用）
      window.chatManagers = {
        layout: layoutManager,
        resize: resizeManager,
        search: searchManager,
        history: historyManager
      };
      
      // 後方互換性のため個別にも公開
      window.chatLayout = layoutManager;
      window.chatResize = resizeManager;
      window.chatSearch = searchManager;
      window.chatHistory = historyManager;
      
      console.log('✅ Chatシステム初期化完了');
    }, 100); // 100ms遅延

    // 既存のchat.jsから移植したナビゲーション制御機能
    let searchInProgress = false;
    const navWarning = document.getElementById('nav-warning');

    // 検索開始時の処理
    function startSearch() {
      searchInProgress = true;
      document.body.classList.add('search-in-progress');

      // ページ離脱の警告
      window.addEventListener('beforeunload', handleBeforeUnload);

      // ナビゲーションリンクのクリックを監視
      document.querySelectorAll('nav a').forEach(link => {
        link.addEventListener('click', handleNavClick);
      });
    }

    // 検索終了時の処理
    function endSearch() {
      searchInProgress = false;
      document.body.classList.remove('search-in-progress');

      // イベントリスナーを削除
      window.removeEventListener('beforeunload', handleBeforeUnload);
      document.querySelectorAll('nav a').forEach(link => {
        link.removeEventListener('click', handleNavClick);
      });

      // 警告メッセージを隠す
      if (navWarning) navWarning.style.display = 'none';
    }

    // ページ離脱時の警告
    function handleBeforeUnload(e) {
      if (searchInProgress) {
        const message = '検索処理中です。ページを離れると処理が中断されます。';
        e.preventDefault();
        e.returnValue = message;
        return message;
      }
    }

    // ナビゲーションリンククリック時の処理
    function handleNavClick(e) {
      if (searchInProgress) {
        e.preventDefault();
        e.stopPropagation();

        // 警告メッセージを表示
        if (navWarning) {
          navWarning.style.display = 'block';

          // 3秒後に自動で隠す
          setTimeout(() => {
            navWarning.style.display = 'none';
          }, 3000);
        }

        return false;
      }
    }

    // 検索進行状況の更新（経過時間付き）
    let searchStartTime = null;
    let searchTimerInterval = null;
    
    function updateSearchProgress(message, details = '') {
      const searchMessage = document.getElementById('search-message');
      const searchDetails = document.getElementById('search-details');

      if (searchMessage) {
        if (searchStartTime) {
          const elapsed = Math.floor((Date.now() - searchStartTime) / 1000);
          const minutes = Math.floor(elapsed / 60);
          const seconds = elapsed % 60;
          const timeStr = minutes > 0 ? `${minutes}分${seconds}秒` : `${seconds}秒`;
          searchMessage.textContent = `${message} (${timeStr})`;
        } else {
          searchMessage.textContent = message;
        }
      }
      if (searchDetails) {
        searchDetails.textContent = details;
      }
    }
    
    // 基本メッセージを保存する変数
    let baseSearchMessage = '';
    
    function startSearchTimer() {
      // 既存のタイマーがあれば停止
      if (searchTimerInterval) {
        clearInterval(searchTimerInterval);
        searchTimerInterval = null;
      }
      
      searchStartTime = Date.now();
      console.log('🕐 検索タイマー開始:', new Date().toLocaleTimeString());
      
      // 現在のメッセージを基本メッセージとして保存
      const searchMessage = document.getElementById('search-message');
      if (searchMessage) {
        baseSearchMessage = searchMessage.textContent.replace(/ \(\d+[分秒]+\)$/, '') || '検索中';
      }
      
      // 1秒間隔で経過時間を更新
      searchTimerInterval = setInterval(() => {
        const searchMessage = document.getElementById('search-message');
        if (searchMessage && searchStartTime) {
          const elapsed = Math.floor((Date.now() - searchStartTime) / 1000);
          const minutes = Math.floor(elapsed / 60);
          const seconds = elapsed % 60;
          const timeStr = minutes > 0 ? `${minutes}分${seconds}秒` : `${seconds}秒`;
          
          // 基本メッセージに時間を追加して直接設定
          searchMessage.textContent = `${baseSearchMessage} (${timeStr})`;
        }
      }, 1000);
    }
    
    function stopSearchTimer() {
      console.log('🛑 検索タイマー停止:', new Date().toLocaleTimeString());
      if (searchTimerInterval) {
        clearInterval(searchTimerInterval);
        searchTimerInterval = null;
        console.log('✅ タイマーをクリアしました');
      }
      searchStartTime = null;
    }

    // グローバル関数として公開（既存のchat.jsとの互換性のため）
    window.chatSearchStart = startSearch;
    window.chatSearchEnd = endSearch;
    window.updateChatSearchProgress = updateSearchProgress;
    window.startSearchTimer = startSearchTimer;
    window.stopSearchTimer = stopSearchTimer;
  });
})();