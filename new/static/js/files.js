// files.js - ファイル管理ページ専用JavaScript

// ページ読み込み時の初期化
document.addEventListener('DOMContentLoaded', function() {
    debugLog('ページ読み込み開始');
    console.log('[INIT] ページ読み込み開始');
    
    // DOM要素の存在確認
    const requiredElements = [
        'files-tbody',
        'no-files',
        'pdf-preview-content',
        'pdf-preview-frame',
        'text-preview-content'
    ];
    
    console.log('[INIT] DOM要素確認:');
    requiredElements.forEach(elementId => {
        const element = document.getElementById(elementId);
        const exists = !!element;
        console.log(`[INIT] ${elementId}: ${exists}`);
        if (!exists) {
            console.error(`[INIT] 警告: ${elementId} が見つかりません`);
        }
    });
    
    // ファイル一覧を読み込み
    loadFiles();
    
    // 権限チェック
    checkUserRole();
    
    // 検索とフィルターのイベントリスナー
    document.getElementById('search-input').addEventListener('input', filterFiles);
    document.getElementById('status-filter').addEventListener('change', filterFiles);
    
    // リサイズハンドルの初期化
    initResizeHandle();
});

// リサイズハンドルの初期化
function initResizeHandle() {
    const resizeHandle = document.getElementById('resize-handle');
    const leftPanel = document.querySelector('.files-left-panel');
    const rightPanel = document.querySelector('.files-right-panel');
    const layout = document.querySelector('.files-layout');
    
    if (!resizeHandle || !leftPanel || !rightPanel || !layout) {
        console.error('[RESIZE] リサイズハンドルの初期化に失敗: 必要な要素が見つかりません');
        return;
    }
    
    let isResizing = false;
    let startX = 0;
    let startLeftWidth = 0;
    
    resizeHandle.addEventListener('mousedown', function(e) {
        isResizing = true;
        startX = e.clientX;
        startLeftWidth = leftPanel.offsetWidth;
        
        // PDFプレビューのポインターイベントを無効化
        const pdfFrame = document.getElementById('pdf-preview-frame');
        if (pdfFrame) {
            pdfFrame.style.pointerEvents = 'none';
        }
        
        document.addEventListener('mousemove', handleMouseMove);
        document.addEventListener('mouseup', handleMouseUp);
        
        e.preventDefault();
    });
    
    function handleMouseMove(e) {
        if (!isResizing) return;
        
        const deltaX = e.clientX - startX;
        const newLeftWidth = startLeftWidth + deltaX;
        const layoutWidth = layout.offsetWidth;
        
        // 最小・最大幅の制限
        const minWidth = 200;
        const maxWidth = layoutWidth - 200;
        
        if (newLeftWidth >= minWidth && newLeftWidth <= maxWidth) {
            leftPanel.style.width = newLeftWidth + 'px';
            leftPanel.style.flex = 'none';
        }
    }
    
    function handleMouseUp() {
        isResizing = false;
        document.removeEventListener('mousemove', handleMouseMove);
        document.removeEventListener('mouseup', handleMouseUp);
        
        // PDFプレビューのポインターイベントを復活
        const pdfFrame = document.getElementById('pdf-preview-frame');
        if (pdfFrame) {
            pdfFrame.style.pointerEvents = 'auto';
        }
    }
}

// デバッグログ関数（共通ステータスバーを使用）
function debugLog(message) {
    if (typeof updateDebugStatus === 'function') {
        updateDebugStatus(message);
    }
    console.log(`[DEBUG] ${message}`);
}

// デバッグクリア（共通ステータスバーを使用）
function clearDebugLocal() {
    if (typeof window.clearDebug === 'function') {
        // 共通のclearDebug関数を呼び出し
        window.clearDebug();
    } else {
        debugLog('ログをクリアしました');
    }
}

