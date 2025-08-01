// app/static/js/chat_history.js

class ChatHistory {
  constructor(searchManager) {
    this.searchManager = searchManager;
    this.selectedHistoryItem = null;
    
    this.initializeEventListeners();
  }

  initializeEventListeners() {
    // 履歴ダイアログのイベントリスナー
    const historyBtn = document.getElementById('history-btn');
    const historyModalClose = document.getElementById('history-modal-close');
    const historyModalOverlay = document.getElementById('history-modal-overlay');
    const expandBtn = document.getElementById('history-expand-btn');
    const restoreBtn = document.getElementById('history-restore-btn');
    const deleteBtn = document.getElementById('history-delete-btn');
    const downloadBtn = document.getElementById('history-download-btn');
    const clearBtn = document.getElementById('history-clear-btn');

    if (historyBtn) {
      historyBtn.addEventListener('click', () => this.showHistoryModal());
    }
    if (historyModalClose) {
      historyModalClose.addEventListener('click', () => this.hideHistoryModal());
    }
    if (historyModalOverlay) {
      historyModalOverlay.addEventListener('click', () => this.hideHistoryModal());
    }

    // 展開ボタン
    if (expandBtn) {
      expandBtn.addEventListener('click', () => {
        if (this.selectedHistoryItem) {
          const selectedElement = document.querySelector(`[data-history-id="${this.selectedHistoryItem.id}"]`);
          if (selectedElement) {
            this.toggleHistoryExpansion(selectedElement);
          }
        }
      });
    }

    // 復元ボタン
    if (restoreBtn) {
      restoreBtn.addEventListener('click', () => {
        if (this.selectedHistoryItem) {
          this.restoreFromHistory(this.selectedHistoryItem);
        }
      });
    }

    // 削除ボタン
    if (deleteBtn) {
      deleteBtn.addEventListener('click', async () => {
        if (this.selectedHistoryItem && confirm('選択した履歴を削除しますか？')) {
          try {
            await fetch(`/history/${this.selectedHistoryItem.id}`, { method: 'DELETE' });
            this.loadHistoryList();
            this.selectedHistoryItem = null;
            this.updateHistoryButtons();
          } catch (error) {
            console.error('履歴削除エラー:', error);
            alert('履歴の削除に失敗しました');
          }
        }
      });
    }

    // ダウンロードボタン
    if (downloadBtn) {
      downloadBtn.addEventListener('click', async () => {
        const format = document.getElementById('history-download-format')?.value || 'txt';
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
    }

    // 全削除ボタン
    if (clearBtn) {
      clearBtn.addEventListener('click', async () => {
        if (confirm('全ての履歴を削除しますか？この操作は取り消せません。')) {
          try {
            await fetch('/history', { method: 'DELETE' });
            this.loadHistoryList();
            this.selectedHistoryItem = null;
            this.updateHistoryButtons();
          } catch (error) {
            console.error('履歴全削除エラー:', error);
            alert('履歴の削除に失敗しました');
          }
        }
      });
    }
  }

  // 履歴ダイアログの表示/非表示
  showHistoryModal() {
    const modal = document.getElementById('history-modal');
    if (modal) {
      modal.style.display = 'block';
      this.loadHistoryList();
    }
  }

  hideHistoryModal() {
    const modal = document.getElementById('history-modal');
    if (modal) {
      modal.style.display = 'none';
      this.selectedHistoryItem = null;
      this.updateHistoryButtons();
    }
  }

  // 履歴一覧の読み込み
  async loadHistoryList() {
    try {
      const response = await fetch('/history');
      const history = await response.json();

      const historyList = document.getElementById('history-list');
      if (!historyList) return;

      historyList.innerHTML = '';

      if (history.length === 0) {
        historyList.innerHTML = '<p style="text-align:center; color:#666; margin:2em;">履歴がありません</p>';
        return;
      }

      history.forEach(item => {
        const historyItem = this.createHistoryItem(item);
        historyList.appendChild(historyItem);
      });

    } catch (error) {
      console.error('履歴読み込みエラー:', error);
      const historyList = document.getElementById('history-list');
      if (historyList) {
        historyList.innerHTML = '<p style="text-align:center; color:#d32f2f; margin:2em;">履歴の読み込みに失敗しました</p>';
      }
    }
  }

  // 履歴アイテムのHTML要素を作成
  createHistoryItem(item) {
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
        <div class="history-item-result">${this.formatHistoryResult(result)}</div>
      </div>
    `;

    // クリックイベント
    div.addEventListener('click', () => this.selectHistoryItem(div, item));

    // ダブルクリックで展開
    div.addEventListener('dblclick', () => this.toggleHistoryExpansion(div));

    return div;
  }

  // 履歴結果をフォーマット
  formatHistoryResult(result) {
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
  selectHistoryItem(element, item) {
    // 既存の選択を解除
    document.querySelectorAll('.history-item.selected').forEach(el => {
      el.classList.remove('selected');
    });

    // 新しい選択を設定
    element.classList.add('selected');
    this.selectedHistoryItem = item;
    this.updateHistoryButtons();
  }

  // 履歴アイテムの展開/折りたたみ
  toggleHistoryExpansion(element) {
    const expanded = element.querySelector('.history-item-expanded');
    if (expanded) {
      expanded.classList.toggle('show');
    }
  }

  // 履歴ボタンの状態更新
  updateHistoryButtons() {
    const expandBtn = document.getElementById('history-expand-btn');
    const restoreBtn = document.getElementById('history-restore-btn');
    const deleteBtn = document.getElementById('history-delete-btn');

    const hasSelection = this.selectedHistoryItem !== null;
    if (expandBtn) expandBtn.disabled = !hasSelection;
    if (restoreBtn) restoreBtn.disabled = !hasSelection;
    if (deleteBtn) deleteBtn.disabled = !hasSelection;
  }

  // 履歴から検索条件を復元
  restoreFromHistory(historyItem) {
    const queryInput = document.getElementById('query');
    const modeSelect = document.getElementById('mode');
    const modelKeySelect = document.getElementById('model_key');

    if (queryInput) queryInput.value = historyItem.query;
    if (modeSelect) modeSelect.value = historyItem.mode;
    if (modelKeySelect) modelKeySelect.value = historyItem.model_key;

    // 結果を表示
    if (this.searchManager) {
      this.searchManager.renderResults(historyItem.result);
    }

    // ダイアログを閉じる
    this.hideHistoryModal();
  }
}

// グローバルに公開
window.ChatHistory = ChatHistory;