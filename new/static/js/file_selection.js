// new/static/js/file_selection.js
// ファイル選択・フィルタリング機能

class FileSelectionManager {
    constructor() {
        this.selectedFiles = new Set();
        this.allFiles = [];
        this.currentFilters = {
            status: null,
            search: '',
            extension: null,
            sizeRange: null
        };
        this.stats = null;
        this.availableFilters = null;
    }

    async initialize() {
        await this.loadStats();
        await this.loadAvailableFilters();
        this.setupEventListeners();
        this.updateUI();
    }

    async loadStats() {
        try {
            const response = await fetch('/api/file-selection/stats', {
                headers: {
                    'Authorization': `Bearer ${Auth.getAuthToken()}`
                },
                credentials: 'include'
            });

            if (response.ok) {
                this.stats = await response.json();
                this.updateStatsDisplay();
            } else {
                console.error('統計データ取得失敗:', response.status);
            }
        } catch (error) {
            console.error('統計データ取得エラー:', error);
        }
    }

    async loadAvailableFilters() {
        try {
            const response = await fetch('/api/file-selection/filters', {
                headers: {
                    'Authorization': `Bearer ${Auth.getAuthToken()}`
                },
                credentials: 'include'
            });

            if (response.ok) {
                this.availableFilters = await response.json();
                this.updateFilterOptions();
            } else {
                console.error('フィルター取得失敗:', response.status);
            }
        } catch (error) {
            console.error('フィルター取得エラー:', error);
        }
    }

    setupEventListeners() {
        // 全選択・全解除
        const selectAllBtn = document.getElementById('select-all-files');
        const deselectAllBtn = document.getElementById('deselect-all-files');
        
        if (selectAllBtn) {
            selectAllBtn.addEventListener('click', () => this.selectAllVisible());
        }
        
        if (deselectAllBtn) {
            deselectAllBtn.addEventListener('click', () => this.deselectAll());
        }

        // フィルター変更
        const statusFilter = document.getElementById('status-filter');
        const searchInput = document.getElementById('file-search');
        const extensionFilter = document.getElementById('extension-filter');

        if (statusFilter) {
            statusFilter.addEventListener('change', (e) => {
                this.currentFilters.status = e.target.value || null;
                this.applyFilters();
            });
        }

        if (searchInput) {
            let searchTimeout;
            searchInput.addEventListener('input', (e) => {
                clearTimeout(searchTimeout);
                searchTimeout = setTimeout(() => {
                    this.currentFilters.search = e.target.value;
                    this.applyFilters();
                }, 300);
            });
        }

        if (extensionFilter) {
            extensionFilter.addEventListener('change', (e) => {
                this.currentFilters.extension = e.target.value || null;
                this.applyFilters();
            });
        }

        // 処理時間推定
        document.addEventListener('selectionChanged', () => {
            this.estimateProcessingTime();
        });
    }

    selectFile(fileId) {
        this.selectedFiles.add(fileId);
        this.updateSelectionUI(fileId, true);
        this.updateSelectionCount();
        this.dispatchSelectionEvent();
    }

    deselectFile(fileId) {
        this.selectedFiles.delete(fileId);
        this.updateSelectionUI(fileId, false);
        this.updateSelectionCount();
        this.dispatchSelectionEvent();
    }

    toggleFile(fileId) {
        if (this.selectedFiles.has(fileId)) {
            this.deselectFile(fileId);
        } else {
            this.selectFile(fileId);
        }
    }

    selectAllVisible() {
        const visibleCheckboxes = document.querySelectorAll('.file-checkbox:not([style*="display: none"])');
        visibleCheckboxes.forEach(checkbox => {
            const fileId = checkbox.dataset.fileId;
            if (fileId) {
                this.selectFile(fileId);
                checkbox.checked = true;
            }
        });
    }

    deselectAll() {
        this.selectedFiles.clear();
        document.querySelectorAll('.file-checkbox').forEach(checkbox => {
            checkbox.checked = false;
        });
        this.updateSelectionCount();
        this.dispatchSelectionEvent();
    }

    updateSelectionUI(fileId, selected) {
        const checkbox = document.querySelector(`[data-file-id="${fileId}"]`);
        if (checkbox) {
            checkbox.checked = selected;
        }

        const row = checkbox?.closest('tr');
        if (row) {
            row.classList.toggle('selected', selected);
        }
    }

    updateSelectionCount() {
        const count = this.selectedFiles.size;
        const countElement = document.getElementById('selected-files');
        if (countElement) {
            countElement.textContent = count;
        }

        // ボタン状態更新
        const startBtn = document.getElementById('start-processing');
        if (startBtn) {
            startBtn.disabled = count === 0;
            startBtn.textContent = count > 0 ? `${count}件を処理開始` : '処理開始';
        }
    }