// Utils関数のエイリアス（main.jsのUtilsを使用）
function showLoading() {
    if (window.Utils) {
        window.Utils.showLoading();
    }
}

function hideLoading() {
    if (window.Utils) {
        window.Utils.hideLoading();
    }
}

function showNotification(message, type = 'info') {
    if (window.Utils) {
        window.Utils.showNotification(message, type);
    }
}

// ファイル一覧を読み込み
async function loadFiles() {
    try {
        debugLog('ファイル一覧読み込み開始');
        showLoading();
        
        // 認証トークンを取得
        const token = Auth.getAuthToken();
        if (!token) {
            debugLog('認証トークンがありません');
            window.location.href = '/login';
            return;
        }
        
        debugLog('APIリクエスト送信中: /api/files');
        const response = await fetch('/api/files', {
            headers: {
                'Authorization': `Bearer ${token}`
            },
            credentials: 'include'  // セッション認証を使用
        });
        
        debugLog(`APIレスポンス受信: ${response.status} ${response.statusText}`);
        
        if (response.ok) {
            const data = await response.json();
            debugLog(`APIレスポンスデータ: ${JSON.stringify(data).substring(0, 200)}...`);
            debugLog(`APIレスポンスの型: ${typeof data}`);
            debugLog(`APIレスポンスのキー: ${Object.keys(data).join(', ')}`);
            
            // APIレスポンスの構造に合わせて修正
            const files = data.files || [];
            debugLog(`ファイル数: ${files.length}`);
            
            if (files.length > 0) {
                debugLog(`最初のファイル: ${JSON.stringify(files[0]).substring(0, 100)}...`);
            }
            
            displayFiles(files);
            debugLog('ファイル一覧表示完了');
        } else if (response.status === 401) {
            debugLog('認証エラー: 未ログインまたはトークン期限切れ');
            window.location.href = '/login';
        } else {
            const errorText = await response.text();
            debugLog(`APIエラー: ${response.status} - ${errorText}`);
            showNotification('ファイルの読み込みに失敗しました', 'error');
        }
    } catch (error) {
        debugLog(`例外発生: ${error.message}`);
        console.error('Error loading files:', error);
        if (error.name === 'TypeError' && error.message.includes('Auth')) {
            debugLog('認証モジュールエラー: ログインページへリダイレクト');
            window.location.href = '/login';
            return;
        }
        showNotification('ファイルの読み込みに失敗しました', 'error');
    } finally {
        hideLoading();
    }
}

