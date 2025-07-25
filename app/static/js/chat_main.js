// app/static/js/chat_main.js @作成日時: 2025-07-25
// REM: chatページのメイン統合ファイル - 各機能モジュールを統合

(function() {
  document.addEventListener("DOMContentLoaded", () => {
    console.log('🚀 Chatシステム初期化開始');

    // DOM要素の存在確認
    const requiredElements = [
      'chat-container', 'search-panel', 'top-container', 
      'left-container', 'results-content'
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
      
      // グローバルに公開（デバッグ用）
      window.chatManagers = {
        layout: layoutManager,
        resize: resizeManager,
        search: searchManager
      };
      
      console.log('✅ Chatシステム初期化完了');
    }, 100); // 100ms遅延

    // 履歴機能の初期化（簡略版）
    const historyBtn = document.getElementById('history-btn');
    if (historyBtn) {
      historyBtn.addEventListener('click', showHistoryModal);
    }

    function showHistoryModal() {
      const modal = document.getElementById('history-modal');
      if (modal) {
        modal.style.display = 'block';
        console.log('履歴モーダル表示');
      }
    }

    // 履歴モーダルの閉じる機能
    const historyModalClose = document.getElementById('history-modal-close');
    const historyModalOverlay = document.getElementById('history-modal-overlay');
    const historyModal = document.getElementById('history-modal');
    
    if (historyModalClose) {
      historyModalClose.addEventListener('click', () => {
        if (historyModal) historyModal.style.display = 'none';
      });
    }
    
    if (historyModalOverlay) {
      historyModalOverlay.addEventListener('click', () => {
        if (historyModal) historyModal.style.display = 'none';
      });
    }
  });
})();