    updateStatsDisplay() {
        if (!this.stats) return;

        // 総ファイル数
        const totalElement = document.getElementById('total-files');
        if (totalElement) {
            totalElement.textContent = this.stats.total_files;
        }

        // ステータス別統計表示
        const statusContainer = document.getElementById('status-breakdown');
        if (statusContainer && this.stats.status_breakdown) {
            statusContainer.innerHTML = this.stats.status_breakdown.map(stat => `
                <div class="status-stat">
                    <span class="status-label ${stat.status}">${this.getStatusLabel(stat.status)}</span>
                    <span class="status-count">${stat.count}件</span>
                    <span class="status-percentage">(${stat.percentage}%)</span>
                </div>
            `).join('');
        }
    }

    updateFilterOptions() {
        if (!this.availableFilters) return;

        // ステータスフィルター
        const statusFilter = document.getElementById('status-filter');
        if (statusFilter && this.availableFilters.status_filters) {
            statusFilter.innerHTML = '<option value="">全ステータス</option>' +
                this.availableFilters.status_filters.map(filter => 
                    `<option value="${filter.value}">${this.getStatusLabel(filter.value)} (${filter.count})</option>`
                ).join('');
        }

        // 拡張子フィルター
        const extensionFilter = document.getElementById('extension-filter');
        if (extensionFilter && this.availableFilters.extension_filters) {
            extensionFilter.innerHTML = '<option value="">全拡張子</option>' +
                this.availableFilters.extension_filters.map(filter => 
                    `<option value="${filter.value}">*.${filter.value} (${filter.count})</option>`
                ).join('');
        }
    }

    async applyFilters() {
        // 既存のloadFileList関数を呼び出してフィルター適用
        if (window.loadFileList) {
            await window.loadFileList(this.currentFilters);
        }
    }

    async estimateProcessingTime() {
        if (this.selectedFiles.size === 0) {
            this.updateTimeEstimate(0, '00:00');
            return;
        }

        try {
            const response = await fetch('/api/file-selection/estimate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${Auth.getAuthToken()}`
                },
                credentials: 'include',
                body: JSON.stringify({
                    file_ids: Array.from(this.selectedFiles),
                    processing_options: this.getProcessingOptions()
                })
            });

            if (response.ok) {
                const estimate = await response.json();
                this.updateTimeEstimate(estimate.estimated_time_seconds, estimate.estimated_time_display);
                this.updateProcessingBreakdown(estimate.breakdown);
            }
        } catch (error) {
            console.error('処理時間推定エラー:', error);
        }
    }

    updateTimeEstimate(seconds, display) {
        const timeElement = document.getElementById('estimated-time');
        if (timeElement) {
            timeElement.textContent = display;
        }
    }

    updateProcessingBreakdown(breakdown) {
        const breakdownElement = document.getElementById('processing-breakdown');
        if (breakdownElement && breakdown) {
            breakdownElement.innerHTML = `
                <div class="breakdown-item">
                    <span>OCR処理:</span>
                    <span>${breakdown.ocr_time}秒</span>
                </div>
                <div class="breakdown-item">
                    <span>LLM整形:</span>
                    <span>${breakdown.llm_time}秒</span>
                </div>
                <div class="breakdown-item">
                    <span>ベクトル化:</span>
                    <span>${breakdown.embedding_time}秒</span>
                </div>
            `;
        }
    }

    getProcessingOptions() {
        const processSelect = document.getElementById('process-select');
        const overwriteExisting = document.getElementById('overwrite-existing');
        
        return {
            process_type: processSelect?.value || 'default',
            overwrite_existing: overwriteExisting?.checked || false
        };
    }

    getStatusLabel(status) {
        const labels = {
            'processed': '処理済み',
            'text_extracted': 'テキスト抽出済み',
            'pending_processing': '未処理'
        };
        return labels[status] || status;
    }

    updateUI() {
        this.updateSelectionCount();
        this.updateStatsDisplay();
        this.updateFilterOptions();
    }

    dispatchSelectionEvent() {
        document.dispatchEvent(new CustomEvent('selectionChanged', {
            detail: {
                selectedFiles: Array.from(this.selectedFiles),
                count: this.selectedFiles.size
            }
        }));
    }

    // 選択状態をクリア
    clearSelection() {
        this.deselectAll();
    }

    // 選択ファイルIDの配列を取得
    getSelectedFileIds() {
        return Array.from(this.selectedFiles);
    }

    // 選択数を取得
    getSelectedCount() {
        return this.selectedFiles.size;
    }
}

// グローバルインスタンス
window.fileSelectionManager = new FileSelectionManager();