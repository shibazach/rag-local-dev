# 🏗️ FastAPI+NiceGUI完全統合アーキテクチャ設計書

**作成日**: 2024-12-19  
**プロジェクト**: R&D RAGシステム  
**方針**: FastAPI+NiceGUI完全統合による企業レベルシステム構築

---

## 📋 **設計方針**

### **基本原則**
1. **共通コンポーネント化最優先**: 最初から再利用可能な設計
2. **型安全性重視**: Pydantic + Python型ヒント完全活用
3. **認証統合**: FastAPI認証システムとNiceGUI完全統合
4. **段階的構築**: 確実に動作する基盤から機能追加

### **技術スタック確定**
- **バックエンド**: FastAPI (Python 3.9+)
- **UI**: NiceGUI (最新安定版)
- **認証**: FastAPI Dependencies + Sessions
- **データベース**: SQLite/PostgreSQL (SQLAlchemy)
- **型定義**: Pydantic v2

---

## 🏗️ **アーキテクチャ構成**

### **ディレクトリ構造**
```
nicegui_app/
├── main.py                 # FastAPI+NiceGUI統合エントリーポイント
├── config/
│   ├── __init__.py
│   ├── settings.py         # Pydantic設定管理
│   └── database.py         # データベース設定
├── auth/
│   ├── __init__.py
│   ├── models.py           # 認証関連モデル
│   ├── dependencies.py     # FastAPI認証依存関数
│   └── handlers.py         # 認証ハンドラー
├── components/
│   ├── __init__.py
│   ├── base.py             # 基底コンポーネント
│   ├── layout.py           # レイアウトコンポーネント
│   ├── forms.py            # フォーム関連コンポーネント
│   ├── tables.py           # テーブル・リスト関連
│   └── navigation.py       # ナビゲーション関連
├── pages/
│   ├── __init__.py
│   ├── dashboard.py        # ダッシュボード
│   ├── data_registration.py # データ登録
│   ├── chat.py             # チャット
│   ├── file_management.py  # ファイル管理
│   └── ocr_comparison.py   # OCR比較
├── models/
│   ├── __init__.py
│   ├── user.py             # ユーザーモデル
│   ├── file.py             # ファイルモデル
│   └── processing.py       # 処理関連モデル
└── services/
    ├── __init__.py
    ├── file_service.py     # ファイル処理サービス
    ├── chat_service.py     # チャット・検索サービス
    └── ocr_service.py      # OCR処理サービス
```

### **統合アーキテクチャ**
```python
# 統合パターン
@ui.page('/protected-page')
async def protected_page(user: User = Depends(get_current_user)):
    """認証済みユーザーのみアクセス可能なページ"""
    
    with PageLayout(user=user, title="ページ名"):
        # 共通コンポーネント使用
        with ui.row():
            FileUploadComponent(user_id=user.id)
            ProcessingStatusComponent(user_id=user.id)
```

---

## 🧩 **共通コンポーネント体系**

### **1. 基底コンポーネント (base.py)**
```python
class RAGComponent:
    """全コンポーネントの基底クラス"""
    def __init__(self, user: User = None):
        self.user = user
        self.element = None
    
    def render(self) -> ui.element:
        """コンポーネントをレンダリング"""
        raise NotImplementedError
    
    def update(self, data: Any) -> None:
        """コンポーネント状態更新"""
        pass
```

### **2. レイアウトコンポーネント (layout.py)**
```python
class PageLayout:
    """統一ページレイアウト"""
    def __init__(self, user: User, title: str, breadcrumbs: List[str] = None):
        self.user = user
        self.title = title
        self.breadcrumbs = breadcrumbs or []
    
    def __enter__(self):
        # ヘッダー・サイドバー・メインエリア構築
        return self
    
    def __exit__(self, *args):
        # フッター・クリーンアップ
        pass

class NavigationSidebar:
    """統一サイドバーナビゲーション"""
    def __init__(self, user: User, current_page: str):
        self.user = user
        self.current_page = current_page
```

