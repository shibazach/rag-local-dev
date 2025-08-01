// new/static/js/ocr_comparison.js
// OCR比較検証ページのメイン機能

class OCRComparisonManager {
    constructor() {
        this.selectedFileId = null;
        this.selectedFileInfo = null;
        this.availableEngines = [];
        this.selectedEngines = new Set();
        this.isProcessing = false;
        this.fileSelector = null;
    }

    async initialize() {
        console.log('OCR比較検証ページ初期化開始');
        
        // ファイル選択機能初期化（データ登録から流用）
        await this.initializeFileSelector();
        
        // OCRエンジン一覧読み込み
        await this.loadAvailableEngines();
        
        // イベントリスナー設定
        this.setupEventListeners();
        
        // ドラッグ可能境界線初期化
        this.initializeResizablePanels();
        
        console.log('OCR比較検証ページ初期化完了');
    }

    async initializeFileSelector() {
        try {
            // FileSelectionManagerを拡張してn=1選択に対応
            class OCRFileSelector extends FileSelectionManager {
                constructor() {
                    super();
                    this.maxSelection = 1; // 単一ファイル選択制限
                }

                onFileSelected(fileId) {
                    // 親クラスの選択状態更新
                    this.selectedFiles.clear();
                    this.selectedFiles.add(fileId);
                    
                    // OCR比較ページ用の処理
                    window.ocrManager.onFileSelected(fileId);
                    this.updateSelectionDisplay();
                }

                updateSelectionDisplay() {
                    const count = this.selectedFiles.size;
                    const countElement = document.getElementById('file-count');
                    if (countElement) {
                        countElement.textContent = count;
                    }
                }
            }

            this.fileSelector = new OCRFileSelector();
            await this.fileSelector.initialize();
            
            console.log('ファイル選択機能初期化完了');
        } catch (error) {
            console.error('ファイル選択機能初期化エラー:', error);
        }
    }

    async loadAvailableEngines() {
        try {
            console.log('OCRエンジン一覧読み込み開始');
            
            const response = await fetch('/api/ocr-comparison/engines', {
                headers: {
                    'Authorization': `Bearer ${Auth.getAuthToken()}`
                },
                credentials: 'include'
            });

            if (response.ok) {
                const data = await response.json();
                this.availableEngines = data.engines || [];
                this.displayEngineSelection();
                console.log(`OCRエンジン ${this.availableEngines.length} 個読み込み完了`);
            } else {
                throw new Error(`API Error: ${response.status}`);
            }
        } catch (error) {
            console.error('OCRエンジン読み込みエラー:', error);
            this.showError('OCRエンジン一覧の読み込みに失敗しました');
        }
    }

