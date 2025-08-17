console.log('[upload] init script start');
// 外部JSではPython側IDは未使用だが、存在しない場合のデフォルトを設定
window.uploadPageId = window.uploadPageId || 'external';

// アップロード機能 - new/系移植版（app/系API対応）

// サーバーフォルダブラウザ機能を最初に定義（即座実行）
(function() {
    console.log('Defining openFolderBrowser function');
    
    window.openFolderBrowser = function() {
        console.log('openFolderBrowser called');
        
        // モーダルHTML構造をPythonで作成してもらう（NiceGUIのDOMに追加）
        const overlay = document.createElement('div');
        overlay.id = 'folder-browser-overlay';
        overlay.style.cssText = 
            'position: fixed;' +
            'top: 0;' +
            'left: 0;' +
            'width: 100%;' +
            'height: 100%;' +
            'background: rgba(0, 0, 0, 0.5);' +
            'z-index: 9999;' +
            'display: flex;' +
            'align-items: center;' +
            'justify-content: center;';
    
        const modal = document.createElement('div');
        modal.id = 'folder-browser-modal';
        modal.style.cssText = 
            'background: white;' +
            'border-radius: 8px;' +
            'box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);' +
            'width: 600px;' +
            'max-height: 80vh;' +
            'display: flex;' +
            'flex-direction: column;';
    
        modal.innerHTML = 
            '<div style="padding: 16px; border-bottom: 1px solid #e5e7eb; display: flex; justify-content: space-between; align-items: center;">' +
                '<h3 style="margin: 0; font-size: 18px; font-weight: 600;">📂 フォルダを選択</h3>' +
                '<button id="close-folder-browser" style="background: none; border: none; font-size: 24px; cursor: pointer; color: #6b7280;">&times;</button>' +
            '</div>' +
            '<div style="padding: 16px; flex: 1; overflow-y: auto;">' +
                '<div id="folder-breadcrumbs" style="background: #f3f4f6; padding: 8px 12px; border-radius: 4px; margin-bottom: 12px; font-family: monospace; font-size: 14px;"></div>' +
                '<ul id="folder-list" style="list-style: none; margin: 0; padding: 0; max-height: 300px; overflow-y: auto; border: 1px solid #e5e7eb; border-radius: 4px;"></ul>' +
            '</div>' +
            '<div style="padding: 16px; border-top: 1px solid #e5e7eb; display: flex; gap: 8px; justify-content: flex-end;">' +
                '<button id="cancel-folder-selection" style="padding: 8px 16px; border: 1px solid #d1d5db; background: white; border-radius: 4px; cursor: pointer;">キャンセル</button>' +
                '<button id="confirm-folder-selection" style="padding: 8px 16px; background: #2563eb; color: white; border: none; border-radius: 4px; cursor: pointer;">✅ 決定</button>' +
            '</div>';
    
        overlay.appendChild(modal);
        document.body.appendChild(overlay);
        
        // イベントリスナー
        document.getElementById('close-folder-browser').onclick = closeFolderBrowser;
        document.getElementById('cancel-folder-selection').onclick = closeFolderBrowser;
        overlay.onclick = (e) => { if (e.target === overlay) closeFolderBrowser(); };
        
        document.getElementById('confirm-folder-selection').onclick = () => {
            if (window.currentFolderPath) {
                selectFolder(window.currentFolderPath);
            } else {
                closeFolderBrowser();
            }
        };
        
        // 初期フォルダをロード
        loadFolders('ignored/input_files');
    };
    
    // フォルダブラウザ関連関数を定義
    window.loadFolders = async function(path) {
        try {
            const base = '/workspace/';
            const fullPath = path && path.startsWith('/') ? path : (base + (path || ''));
            const response = await fetch('/api/list-folders?path=' + encodeURIComponent(fullPath));
            
            if (!response.ok) {
                throw new Error('HTTP ' + response.status);
            }
            
            const api = await response.json();
            const data = api.data || {};
            if (api.status && api.status !== 'success') {
                throw new Error(api.message || 'フォルダ情報の取得に失敗しました');
            }
            
            // パンくずリストを更新
            const breadcrumbs = document.getElementById('folder-breadcrumbs');
            breadcrumbs.textContent = data.current_path || fullPath;
            
            // フォルダリストを更新
            const folderList = document.getElementById('folder-list');
            folderList.innerHTML = '';
            
            // 現在のパスを保存
            window.currentFolderPath = (data.current_path || fullPath).replace(/^\/workspace\//, '');
            
            // 上に戻るリンク
            if (data.parent) {
                const upItem = document.createElement('li');
                upItem.innerHTML = '🔙 上へ';
                upItem.style.cssText = 
                    'padding: 12px;' +
                    'border-bottom: 1px solid #f3f4f6;' +
                    'cursor: pointer;' +
                    'font-weight: 500;' +
                    'color: #2563eb;';
                upItem.onclick = () => {
                    const parentPath = data.parent.replace(/^\/workspace\//, '');
                    loadFolders(parentPath);
                };
                upItem.onmouseover = () => upItem.style.background = '#f3f4f6';
                upItem.onmouseout = () => upItem.style.background = 'white';
                folderList.appendChild(upItem);
            }
            
            // フォルダ一覧
            (data.folders || []).forEach(folderObj => {
                const folderName = folderObj.name || folderObj;
                const item = document.createElement('li');
                item.innerHTML = '📁 ' + folderName;
                item.style.cssText = 
                    'padding: 12px;' +
                    'border-bottom: 1px solid #f3f4f6;' +
                    'cursor: pointer;' +
                    'font-size: 14px;';
                item.onclick = () => {
                    const current = (data.current_path || fullPath).replace(/^\/workspace\//, '');
                    const newPath = current ? current + '/' + folderName : folderName;
                    loadFolders(newPath);
                };
                item.ondblclick = () => {
                    const current = (data.current_path || fullPath).replace(/^\/workspace\//, '');
                    const newPath = current ? current + '/' + folderName : folderName;
                    selectFolder(newPath);
                };
                item.onmouseover = () => item.style.background = '#f3f4f6';
                item.onmouseout = () => item.style.background = 'white';
                folderList.appendChild(item);
            });
            
        } catch (error) {
            console.error('フォルダ読み込みエラー:', error);
            const folderList = document.getElementById('folder-list');
            folderList.innerHTML = '<li style="padding: 12px; color: #dc2626; text-align: center;">❌ ' + error.message + '</li>';
        }
    };

    window.selectFolder = function(path) {
        const fullPath = '/workspace/' + path;
        
        // フォルダパス入力要素に直接設定
        if (window.folderPathUpdateId) {
            const folderPathInput = document.getElementById(window.folderPathUpdateId);
            if (folderPathInput) {
                folderPathInput.value = fullPath;
                // inputイベントとchangeイベントの両方を発火
                folderPathInput.dispatchEvent(new Event('input', { bubbles: true }));
                folderPathInput.dispatchEvent(new Event('change', { bubbles: true }));
            }
        }
        
        closeFolderBrowser();
    };

    window.closeFolderBrowser = function() {
        const overlay = document.getElementById('folder-browser-overlay');
        if (overlay) {
            overlay.remove();
        }
    };
})();

// ドラッグ&ドロップ/ファイル選択の設定（後からDOMが生成される場合にも確実にバインド）
(function initUploadHandlers(){
    const preventDefaults = () => {
        // ブラウザのデフォルトDnD挙動を全体で抑止（PDFが新規タブで開くのを防ぐ）
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            window.addEventListener(eventName, (e) => {
                e.preventDefault();
                e.stopPropagation();
            }, { passive: false });
        });
    };

    const attach = () => {
        const uploadBox = document.getElementById('upload-box');
        const fileInput = document.getElementById('file-input');
        if (!uploadBox || !fileInput) return false;

        preventDefaults();

        // DnD
        uploadBox.addEventListener('dragover', (e) => {
            e.preventDefault();
            e.stopPropagation();
            uploadBox.style.borderColor = '#3b82f6';
            uploadBox.style.backgroundColor = '#eff6ff';
        });
        uploadBox.addEventListener('dragleave', (e) => {
            e.preventDefault();
            e.stopPropagation();
            uploadBox.style.borderColor = '#d1d5db';
            uploadBox.style.backgroundColor = '#f9fafb';
        });
        uploadBox.addEventListener('drop', (e) => {
            e.preventDefault();
            e.stopPropagation();
            uploadBox.style.borderColor = '#d1d5db';
            uploadBox.style.backgroundColor = '#f9fafb';
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                window.handleFiles(files);
            }
        });

        // ファイル選択
        fileInput.addEventListener('change', (e) => {
            const files = Array.from(e.target.files || []);
            if (files.length === 0) return;

            if (e.target.dataset.isFolderSelect === 'true') {
                console.log('フォルダ選択:', files.length + '個のファイル');
                if (files[0] && files[0].webkitRelativePath) {
                    // フォルダ名だけでなく、仮想的なフルパスを表示
                    const folderName = files[0].webkitRelativePath.split('/')[0];
                    const folderPath = `/workspace/ignored/input_files/${folderName}`; // 仮想パス
                    console.log('フォルダパス設定:', folderPath);
                    if (window.folderPathUpdateId) {
                        const folderPathInput = document.getElementById(window.folderPathUpdateId);
                        console.log('フォルダパス入力要素:', folderPathInput);
                        if (folderPathInput) {
                            // NiceGUIのinput要素は直接値を設定してchangeイベントを発火
                            folderPathInput.value = folderPath;
                            // inputイベントとchangeイベントの両方を発火
                            folderPathInput.dispatchEvent(new Event('input', { bubbles: true }));
                            folderPathInput.dispatchEvent(new Event('change', { bubbles: true }));
                        }
                    } else {
                        console.warn('folderPathUpdateIdが未設定');
                    }
                }
                window.selectedFolderFiles = files;
                // フォルダ選択後のメッセージ表示は不要（テキストボックスへの反映のみ）
                e.target.removeAttribute('webkitdirectory');
                e.target.removeAttribute('directory');
                delete e.target.dataset.isFolderSelect;
            } else {
                console.log('ファイル選択:', files.length + '個のファイル');
                // 選択完了後に即アップロード
                window.selectedFiles = files; // フォールバック用途に保持
                window.uploadFiles(files);
                // 再選択可能にする
                e.target.value = '';
                e.target.removeAttribute('webkitdirectory');
                e.target.removeAttribute('directory');
                delete e.target.dataset.isFolderSelect;
            }
        });

        // クリックでファイル選択
        uploadBox.addEventListener('click', () => fileInput.click());

        console.log('[upload] ハンドラをバインドしました');
        window.uploadHandlersAttached = true;
        return true;
    };

    if (!attach()) {
        // 後からDOMが来る場合に備えて監視＋ポーリング
        const observer = new MutationObserver(() => {
            if (!window.uploadHandlersAttached) {
                attach();
            } else {
                observer.disconnect();
            }
        });
        observer.observe(document.body, { childList: true, subtree: true });
        let tries = 0;
        const iv = setInterval(() => {
            if (window.uploadHandlersAttached) { clearInterval(iv); return; }
            if (attach()) { clearInterval(iv); return; }
            if (++tries > 50) { clearInterval(iv); }
        }, 100);
    }
})();

// ファイル処理（グローバル公開）
window.handleFiles = function(files) {
    if (files.length === 0) return;
    
    // ファイルサイズチェック（100MB制限）
    const maxSize = 100 * 1024 * 1024; // 100MB
    const validFiles = Array.from(files).filter(file => {
        if (file.size > maxSize) {
            // NiceGUIのnotify機能を使用
            window.pywebview && window.pywebview.api ? 
                window.pywebview.api.notify(`ファイルサイズが大きすぎます: ${file.name}`, 'error') :
                console.warn(`ファイルサイズが大きすぎます: ${file.name}`);
            return false;
        }
        return true;
    });
    
    if (validFiles.length === 0) return;
    
    window.uploadFiles(validFiles);
}

// ファイルアップロード（app/系API対応）
window.uploadFiles = async function(files) {
    const progressContainer = document.getElementById('upload-progress');
    const progressFill = document.getElementById('progress-fill');
    const progressText = document.getElementById('progress-text');
    const progressCurrent = document.getElementById('progress-current');
    const progressTotal = document.getElementById('progress-total');
    const progressDetails = document.getElementById('progress-details');
    const resultsContainer = document.getElementById('upload-results');
    const waitingContainer = document.getElementById('upload-waiting');
    
    // プログレスバーを表示（要素が存在する場合のみ）
    if (progressContainer) {
        progressContainer.style.display = 'block';
    }
    if (waitingContainer) {
        waitingContainer.style.display = 'none';
    }
    if (progressTotal) {
        progressTotal.textContent = files.length;
    }
    if (progressCurrent) {
        progressCurrent.textContent = '0';
    }
    
    // 全ファイルを一度に送信するためのFormDataを作成
    const formData = new FormData();
    for (let i = 0; i < files.length; i++) {
        formData.append('files', files[i]);
    }
    
    let results = [];
    
    try {
        // プログレス更新 - アップロード段階
        if (progressFill) {
            progressFill.style.width = '50%';
        }
        if (progressText) {
            progressText.textContent = '50%';
        }
        if (progressCurrent) {
            progressCurrent.textContent = files.length;
        }
        if (progressDetails) {
            progressDetails.innerHTML = `
                <p>📤 ファイルをアップロード中...</p>
                <p style="color: #6b7280; font-size: 12px;">📄 OCR処理は後で実行されます</p>
                <p style="color: #6b7280; font-size: 12px;">🧠 ベクトル化は後で実行されます</p>
            `;
        }
        
        const response = await fetch('/api/upload/batch', {
            method: 'POST',
            body: formData
        });
        
        if (response.ok) {
            const result = await response.json();
            
            // プログレス100%表示
            progressFill.style.width = '100%';
            progressText.textContent = '100%';
            progressDetails.innerHTML = `
                <p>✅ アップロード完了！</p>
                <p style="color: #6b7280; font-size: 12px;">📄 OCR処理と🧠ベクトル化はバックグラウンドで続行されます</p>
            `;
            
            // app/系APIのレスポンス形式に対応
            results = result.results || [];
            // セッションIDが返ってきたら、Python側へ通知
            if (result.session_id) {
                window.latestUploadSessionId = result.session_id;
                console.log('[upload] session_id:', result.session_id);
            }
            
        } else {
            const error = await response.json();
            // エラーの場合、全ファイルを失敗として扱う
            for (let i = 0; i < files.length; i++) {
                results.push({
                    file_name: files[i].name,
                    status: 'error',
                    message: error.detail || 'アップロードに失敗しました'
                });
            }
        }
    } catch (error) {
        console.error('Error uploading files:', error);
        // エラーの場合、全ファイルを失敗として扱う
        for (let i = 0; i < files.length; i++) {
            results.push({
                file_name: files[i].name,
                status: 'error',
                message: 'ネットワークエラーが発生しました'
            });
        }
    }
    
    // 少し待機してから結果を表示
            setTimeout(() => {
        window.displayResults(results);
        if (progressContainer) {
            progressContainer.style.display = 'none';
        }
        if (waitingContainer) {
            waitingContainer.style.display = 'none';
        }
        
        // 結果があることを示すフラグを設定
        window.hasUploadResults = true;
    }, 1500);
}

// 結果を表示（グローバル変数に保存）
window.displayResults = function(results) {
    console.log('displayResults called with:', results);
    
    // 配列でない場合のエラーハンドリング
    if (!Array.isArray(results)) {
        console.error('displayResults: results is not an array', results);
        // オブジェクトの場合、resultsプロパティを確認
        if (results && results.results && Array.isArray(results.results)) {
            results = results.results;
            console.log('Using results.results array:', results);
        } else {
            console.error('Cannot find array data in results');
            return;
        }
    }
    
    // グローバル変数に結果を保存（Python側から取得可能）
    window.uploadResults = results;
    
    // 直接UIを更新（待機メッセージを隠してテーブルを表示）
    const waitingDiv = document.getElementById('upload-waiting');
    if (waitingDiv) {
        waitingDiv.style.display = 'none';
    }
    
    // 最もシンプルな方法：グローバル変数に保存して、Python側で取得
    window.latestUploadResults = results;
    console.log('[DEBUG] Results saved to window.latestUploadResults');
}

// ファイルサイズのフォーマット
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// サーバーフォルダアップロード（new/系移植版）
window.uploadServerFolder = async function(folderPath, includeSubfolders) {
    const progressContainer = document.getElementById('upload-progress');
    const progressFill = document.getElementById('progress-fill');
    const progressText = document.getElementById('progress-text');
    const progressCurrent = document.getElementById('progress-current');
    const progressTotal = document.getElementById('progress-total');
    const progressDetails = document.getElementById('progress-details');
    const waitingDiv = document.getElementById('upload-waiting');
    
    // UI状態変更
    if (waitingDiv) waitingDiv.style.display = 'none';
    if (progressContainer) progressContainer.style.display = 'block';
    
    // プログレス初期化
    if (progressTotal) progressTotal.textContent = '?';
    if (progressCurrent) progressCurrent.textContent = '0';
    if (progressFill) progressFill.style.width = '30%';
    if (progressText) progressText.textContent = '30%';
    if (progressDetails) {
        progressDetails.innerHTML = 
            '<p>📂 サーバーフォルダをスキャン中...</p>' +
            '<p class="text-muted">対応ファイルを検索しています</p>';
    }
    
    try {
        const formData = new FormData();
        formData.append('folder_path', folderPath);
        formData.append('include_subfolders', includeSubfolders);
        
        const response = await fetch('/api/upload/folder', {
            method: 'POST',
            body: formData
        });
        
        if (response.ok) {
            const result = await response.json();
            console.log('サーバーフォルダアップロード結果:', result);
            
            // プログレス更新 - 完了
            if (progressFill) progressFill.style.width = '100%';
            if (progressText) progressText.textContent = '100%';
            if (progressDetails) {
                progressDetails.innerHTML = 
                    '<p>✅ フォルダアップロード完了</p>' +
                    '<p class="text-muted">結果を表示しています</p>';
            }
            
            // 少し待ってから結果表示
            setTimeout(() => {
                if (progressContainer) progressContainer.style.display = 'none';
                
                // サーバーフォルダアップロードのレスポンス形式に対応
                const resultsData = result.results || result;
                console.log('displayResults に渡すデータ:', resultsData);
                console.log('resultsData is Array:', Array.isArray(resultsData));
                window.displayResults(resultsData);
                // 結果があることを示すフラグを設定
                window.hasUploadResults = true;
            }, 1000);
            
        } else {
            throw new Error('サーバーエラー: ' + response.status);
        }
        
    } catch (error) {
        console.error('サーバーフォルダアップロードエラー:', error);
        
        // エラー表示
        if (progressContainer) progressContainer.style.display = 'none';
        
        alert('フォルダアップロードに失敗しました: ' + (error.message || '不明なエラー'));
    }
}