### **3. フォームコンポーネント (forms.py)**
```python
class RAGForm:
    """統一フォームコンポーネント"""
    def __init__(self, schema: Type[BaseModel]):
        self.schema = schema
        self.data = {}
    
    def render_field(self, field_name: str, field_info: FieldInfo):
        """フィールド型に応じた入力コンポーネント生成"""
        pass
    
    def validate(self) -> Tuple[bool, Dict[str, str]]:
        """Pydanticバリデーション実行"""
        pass

class FileUploadComponent:
    """ファイルアップロード専用コンポーネント"""
    def __init__(self, user_id: int, accepted_types: List[str]):
        self.user_id = user_id
        self.accepted_types = accepted_types
```

### **4. データ表示コンポーネント (tables.py)**
```python
class RAGTable:
    """統一テーブルコンポーネント"""
    def __init__(self, 
                 data: List[BaseModel], 
                 columns: List[str],
                 actions: List[Callable] = None):
        self.data = data
        self.columns = columns
        self.actions = actions or []
    
    def render(self) -> ui.table:
        """ページング・ソート・フィルタ付きテーブル"""
        pass

class ProcessingStatusComponent:
    """処理状況表示コンポーネント"""
    def __init__(self, user_id: int):
        self.user_id = user_id
    
    @ui.refreshable
    def status_display(self):
        """リアルタイム処理状況更新"""
        pass
```

---

## 🔐 **認証統合システム**

### **FastAPI Dependencies統合**
```python
# auth/dependencies.py
async def get_current_user(request: Request) -> User:
    """FastAPI依存関数 - NiceGUIページで使用可能"""
    session_id = request.cookies.get("session_id")
    if not session_id:
        raise HTTPException(status_code=401)
    
    user = await get_user_by_session(session_id)
    if not user:
        raise HTTPException(status_code=401)
    
    return user

# ページでの使用
@ui.page('/dashboard')
async def dashboard(user: User = Depends(get_current_user)):
    """認証必須ダッシュボード"""
    with PageLayout(user=user, title="ダッシュボード"):
        # ユーザー情報を活用したUI構築
        pass
```

### **権限制御システム**
```python
class Permission(Enum):
    READ_FILES = "read_files"
    UPLOAD_FILES = "upload_files"
    ADMIN_ACCESS = "admin_access"

def require_permission(permission: Permission):
    """権限チェックデコレータ"""
    def decorator(func):
        async def wrapper(user: User = Depends(get_current_user)):
            if not user.has_permission(permission):
                raise HTTPException(status_code=403)
            return await func(user)
        return wrapper
    return decorator
```

---

## 📊 **データフロー設計**

### **リアルタイム更新パターン**
```python
class ProcessingManager:
    """ファイル処理管理"""
    def __init__(self):
        self.active_processes = {}
    
    async def start_processing(self, file_id: int, user_id: int):
        """処理開始 - UI自動更新"""
        process = FileProcessingTask(file_id, user_id)
        self.active_processes[file_id] = process
        
        # NiceGUIリアルタイム更新
        await self.notify_ui_update(user_id, process.status)
    
    async def notify_ui_update(self, user_id: int, status: ProcessingStatus):
        """UI状態更新通知"""
        # WebSocket経由でリアルタイム更新
        pass
```

---

## 🎯 **実装フェーズ**

### **Phase 1: 基盤構築**
1. FastAPI+NiceGUI統合基盤
2. 認証システム統合
3. 基底コンポーネント実装
4. PageLayoutコンポーネント

### **Phase 2: 基本ページ**
1. ダッシュボードページ（コントロールなし）
2. ログインページ
3. 基本ナビゲーション
4. エラーハンドリング

### **Phase 3: データ関連ページ**
1. データ登録ページ基本構造
2. ファイル管理ページ基本構造
3. チャットページ基本構造
4. OCR比較ページ基本構造

### **Phase 4: 機能実装**
1. ファイルアップロードコンポーネント
2. テーブル・リストコンポーネント
3. フォーム・バリデーション
4. リアルタイム更新システム

---

## 📝 **品質保証**

### **型安全性**
- 全コンポーネントでPydantic型定義必須
- mypy静的型チェック通過必須
- FastAPI自動API文書生成活用

### **テスタビリティ**
- コンポーネント単体テスト可能設計
- モックデータ活用テスト環境
- E2Eテスト考慮設計

### **保守性**
- 共通コンポーネント最優先
- DRY原則徹底
- 文書化とコメント充実

---

**次のステップ**: Phase 1基盤構築開始