// ファイル一覧を表示
function displayFiles(files) {
    try {
        debugLog(`displayFiles開始: ${files.length}個のファイル`);
        
        const tbody = document.getElementById('files-tbody');
        const noFiles = document.getElementById('no-files');
        
        if (!tbody) {
            debugLog('エラー: files-tbody要素が見つかりません');
            return;
        }
        
        if (!noFiles) {
            debugLog('エラー: no-files要素が見つかりません');
            return;
        }
        
        if (files.length === 0) {
            debugLog('ファイルが0個のため、空の表示を設定');
            tbody.innerHTML = '';
            noFiles.style.display = 'block';
            return;
        }
        
        debugLog('ファイル一覧のHTML生成開始');
        noFiles.style.display = 'none';
        
        const fileRows = [];
        for (let i = 0; i < files.length; i++) {
            const file = files[i];
            console.log(`[DEBUG] ファイル${i + 1}:`, file);
            debugLog(`ファイル${i + 1}: ${file.file_name} (${file.file_size} bytes) - ステータス: ${file.status}`);
            
            try {
                // ページ数情報を取得（PDFの場合）
                const pageCount = file.page_count || '-';
                const fileNumber = i + 1;
                const iconAvailability = getIconAvailability(file);
                const row = `
                    <tr data-filename="${file.file_name}" data-status="${file.status}" data-file-number="${fileNumber}">
                        <td>
                            <div class="file-info">
                                <span class="file-icon">📄</span>
                                <a href="#" onclick="previewFile('${file.id}', ${fileNumber})" class="file-name-link">No.${fileNumber.toString().padStart(5, '0')} / ${file.file_name}</a>
                            </div>
                        </td>
                        <td>${pageCount}</td>
                        <td>
                            <span class="status-badge status-${file.status}">
                                ${getStatusText(file.status)}
                            </span>
                        </td>
                        <td>
                            <div class="file-actions">
                                <button class="btn btn-sm" 
                                        onclick="viewFile('${file.id}')" 
                                        title="詳細表示">
                                    👁️
                                </button>
                                <button class="btn btn-sm ${!iconAvailability.rawTextPreview ? 'disabled' : ''}" 
                                        onclick="${iconAvailability.rawTextPreview ? 'previewRawText(\'' + file.id + '\', ' + fileNumber + ')' : 'return false'}" 
                                        title="${iconAvailability.rawTextPreview ? '生データプレビュー' : '生データがありません'}"
                                        ${!iconAvailability.rawTextPreview ? 'disabled' : ''}>
                                    📄
                                </button>
                                <button class="btn btn-sm ${!iconAvailability.refinedTextPreview ? 'disabled' : ''}" 
                                        onclick="${iconAvailability.refinedTextPreview ? 'previewRefinedText(\'' + file.id + '\', ' + fileNumber + ')' : 'return false'}" 
                                        title="${iconAvailability.refinedTextPreview ? '整形データプレビュー' : '整形データがありません'}"
                                        ${!iconAvailability.refinedTextPreview ? 'disabled' : ''}>
                                    ✨
                                </button>
                                <button class="btn btn-sm admin-only" onclick="deleteFile('${file.id}')" title="削除">
                                    🗑️
                                </button>
                            </div>
                        </td>
                    </tr>
                `;
                fileRows.push(row);
            } catch (error) {
                debugLog(`ファイル${i + 1}のHTML生成エラー: ${error.message}`);
            }
        }
        
        debugLog(`HTML生成完了: ${fileRows.length}個の行を生成`);
        tbody.innerHTML = fileRows.join('');
        debugLog('ファイル一覧表示完了');
        
    } catch (error) {
        debugLog(`displayFilesエラー: ${error.message}`);
        console.error('displayFiles error:', error);
    }
}

// ファイルを検索・フィルター
function filterFiles() {
    const searchTerm = document.getElementById('search-input').value.toLowerCase();
    const statusFilter = document.getElementById('status-filter').value;
    const rows = document.querySelectorAll('#files-tbody tr');
    
    rows.forEach(row => {
        const filenameElement = row.querySelector('.file-name-link');
        const filename = filenameElement ? filenameElement.textContent.toLowerCase() : '';
        const status = row.dataset.status;
        
        const matchesSearch = filename.includes(searchTerm);
        const matchesStatus = !statusFilter || status === statusFilter;
        
        row.style.display = matchesSearch && matchesStatus ? '' : 'none';
    });
}

// ファイルの詳細表示
async function viewFile(fileId) {
    try {
        debugLog(`ファイル詳細表示開始: ${fileId}`);
        if (window.Utils) {
            window.Utils.showLoading();
        }
        
        const response = await fetch(`/api/files/${fileId}`, {
            credentials: 'include'
        });
        
        debugLog(`APIレスポンス: ${response.status} ${response.statusText}`);
        
        if (response.ok) {
            const data = await response.json();
            debugLog(`ファイル詳細データ: ${JSON.stringify(data).substring(0, 200)}...`);
            const file = data.file || data;
            // 既存のモーダルを削除してから新規生成
            document.querySelectorAll('.modal').forEach(m => m.remove());
            showFileDetails(file);
        } else {
            const errorText = await response.text();
            debugLog(`APIエラー: ${response.status} - ${errorText}`);
            if (window.Utils) {
                window.Utils.showNotification('ファイルの詳細取得に失敗しました', 'error');
            }
        }
    } catch (error) {
        debugLog(`例外発生: ${error.message}`);
        console.error('Error viewing file:', error);
        if (window.Utils) {
            window.Utils.showNotification('ファイルの詳細取得に失敗しました', 'error');
        }
    } finally {
        if (window.Utils) {
            window.Utils.hideLoading();
        }
    }
}

