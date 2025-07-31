# 🚀 新規UIページ追加テンプレート

## 📋 **必須チェックリスト**

### 1. **ルーター登録 (routes/ui.py)**
```python
from auth_utils import require_login, require_admin  # 必須インポート

# ログイン必須ページの場合
@router.get("/new-page", response_class=HTMLResponse)
async def new_page(request: Request):
    """新規ページ（認証必要）"""
    auth_result = require_login(request)
    if isinstance(auth_result, RedirectResponse):
        return auth_result
    return templates.TemplateResponse("new_page.html", {"request": request})

# admin権限必須ページの場合
@router.get("/admin-page", response_class=HTMLResponse)
async def admin_page(request: Request):
    """新規管理ページ（admin権限必要）"""
    auth_result = require_admin(request)
    if isinstance(auth_result, RedirectResponse):
        return auth_result
    return templates.TemplateResponse("admin_page.html", {"request": request})

# 認証不要ページの場合
@router.get("/public-page", response_class=HTMLResponse)
async def public_page(request: Request):
    """公開ページ（認証不要）"""
    return templates.TemplateResponse("public_page.html", {"request": request})
```

### 2. **テンプレート作成 (templates/)**
```html
{% extends "base_new.html" %}  <!-- 必須: 新システム用ベース -->
{% block extra_css %}
<link rel="stylesheet" href="{{ url_for('static', path='css/new_page.css') }}">
{% endblock %}
{% block content %}
<div class="page-container">
    <div class="page-header">
        <div class="page-title">
            <h1>📊 新規ページ</h1>
            <p class="page-description">ページの説明</p>
        </div>
    </div>
    <!-- メインコンテンツ -->
</div>
{% endblock %}
```

### 3. **CSS作成 (static/css/)**
- `static/css/new_page.css` を作成
- `main.css` の共通スタイルを活用
- ページ固有のスタイルのみ定義

### 4. **JavaScript作成 (static/js/)** ※必要に応じて
- `static/js/new_page.js` を作成
- 共通関数は `main.js` から利用

### 5. **ナビゲーション更新**
#### A. **templates/components/header.html**
```html
<a href="/new-page" class="nav-item nav-admin-only" data-page="new-page" style="display: none;">
    <span class="nav-icon">📊</span>
    <span class="nav-text">新規ページ</span>
</a>
```

#### B. **templates/base.html** (旧テンプレート対応)
同様のメニュー項目を追加

#### C. **templates/index.html** (ホーム画面のメニューグリッド)
```html
<a href="/new-page" class="menu-item admin-only" style="display: none;">
    <div class="menu-icon">📊</div>
    <div class="menu-title">新規ページ</div>
    <div class="menu-description">ページの説明</div>
</a>
```

### 6. **JavaScript ナビゲーション更新**
#### **static/js/header.js**
```javascript
function setActiveNavigation(currentPath) {
    // 既存のケース
    case '/new-page':
        activeItem = 'new-page';
        break;
}
```

## ⚠️ **注意事項**

### 認証処理
- **絶対に手動で認証チェックを書かない**
- 必ず `auth_utils.py` の関数を使用
- `user.role` は使用禁止 → `user.get('role')` を使用

### テンプレート
- `{% extends "base.html" %}` は使用禁止
- 必ず `{% extends "base_new.html" %}` を使用

### エラーページ更新
- `templates/404.html` 
- `templates/500.html`
- 両方とも `base_new.html` を継承していることを確認

## 🔄 **作業フロー**

1. **ルーター作成** → `routes/ui.py` に追加
2. **テンプレート作成** → `templates/` に配置
3. **スタイル作成** → `static/css/` に配置
4. **ナビゲーション更新** → 3箇所すべて更新
5. **動作確認** → サーバー再起動してテスト

## 🚨 **絶対に避けるべき問題**

- `AttributeError: 'dict' object has no attribute 'role'`
- `ImportError: cannot import name` 
- `404 Not Found` for new routes
- `500 Internal Server Error` on auth check

## 📝 **デバッグ用チェックコマンド**

```bash
# ルート登録確認
curl -s "http://localhost:8000/openapi.json" | grep "new-page"

# ページアクセス確認
curl -I "http://localhost:8000/new-page"

# テンプレート存在確認
ls -la templates/new_page.html
```

---
**このテンプレートに従うことで、同じエラーの再発を防止できます。**