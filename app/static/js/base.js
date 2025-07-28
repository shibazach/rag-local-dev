// app/static/js/base.js

class BaseSystem {
  constructor() {
    this.initialize();
  }

  initialize() {
    // システムメトリクス監視を開始
    this.startSystemMonitoring();
    
    // 辞書機能の初期化
    this.initializeDictionary();
    
    // 辞書ボタンの件数を読み込み
    this.loadDictButtonCounts();
  }

  // システムメトリクス監視（タイムアウト付き）
  startSystemMonitoring() {
    setInterval(async () => {
      try {
        // 5秒タイムアウトを設定
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 5000);
        
        const res = await fetch('/metrics', { 
          signal: controller.signal 
        });
        clearTimeout(timeoutId);
        
        if (!res.ok) return;
        const j = await res.json();
        // j.cpu が未定義の場合はスキップ
        if (!j || typeof j.cpu !== 'number') return;
        document.getElementById('cpu-usage').textContent = j.cpu.toFixed(1);
        // GPU 情報がある場合のみ表示
        if (j.gpu && typeof j.gpu.util === 'number') {
          document.getElementById('gpu-info').style.display = 'block';
          document.getElementById('gpu-util').textContent = j.gpu.util.toFixed(1);
          // GPU power が数値なら表示
          if (typeof j.gpu.power === 'number') {
            document.getElementById('gpu-power').textContent = j.gpu.power.toFixed(1);
          }
        }
      } catch (e) {
        if (e.name === 'AbortError') {
          console.warn('metrics fetch timeout (5s)');
        } else {
          console.error('metrics fetch error:', e);
        }
        // エラー時も表示を更新（サーバーが重い状態を示す）
        document.getElementById('cpu-usage').textContent = '高負荷';
      }
    }, 3000);
  }

  // 辞書機能の初期化
  initializeDictionary() {
    // 辞書モーダルの作成
    const dictModal = document.createElement('div');
    dictModal.id = 'dict-modal';
    dictModal.className = 'modal';
    dictModal.innerHTML = `
      <div class="modal-content" style="width: 90%; max-width: 1000px;">
        <div class="modal-header">
          <h3 id="dict-modal-title">辞書編集</h3>
          <span class="close" id="dict-modal-close">&times;</span>
        </div>
        <div style="height: 70vh; padding: 1em;">
          <div style="margin-bottom: 1em;">
            <button id="dict-save-btn" class="btn-primary" style="margin-right: 0.5em;">💾 保存</button>
            <button id="dict-add-btn" class="btn-secondary">➕ エントリ追加</button>
          </div>
          <textarea id="dict-textarea" style="width: 100%; height: calc(100% - 60px); font-family: monospace; font-size: 0.9em; padding: 0.5em; border: 1px solid #ddd; border-radius: 4px; resize: none;"></textarea>
        </div>
      </div>
    `;
    document.body.appendChild(dictModal);

    const dictModalClose = document.getElementById('dict-modal-close');
    const dictSaveBtn = document.getElementById('dict-save-btn');
    const dictAddBtn = document.getElementById('dict-add-btn');
    const dictTextarea = document.getElementById('dict-textarea');

    let currentDict = null;

    // モーダル閉じる処理
    const closeModal = () => {
      dictModal.style.display = 'none';
    };

    dictModalClose.addEventListener('click', closeModal);
    dictModal.addEventListener('click', (e) => {
      if (e.target === dictModal) closeModal();
    });

    // 直接辞書編集を開く
    window.loadDictDirect = async (dictName) => {
      dictModal.style.display = 'block';

      try {
        // 辞書情報を取得してタイトルを更新
        const [contentResponse, listResponse] = await Promise.all([
          fetch(`/api/dict/content/${encodeURIComponent(dictName)}`),
          fetch('/api/dict/list')
        ]);

        const dictData = await contentResponse.json();
        const dictList = await listResponse.json();

        currentDict = dictData;

        // タイトルに詳細情報を表示
        const dictInfo = dictList.find(d => d.name === dictName);
        if (dictInfo) {
          const titleElement = document.getElementById('dict-modal-title');
          const icon = dictName === '一般用語' ? '📄' :
            dictName === '専門用語' ? '🔬' :
              dictName === '誤字修正' ? '🔧' : '⚙️';
          titleElement.innerHTML = `
            <div style="font-size:1.2em; font-weight:bold; line-height:1.5em;">${icon} ${dictName}</div>
            <div style="font-size:0.75em; color:#666; font-weight:normal; margin-top:0.2em;">${dictInfo.description} | ${dictInfo.entry_count}件 | ${dictInfo.modified}</div>
          `;
        }

        // CSVデータをテキストエリアに表示
        let content = '';
        if (dictData.headers && dictData.headers.length > 0) {
          content += dictData.headers.join(',') + '\n';
        }
        if (dictData.data && dictData.data.length > 0) {
          dictData.data.forEach(row => {
            content += row.join(',') + '\n';
          });
        }

        dictTextarea.value = content;

      } catch (error) {
        alert('辞書の読み込みに失敗しました: ' + error.message);
        console.error('辞書読み込みエラー:', error);
        dictModal.style.display = 'none';
      }
    };

    // 辞書を保存
    dictSaveBtn.addEventListener('click', async () => {
      if (!currentDict) return;

      try {
        const formData = new FormData();
        formData.append('content', dictTextarea.value);

        const response = await fetch(`/api/dict/save/${encodeURIComponent(currentDict.name)}`, {
          method: 'POST',
          body: formData
        });

        const result = await response.json();

        if (result.success) {
          alert('保存しました');
          // 辞書件数を更新
          this.loadDictButtonCounts();
        } else {
          alert('保存に失敗しました: ' + result.message);
        }

      } catch (error) {
        alert('保存エラー: ' + error.message);
        console.error('保存エラー:', error);
      }
    });

    // エントリ追加
    dictAddBtn.addEventListener('click', () => {
      if (!currentDict) return;

      let newEntry = '';
      if (currentDict.type === 'single_column') {
        newEntry = prompt('追加する用語を入力してください:');
        if (newEntry) {
          dictTextarea.value += newEntry + '\n';
        }
      } else if (currentDict.type === 'two_column') {
        newEntry = prompt('誤字,正字 の形式で入力してください:');
        if (newEntry && newEntry.includes(',')) {
          dictTextarea.value += newEntry + '\n';
        } else if (newEntry) {
          alert('カンマ区切りで入力してください（例: 契約所,契約書）');
        }
      } else {
        alert('この辞書タイプの追加機能は未実装です');
      }
    });

    // 辞書リンクのクリックイベント（onclickで処理されるため、追加のイベントリスナーは不要）
  }

  // 辞書ボタンの件数を読み込み
  async loadDictButtonCounts() {
    try {
      const response = await fetch('/api/dict/list');
      const dicts = await response.json();
      
      dicts.forEach(dict => {
        const countElement = document.getElementById(`dict-count-${dict.name}`);
        if (countElement) {
          countElement.textContent = `${dict.entry_count}件`;
        }
      });
    } catch (error) {
      console.warn('辞書件数の読み込みに失敗:', error);
    }
  }

  // 辞書件数の更新（他のページから呼び出し可能）
  updateDictCount(dictName, count) {
    const countElement = document.getElementById(`dict-count-${dictName}`);
    if (countElement) {
      countElement.textContent = `${count}件`;
    }
  }
}

// ページ読み込み時の初期化
document.addEventListener('DOMContentLoaded', () => {
  const baseSystem = new BaseSystem();
  
  // グローバルに公開
  window.baseSystem = baseSystem;
});