// ファイル詳細モーダル生成
function showFileDetails(file) {
    // プロパティ名の互換性対応
    const fileName = file.file_name || file.filename || '-';
    const fileSizeBytes = file.file_size || file.size || 0;
    const fileSize = (typeof fileSizeBytes === 'number') ? formatFileSize(fileSizeBytes) : '-';
    const pageCount = file.page_count || '-';
    const createdAt = file.created_at || file.uploaded_at || null;
    // 既存のモーダルを削除
    document.querySelectorAll('.modal').forEach(m => m.remove());
    const modal = document.createElement('div');
    modal.className = 'modal';
    modal.innerHTML = `
        <div class="modal-content">
            <div class="modal-header">
                <h3>ファイル詳細</h3>
                <button class="close-btn" onclick="this.closest('.modal').remove()">&times;</button>
            </div>
            <div class="modal-body">
                <div class="file-detail">
                    <strong>ファイル名:</strong> ${fileName}
                </div>
                <div class="file-detail">
                    <strong>サイズ:</strong> ${fileSize}
                </div>
                <div class="file-detail">
                    <strong>ページ数:</strong> ${pageCount}
                </div>
                <div class="file-detail">
                    <strong>ステータス:</strong> 
                    <span class="status-badge status-${file.status}">
                        ${getStatusText(file.status)}
                    </span>
                </div>
                <div class="file-detail">
                    <strong>アップロード日時:</strong> ${formatDate(createdAt)}
                </div>
                ${file.text_content ? `
                <div class="file-detail">
                    <strong>テキスト内容:</strong>
                    <div class="text-content">
                        <pre>${file.text_content}</pre>
                    </div>
                </div>
                ` : ''}
            </div>
        </div>
    `;
    document.body.appendChild(modal);
}

// ファイルを削除
async function deleteFile(fileId) {
    if (!confirm('このファイルを削除しますか？')) {
        return;
    }
    
    try {
        debugLog(`ファイル削除開始: ${fileId}`);
        showLoading();
        
        const response = await fetch(`/api/files/${fileId}`, {
            method: 'DELETE',
            credentials: 'include'
        });
        
        debugLog(`削除APIレスポンス: ${response.status} ${response.statusText}`);
        
        if (response.ok) {
            debugLog('ファイル削除成功');
            showNotification('ファイルを削除しました', 'success');
            loadFiles(); // 一覧を再読み込み
        } else {
            const errorText = await response.text();
            debugLog(`削除APIエラー: ${response.status} - ${errorText}`);
            showNotification('ファイルの削除に失敗しました', 'error');
        }
    } catch (error) {
        debugLog(`削除例外発生: ${error.message}`);
        console.error('Error deleting file:', error);
        showNotification('ファイルの削除に失敗しました', 'error');
    } finally {
        hideLoading();
    }
}

