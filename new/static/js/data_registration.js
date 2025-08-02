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
        
        // SSEProgressClientクラスの存在確認
        if (typeof SSEProgressClient === 'undefined') {
            console.error('[DataRegistration] SSEProgressClientクラスが定義されていません');
            this.showError('SSEクライアントの読み込みに失敗しました。ページを再読み込みしてください。');
            return;
        } else {
            console.log('[DataRegistration] SSEProgressClientクラス確認: OK');
        }
        
        // 重複実行防止フラグ初期化
        this.isProcessing = false;
        this.selectedFiles = new Set();
        
        // デバッグログ有効化
        window.DEBUG_DATA_REGISTRATION = true;
        console.log('[DataRegistration] デバッグモード有効化');
        
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

            // ヘッダーチェックボックス（全選択/全解除）
        const headerCheckbox = document.getElementById('header-checkbox');
        if (headerCheckbox) {
            headerCheckbox.addEventListener('change', () => {
                this.handleHeaderCheckboxChange();
            });
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
                this.renderFileList(result.files || []);
                // 初期読み込み時は全ファイル数を取得
                if (result.total) {
                    this.updateTotalCount(result.total);
                }
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
        this.updateSelectedCount();
        this.updateTotalCount(files.length);
    },
    
    // フィルタリング結果をレンダリング
    renderFilteredFileList(files, totalCount) {
        const tbody = document.getElementById('file-list-tbody');
        if (!tbody) return;

        tbody.innerHTML = '';

        files.forEach(file => {
            const row = this.createFileRow(file);
            tbody.appendChild(row);
        });

        this.updateProcessButtonState();
        this.updateSelectedCount();
        this.updateTotalCount(totalCount);
        this.updateHeaderCheckboxState();
    },

    // ファイル行を作成
    createFileRow(file) {
        // ファイルIDの確実な取得
        const fileId = file.file_id || file.id || file.fileName || `file_${Date.now()}_${Math.random()}`;
        
        console.log('[DataRegistration] createFileRow:', {
            originalFile: file,
            extractedFileId: fileId
        });
        
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>
                <input type="checkbox" class="file-checkbox" 
                       data-file-id="${fileId}" 
                       ${this.selectedFiles.has(fileId) ? 'checked' : ''}>
            </td>
            <td>${file.file_name || file.fileName || 'Unknown'}</td>
            <td>${file.page_count || file.pages || '-'}</td>
            <td>
                <span class="status-badge status-${file.status || 'unknown'}">
                    ${this.getStatusText(file.status)}
                </span>
            </td>
            <td>${this.formatFileSize(file.file_size || file.size || 0)}</td>
        `;

        // チェックボックスイベント
        const checkbox = row.querySelector('.file-checkbox');
        checkbox.addEventListener('change', (e) => {
            this.handleFileCheckboxChange(e);
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

    // 選択件数表示更新
    updateSelectedCount() {
        const selectedCountSpan = document.getElementById('selected-count');
        if (selectedCountSpan) {
            const count = this.selectedFiles.size;
            selectedCountSpan.textContent = count;
            console.log('[DataRegistration] updateSelectedCount:', {
                displayedCount: count,
                actualSelectedFiles: Array.from(this.selectedFiles)
            });
        } else {
            console.warn('[DataRegistration] updateSelectedCount: selected-count element not found');
        }
    },

    // 総件数表示更新
    updateTotalCount(count) {
        const fileCountInfo = document.getElementById('file-count-info');
        if (fileCountInfo) {
            fileCountInfo.textContent = `${count}件のファイル`;
        }
    },

    // ヘッダーチェックボックス状態更新
    updateHeaderCheckboxState() {
        const headerCheckbox = document.getElementById('header-checkbox');
        const fileCheckboxes = document.querySelectorAll('.file-checkbox');
        
        if (!headerCheckbox || fileCheckboxes.length === 0) return;
        
        const checkedCount = Array.from(fileCheckboxes).filter(cb => cb.checked).length;
        const totalCount = fileCheckboxes.length;
        
        if (checkedCount === 0) {
            // 未選択
            headerCheckbox.checked = false;
            headerCheckbox.indeterminate = false;
        } else if (checkedCount === totalCount) {
            // 全選択
            headerCheckbox.checked = true;
            headerCheckbox.indeterminate = false;
        } else {
            // 一部選択
            headerCheckbox.checked = false;
            headerCheckbox.indeterminate = true;
        }
        
        console.log('[DataRegistration] Header state updated:', {
            checkedCount: checkedCount,
            totalCount: totalCount,
            headerChecked: headerCheckbox.checked,
            headerIndeterminate: headerCheckbox.indeterminate
        });
    },

    // ヘッダーチェックボックス変更処理
    handleHeaderCheckboxChange() {
        const headerCheckbox = document.getElementById('header-checkbox');
        const fileCheckboxes = document.querySelectorAll('.file-checkbox');
        
        if (!headerCheckbox || fileCheckboxes.length === 0) return;
        
        const isChecked = headerCheckbox.checked;
        console.log('[DataRegistration] Header checkbox changed:', isChecked);
        
        // 全ファイルチェックボックスを統一
        fileCheckboxes.forEach(checkbox => {
            checkbox.checked = isChecked;
        });
        
        // selectedFilesを更新
        this.selectedFiles.clear();
        if (isChecked) {
            fileCheckboxes.forEach(checkbox => {
                const fileId = checkbox.getAttribute('data-file-id');
                if (fileId) {
                    this.selectedFiles.add(fileId);
                }
            });
        }
        
        // UI更新
        this.updateSelectedCount();
        this.updateProcessButtonState();
        
        // indeterminateを無効化
        headerCheckbox.indeterminate = false;
        
        console.log('[DataRegistration] Header change complete:', {
            checked: isChecked,
            selectedCount: this.selectedFiles.size
        });
    },

    // ファイルチェックボックス変更処理
    handleFileCheckboxChange(event) {
        const checkbox = event.target;
        const fileId = checkbox.getAttribute('data-file-id');
        
        if (!fileId) return;
        
        // selectedFilesを更新
        if (checkbox.checked) {
            this.selectedFiles.add(fileId);
        } else {
            this.selectedFiles.delete(fileId);
        }
        
        console.log('[DataRegistration] File checkbox changed:', {
            fileId: fileId,
            checked: checkbox.checked,
            selectedCount: this.selectedFiles.size
        });
        
        // ヘッダーチェックボックス状態を計算
        this.updateHeaderCheckboxState();
        
        // UI更新
        this.updateSelectedCount();
        this.updateProcessButtonState();
    },

    // ファイルフィルタリング
    async filterFiles() {
        const statusFilter = document.getElementById('status-filter');
        const searchInput = document.getElementById('search-input');
        
        const status = statusFilter?.value || '';
        const searchTerm = searchInput?.value.trim() || '';
        
        console.log('[DataRegistration] フィルタリング実行:', { status, searchTerm });
        
        try {
            // APIパラメータ構築
            const params = new URLSearchParams({
                page: '1',
                page_size: '1000' // フィルタリング用に多めに取得
            });
            
            if (status) {
                params.append('status', status);
            }
            
            if (searchTerm) {
                params.append('filename', searchTerm); // ファイル名検索パラメータ
            }
            
            const response = await fetch(`/api/files?${params.toString()}`, {
                credentials: 'include'
            });
            
            if (response.ok) {
                const result = await response.json();
                console.log('[DataRegistration] フィルター結果:', result);
                
                // フィルタリング結果を表示
                this.renderFilteredFileList(result.files || [], result.total || 0);
            } else {
                console.error('[DataRegistration] フィルタリング失敗:', response.status);
                this.showError('ファイルのフィルタリングに失敗しました。');
            }
        } catch (error) {
            console.error('[DataRegistration] フィルタリングエラー:', error);
            this.showError('フィルタリング中にエラーが発生しました。');
        }
    },

    // 処理開始
    async startProcessing() {
        // 重複実行防止チェック
        if (this.isProcessing) {
            console.log('[DataRegistration] 🚨 処理が既に実行中のため、重複実行を防止します');
            this.addToProcessingLog('WARN', '⚠️ 処理が既に実行中です - 重複実行防止');
            return;
        }
        
        // 処理中フラグを設定
        this.isProcessing = true;
        
        console.log('[DataRegistration] 🔥 処理開始 - 重複実行防止フラグ設定完了');
        
        // 強制的にファイル選択状態を再確認・同期
        this.updateSelectedCount();
        
        console.log('[DataRegistration] 🔥 選択ファイル強制確認:', {
            selectedFilesSize: this.selectedFiles.size,
            selectedFilesArray: Array.from(this.selectedFiles),
            checkboxes: document.querySelectorAll('input[name="file-select"]:checked').length
        });
        
        if (this.selectedFiles.size === 0) {
            // チェックボックスから直接選択状態を取得して強制同期
            const checkedBoxes = document.querySelectorAll('input[name="file-select"]:checked');
            console.log('[DataRegistration] 🔥 チェック済みチェックボックス:', checkedBoxes.length);
            
            if (checkedBoxes.length > 0) {
                // 重複を防ぐためSetを新規作成
                this.selectedFiles.clear();
                checkedBoxes.forEach(checkbox => {
                    this.selectedFiles.add(checkbox.value);
                });
                console.log('[DataRegistration] 🔥 強制同期後の選択ファイル:', this.selectedFiles.size);
                console.log('[DataRegistration] 🔥 選択ファイル詳細:', Array.from(this.selectedFiles));
            } else {
                this.showError('処理するファイルを選択してください。');
                return;
            }
        }

        console.log('[DataRegistration] 処理開始:', {
            selectedFiles: Array.from(this.selectedFiles),
            settings: this.settings,
            sseClientExists: !!this.sseClient
        });
        
        // 処理開始時刻を記録
        this.processingStartTime = new Date();
        
        // 進行中ログIDをリセット
        this.currentProgressLogId = null;
        
        // 既存の更新タイマーをクリア
        if (this.progressUpdateTimer) {
            clearInterval(this.progressUpdateTimer);
            this.progressUpdateTimer = null;
        }
        
        // 処理開始ログ
        this.addToProcessingLog('INFO', `処理開始 - 選択ファイル数: ${this.selectedFiles.size}`);
        
        this.setProcessingState(true);
        
        try {
            // SSEクライアント初期化
            if (!this.sseClient) {
                console.log('[DataRegistration] SSEクライアントを初期化中...');
                this.initializeSSEClient();
                
                if (!this.sseClient) {
                    throw new Error('SSEクライアントの初期化に失敗しました');
                }
                console.log('[DataRegistration] SSEクライアント初期化完了');
            }
            
            // 処理開始（409エラー自動リトライ付き）
            console.log('[DataRegistration] SSEクライアントで処理開始中...');
            this.addToProcessingLog('INFO', '🔗 SSE接続・処理要求送信中...');
            
            try {
                await this.sseClient.startProcessing(this.selectedFiles, this.settings);
                this.addToProcessingLog('INFO', '✅ 処理要求完了、バックエンド処理開始待機中...');
            } catch (conflictError) {
                if (conflictError.message.includes('409') || conflictError.message.includes('実行中')) {
                    this.addToProcessingLog('WARN', '🔄 処理が実行中のため、状態をリセットして再試行します...');
                    
                    // 状態リセット
                    await this.resetProcessingState();
                    await new Promise(resolve => setTimeout(resolve, 1000));
                    
                    // 再試行
                    this.addToProcessingLog('INFO', '🔄 リセット後、処理を再試行中...');
                    await this.sseClient.startProcessing(this.selectedFiles, this.settings);
                    this.addToProcessingLog('INFO', '✅ 状態リセット後、処理を開始しました');
                } else {
                    throw conflictError;
                }
            }
            
        } catch (error) {
            console.error('[DataRegistration] 処理開始エラー:', error);
            console.error('[DEBUG] エラー詳細:', error.stack);
            this.addToProcessingLog('ERROR', `処理開始エラー: ${error.message}`);
            this.addToProcessingLog('ERROR', `エラー詳細: ${error.stack || 'スタック情報なし'}`);
            this.showError(`処理開始エラー: ${error.message}`);
            this.setProcessingState(false);
        } finally {
            // 重複実行防止フラグを解除
            this.isProcessing = false;
            console.log('[DataRegistration] 🔥 処理完了 - 重複実行防止フラグ解除');
        }
    },

    // 処理停止
    async stopProcessing() {
        console.log('[DataRegistration] 処理停止要求');
        
        try {
            if (this.sseClient) {
                const result = await this.sseClient.cancelProcessing();
                if (result && result.message) {
                    this.addToProcessingLog('INFO', `🛑 ${result.message}`);
                }
            }
        } catch (error) {
            console.error('[DataRegistration] 停止エラー:', error);
            this.addToProcessingLog('ERROR', `停止エラー: ${error.message}`);
        }
        
        this.setProcessingState(false);
    },

    // 処理状態リセット
    async resetProcessingState() {
        console.log('[DataRegistration] 処理状態リセット');
        
        try {
            const response = await fetch('/api/ingest/reset', {
                method: 'POST',
                credentials: 'include'
            });
            
            if (!response.ok) {
                const contentType = response.headers.get('content-type');
                let errorMessage = `HTTP ${response.status}`;
                if (contentType && contentType.includes('application/json')) {
                    const errorData = await response.json();
                    errorMessage = errorData.detail || errorMessage;
                }
                throw new Error(errorMessage);
            }
            
            const result = await response.json();
            console.log('[DataRegistration] リセット完了:', result);
            return result;
            
        } catch (error) {
            console.error('[DataRegistration] リセットエラー:', error);
            throw error;
        }
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

    // 進捗イベント処理（OLD系互換）
    handleProgress(event) {
        console.log('[DataRegistration] 🔥 進捗イベント受信:', event);
        console.log('[DataRegistration] 🔥 イベントタイプ:', event.type);
        console.log('[DataRegistration] 🔥 イベントデータ:', event.data);
        
        if (window.DEBUG_DATA_REGISTRATION) {
            console.log('[DataRegistration] 進捗:', event);
        }
        
        // 詳細手順イベントの処理（展開可能な詳細情報付き）
        if (event.type === 'file_progress') {
            const data = event.data;
            let logMessage = '';
            
            if (data.step && data.detail) {
                logMessage = `${data.step}: ${data.detail}`;
            } else if (data.step) {
                logMessage = data.step;
            }
            
            // 展開可能な詳細情報を作成
            let expandableDetails = [];
            
            if (data.ocr_text) {
                expandableDetails.push({
                    title: '📄 OCR抽出テキスト',
                    content: data.ocr_text,
                    type: 'text'
                });
            }
            
            if (data.llm_prompt) {
                expandableDetails.push({
                    title: '💬 LLMプロンプト（全文）',
                    content: data.llm_prompt,
                    type: 'prompt'
                });
            }
            
            if (data.llm_result) {
                expandableDetails.push({
                    title: '✨ LLM整形結果',
                    content: data.llm_result,
                    type: 'result'
                });
            }
            
            // 長時間処理の判定とリアルタイム更新
            const isLongProcess = data.step && (
                data.step.includes('処理中') || 
                data.step.includes('実行中') || 
                data.step.includes('OCR処理開始') || 
                data.step.includes('LLM処理中')
            );
            
            console.log('[DataRegistration] 🔥 展開可能詳細数:', expandableDetails.length);
            console.log('[DataRegistration] 🔥 ログメッセージ:', logMessage);
            console.log('[DataRegistration] 🔥 長時間処理判定:', isLongProcess);
            
            if (isLongProcess) {
                // 前の進行中ログがあれば完了させる
                if (this.currentProgressLogId) {
                    this.completeProgressLog(this.currentProgressLogId, logMessage);
                }
                
                // 新しい進行中ログを開始
                console.log('[DataRegistration] 🔥 リアルタイム更新ログ開始:', logMessage);
                this.currentProgressLogId = this.addProgressLog('INFO', logMessage, true);
            } else {
                // 進行中ログがあれば完了させる
                if (this.currentProgressLogId) {
                    this.completeProgressLog(this.currentProgressLogId, logMessage);
                    this.currentProgressLogId = null;
                }
                
                // 展開可能詳細がある場合は特別な形式でログに追加
                if (expandableDetails.length > 0) {
                    console.log('[DataRegistration] 🔥 展開可能ログ呼び出し');
                    this.addExpandableProcessingLog('INFO', logMessage, expandableDetails);
                } else {
                    console.log('[DataRegistration] 🔥 通常ログ呼び出し');
                    this.addToProcessingLog('INFO', logMessage);
                }
            }
            return;
        }
        
        // 開始・完了メッセージ
        if (event.type === 'start' && event.data?.total_files) {
            this.addToProcessingLog('INFO', `📄 ${event.data.total_files} 件のファイル処理を開始`);
        }
        
        if (event.type === 'file_start' && event.data?.file_name) {
            // ファイル単位の区切り線を追加
            this.addFileSeparator();
            
            // ファイル名を太字クリッカブル青字アンダーラインで表示
            // file_idはfile_startイベントで渡される場合とfile_indexから取得する場合がある
            const fileId = event.data.file_id || this.getFileIdFromSelectedFiles(event.data.file_index);
            this.addFileHeader(event.data.file_name, fileId);
        }
        
        if (event.type === 'complete') {
            this.addToProcessingLog('INFO', '🎉 全処理が完了しました');
        }
        
        // 従来の処理（互換性のため）
        if (event.fileName && event.step) {
            this.addToProcessingLog('INFO', `${event.fileName}: ${event.step}`);
            if (event.detail) {
                this.addToProcessingLog('INFO', `  → ${event.detail}`);
            }
        } else if (event.message) {
            this.addToProcessingLog('INFO', event.message);
        }
    },

    // 完了イベント処理
    handleComplete(event) {
        console.log('[DataRegistration] 完了:', event);
        
        // 進行中ログがあれば完了させる
        if (this.currentProgressLogId) {
            this.completeProgressLog(this.currentProgressLogId, '🎉 全処理完了');
            this.currentProgressLogId = null;
        }
        
        // 重複実行防止フラグを解除
        this.isProcessing = false;
        console.log('[DataRegistration] 🔥 完了処理 - 重複実行防止フラグ解除');
        
        this.setProcessingState(false);
        // 完了処理
        // 完了メッセージはログに表示済み
        
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
        
        // 詳細ログに追加
        this.addToProcessingLog('ERROR', message || 'エラーが発生しました');
        
        // エラーは処理ログペインにのみ表示（ダイアログなし）
        
        this.setProcessingState(false);
        this.showError(message);
    },

    // キャンセル処理
    handleCancel(message) {
        console.log('[DataRegistration] キャンセル:', message);
        this.setProcessingState(false);
        this.showInfo(message);
        // キャンセル処理完了
    },

    // OLD系では進捗バーは使用せず、ログペインのみ使用

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
            // リセット処理
            // OLD系では進捗メッセージ不要
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
    },

    // 処理ログに追加（OLD系互換）
    addToProcessingLog(level, message, data = null) {
        const logContainer = document.querySelector('.log-container');
        if (!logContainer) return;

        const timestamp = new Date().toLocaleTimeString('ja-JP');
        const logEntry = document.createElement('div');
        
        // 経過秒数計算
        let elapsedText = '';
        if (this.processingStartTime) {
            const elapsed = Math.floor((new Date() - this.processingStartTime) / 1000);
            elapsedText = ` (+${elapsed}s)`;
        }
        
        // 統一スタイル適用
        logEntry.className = 'log-entry';
        logEntry.innerHTML = `<span class="log-time">[${timestamp}${elapsedText}]</span> <span class="log-message">${message}</span>`;
        
        // データがある場合は次の行に表示
        if (data && typeof data === 'object' && Object.keys(data).length > 0) {
            logEntry.innerHTML += `<br><span style="color: #999; margin-left: 20px;">→ ${JSON.stringify(data, null, 2)}</span>`;
        }
        
        // 正しい順序：新しいログを末尾に追加
        logContainer.insertBefore(logEntry, logContainer.firstChild);
        
        // 自動スクロール（上へ）
        logContainer.scrollTop = 0;
        
        console.log(`[LOG] ${message}`);
    },

    // リアルタイム更新可能ログエントリ追加
    addProgressLog(level, message, isProcessing = false) {
        const logContainer = document.querySelector('.log-container');
        if (!logContainer) return;

        const timestamp = new Date().toLocaleTimeString('ja-JP');
        const logEntry = document.createElement('div');
        
        // 経過秒数計算
        let elapsedText = '';
        if (this.processingStartTime) {
            const elapsed = Math.floor((new Date() - this.processingStartTime) / 1000);
            elapsedText = ` (+${elapsed}s)`;
        }
        
        // ログエントリのID設定（更新用）
        const entryId = `progress-log-${Date.now()}`;
        logEntry.id = entryId;
        logEntry.className = 'log-entry';
        logEntry.innerHTML = `<span class="log-time">[${timestamp}${elapsedText}]</span> <span class="log-message">${message}</span>`;
        
        // 正しい順序：新しいログを末尾に追加
        logContainer.insertBefore(logEntry, logContainer.firstChild);
        
        // 自動スクロール（上へ）
        logContainer.scrollTop = 0;
        
        // 処理中の場合、リアルタイム更新開始
        if (isProcessing) {
            this.startProgressUpdater(entryId, message);
        }
        
        console.log(`[PROGRESS-LOG] ${message}`);
        
        return entryId; // 更新用IDを返す
    },

    // リアルタイム経過時間更新
    startProgressUpdater(entryId, baseMessage) {
        // 既存の更新タイマーをクリア
        if (this.progressUpdateTimer) {
            clearInterval(this.progressUpdateTimer);
        }
        
        const startTime = new Date();
        
        this.progressUpdateTimer = setInterval(() => {
            const logEntry = document.getElementById(entryId);
            if (!logEntry) {
                clearInterval(this.progressUpdateTimer);
                return;
            }
            
            const elapsed = Math.floor((new Date() - startTime) / 1000);
            const timestamp = new Date().toLocaleTimeString('ja-JP');
            
            // 全体経過時間
            let totalElapsedText = '';
            if (this.processingStartTime) {
                const totalElapsed = Math.floor((new Date() - this.processingStartTime) / 1000);
                totalElapsedText = ` (+${totalElapsed}s)`;
            }
            
            // リアルタイム更新（統一スタイル）
            logEntry.innerHTML = `<span class="log-time">[${timestamp}${totalElapsedText}]</span> <span class="log-message">${baseMessage} <span style="color: #007bff;">(${elapsed}秒経過)</span></span>`;
        }, 1000); // 1秒毎に更新
    },

    // 進行中ログの完了
    completeProgressLog(entryId, finalMessage) {
        if (this.progressUpdateTimer) {
            clearInterval(this.progressUpdateTimer);
            this.progressUpdateTimer = null;
        }
        
        const logEntry = document.getElementById(entryId);
        if (logEntry) {
            const timestamp = new Date().toLocaleTimeString('ja-JP');
            
            // 全体経過時間
            let elapsedText = '';
            if (this.processingStartTime) {
                const elapsed = Math.floor((new Date() - this.processingStartTime) / 1000);
                elapsedText = ` (+${elapsed}s)`;
            }
            
            // 最終状態で固定（統一スタイル）
            logEntry.innerHTML = `<span class="log-time">[${timestamp}${elapsedText}]</span> <span class="log-message">${finalMessage}</span>`;
        }
    },

    // 展開可能詳細付きログエントリ追加（ダイアログ表示）
    addExpandableProcessingLog(level, message, expandableDetails) {
        const logContainer = document.querySelector('.log-container');
        if (!logContainer) {
            console.error('[DataRegistration] .log-container が見つかりません！');
            return;
        }

        const timestamp = new Date().toLocaleTimeString('ja-JP');
        
        // 経過秒数計算
        let elapsedText = '';
        if (this.processingStartTime) {
            const elapsed = Math.floor((new Date() - this.processingStartTime) / 1000);
            elapsedText = ` (+${elapsed}s)`;
        }
        
        // メインログエントリ（行全体がクリッカブル、青字アンダーライン）
        const mainEntry = document.createElement('div');
        mainEntry.style.cursor = 'pointer';
        mainEntry.style.color = '#007bff';
        mainEntry.style.textDecoration = 'underline';
        mainEntry.style.padding = '2px 4px';
        mainEntry.style.borderRadius = '4px';
        mainEntry.style.transition = 'background-color 0.2s';
        mainEntry.className = 'log-entry expandable-entry';
        mainEntry.innerHTML = `<span class="log-time">[${timestamp}${elapsedText}]</span> <span class="log-message" style="color: #007bff; text-decoration: underline;">${message}</span>`;
        
        // ホバー効果
        mainEntry.addEventListener('mouseenter', () => {
            mainEntry.style.backgroundColor = '#f0f8ff';
        });
        mainEntry.addEventListener('mouseleave', () => {
            mainEntry.style.backgroundColor = '';
        });
        
        // クリックでダイアログ表示
        mainEntry.addEventListener('click', () => {
            this.showDetailsDialog(message, expandableDetails);
        });
        
        // ログに追加
        logContainer.appendChild(mainEntry);
        
        // 自動スクロール
        logContainer.scrollTop = logContainer.scrollHeight;
        
        console.log(`[EXPANDABLE-LOG] ${message}`, expandableDetails);
    },

    // 詳細ダイアログを表示（タブ切り替え式）
    showDetailsDialog(title, details) {
        // 既存のダイアログがあれば削除
        const existingDialog = document.getElementById('details-dialog');
        if (existingDialog) {
            existingDialog.remove();
        }

        // ダイアログ作成
        const dialog = document.createElement('div');
        dialog.id = 'details-dialog';
        dialog.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.5);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 10000;
        `;

        const dialogContent = document.createElement('div');
        dialogContent.style.cssText = `
            background: white;
            border-radius: 8px;
            padding: 0;
            width: 90%;
            height: 85%;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
            display: flex;
            flex-direction: column;
        `;

        // ヘッダー
        const header = document.createElement('div');
        header.style.cssText = `
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 15px 20px;
            border-bottom: 1px solid #eee;
            background: #f8f9fa;
            border-radius: 8px 8px 0 0;
        `;
        header.innerHTML = `
            <h3 style="margin: 0; font-size: 16px;">${this.escapeHtml(title)}</h3>
            <button id="close-dialog" style="background: none; border: none; font-size: 20px; cursor: pointer; color: #666;">&times;</button>
        `;

        // タブヘッダー
        const tabHeaders = document.createElement('div');
        tabHeaders.style.cssText = `
            display: flex;
            border-bottom: 1px solid #ddd;
            background: #f8f9fa;
        `;

        // タブコンテンツ
        const tabContents = document.createElement('div');
        tabContents.style.cssText = `
            flex: 1;
            overflow: hidden;
            display: flex;
            flex-direction: column;
        `;

        // タブ作成
        details.forEach((detail, index) => {
            // タブヘッダー
            const tabHeader = document.createElement('button');
            tabHeader.style.cssText = `
                padding: 12px 20px;
                border: none;
                background: ${index === 0 ? '#fff' : 'transparent'};
                border-bottom: ${index === 0 ? '2px solid #007bff' : '2px solid transparent'};
                cursor: pointer;
                font-size: 14px;
                transition: all 0.2s;
            `;
            tabHeader.textContent = detail.title;
            tabHeaders.appendChild(tabHeader);

            // タブコンテンツ
            const tabContent = document.createElement('div');
            tabContent.style.cssText = `
                flex: 1;
                padding: 20px;
                overflow-y: auto;
                display: ${index === 0 ? 'block' : 'none'};
                font-family: monospace;
                font-size: 12px;
                line-height: 1.4;
                white-space: pre-wrap;
                background: #fff;
            `;
            tabContent.textContent = detail.content;
            tabContents.appendChild(tabContent);

            // タブ切り替えイベント
            tabHeader.addEventListener('click', () => {
                // すべてのタブを非アクティブ化
                tabHeaders.querySelectorAll('button').forEach(btn => {
                    btn.style.background = 'transparent';
                    btn.style.borderBottom = '2px solid transparent';
                });
                tabContents.querySelectorAll('div').forEach(content => {
                    content.style.display = 'none';
                });

                // 選択されたタブをアクティブ化
                tabHeader.style.background = '#fff';
                tabHeader.style.borderBottom = '2px solid #007bff';
                tabContent.style.display = 'block';
            });
        });

        dialogContent.appendChild(header);
        dialogContent.appendChild(tabHeaders);
        dialogContent.appendChild(tabContents);
        dialog.appendChild(dialogContent);
        document.body.appendChild(dialog);

        // 閉じるボタンイベント
        document.getElementById('close-dialog').addEventListener('click', () => {
            dialog.remove();
        });

        // 背景クリックで閉じる
        dialog.addEventListener('click', (e) => {
            if (e.target === dialog) {
                dialog.remove();
            }
        });

        // ESCキーで閉じる
        const escapeHandler = (e) => {
            if (e.key === 'Escape') {
                dialog.remove();
                document.removeEventListener('keydown', escapeHandler);
            }
        };
        document.addEventListener('keydown', escapeHandler);
    },

    // HTMLエスケープ関数
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    },

    // ファイル単位の区切り線追加
    addFileSeparator() {
        const logContainer = document.querySelector('.log-container');
        if (!logContainer) return;

        const separator = document.createElement('div');
        separator.style.cssText = `
            border-top: 1px solid #ddd;
            margin: 10px 0;
            height: 1px;
        `;
        
        // 正しい順序：新しいログを末尾に追加
        logContainer.insertBefore(separator, logContainer.firstChild);
    },

    // ファイルヘッダー追加（太字クリッカブル青字アンダーライン）
    addFileHeader(fileName, fileId) {
        const logContainer = document.querySelector('.log-container');
        if (!logContainer) return;

        const timestamp = new Date().toLocaleTimeString('ja-JP');
        const headerEntry = document.createElement('div');
        
        // 経過秒数計算
        let elapsedText = '';
        if (this.processingStartTime) {
            const elapsed = Math.floor((new Date() - this.processingStartTime) / 1000);
            elapsedText = ` (+${elapsed}s)`;
        }
        
        headerEntry.style.cssText = `
            padding: 8px 4px;
            cursor: pointer;
            font-weight: bold;
            color: #007bff;
            text-decoration: underline;
            background: #f8f9ff;
            border-radius: 4px;
            margin-bottom: 5px;
            transition: background-color 0.2s;
        `;
        
        headerEntry.innerHTML = `<span style="color: #666; font-size: 11px; font-weight: normal;">[${timestamp}${elapsedText}]</span> <span style="font-weight: bold; color: #007bff;">📄 ${this.escapeHtml(fileName)}</span>`;
        
        // ホバー効果
        headerEntry.addEventListener('mouseenter', () => {
            headerEntry.style.backgroundColor = '#e3f2fd';
        });
        headerEntry.addEventListener('mouseleave', () => {
            headerEntry.style.backgroundColor = '#f8f9ff';
        });
        
        // クリックでPDFプレビュー表示
        headerEntry.addEventListener('click', () => {
            this.showPdfPreview(fileName, fileId);
        });
        
        // 正しい順序：新しいログを末尾に追加
        logContainer.insertBefore(headerEntry, logContainer.firstChild);
        
        // 自動スクロール（上へ）
        logContainer.scrollTop = 0;
        
        console.log(`[FILE-HEADER] ${fileName}`);
    },

    // PDFプレビューダイアログ表示
    showPdfPreview(fileName, fileId) {
        // 既存のダイアログがあれば削除
        const existingDialog = document.getElementById('pdf-preview-dialog');
        if (existingDialog) {
            existingDialog.remove();
        }

        // ダイアログ作成
        const dialog = document.createElement('div');
        dialog.id = 'pdf-preview-dialog';
        dialog.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.5);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 10000;
        `;

        const dialogContent = document.createElement('div');
        dialogContent.style.cssText = `
            background: white;
            border-radius: 8px;
            padding: 0;
            width: 80%;
            height: 80%;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
            display: flex;
            flex-direction: column;
            resize: both;
            overflow: auto;
            min-width: 400px;
            min-height: 300px;
        `;

        // ヘッダー
        const header = document.createElement('div');
        header.style.cssText = `
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 15px 20px;
            border-bottom: 1px solid #eee;
            background: #f8f9fa;
            border-radius: 8px 8px 0 0;
        `;
        header.innerHTML = `
            <h3 style="margin: 0; font-size: 16px;">📄 ${this.escapeHtml(fileName)}</h3>
            <button id="close-pdf-dialog" style="background: none; border: none; font-size: 20px; cursor: pointer; color: #666;">&times;</button>
        `;

        // PDFビューアーコンテナ
        const pdfContainer = document.createElement('div');
        pdfContainer.style.cssText = `
            flex: 1;
            padding: 0;
            overflow: hidden;
            background: #f5f5f5;
        `;

        // PDFビューアー（iframe）
        const pdfViewer = document.createElement('iframe');
        pdfViewer.style.cssText = `
            width: 100%;
            height: 100%;
            border: none;
            background: white;
        `;
        
        // PDFのURLを設定（ファイルIDを使用）
        pdfViewer.src = `/api/files/${fileId}/preview`;
        
        pdfContainer.appendChild(pdfViewer);
        dialogContent.appendChild(header);
        dialogContent.appendChild(pdfContainer);
        dialog.appendChild(dialogContent);
        document.body.appendChild(dialog);

        // 閉じるボタンイベント
        document.getElementById('close-pdf-dialog').addEventListener('click', () => {
            dialog.remove();
        });

        // 背景クリックで閉じる
        dialog.addEventListener('click', (e) => {
            if (e.target === dialog) {
                dialog.remove();
            }
        });

        // ESCキーで閉じる
        const escapeHandler = (e) => {
            if (e.key === 'Escape') {
                dialog.remove();
                document.removeEventListener('keydown', escapeHandler);
            }
        };
        document.addEventListener('keydown', escapeHandler);
    },

    // 選択ファイルからfile_idを取得
    getFileIdFromSelectedFiles(fileIndex) {
        if (!fileIndex || fileIndex < 1) return null;
        
        // selectedFilesから指定インデックスのファイルIDを取得
        const selectedFilesArray = Array.from(this.selectedFiles);
        if (fileIndex <= selectedFilesArray.length) {
            return selectedFilesArray[fileIndex - 1];
        }
        
        return null;
    },

    // 状態リセット機能
    async resetProcessingState() {
        try {
            console.log('[DataRegistration] 処理状態をリセット中...');
            
            const response = await fetch('/api/ingest/reset', {
                method: 'POST',
                credentials: 'include'
            });
            
            if (response.ok) {
                this.addToProcessingLog('INFO', '処理状態をリセットしました');
                this.setProcessingState(false);
                this.selectedFiles.clear();
                this.updateSelectedCount();
                this.updateHeaderCheckboxState();
                console.log('[DataRegistration] リセット完了');
            } else {
                console.error('[DataRegistration] リセット失敗:', response.status);
            }
        } catch (error) {
            console.error('[DataRegistration] リセットエラー:', error);
        }
    }
};

// ページ読み込み時に初期化
document.addEventListener('DOMContentLoaded', () => {
    DataRegistration.init();
});

// グローバルに公開
window.DataRegistration = DataRegistration;