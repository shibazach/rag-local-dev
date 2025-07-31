# 🔐 認証システム対応ガイド

## 📋 **根本原因と解決策**

### 🚨 **発生していた問題**
```
AttributeError: 'dict' object has no attribute 'role'
at routes/ui.py: if not user or user.role != 'admin':
```

### ✅ **解決方法**
1. **型不整合修正**: `user.role` → `user.get('role')`
2. **統一化ユーティリティ作成**: `auth_utils.py`
3. **テンプレート化**: 新規ページ追加プロセスの標準化

## 🔧 **認証システム構成**

### **core認証モジュール (auth.py)**
```python
def get_optional_user(request):
    """辞書形式でユーザー情報を返す"""
    return {
        "username": "admin",
        "role": "admin", 
        "is_active": True
    }
```

### **統一化ユーティリティ (auth_utils.py)**
```python
def require_login(request: Request):
    """ログイン必須チェック"""
    
def require_admin(request: Request):
    """admin権限必須チェック"""
    
def is_admin_user(user):
    """admin権限判定"""
```

## 📝 **正しい使用方法**

### ❌ **間違った書き方**
```python
user = get_optional_user(request)
if not user or user.role != 'admin':  # AttributeError!
    return RedirectResponse(url="/login")
```

### ✅ **正しい書き方**
```python
# 方法1: 統一化ユーティリティ使用（推奨）
auth_result = require_admin(request)
if isinstance(auth_result, RedirectResponse):
    return auth_result

# 方法2: 直接辞書アクセス
user = get_optional_user(request)
if not user or user.get('role') != 'admin':
    return RedirectResponse(url="/login")
```

## 🎯 **新規ページ追加での認証実装パターン**

### **パターン1: ログイン必須**
```python
@router.get("/new-page", response_class=HTMLResponse)
async def new_page(request: Request):
    auth_result = require_login(request)
    if isinstance(auth_result, RedirectResponse):
        return auth_result
    return templates.TemplateResponse("new_page.html", {"request": request})
```

### **パターン2: admin権限必須**
```python
@router.get("/admin-page", response_class=HTMLResponse) 
async def admin_page(request: Request):
    auth_result = require_admin(request)
    if isinstance(auth_result, RedirectResponse):
        return auth_result
    return templates.TemplateResponse("admin_page.html", {"request": request})
```

### **パターン3: 認証不要**
```python
@router.get("/public-page", response_class=HTMLResponse)
async def public_page(request: Request):
    return templates.TemplateResponse("public_page.html", {"request": request})
```

## 🚨 **絶対に避けるべき書き方**

```python
# ❌ これらは全てエラーになる
user.role                    # AttributeError
user['role']                 # KeyError の可能性
if user.role == 'admin':     # AttributeError
user.username               # AttributeError

# ✅ 安全な書き方
user.get('role')            # None を返す安全なアクセス
user.get('username', '')    # デフォルト値付き
```

## 🔄 **移行・修正プロセス**

### **段階1: 緊急修正**
- 全ての `user.role` を `user.get('role')` に置換

### **段階2: 統一化実装**
- `auth_utils.py` 作成
- 統一された認証関数の実装

### **段階3: 既存コード移行**
- 既存ルートを統一化ユーティリティに移行
- 重複したロジックの削除

### **段階4: テンプレート化**
- 新規ページ追加のテンプレート作成
- ドキュメント化

## 📊 **実装状況チェックリスト**

- [x] `user.role` → `user.get('role')` 全箇所修正
- [x] `auth_utils.py` 作成完了
- [x] 全UIルートの統一化完了
- [x] テンプレート・ガイド作成完了
- [ ] APIルートの統一化 (必要に応じて)
- [ ] テストケース追加 (必要に応じて)

## 🎯 **今後の対応方針**

1. **新規ページ作成時**: 必ずテンプレートに従う
2. **認証変更時**: `auth_utils.py` のみ修正
3. **権限追加時**: 新しい関数を `auth_utils.py` に追加
4. **コードレビュー**: 認証関連は必ずチェック

---
**このガイドに従うことで、認証関連のエラーを完全に防止できます。**