// ファイルプレビュー
async function previewFile(fileId, previewType, fileNumber = null) {
    try {
        debugLog(`ファイルプレビュー開始: ${fileId}, タイプ: ${previewType}, 番号: ${fileNumber}`);
        console.log(`[PREVIEW] ファイルプレビュー開始: fileId=${fileId}, previewType=${previewType}, fileNumber=${fileNumber}`);
        
        const response = await fetch(`/api/files/${fileId}/preview`, {
            method: 'GET',
            credentials: 'include'
        });
        
        console.log(`[PREVIEW] APIレスポンス: status=${response.status}, ok=${response.ok}`);
        debugLog(`APIレスポンス: status=${response.status}, ok=${response.ok}`);
        
        if (response.ok) {
            const contentType = response.headers.get('content-type');
            console.log(`[PREVIEW] Content-Type: ${contentType}`);
            debugLog(`プレビューコンテンツタイプ: ${contentType}`);
            
            if (contentType && contentType.includes('application/pdf')) {
                // PDFファイルの場合
                console.log(`[PREVIEW] PDFプレビューを表示: fileId=${fileId}`);
                debugLog('PDFプレビューを表示');
                showPdfPreview(fileId, fileNumber);
            } else {
                // テキストまたはバイナリプレビューの場合
                const data = await response.json();
                console.log(`[PREVIEW] プレビューデータ:`, data);
                debugLog(`プレビューデータ受信: ${JSON.stringify(data).substring(0, 100)}...`);
                
                if (data.type === 'text') {
                    console.log(`[PREVIEW] テキストプレビューを表示`);
                    debugLog('テキストプレビューを表示');
                    showTextPreview(data.content, fileNumber);
                } else {
                    console.log(`[PREVIEW] バイナリプレビューを表示`);
                    debugLog('バイナリプレビューを表示');
                    showTextPreview(data.content, fileNumber);
                }
            }
        } else {
            const errorData = await response.json();
            const errorMessage = `HTTP ${response.status}: ${errorData.detail || 'Unknown error'}`;
            console.error(`[PREVIEW] プレビューエラー: ${errorMessage}`);
            console.error(`[PREVIEW] エラーレスポンス:`, errorData);
            debugLog(`プレビューエラー: ${response.status} - ${errorData.detail}`);
            showNotification(`プレビューエラー: ${errorMessage}`, 'error');
        }
    } catch (error) {
        const errorMessage = `${error.name}: ${error.message}`;
        console.error(`[PREVIEW] プレビュー例外エラー:`, error);
        console.error(`[PREVIEW] エラー詳細:`, {
            name: error.name,
            message: error.message,
            stack: error.stack
        });
        debugLog(`プレビューエラー: ${errorMessage}`);
        showNotification(`プレビューエラー: ${errorMessage}`, 'error');
    }
}

// PDFプレビューを表示
function showPdfPreview(fileId, fileNumber = null) {
    debugLog(`PDFプレビュー開始: ${fileId}, 番号: ${fileNumber}`);
    
    // プレースホルダーを非表示
    document.getElementById('preview-placeholder').style.display = 'none';
    document.getElementById('text-preview-content').style.display = 'none';
    
    // 右パネルから分割表示クラスを削除（全画面PDFプレビュー）
    const rightPanel = document.querySelector('.files-right-panel');
    rightPanel.classList.remove('split-view');
    
    // PDFプレビューコンテナを表示
    const pdfContent = document.getElementById('pdf-preview-content');
    const pdfFrame = document.getElementById('pdf-preview-frame');
    const pdfFallback = document.getElementById('pdf-fallback');
    
    pdfContent.style.display = 'block';
    pdfFallback.style.display = 'none';
    
    // ステータスバーにファイル情報を表示
    if (fileNumber) {
        const fileNameLink = document.querySelector(`tr[data-file-number="${fileNumber}"] .file-name-link`);
        const fullText = fileNameLink.textContent;
        const fileName = fullText.includes(' / ') ? fullText.split(' / ')[1] : fullText;
        updateStatusBar(`📄 No.${fileNumber.toString().padStart(5, '0')} ${fileName}`);
    }
    
    // iframeのsrcを設定
    const pdfUrl = `/api/files/${fileId}/preview`;
    pdfFrame.src = pdfUrl;
    
    // ダウンロードリンクも更新
    const downloadLink = document.getElementById('pdf-download-link');
    if (downloadLink) {
        downloadLink.href = pdfUrl;
        downloadLink.target = '_blank';
    }
    
    debugLog(`PDFプレビュー設定完了: ${pdfUrl}`);
}

