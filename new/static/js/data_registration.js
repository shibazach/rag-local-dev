// new/static/js/data_registration.js
// データ登録ページ専用JavaScript

// 設定管理
const DataRegistration = {
    // 処理設定
    settings: {
        ocrEngine: 'ocrmypdf',
        embeddingModels: ['intfloat-e5-large-v2'],
        llmTimeout: 300,
        qualityThreshold: 0.0,
        overwriteExisting: true
    },
    
    // 選択されたファイル
    selectedFiles: new Set(),
    
    // 利用可能な設定情報
    availableConfig: null,

    // 初期化
    async init() {
        console.log('[DataRegistration] 初期化開始');
        
        await this.loadAvailableConfig();
        this.setupEventListeners();
        await this.loadFileList();
        
        console.log('[DataRegistration] 初期化完了');
    },

    // 利用可能な設定を読み込み
    async loadAvailableConfig() {
        try {
            console.log('[DataRegistration] 設定情報を読み込み中...');
            
            // 新系のOCRエンジン情報をテスト
            const response = await fetch('/api/processing/config', {
                credentials: 'include'
            });
            
            if (response.ok) {
                this.availableConfig = await response.json();
                console.log('[DataRegistration] 新系API設定読み込み成功:', this.availableConfig);
                this.updateUIWithConfig();
            } else {
                console.warn('[DataRegistration] 新系API利用不可、旧系にフォールバック');
                await this.loadLegacyConfig();
            }
        } catch (error) {
            console.error('[DataRegistration] 設定読み込みエラー:', error);
            await this.loadLegacyConfig();
        }
    },

    // 旧系設定にフォールバック
    async loadLegacyConfig() {
        try {
            const response = await fetch('/ingest/config', {
                credentials: 'include'
            });
            
            if (response.ok) {
                const legacyConfig = await response.json();
                console.log('[DataRegistration] 旧系設定読み込み成功:', legacyConfig);
                
                // 旧系設定を新系形式に変換
                this.availableConfig = {
                    success: true,
                    data: {
                        ocr_engines: legacyConfig.ocr?.available_engines || {},
                        embedding_models: legacyConfig.embedding_options || {},
                        default_settings: {
                            ocr_engine: legacyConfig.ocr?.default_engine || 'ocrmypdf',
                            embedding_models: Object.keys(legacyConfig.embedding_options || {}).slice(0, 1),
                            llm_timeout: 300,
                            quality_threshold: 0.0,
                            overwrite_existing: true
                        }
                    }
                };
                this.updateUIWithConfig();
            }
        } catch (error) {
            console.error('[DataRegistration] 旧系設定読み込みエラー:', error);
            this.setDefaultConfig();
        }
    },

    // デフォルト設定を適用
    setDefaultConfig() {
        console.log('[DataRegistration] デフォルト設定を適用');
        this.availableConfig = {
            success: true,
            data: {
                ocr_engines: {
                    'ocrmypdf': { name: 'OCRMyPDF', available: true },
                    'tesseract': { name: 'Tesseract', available: true }
                },
                embedding_models: {
                    'intfloat-e5-large-v2': { name: 'intfloat/e5-large-v2', available: true }
                },
                default_settings: {
                    ocr_engine: 'ocrmypdf',
                    embedding_models: ['intfloat-e5-large-v2'],
                    llm_timeout: 300,
                    quality_threshold: 0.0,
                    overwrite_existing: true
                }
            }
        };
        this.updateUIWithConfig();
    },

    // 設定をUIに反映
    updateUIWithConfig() {
        if (!this.availableConfig?.data) return;

        const config = this.availableConfig.data;
        
        // デフォルト設定を適用
        Object.assign(this.settings, config.default_settings);
        
        // OCRエンジン情報を表示
        console.log('[DataRegistration] 利用可能OCRエンジン:', config.ocr_engines);
        
        // 埋め込みモデル情報を表示
        console.log('[DataRegistration] 利用可能埋め込みモデル:', config.embedding_models);
        
        // 現在のモデル表示を更新
        this.updateCurrentModelDisplay();
    },

    // 現在のモデル表示を更新
    updateCurrentModelDisplay() {
        const modelDisplay = document.getElementById('current-model');
        if (modelDisplay) {
            const model = this.settings.embeddingModels?.[0] || 'デフォルト';
            modelDisplay.textContent = model;
        }
    },

    // イベントリスナー設定
    setupEventListeners() {
        // 処理開始ボタン
        const startBtn = document.getElementById('start-processing');
        if (startBtn) {
            startBtn.addEventListener('click', () => this.startProcessing());
        }

        // 停止ボタン
        const stopBtn = document.getElementById('stop-processing');
        if (stopBtn) {
            stopBtn.addEventListener('click', () => this.stopProcessing());
        }

        // ステータスフィルター
        const statusFilter = document.getElementById('status-filter');
        if (statusFilter) {
            statusFilter.addEventListener('change', () => this.filterFiles());
        }

        // 検索入力
        const searchInput = document.getElementById('search-input');
        if (searchInput) {
            searchInput.addEventListener('input', () => this.filterFiles());
        }

        // 全選択/全解除
        const selectAllBtn = document.getElementById('select-all');
        if (selectAllBtn) {
            selectAllBtn.addEventListener('click', () => this.toggleSelectAll());
        }

        // 設定変更
        this.setupSettingsListeners();
    },

    // 設定変更リスナー
    setupSettingsListeners() {
        // 上書き設定
        const overwriteCheckbox = document.getElementById('overwrite-existing');
        if (overwriteCheckbox) {
            overwriteCheckbox.addEventListener('change', (e) => {
                this.settings.overwriteExisting = e.target.checked;
            });
        }

        // 品質しきい値
        const qualityInput = document.getElementById('quality-threshold');
        if (qualityInput) {
            qualityInput.addEventListener('change', (e) => {
                this.settings.qualityThreshold = parseFloat(e.target.value);
            });
        }

        // LLMタイムアウト
        const timeoutInput = document.getElementById('llm-timeout');
        if (timeoutInput) {
            timeoutInput.addEventListener('change', (e) => {
                this.settings.llmTimeout = parseInt(e.target.value);
            });
        }
    },

    // ファイル一覧を読み込み
    async loadFileList() {
        try {
            console.log('[DataRegistration] ファイル一覧読み込み中...');
            
            const response = await fetch('/api/files?page=1&page_size=100', {
                credentials: 'include'
            });
            
            if (response.ok) {
                const result = await response.json();
                console.log('[DataRegistration] ファイル一覧取得成功:', result);
                this.renderFileList(result.data?.files || []);
            } else if (response.status === 401) {
                console.warn('[DataRegistration] 認証が必要です');
                this.showError('認証が必要です。ログインしてください。');
            } else {
                console.error('[DataRegistration] ファイル一覧取得失敗:', response.status);
                this.showError('ファイル一覧の取得に失敗しました。');
            }
        } catch (error) {
            console.error('[DataRegistration] ファイル一覧読み込みエラー:', error);
            this.showError('ファイル一覧の読み込み中にエラーが発生しました。');
        }
    },

    // ファイル一覧をレンダリング
    renderFileList(files) {
        const tbody = document.getElementById('file-list-tbody');
        if (!tbody) return;

        tbody.innerHTML = '';

        files.forEach(file => {
            const row = this.createFileRow(file);
            tbody.appendChild(row);
        });

        this.updateProcessButtonState();
    },

    // ファイル行を作成
    createFileRow(file) {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>
                <input type="checkbox" class="file-checkbox" 
                       data-file-id="${file.file_id}" 
                       ${this.selectedFiles.has(file.file_id) ? 'checked' : ''}>
            </td>
            <td>${file.file_name || 'Unknown'}</td>
            <td>
                <span class="status-badge status-${file.status || 'unknown'}">
                    ${this.getStatusText(file.status)}
                </span>
            </td>
            <td>${this.formatDate(file.created_at)}</td>
            <td>${this.formatFileSize(file.file_size || 0)}</td>
        `;

        // チェックボックスイベント
        const checkbox = row.querySelector('.file-checkbox');
        checkbox.addEventListener('change', (e) => {
            if (e.target.checked) {
                this.selectedFiles.add(file.file_id);
            } else {
                this.selectedFiles.delete(file.file_id);
            }
            this.updateProcessButtonState();
        });

        return row;
    },

    // ステータステキスト取得
    getStatusText(status) {
        const statusMap = {
            'pending_processing': '未処理',
            'processing': '処理中',
            'text_extracted': '未整形',
            'text_refined': '未ベクトル化',
            'processed': '処理完了',
            'error': 'エラー'
        };
        return statusMap[status] || status || '不明';
    },

    // 日付フォーマット
    formatDate(dateString) {
        if (!dateString) return '-';
        const date = new Date(dateString);
        return date.toLocaleString('ja-JP');
    },

    // ファイルサイズフォーマット
    formatFileSize(bytes) {
        if (bytes === 0) return '0 B';
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(1024));
        return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i];
    },

    // 処理ボタン状態更新
    updateProcessButtonState() {
        const startBtn = document.getElementById('start-processing');
        if (startBtn) {
            startBtn.disabled = this.selectedFiles.size === 0;
        }
    },

    // 全選択/全解除切り替え
    toggleSelectAll() {
        const checkboxes = document.querySelectorAll('.file-checkbox');
        const allChecked = Array.from(checkboxes).every(cb => cb.checked);

        checkboxes.forEach(checkbox => {
            checkbox.checked = !allChecked;
            const fileId = checkbox.dataset.fileId;
            if (checkbox.checked) {
                this.selectedFiles.add(fileId);
            } else {
                this.selectedFiles.delete(fileId);
            }
        });

        this.updateProcessButtonState();
    },

    // ファイルフィルタリング
    filterFiles() {
        // TODO: フィルタリング実装
        console.log('[DataRegistration] フィルタリング機能は未実装');
    },

    // 処理開始
    async startProcessing() {
        if (this.selectedFiles.size === 0) {
            this.showError('処理するファイルを選択してください。');
            return;
        }

        console.log('[DataRegistration] 処理開始:', Array.from(this.selectedFiles));
        this.setProcessingState(true);
        
        try {
            // SSEクライアント初期化
            if (!this.sseClient) {
                this.initializeSSEClient();
            }
            
            // 処理開始
            await this.sseClient.startProcessing(this.selectedFiles, this.settings);
            
        } catch (error) {
            console.error('[DataRegistration] 処理開始エラー:', error);
            this.showError(`処理開始エラー: ${error.message}`);
            this.setProcessingState(false);
        }
    },

    // 処理停止
    async stopProcessing() {
        console.log('[DataRegistration] 処理停止要求');
        
        try {
            if (this.sseClient) {
                await this.sseClient.cancelProcessing();
            }
        } catch (error) {
            console.error('[DataRegistration] 停止エラー:', error);
            this.showError(`停止エラー: ${error.message}`);
        }
        
        this.setProcessingState(false);
    },

    // SSEクライアント初期化
    initializeSSEClient() {
        this.sseClient = new SSEProgressClient({
            onProgress: (event) => this.handleProgress(event),
            onComplete: (event) => this.handleComplete(event),
            onError: (message) => this.handleError(message),
            onCancel: (message) => this.handleCancel(message)
        });
    },

    // 進捗イベント処理
    handleProgress(event) {
        console.log('[DataRegistration] 進捗:', event);
        
        // 進捗バー更新
        this.updateProgressBar(event.progress || 0);
        
        // メッセージ表示
        this.updateProgressMessage(event.message);
        
        // ファイル別進捗
        if (event.fileName) {
            this.updateFileProgress(event.fileName, event);
        }
    },

    // 完了イベント処理
    handleComplete(event) {
        console.log('[DataRegistration] 完了:', event);
        
        this.setProcessingState(false);
        this.updateProgressBar(100);
        this.updateProgressMessage('全ての処理が完了しました');
        
        // 結果表示
        if (event.results) {
            this.displayResults(event.results);
        }
        
        this.showSuccess(`処理完了: ${event.totalFiles}ファイル (${Math.round(event.processingTime)}秒)`);
        
        // ファイル一覧を再読み込み
        setTimeout(() => {
            this.loadFileList();
        }, 1000);
    },

    // エラー処理
    handleError(message) {
        console.error('[DataRegistration] エラー:', message);
        this.setProcessingState(false);
        this.showError(message);
        this.updateProgressMessage('エラーが発生しました');
    },

    // キャンセル処理
    handleCancel(message) {
        console.log('[DataRegistration] キャンセル:', message);
        this.setProcessingState(false);
        this.showInfo(message);
        this.updateProgressMessage('処理がキャンセルされました');
    },

    // 進捗バー更新
    updateProgressBar(progress) {
        const progressBar = document.querySelector('.progress-bar-fill');
        const progressText = document.querySelector('.progress-text');
        
        if (progressBar) {
            progressBar.style.width = `${progress}%`;
        }
        
        if (progressText) {
            progressText.textContent = `${Math.round(progress)}%`;
        }
    },

    // 進捗メッセージ更新
    updateProgressMessage(message) {
        const messageElement = document.querySelector('.progress-message');
        if (messageElement) {
            messageElement.textContent = message;
        }
    },

    // ファイル別進捗更新
    updateFileProgress(fileName, event) {
        // ファイル行を特定して進捗表示を更新
        const rows = document.querySelectorAll('#file-list-tbody tr');
        rows.forEach(row => {
            const fileNameCell = row.querySelector('td:nth-child(2)');
            if (fileNameCell && fileNameCell.textContent === fileName) {
                const statusCell = row.querySelector('td:nth-child(3)');
                if (statusCell) {
                    const badge = statusCell.querySelector('.status-badge');
                    if (badge) {
                        badge.textContent = event.step || '処理中';
                        badge.className = 'status-badge status-processing';
                    }
                }
            }
        });
    },

    // 結果表示
    displayResults(results) {
        console.log('[DataRegistration] 処理結果:', results);
        
        let successCount = 0;
        let errorCount = 0;
        
        results.forEach(result => {
            if (result.status === 'completed') {
                successCount++;
            } else {
                errorCount++;
            }
        });
        
        this.showInfo(`処理結果: 成功 ${successCount}件, エラー ${errorCount}件`);
    },

    // 処理状態設定
    setProcessingState(isProcessing) {
        const startBtn = document.getElementById('start-processing');
        const stopBtn = document.getElementById('stop-processing');
        const progressPanel = document.getElementById('progress-panel');

        if (startBtn && stopBtn) {
            startBtn.style.display = isProcessing ? 'none' : 'inline-block';
            stopBtn.style.display = isProcessing ? 'inline-block' : 'none';
        }

        if (progressPanel) {
            progressPanel.style.display = isProcessing ? 'block' : 'none';
        }

        // 進捗リセット
        if (!isProcessing) {
            this.updateProgressBar(0);
            this.updateProgressMessage('処理準備中...');
        }
    },

    // 通知表示
    showSuccess(message) {
        this.showNotification(message, 'success');
    },

    showError(message) {
        this.showNotification(message, 'error');
    },

    showInfo(message) {
        this.showNotification(message, 'info');
    },

    showNotification(message, type = 'info') {
        // Utils.showNotificationがある場合は使用
        if (typeof Utils !== 'undefined' && Utils.showNotification) {
            Utils.showNotification(message, type);
        } else {
            console.log(`[${type.toUpperCase()}] ${message}`);
        }
    }
};

// ページ読み込み時に初期化
document.addEventListener('DOMContentLoaded', () => {
    DataRegistration.init();
});

// グローバルに公開
window.DataRegistration = DataRegistration;