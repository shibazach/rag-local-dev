// app/static/js/chat_search.js @作成日時: 2025-07-25
// REM: chatページの検索機能

class ChatSearch {
  constructor(layoutManager) {
    this.layoutManager = layoutManager;
    this.searchBtn = document.getElementById('search-btn');
    this.cancelBtn = document.getElementById('cancel-btn');
    this.queryInput = document.getElementById('query');
    this.resultsDiv = document.getElementById('results');
    this.answerDiv = document.getElementById('answer');
    this.loadingSpan = document.getElementById('loading');
    
    this.searchInProgress = false;
    
    this.initializeEventListeners();
  }

  initializeEventListeners() {
    if (this.searchBtn) {
      this.searchBtn.addEventListener('click', () => this.startSearch());
    }
    if (this.cancelBtn) {
      this.cancelBtn.addEventListener('click', () => this.cancelSearch());
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
      alert('既に検索が実行中です');
      return;
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
      this.showSearchMessage('検索を開始しています...');

      // 検索パラメータを収集
      const searchParams = this.collectSearchParams();
      
      // 検索実行（実際の検索APIは既存のchat.jsから移植する必要があります）
      const results = await this.performSearch(searchParams);
      
      // 結果表示
      this.displayResults(results);

    } catch (error) {
      console.error('❌ 検索エラー:', error);
      this.showSearchMessage('エラー: ' + error.message);
    } finally {
      this.onSearchComplete();
    }
  }

  collectSearchParams() {
    return {
      query: this.queryInput.value.trim(),
      mode: document.getElementById('mode')?.value || 'ファイル別（要約+一致度）',
      model_key: document.getElementById('model_key')?.value || '',
      search_limit: parseInt(document.getElementById('search_limit')?.value) || 10,
      min_score: parseFloat(document.getElementById('min_score')?.value) || 0.0
    };
  }

  async performSearch(params) {
    // TODO: 実際の検索API呼び出しを実装
    // 既存のchat.jsから検索ロジックを移植する必要があります
    console.log('検索パラメータ:', params);
    
    // 仮の実装（実際のAPIに置き換える）
    return new Promise((resolve) => {
      setTimeout(() => {
        resolve({
          results: [
            {
              file_name: 'sample.pdf',
              file_id: 'sample_id',
              content: 'サンプル検索結果です。',
              score: 0.85
            }
          ]
        });
      }, 2000);
    });
  }

  displayResults(data) {
    if (!this.resultsDiv) return;
    
    this.resultsDiv.innerHTML = '';
    
    if (data.results && data.results.length > 0) {
      data.results.forEach((result, index) => {
        const card = this.createResultCard(result, index);
        this.resultsDiv.appendChild(card);
      });
    } else {
      this.resultsDiv.innerHTML = '<p>検索結果が見つかりませんでした。</p>';
    }
  }

  createResultCard(result, index) {
    const card = document.createElement('div');
    card.className = 'card';
    
    const title = document.createElement('h3');
    const link = document.createElement('a');
    link.href = '#';
    link.textContent = result.file_name;
    link.addEventListener('click', (e) => {
      e.preventDefault();
      if (result.file_id && this.layoutManager) {
        this.layoutManager.togglePDFPreview(result.file_id, result.file_name);
      }
    });
    title.appendChild(link);
    card.appendChild(title);
    
    const content = document.createElement('pre');
    content.textContent = result.content;
    card.appendChild(content);
    
    const score = document.createElement('div');
    score.textContent = `一致度: ${(result.score * 100).toFixed(1)}%`;
    score.style.color = '#666';
    score.style.fontSize = '0.9em';
    card.appendChild(score);
    
    return card;
  }

  async cancelSearch() {
    if (!this.searchInProgress) return;
    
    if (!confirm('検索をキャンセルしますか？')) return;

    try {
      // TODO: 検索キャンセルAPI呼び出し
      this.showSearchMessage('⏹️ キャンセル中...');
      
      // ボタン状態を更新
      if (this.searchBtn) this.searchBtn.textContent = 'キャンセル中...';
      if (this.cancelBtn) {
        this.cancelBtn.textContent = 'キャンセル中...';
        this.cancelBtn.disabled = true;
      }
      
    } catch (error) {
      console.error('キャンセルエラー:', error);
      this.showSearchMessage('❌ キャンセルエラー: ' + error.message);
    } finally {
      this.onSearchComplete();
    }
  }

  onSearchComplete() {
    this.searchInProgress = false;
    this.setFormDisabled(false);
    
    if (this.searchBtn) this.searchBtn.textContent = '🔍 検索実行';
    if (this.loadingSpan) this.loadingSpan.style.display = 'none';
  }

  setFormDisabled(disabled) {
    const formElements = document.querySelectorAll('#search-panel input, #search-panel select, #search-panel button, #search-panel textarea');
    formElements.forEach(el => {
      if (el.name !== 'pdf_mode') el.disabled = disabled;
    });
    
    if (this.cancelBtn) this.cancelBtn.disabled = !disabled;
  }

  clearResults() {
    if (this.resultsDiv) this.resultsDiv.innerHTML = '';
    if (this.answerDiv) this.answerDiv.style.display = 'none';
  }

  showSearchMessage(message) {
    if (this.resultsDiv) {
      this.resultsDiv.innerHTML = `<p style="color: #666; font-style: italic;">${message}</p>`;
    }
  }
}

// グローバルに公開
window.ChatSearch = ChatSearch;