// 上下分割表示：上段PDF、下段テキスト
function showSplitPreview(fileId, textContent, fileNumber = null) {
    debugLog(`上下分割プレビュー開始: ${fileId}, 番号: ${fileNumber}`);
    
    // プレースホルダーを非表示
    document.getElementById('preview-placeholder').style.display = 'none';
    
    // 右パネルに分割表示クラスを追加
    const rightPanel = document.querySelector('.files-right-panel');
    rightPanel.classList.add('split-view');
    
    // PDF部分（上段）を設定
    const pdfContent = document.getElementById('pdf-preview-content');
    const pdfFrame = document.getElementById('pdf-preview-frame');
    const pdfFallback = document.getElementById('pdf-fallback');
    
    pdfContent.style.display = 'block';
    pdfFallback.style.display = 'none';
    
    // テキスト部分（下段）を設定
    const textContainer = document.getElementById('text-preview-content');
    const textElement = document.getElementById('text-preview-text');
    
    textContainer.style.display = 'block';
    
    // ステータスバーにファイル情報を表示
    if (fileNumber) {
        const fileNameLink = document.querySelector(`tr[data-file-number="${fileNumber}"] .file-name-link`);
        const fullText = fileNameLink.textContent;
        const fileName = fullText.includes(' / ') ? fullText.split(' / ')[1] : fullText;
        updateStatusBar(`📄 No.${fileNumber.toString().padStart(5, '0')} ${fileName}`);
        
        // テキストファイル情報を下段に表示
        const textFileInfo = document.createElement('div');
        textFileInfo.className = 'text-file-info';
        textFileInfo.innerHTML = `<strong>No.${fileNumber.toString().padStart(5, '0')} ${fileName}</strong>`;
        textFileInfo.style.cssText = 'background: #f8f9fa; padding: 10px; margin-top: 15px; border-radius: 4px; border-left: 4px solid #007bff; font-size: 14px;';
        
        // 既存のテキストファイル情報を削除
        const existingTextInfo = textContainer.querySelector('.text-file-info');
        if (existingTextInfo) {
            existingTextInfo.remove();
        }
        
        textContainer.appendChild(textFileInfo);
    }
    
    // PDFのiframeのsrcを設定
    const pdfUrl = `/api/files/${fileId}/preview`;
    pdfFrame.src = pdfUrl;
    
    // テキスト内容を設定
    textElement.textContent = textContent;
    
    // ダウンロードリンクも更新
    const downloadLink = document.getElementById('pdf-download-link');
    if (downloadLink) {
        downloadLink.href = pdfUrl;
        downloadLink.target = '_blank';
    }
    
    debugLog(`上下分割プレビュー設定完了: ${pdfUrl}`);
}

// テキストプレビューを右ペインに表示
function showTextPreview(content, fileNumber = null) {
    const placeholder = document.getElementById('preview-placeholder');
    const textContent = document.getElementById('text-preview-content');
    const textElement = document.getElementById('text-preview-text');
    
    console.log(`[PREVIEW] テキストプレビュー表示, 番号: ${fileNumber}`);
    
    // プレビューを表示
    placeholder.style.display = 'none';
    textContent.style.display = 'block';
    
    // ファイル番号とファイル名を表示（下段に配置）
    if (fileNumber) {
        const fileName = document.querySelector(`tr[data-file-number="${fileNumber}"] .file-name-link`).textContent;
        const fileInfo = document.createElement('div');
        fileInfo.className = 'text-file-info';
        fileInfo.innerHTML = `<strong>${fileName}</strong>`;
        fileInfo.style.cssText = 'background: #f8f9fa; padding: 10px; margin-top: 15px; border-radius: 4px; border-left: 4px solid #007bff; font-size: 14px;';
        
        // 既存のファイル情報を削除
        const existingInfo = textContent.querySelector('.text-file-info');
        if (existingInfo) {
            existingInfo.remove();
        }
        
        // 下段に追加
        textContent.appendChild(fileInfo);
    }
    
    // テキスト内容を設定
    textElement.textContent = content;
    
    console.log(`[PREVIEW] テキストプレビュー表示完了`);
}