    displayEngineSelection() {
        const container = document.getElementById('engine-selection');
        if (!container) return;

        if (this.availableEngines.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <span>利用可能なOCRエンジンがありません</span>
                </div>
            `;
            return;
        }

        const engineOptionsHtml = this.availableEngines.map(engine => `
            <div class="engine-option">
                <input type="checkbox" 
                       id="engine-${engine.id}" 
                       value="${engine.name}"
                       ${engine.available ? '' : 'disabled'}>
                <label for="engine-${engine.id}" class="engine-name">${engine.name}</label>
                <span class="engine-status ${engine.available ? 'status-available' : 'status-unavailable'}">
                    ${engine.available ? '利用可能' : '利用不可'}
                </span>
            </div>
        `).join('');

        container.innerHTML = engineOptionsHtml;

        // エンジン選択チェックボックスのイベントリスナー
        container.querySelectorAll('input[type="checkbox"]').forEach(checkbox => {
            checkbox.addEventListener('change', (e) => {
                if (e.target.checked) {
                    this.selectedEngines.add(e.target.value);
                } else {
                    this.selectedEngines.delete(e.target.value);
                }
                this.updateStartButtonState();
            });
        });
    }

    setupEventListeners() {
        // 実行ボタン
        const startBtn = document.getElementById('start-comparison');
        if (startBtn) {
            startBtn.addEventListener('click', () => this.startComparison());
        }

        // キャンセルボタン
        const cancelBtn = document.getElementById('cancel-comparison');
        if (cancelBtn) {
            cancelBtn.addEventListener('click', () => this.cancelComparison());
        }

        // 結果クリアボタン
        const clearBtn = document.getElementById('clear-results');
        if (clearBtn) {
            clearBtn.addEventListener('click', () => this.clearResults());
        }

        // ヘルプボタン
        const helpBtn = document.getElementById('help-btn');
        if (helpBtn) {
            helpBtn.addEventListener('click', () => this.showHelp());
        }

        // エクスポートボタン
        const exportBtn = document.getElementById('export-results');
        if (exportBtn) {
            exportBtn.addEventListener('click', () => this.exportResults());
        }
    }

    onFileSelected(fileId) {
        console.log('ファイル選択:', fileId);
        this.selectedFileId = fileId;
        this.loadFileInfo(fileId);
        this.updateStartButtonState();
    }

    async loadFileInfo(fileId) {
        try {
            const response = await fetch(`/api/ocr-comparison/file/${fileId}/info`, {
                headers: {
                    'Authorization': `Bearer ${Auth.getAuthToken()}`
                },
                credentials: 'include'
            });

            if (response.ok) {
                this.selectedFileInfo = await response.json();
                this.displaySelectedFileInfo();
            } else {
                throw new Error(`ファイル情報取得エラー: ${response.status}`);
            }
        } catch (error) {
            console.error('ファイル情報取得エラー:', error);
            this.showError('ファイル情報の取得に失敗しました');
        }
    }

    displaySelectedFileInfo() {
        const infoPanel = document.getElementById('selected-file-info');
        if (!infoPanel || !this.selectedFileInfo) return;

        // ファイル情報表示
        document.getElementById('selected-file-name').textContent = this.selectedFileInfo.file_name;
        document.getElementById('selected-file-size').textContent = this.formatFileSize(this.selectedFileInfo.size);
        document.getElementById('selected-file-pages').textContent = this.selectedFileInfo.page_count || '-';
        document.getElementById('selected-file-type').textContent = this.selectedFileInfo.mime_type;

        infoPanel.style.display = 'block';
    }

    formatFileSize(bytes) {
        if (bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    updateStartButtonState() {
        const startBtn = document.getElementById('start-comparison');
        if (!startBtn) return;

        const canStart = this.selectedFileId && 
                        this.selectedEngines.size > 0 && 
                        !this.isProcessing;

        startBtn.disabled = !canStart;
    }

    async startComparison() {
        if (!this.selectedFileId || this.selectedEngines.size === 0) {
            this.showError('ファイルとOCRエンジンを選択してください');
            return;
        }

        try {
            this.isProcessing = true;
            this.updateProcessingState(true);

            // パラメータ取得
            const pageNum = parseInt(document.getElementById('page-number').value) || 1;
            const useCorrection = document.getElementById('use-correction').checked;
            const enginesList = Array.from(this.selectedEngines).join(',');

            console.log('OCR比較処理開始:', {
                fileId: this.selectedFileId,
                engines: enginesList,
                pageNum,
                useCorrection
            });

            // API呼び出し
            const formData = new FormData();
            formData.append('file_id', this.selectedFileId);
            formData.append('engines', enginesList);
            formData.append('page_num', pageNum);
            formData.append('use_correction', useCorrection);

            const response = await fetch('/api/ocr-comparison/process', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${Auth.getAuthToken()}`
                },
                credentials: 'include',
                body: formData
            });

            if (response.ok) {
                const result = await response.json();
                this.displayComparisonResults(result);
                console.log('OCR比較処理完了');
            } else {
                const errorData = await response.json();
                throw new Error(errorData.detail || `API Error: ${response.status}`);
            }

        } catch (error) {
            console.error('OCR比較処理エラー:', error);
            this.showError(`OCR比較処理でエラーが発生しました: ${error.message}`);
        } finally {
            this.isProcessing = false;
            this.updateProcessingState(false);
        }
    }

    updateProcessingState(isProcessing) {
        const statusPanel = document.getElementById('processing-status');
        const overlay = document.getElementById('processing-overlay');
        const startBtn = document.getElementById('start-comparison');
        const cancelBtn = document.getElementById('cancel-comparison');

        if (isProcessing) {
            statusPanel.style.display = 'flex';
            overlay.style.display = 'flex';
            startBtn.disabled = true;
            cancelBtn.disabled = false;
        } else {
            statusPanel.style.display = 'none';
            overlay.style.display = 'none';
            cancelBtn.disabled = true;
            this.updateStartButtonState();
        }
    }

    cancelComparison() {
        console.log('OCR比較処理キャンセル要求');
        this.isProcessing = false;
        this.updateProcessingState(false);
        // 実際のAPI呼び出しキャンセル処理は今後実装
    }

    displayComparisonResults(data) {
        const container = document.getElementById('results-container');
        if (!container) return;

        const { file_info, processing_info, results, comparison } = data;

        // 結果表示HTML生成
        const resultsHtml = this.generateResultsHtml(results, comparison, processing_info);
        container.innerHTML = resultsHtml;

        // エクスポート・クリアボタンを有効化
        document.getElementById('export-results').disabled = false;
        document.getElementById('clear-results').disabled = false;

        console.log('比較結果表示完了');
    }

    generateResultsHtml(results, comparison, processingInfo) {
        const engineResults = Object.entries(results).map(([engineName, result]) => {
            const statusClass = result.success ? 'success' : 'error';
            const statusText = result.success ? '成功' : 'エラー';
            
            return `
                <div class="engine-result ${statusClass}">
                    <div class="result-header">
                        <div class="engine-title">${engineName}</div>
                        <div class="result-status ${statusClass}">${statusText}</div>
                    </div>
                    ${result.success ? `
                        <div class="result-stats">
                            <div class="stat-item">
                                処理時間: <span class="stat-value">${result.processing_time}秒</span>
                            </div>
                            <div class="stat-item">
                                信頼度: <span class="stat-value">${(result.confidence * 100).toFixed(1)}%</span>
                            </div>
                            <div class="stat-item">
                                文字数: <span class="stat-value">${result.text.length}</span>
                            </div>
                            ${result.correction_count ? `
                                <div class="stat-item">
                                    修正箇所: <span class="stat-value">${result.correction_count}</span>
                                </div>
                            ` : ''}
                        </div>
                        <div class="result-text ${result.corrections ? 'has-corrections' : ''}">
                            ${result.html_text || this.escapeHtml(result.text)}
                        </div>
                    ` : `
                        <div class="result-error">
                            <p>エラー: ${result.error}</p>
                        </div>
                    `}
                </div>
            `;
        }).join('');

        const summaryHtml = this.generateSummaryHtml(comparison, processingInfo);

        return `
            <div class="comparison-results">
                ${engineResults}
            </div>
            ${summaryHtml}
        `;
    }

    generateSummaryHtml(comparison, processingInfo) {
        if (!comparison || comparison.successful_engines === 0) {
            return `
                <div class="comparison-summary">
                    <h3 class="summary-title">⚠️ 比較結果サマリー</h3>
                    <p>すべてのエンジンで処理に失敗しました。</p>
                </div>
            `;
        }

        return `
            <div class="comparison-summary">
                <h3 class="summary-title">📊 比較結果サマリー</h3>
                <div class="summary-stats">
                    <div class="summary-stat">
                        <span class="stat-label">処理エンジン数</span>
                        <span class="stat-value">${comparison.successful_engines}/${comparison.total_engines}</span>
                    </div>
                    ${comparison.fastest_engine ? `
                        <div class="summary-stat">
                            <span class="stat-label">最速エンジン</span>
                            <span class="stat-value">${comparison.fastest_engine.name}</span>
                        </div>
                    ` : ''}
                    ${comparison.highest_confidence_engine ? `
                        <div class="summary-stat">
                            <span class="stat-label">最高信頼度</span>
                            <span class="stat-value">${comparison.highest_confidence_engine.name}</span>
                        </div>
                    ` : ''}
                    ${comparison.recommended_engine ? `
                        <div class="summary-stat">
                            <span class="stat-label">推奨エンジン</span>
                            <span class="stat-value">${comparison.recommended_engine.name}</span>
                        </div>
                    ` : ''}
                    <div class="summary-stat">
                        <span class="stat-label">総処理時間</span>
                        <span class="stat-value">${processingInfo.total_processing_time}秒</span>
                    </div>
                </div>
            </div>
        `;
    }

    clearResults() {
        const container = document.getElementById('results-container');
        if (container) {
            container.innerHTML = `
                <div class="empty-state">
                    <div class="empty-icon">📊</div>
                    <div class="empty-text">
                        <h4>OCR比較結果がここに表示されます</h4>
                        <p>ファイルを選択してOCRエンジンを指定し、「OCR比較実行」ボタンをクリックしてください。</p>
                    </div>
                </div>
            `;
        }

        // ボタンを無効化
        document.getElementById('export-results').disabled = true;
        document.getElementById('clear-results').disabled = true;

        console.log('比較結果をクリアしました');
    }

    exportResults() {
        // 結果エクスポート機能（今後実装）
        console.log('結果エクスポート機能は今後実装予定');
        this.showInfo('結果エクスポート機能は今後実装予定です');
    }

    showHelp() {
        const modal = document.getElementById('help-modal');
        if (modal) {
            modal.style.display = 'flex';
        }
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML.replace(/\n/g, '<br>');
    }

    showError(message) {
        if (window.Utils) {
            window.Utils.showNotification(message, 'error');
        } else {
            alert('エラー: ' + message);
        }
    }

    showInfo(message) {
        if (window.Utils) {
            window.Utils.showNotification(message, 'info');
        } else {
            alert('情報: ' + message);
        }
    }

    async loadFileList() {
        try {
            const response = await fetch('/api/files', {
                credentials: 'include'
            });
            
            if (response.ok) {
                const data = await response.json();
                this.displayFileList(data.files || []);
            } else {
                console.error('ファイル一覧の取得に失敗しました');
                this.showError('ファイル一覧の取得に失敗しました');
            }
        } catch (error) {
            console.error('ファイル一覧取得エラー:', error);
            this.showError(`ファイル一覧取得エラー: ${error.message}`);
        }
    }

    displayFileList(files) {
        const tbody = document.getElementById('file-dialog-list');
        tbody.innerHTML = '';
        
        // デフォルトで未処理に絞り込み
        const statusFilter = document.getElementById('status-filter').value || 'pending_processing';
        const filteredFiles = files.filter(file => 
            !statusFilter || file.status === statusFilter
        );
        
        if (filteredFiles.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="4" class="loading-state">
                        該当するファイルがありません
                    </td>
                </tr>
            `;
            return;
        }
        
        filteredFiles.forEach(file => {
            const row = document.createElement('tr');
            row.dataset.fileId = file.id;
            row.dataset.status = file.status;
            row.dataset.fileName = file.file_name;
            
            const pageCount = file.page_count || '-';
            const fileSize = this.formatFileSize(file.file_size || 0);
            const statusText = this.getStatusText(file.status);
            
            row.innerHTML = `
                <td class="file-name" title="${file.file_name}">${file.file_name}</td>
                <td>${pageCount}</td>
                <td>
                    <span class="status-badge status-${file.status}">
                        ${statusText}
                    </span>
                </td>
                <td>${fileSize}</td>
            `;
            
            tbody.appendChild(row);
            
            // 行クリックイベント
            row.addEventListener('click', () => {
                // 他の選択を解除
                document.querySelectorAll('.file-table tbody tr').forEach(tr => {
                    tr.classList.remove('selected');
                });
                row.classList.add('selected');
                
                // 選択ボタンを有効化
                document.getElementById('file-dialog-select').disabled = false;
                
                // 選択されたファイル情報を保存
                this.selectedFileId = file.id;
                this.selectedFileInfo = { id: file.id, file_name: file.file_name };
            });
            
            // ダブルクリックで選択完了
            row.addEventListener('dblclick', () => {
                this.selectFile(file.id, file.file_name);
            });
        });
        
        // フィルター処理の設定
        this.setupFileFilters();
    }

    formatFileSize(bytes) {
        if (bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    getStatusText(status) {
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

    setupFileFilters() {
        const statusFilter = document.getElementById('status-filter');
        const searchInput = document.getElementById('file-search');
        
        statusFilter.addEventListener('change', () => this.filterFiles());
        searchInput.addEventListener('input', () => this.filterFiles());
    }

    filterFiles() {
        const statusFilter = document.getElementById('status-filter').value;
        const searchTerm = document.getElementById('file-search').value.toLowerCase();
        const rows = document.querySelectorAll('.file-table tbody tr');
        
        rows.forEach(row => {
            if (!row.dataset.fileId) return; // Skip loading state row
            
            const status = row.dataset.status;
            const fileName = row.dataset.fileName.toLowerCase();
            
            const matchesStatus = !statusFilter || status === statusFilter;
            const matchesSearch = !searchTerm || fileName.includes(searchTerm);
            
            row.style.display = matchesStatus && matchesSearch ? '' : 'none';
        });
    }

    selectFile(fileId, fileName) {
        // 選択されたファイル情報を更新
        document.getElementById('selected-file-name').textContent = fileName;
        this.selectedFileId = fileId;
        this.selectedFileInfo = { id: fileId, file_name: fileName };
        
        // OCR実行ボタンを有効化
        document.getElementById('start-ocr-btn').disabled = false;
        
        // ダイアログを閉じる
        document.getElementById('file-dialog').style.display = 'none';
        
        console.log('[OCR] ファイル選択完了:', fileName);
    }

    initializeResizablePanels() {
        // 縦の境界線（左右分割）
        const verticalSplitter = document.querySelector('.vertical-splitter');
        if (verticalSplitter) {
            this.makeDraggable(verticalSplitter, 'vertical');
        }

        // 横の境界線（上下分割）
        const horizontalSplitterLeft = document.querySelector('.horizontal-splitter-left');
        const horizontalSplitterRight = document.querySelector('.horizontal-splitter-right');
        
        if (horizontalSplitterLeft) {
            this.makeDraggable(horizontalSplitterLeft, 'horizontal-left');
        }
        if (horizontalSplitterRight) {
            this.makeDraggable(horizontalSplitterRight, 'horizontal-right');
        }
    }

    makeDraggable(splitter, type) {
        let isResizing = false;
        let startX, startY;
        const mainContent = document.querySelector('.ocr-main-content');

        splitter.addEventListener('mousedown', (e) => {
            isResizing = true;
            startX = e.clientX;
            startY = e.clientY;
            document.body.style.cursor = type === 'vertical' ? 'col-resize' : 'row-resize';
            document.body.style.userSelect = 'none';
            
            // PDFプレビューのポインターイベントを無効化
            const pdfFrame = document.getElementById('pdf-preview');
            if (pdfFrame) {
                pdfFrame.style.pointerEvents = 'none';
            }
            
            e.preventDefault();
        });

        document.addEventListener('mousemove', (e) => {
            if (!isResizing) return;

            const rect = mainContent.getBoundingClientRect();
            
            if (type === 'vertical') {
                // 縦分割の処理
                const percentage = ((e.clientX - rect.left) / rect.width) * 100;
                const clampedPercentage = Math.min(Math.max(percentage, 20), 80); // 20%-80%の範囲
                
                mainContent.style.gridTemplateColumns = `${clampedPercentage}% 6px ${100 - clampedPercentage}%`;
            } else if (type === 'horizontal-left') {
                // 左側の横分割
                const percentage = ((e.clientY - rect.top) / rect.height) * 100;
                const clampedPercentage = Math.min(Math.max(percentage, 15), 70); // 15%-70%の範囲
                
                mainContent.style.gridTemplateRows = `${clampedPercentage}% 6px ${100 - clampedPercentage}%`;
            } else if (type === 'horizontal-right') {
                // 右側の横分割（Grid Template Rows調整）
                const percentage = ((e.clientY - rect.top) / rect.height) * 100;
                const clampedPercentage = Math.min(Math.max(percentage, 15), 70); // 15%-70%の範囲
                
                // 右側のグリッド行比率を調整
                const currentCols = mainContent.style.gridTemplateColumns || '1fr 6px 1fr';
                mainContent.style.gridTemplateColumns = currentCols;
                mainContent.style.gridTemplateRows = `${clampedPercentage}% 6px ${100 - clampedPercentage}%`;
            }
        });

        document.addEventListener('mouseup', () => {
            if (isResizing) {
                isResizing = false;
                document.body.style.cursor = '';
                document.body.style.userSelect = '';
                
                // PDFプレビューのポインターイベントを復元
                const pdfFrame = document.getElementById('pdf-preview');
                if (pdfFrame) {
                    pdfFrame.style.pointerEvents = '';
                }
            }
        });
    }
}

// ヘルプモーダルを閉じる関数
function closeHelpModal() {
    const modal = document.getElementById('help-modal');
    if (modal) {
        modal.style.display = 'none';
    }
}

// ページ読み込み時の初期化
document.addEventListener('DOMContentLoaded', async function() {
    console.log('OCR比較検証ページ読み込み開始');
    
    // グローバルにアクセス可能にする
    window.ocrManager = new OCRComparisonManager();
    
    try {
        await window.ocrManager.initialize();
    } catch (error) {
        console.error('OCR比較検証ページ初期化エラー:', error);
    }
});

// モーダル外クリックで閉じる
document.addEventListener('click', function(e) {
    const modal = document.getElementById('help-modal');
    if (modal && e.target === modal) {
        closeHelpModal();
    }
});