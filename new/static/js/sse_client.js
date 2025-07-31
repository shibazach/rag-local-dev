// new/static/js/sse_client.js
// SSE進捗表示クライアント

class SSEProgressClient {
    constructor(options = {}) {
        this.baseUrl = options.baseUrl || '';
        this.onProgress = options.onProgress || this.defaultProgressHandler;
        this.onComplete = options.onComplete || this.defaultCompleteHandler;
        this.onError = options.onError || this.defaultErrorHandler;
        this.onCancel = options.onCancel || this.defaultCancelHandler;
        
        this.eventSource = null;
        this.isConnected = false;
        this.currentJobId = null;
    }

    // 処理開始とSSE接続
    async startProcessing(selectedFiles, settings) {
        try {
            console.log('[SSE] 処理開始要求:', { files: selectedFiles.length, settings });
            
            // 1. 処理開始API呼び出し
            const response = await fetch(`${this.baseUrl}/api/ingest/start`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                credentials: 'include',
                body: JSON.stringify({
                    selected_files: Array.from(selectedFiles),
                    settings: settings
                })
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || `HTTP ${response.status}`);
            }

            const result = await response.json();
            this.currentJobId = result.data.job_id;
            
            console.log('[SSE] 処理開始成功:', result.data);
            
            // 2. SSE接続開始
            this.connectSSE();
            
            return result.data;
            
        } catch (error) {
            console.error('[SSE] 処理開始エラー:', error);
            this.onError(`処理開始エラー: ${error.message}`);
            throw error;
        }
    }

    // SSE接続
    connectSSE() {
        if (this.eventSource) {
            this.eventSource.close();
        }

        console.log('[SSE] 接続開始');
        
        this.eventSource = new EventSource(`${this.baseUrl}/api/ingest/stream`);
        
        this.eventSource.onopen = () => {
            console.log('[SSE] 接続確立');
            this.isConnected = true;
        };

        this.eventSource.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                this.handleProgressEvent(data);
            } catch (error) {
                console.error('[SSE] メッセージ解析エラー:', error);
            }
        };

        this.eventSource.onerror = (error) => {
            console.error('[SSE] 接続エラー:', error);
            this.isConnected = false;
            
            if (this.eventSource.readyState === EventSource.CLOSED) {
                console.log('[SSE] 接続が閉じられました');
            }
        };
    }

    // 進捗イベント処理
    handleProgressEvent(data) {
        console.log('[SSE] 進捗イベント:', data);
        
        switch (data.type) {
            case 'start':
                this.onProgress({
                    type: 'start',
                    message: '処理を開始しました',
                    totalFiles: data.data.total_files,
                    progress: 0
                });
                break;

            case 'file_start':
                this.onProgress({
                    type: 'file_start',
                    message: `${data.data.file_name} の処理を開始`,
                    fileName: data.data.file_name,
                    fileIndex: data.data.file_index,
                    totalFiles: data.data.total_files,
                    progress: data.data.progress
                });
                break;

            case 'ocr_progress':
                this.onProgress({
                    type: 'ocr_progress',
                    message: `${data.data.file_name}: ${data.data.step}`,
                    fileName: data.data.file_name,
                    step: data.data.step,
                    stepProgress: data.data.progress
                });
                break;

            case 'llm_progress':
                this.onProgress({
                    type: 'llm_progress',
                    message: `${data.data.file_name}: ${data.data.step}`,
                    fileName: data.data.file_name,
                    step: data.data.step,
                    stepProgress: data.data.progress
                });
                break;

            case 'embedding_progress':
                this.onProgress({
                    type: 'embedding_progress',
                    message: `${data.data.file_name}: ${data.data.step}`,
                    fileName: data.data.file_name,
                    step: data.data.step,
                    stepProgress: data.data.progress
                });
                break;

            case 'file_complete':
                this.onProgress({
                    type: 'file_complete',
                    message: `${data.data.file_name} の処理が完了`,
                    fileName: data.data.file_name,
                    fileIndex: data.data.file_index,
                    totalFiles: data.data.total_files,
                    progress: data.data.progress,
                    result: data.data.result
                });
                break;

            case 'complete':
                this.onComplete({
                    message: '全ての処理が完了しました',
                    totalFiles: data.data.total_files,
                    processingTime: data.data.processing_time,
                    results: data.data.results
                });
                this.disconnect();
                break;

            case 'cancelled':
                this.onCancel(data.message || '処理がキャンセルされました');
                this.disconnect();
                break;

            case 'error':
                this.onError(data.message || '処理エラーが発生しました');
                this.disconnect();
                break;

            default:
                console.warn('[SSE] 未知のイベントタイプ:', data.type);
        }
    }

    // 処理キャンセル
    async cancelProcessing() {
        try {
            console.log('[SSE] キャンセル要求');
            
            const response = await fetch(`${this.baseUrl}/api/ingest/cancel`, {
                method: 'POST',
                credentials: 'include'
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || `HTTP ${response.status}`);
            }

            const result = await response.json();
            console.log('[SSE] キャンセル要求送信済み:', result);
            
            return result;
            
        } catch (error) {
            console.error('[SSE] キャンセルエラー:', error);
            this.onError(`キャンセルエラー: ${error.message}`);
            throw error;
        }
    }

    // SSE切断
    disconnect() {
        if (this.eventSource) {
            console.log('[SSE] 切断');
            this.eventSource.close();
            this.eventSource = null;
        }
        this.isConnected = false;
        this.currentJobId = null;
    }

    // 処理状況取得
    async getStatus() {
        try {
            const response = await fetch(`${this.baseUrl}/api/ingest/status`, {
                credentials: 'include'
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || `HTTP ${response.status}`);
            }

            return await response.json();
            
        } catch (error) {
            console.error('[SSE] 状況取得エラー:', error);
            throw error;
        }
    }

    // デフォルトハンドラ
    defaultProgressHandler(event) {
        console.log('[SSE] 進捗:', event.message, `(${event.progress || 0}%)`);
    }

    defaultCompleteHandler(event) {
        console.log('[SSE] 完了:', event.message);
    }

    defaultErrorHandler(message) {
        console.error('[SSE] エラー:', message);
    }

    defaultCancelHandler(message) {
        console.log('[SSE] キャンセル:', message);
    }
}

// モジュール公開
if (typeof module !== 'undefined' && module.exports) {
    module.exports = SSEProgressClient;
} else {
    window.SSEProgressClient = SSEProgressClient;
}