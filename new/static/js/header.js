// 共通ヘッダーJavaScript

// ページ読み込み時に実行
document.addEventListener('DOMContentLoaded', function() {
    initializeHeader();
});

// ヘッダー初期化
function initializeHeader() {
    setActiveNavigation();
    checkAuthStatus();
    setupEventListeners();
}

// 現在のページに応じてナビゲーションをアクティブにする
function setActiveNavigation() {
    const currentPath = window.location.pathname;
    const navItems = document.querySelectorAll('.nav-item');
    
    navItems.forEach(item => {
        item.classList.remove('active');
        const href = item.getAttribute('href');
        
        // 正確なパス一致またはルートパス処理
        if (href === currentPath || 
            (currentPath === '/' && href === '/') ||
            (currentPath.startsWith('/files') && href === '/files') ||
            (currentPath.startsWith('/chat') && href === '/chat') ||
            (currentPath.startsWith('/upload') && href === '/upload') ||
            (currentPath.startsWith('/ocr-comparison') && href === '/ocr-comparison') ||
            (currentPath.startsWith('/data-registration') && href === '/data-registration') ||
            (currentPath.startsWith('/admin') && href === '/admin')) {
            item.classList.add('active');
        }
    });
}

// 認証状態の確認
async function checkAuthStatus() {
    try {
        const response = await fetch('/api/user/profile', {
            credentials: 'include'
        });
        
        if (response.ok) {
            const data = await response.json();
            showAuthenticatedState(data.data);
        } else {
            showUnauthenticatedState();
        }
    } catch (error) {
        console.error('認証状態確認エラー:', error);
        showUnauthenticatedState();
    }
}

// 認証済み状態の表示
function showAuthenticatedState(userData) {
    const userInfo = document.getElementById('user-info');
    const loginLink = document.getElementById('login-link');
    const username = document.getElementById('username');
    
    if (userInfo && loginLink && username) {
        username.textContent = userData.username;
        userInfo.style.display = 'flex';
        loginLink.style.display = 'none';
        
        // 管理者権限に応じてナビゲーションを表示
        updateNavigationByRole(userData.role);
    }
}

// 未認証状態の表示
function showUnauthenticatedState() {
    const userInfo = document.getElementById('user-info');
    const loginLink = document.getElementById('login-link');
    
    if (userInfo && loginLink) {
        userInfo.style.display = 'none';
        loginLink.style.display = 'block';
        
        // 未認証時は管理者ナビゲーションを非表示
        hideAdminNavigation();
    }
}

// ユーザー権限に応じてナビゲーションを更新
function updateNavigationByRole(role) {
    const adminNavItems = document.querySelectorAll('.nav-admin-only');
    
    if (role === 'admin') {
        adminNavItems.forEach(item => {
            item.style.display = 'flex';
        });
    } else {
        hideAdminNavigation();
    }
}

// 管理者ナビゲーションを非表示
function hideAdminNavigation() {
    const adminNavItems = document.querySelectorAll('.nav-admin-only');
    adminNavItems.forEach(item => {
        item.style.display = 'none';
    });
}

// イベントリスナーの設定
function setupEventListeners() {
    const logoutBtn = document.getElementById('logout-btn');
    
    if (logoutBtn) {
        logoutBtn.addEventListener('click', handleLogout);
    }
}

// ログアウト処理
async function handleLogout() {
    try {
        const response = await fetch('/api/auth/logout', {
            method: 'POST',
            credentials: 'include'
        });
        
        if (response.ok) {
            window.location.href = '/login';
        } else {
            console.error('ログアウトに失敗しました');
        }
    } catch (error) {
        console.error('ログアウトエラー:', error);
    }
} 