// 生データ（raw_text）を取得してプレビュー表示
async function previewRawText(fileId, fileNumber = null) {
    try {
        debugLog(`生データ取得開始: ${fileId}, 番号: ${fileNumber}`);
        console.log(`[RAW_TEXT_PREVIEW] 生データ取得開始: fileId=${fileId}, fileNumber=${fileNumber}`);
        
        const response = await fetch(`/api/files/${fileId}`, {
            credentials: 'include'
        });
        
        console.log(`[RAW_TEXT_PREVIEW] APIレスポンス: status=${response.status}, ok=${response.ok}`);
        
        if (response.ok) {
            const data = await response.json();
            const file = data.file || data;
            console.log(`[RAW_TEXT_PREVIEW] ファイルデータ:`, file);
            
            // 生データを取得
            const textContent = file.raw_text || '生データがありません';
            
            console.log(`[RAW_TEXT_PREVIEW] 生データ取得: ${textContent.length}文字`);
            debugLog(`生データ取得: ${textContent.length}文字`);
            
            // 上下分割プレビューを表示（上：PDF、下：テキスト）
            showSplitPreview(fileId, textContent, fileNumber);
            
        } else {
            const errorData = await response.json();
            const errorMessage = `HTTP ${response.status}: ${errorData.detail || 'Unknown error'}`;
            console.error(`[RAW_TEXT_PREVIEW] 生データ取得エラー: ${errorMessage}`);
            debugLog(`生データ取得エラー: ${response.status} - ${errorData.detail}`);
            showNotification(`生データ取得エラー: ${errorMessage}`, 'error');
        }
    } catch (error) {
        const errorMessage = `${error.name}: ${error.message}`;
        console.error(`[RAW_TEXT_PREVIEW] 生データ取得例外エラー:`, error);
        debugLog(`生データ取得エラー: ${errorMessage}`);
        showNotification(`生データ取得エラー: ${errorMessage}`, 'error');
    }
}

// 整形データ（refined_text）を取得してプレビュー表示
async function previewRefinedText(fileId, fileNumber = null) {
    try {
        debugLog(`整形データ取得開始: ${fileId}, 番号: ${fileNumber}`);
        console.log(`[REFINED_TEXT_PREVIEW] 整形データ取得開始: fileId=${fileId}, fileNumber=${fileNumber}`);
        
        const response = await fetch(`/api/files/${fileId}`, {
            credentials: 'include'
        });
        
        console.log(`[REFINED_TEXT_PREVIEW] APIレスポンス: status=${response.status}, ok=${response.ok}`);
        
        if (response.ok) {
            const data = await response.json();
            const file = data.file || data;
            console.log(`[REFINED_TEXT_PREVIEW] ファイルデータ:`, file);
            
            // 整形データを取得
            const textContent = file.refined_text || '整形データがありません';
            
            console.log(`[REFINED_TEXT_PREVIEW] 整形データ取得: ${textContent.length}文字`);
            debugLog(`整形データ取得: ${textContent.length}文字`);
            
            // 上下分割プレビューを表示（上：PDF、下：テキスト）
            showSplitPreview(fileId, textContent, fileNumber);
            
        } else {
            const errorData = await response.json();
            const errorMessage = `HTTP ${response.status}: ${errorData.detail || 'Unknown error'}`;
            console.error(`[REFINED_TEXT_PREVIEW] 整形データ取得エラー: ${errorMessage}`);
            debugLog(`整形データ取得エラー: ${response.status} - ${errorData.detail}`);
            showNotification(`整形データ取得エラー: ${errorMessage}`, 'error');
        }
    } catch (error) {
        const errorMessage = `${error.name}: ${error.message}`;
        console.error(`[REFINED_TEXT_PREVIEW] 整形データ取得例外エラー:`, error);
        debugLog(`整形データ取得エラー: ${errorMessage}`);
        showNotification(`整形データ取得エラー: ${errorMessage}`, 'error');
    }
}

