// new/static/js/main.js
// 新しいRAGシステムのメインJavaScript

// ユーティリティ関数
const Utils = {
    // 通知を表示
    showNotification: function(message, type = 'info') {
        const notifications = document.getElementById('notifications');
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.textContent = message;
        
        notifications.appendChild(notification);
        
        // 3秒後に自動削除
        setTimeout(() => {
            notification.remove();
        }, 3000);
    },
    
    // ローディングオーバーレイを表示
    showLoading: function() {
        document.getElementById('loading-overlay').style.display = 'flex';
    },
    
    // ローディングオーバーレイを非表示
    hideLoading: function() {
        document.getElementById('loading-overlay').style.display = 'none';
    },
    
    // API呼び出し
    apiCall: async function(url, options = {}) {
        const defaultOptions = {
            credentials: 'include',
            headers: {
                'Content-Type': 'application/json',
            },
        };
        
        const finalOptions = { ...defaultOptions, ...options };
        
        try {
            const response = await fetch(url, finalOptions);
            
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error('API呼び出しエラー:', error);
            throw error;
        }
    },
    
    // 日付をフォーマット
    formatDate: function(dateString) {
        if (!dateString) return '-';
        
        const date = new Date(dateString);
        return date.toLocaleString('ja-JP', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit'
        });
    },
    
    // ファイルサイズをフォーマット
    formatFileSize: function(bytes) {
        if (bytes === 0) return '0 Bytes';
        
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }
};

// 認証管理
const Auth = {
    // 認証トークン取得
    getAuthToken: function() {
        // セッションからトークンを取得するか、デフォルト値を返す
        return localStorage.getItem('auth_token') || 'admin-token';
    },
    
    // ログイン状態を確認
    checkAuth: async function() {
        try {
            const response = await Utils.apiCall('/api/user/profile');
            return response.data;
        } catch (error) {
            return null;
        }
    },
    
    // ログアウト
    logout: async function() {
        try {
            await Utils.apiCall('/api/auth/logout', { method: 'POST' });
            window.location.href = '/';
        } catch (error) {
            Utils.showNotification('ログアウトに失敗しました', 'error');
        }
    }
};

// ファイル管理
const FileManager = {
    // ファイル一覧を取得
    getFiles: async function() {
        try {
            const response = await Utils.apiCall('/api/files');
            return response.data;
        } catch (error) {
            Utils.showNotification('ファイル一覧の取得に失敗しました', 'error');
            return [];
        }
    },
    
    // ファイルをアップロード
    uploadFile: async function(file) {
        const formData = new FormData();
        formData.append('file', file);
        
        try {
            Utils.showLoading();
            const response = await fetch('/api/files/upload', {
                method: 'POST',
                credentials: 'include',
                body: formData
            });
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'アップロードに失敗しました');
            }
            
            const result = await response.json();
            Utils.showNotification('ファイルのアップロードが完了しました', 'success');
            return result.data;
        } catch (error) {
            Utils.showNotification(`アップロードエラー: ${error.message}`, 'error');
            throw error;
        } finally {
            Utils.hideLoading();
        }
    },
    
    // ファイルを削除
    deleteFile: async function(fileId) {
        if (!confirm('このファイルを削除しますか？')) {
            return false;
        }
        
        try {
            Utils.showLoading();
            await Utils.apiCall(`/api/files/${fileId}`, { method: 'DELETE' });
            Utils.showNotification('ファイルを削除しました', 'success');
            return true;
        } catch (error) {
            Utils.showNotification(`削除エラー: ${error.message}`, 'error');
            return false;
        } finally {
            Utils.hideLoading();
        }
    }
};

// チャット管理
const ChatManager = {
    // セッション一覧を取得
    getSessions: async function() {
        try {
            const response = await Utils.apiCall('/api/chat/sessions');
            return response.data;
        } catch (error) {
            Utils.showNotification('セッション一覧の取得に失敗しました', 'error');
            return [];
        }
    },
    
    // 新しいセッションを作成
    createSession: async function(title) {
        try {
            const response = await Utils.apiCall('/api/chat/sessions', {
                method: 'POST',
                body: JSON.stringify({ title })
            });
            return response.data;
        } catch (error) {
            Utils.showNotification('セッションの作成に失敗しました', 'error');
            throw error;
        }
    },
    
    // メッセージを送信
    sendMessage: async function(sessionId, message) {
        try {
            const response = await Utils.apiCall(`/api/chat/sessions/${sessionId}/messages`, {
                method: 'POST',
                body: JSON.stringify({ message })
            });
            return response.data;
        } catch (error) {
            Utils.showNotification('メッセージの送信に失敗しました', 'error');
            throw error;
        }
    },
    
    // メッセージ一覧を取得
    getMessages: async function(sessionId) {
        try {
            const response = await Utils.apiCall(`/api/chat/sessions/${sessionId}/messages`);
            return response.data;
        } catch (error) {
            Utils.showNotification('メッセージの取得に失敗しました', 'error');
            return [];
        }
    }
};

// ページ読み込み時の初期化
document.addEventListener('DOMContentLoaded', function() {
    console.log('新しいRAGシステムが読み込まれました');
    
    // グローバル関数として公開
    window.Utils = Utils;
    window.Auth = Auth;
    window.FileManager = FileManager;
    window.ChatManager = ChatManager;
});

// エラーハンドリング
window.addEventListener('error', function(event) {
    console.error('JavaScriptエラー:', event.error);
    Utils.showNotification('エラーが発生しました', 'error');
});

// 未処理のPromise拒否をキャッチ
window.addEventListener('unhandledrejection', function(event) {
    console.error('未処理のPromise拒否:', event.reason);
    Utils.showNotification('エラーが発生しました', 'error');
}); 