// プレビューを閉じる
function closePreview() {
    const placeholder = document.getElementById('preview-placeholder');
    const pdfContent = document.getElementById('pdf-preview-content');
    const textContent = document.getElementById('text-preview-content');
    
    console.log(`[PREVIEW] プレビューを閉じる`);
    
    // 右パネルから分割表示クラスを削除
    const rightPanel = document.querySelector('.files-right-panel');
    rightPanel.classList.remove('split-view');
    
    // プレビューを非表示
    placeholder.style.display = 'block';
    pdfContent.style.display = 'none';
    textContent.style.display = 'none';
    
    // ステータスバーをクリア
    updateStatusBar('');
    
    console.log(`[PREVIEW] プレビューを閉じました`);
}

// ステータスバーにメッセージを表示
function updateStatusBar(message) {
    try {
        // ブラウザのステータスバーに表示
        window.status = message;
        
        // ブラウザタイトルにも反映（フォールバック）
        if (message) {
            document.title = message;
        } else {
            document.title = 'ファイル管理';
        }
        
        console.log(`[STATUS] ${message}`);
    } catch (error) {
        console.error('ステータスバー更新エラー:', error);
    }
}

// ユーザー権限をチェックしてUIを調整
async function checkUserRole() {
    try {
        // 一時的に全ユーザーに削除権限を付与
        // TODO: 後で適切な権限チェックAPIに変更
        document.querySelectorAll('.admin-only').forEach(element => {
            element.style.display = '';
        });
        debugLog('削除ボタンを表示（一時的にすべてのユーザー）');
        
        /* 元のコード - 適切なAPIが実装されたら復活
        const response = await fetch('/api/user/profile', {
            credentials: 'include'
        });
        
        if (response.ok) {
            const data = await response.json();
            const role = data.data.role;
            
            // admin権限の場合、削除ボタンを表示
            if (role === 'admin') {
                document.querySelectorAll('.admin-only').forEach(element => {
                    element.style.display = '';
                });
                debugLog('Admin権限確認: 削除ボタンを表示');
            } else {
                debugLog('User権限確認: 削除ボタンを非表示のまま');
            }
        } else {
            debugLog('権限確認失敗: 未認証状態');
        }
        */
    } catch (error) {
        debugLog(`権限確認エラー: ${error.message}`);
    }
}

// ステータステキストを取得
function getStatusText(status) {
    const statusMap = {
        'pending_processing': '未処理',
        'processing': '処理中',
        'text_extracted': '未整形',
        'text_refined': '未ベクトル化',
        'processed': '処理完了',
        'error': 'エラー'
    };
    return statusMap[status] || status;
}

// ステータスに基づいてアイコンの有効性を判定
function getIconAvailability(file) {
    // ファイル一覧では raw_text/refined_text が取得できないため、
    // ステータスに基づいて判定する
    const status = file.status;
    
    // ステータスベースでのデータ存在判定
    const hasRawText = status === 'text_extracted' || status === 'text_refined' || status === 'processed';
    const hasRefinedText = status === 'text_refined' || status === 'processed';
    
    return {
        pdfPreview: true, // PDFは常に表示可能
        rawTextPreview: hasRawText, // ステータスに基づく生データ有無
        refinedTextPreview: hasRefinedText, // ステータスに基づく整形データ有無
        delete: true // 削除は常に可能
    };
}

// ファイルサイズをフォーマット
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// 日付をフォーマット
function formatDate(dateString) {
    if (!dateString) return '-';
    
    const date = new Date(dateString);
    return date.toLocaleString('ja-JP', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
    });
} 