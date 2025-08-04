# 🧩 共通コンポーネントシステム設計書

**作成日**: 2024-12-19  
**プロジェクト**: FastAPI+NiceGUI統合R&D RAGシステム  
**目的**: 一貫性のある再利用可能コンポーネント体系構築

---

## 🎯 **コンポーネント設計原則**

### **1. 統一性**
- 全コンポーネントで一貫したAPI設計
- 統一されたスタイリング・色使い
- 共通の命名規則・パターン

### **2. 再利用性**
- プロジェクト全体で使い回し可能
- 設定可能なパラメータ化
- 柔軟なカスタマイズ対応

### **3. 型安全性**
- Pydanticモデル活用
- Python型ヒント完全対応
- 実行時エラーの事前防止

---

## 🏗️ **コンポーネント階層**

```
RAGComponent (基底クラス)
├── PageLayout (ページ全体レイアウト)
├── NavigationSidebar (ナビゲーション)
├── RAGForm (フォーム関連)
│   ├── FileUploadComponent
│   ├── SettingsForm
│   └── SearchForm
├── RAGTable (データ表示)
│   ├── FileListTable
│   ├── ProcessingStatusTable
│   └── SearchResultsTable
└── StatusComponent (状況表示)
    ├── ProcessingStatusComponent
    ├── StatisticsCard
    └── NotificationArea
```

---

## 🔧 **基底コンポーネント (RAGComponent)**

### **共通機能**
```python
class RAGComponent:
    def __init__(self, user: Optional[User] = None)
    def render(self) -> ui.element  # 必須実装
    def update(self, data: Any) -> None
    def has_permission(self, permission: str) -> bool
    def require_permission(self, permission: str) -> bool
```

### **権限管理統合**
- ユーザー権限の自動チェック
- 権限不足時の適切なフィードバック
- 管理者・一般ユーザーの動的UI切り替え

---

## 🖼️ **レイアウトコンポーネント**

### **PageLayout**
```python
with PageLayout(user=user, title="ページ名"):
    # メインコンテンツ
    pass
```

**機能**:
- 統一ヘッダー・フッター・サイドバー
- 認証状態に応じた動的ナビゲーション
- ブレッドクラム・ページタイトル管理
- レスポンシブ対応

### **NavigationSidebar**
- 権限ベースメニュー表示
- 現在ページのハイライト
- アイコン・ラベル統一

---

## 📝 **フォームコンポーネント**

### **RAGForm**
```python
form = RAGForm(schema=UserCreate)
form.render()
is_valid, errors = form.validate()
data = form.get_data()
```

**特徴**:
- Pydanticスキーマ自動フォーム生成
- リアルタイムバリデーション
- エラー表示・フィールドハイライト
- 型安全なデータ取得

### **FileUploadComponent**
```python
upload = FileUploadComponent(
    user_id=user.id,
    accepted_types=['.pdf', '.docx'],
    max_size=100*1024*1024
)
```

**機能**:
- ドラッグ&ドロップ対応
- ファイル形式・サイズ検証
- アップロード進捗表示
- 複数ファイル管理

---

## 📊 **テーブル・データ表示コンポーネント**

### **RAGTable**
```python
table = RAGTable(
    data=file_list,
    columns=[
        {'name': 'name', 'label': 'ファイル名', 'field': 'name'},
        {'name': 'size', 'label': 'サイズ', 'field': 'size'}
    ],
    actions=[
        {'label': '表示', 'icon': 'visibility', 'handler': view_file},
        {'label': '削除', 'icon': 'delete', 'handler': delete_file}
    ]
)
```

**機能**:
- 自動ページング・ソート・フィルタ
- カスタムアクションボタン
- レスポンシブ表示
- データ更新・リアルタイム同期

### **ProcessingStatusComponent**
```python
status = ProcessingStatusComponent(user_id=user.id)
status.update_status({
    'current_file': 'document.pdf',
    'progress': 0.7,
    'total_files': 10,
    'completed_files': 7
})
```

**機能**:
- リアルタイム処理状況表示
- プログレスバー・統計情報
- ログエントリ管理
- 自動更新タイマー

---

## 🎨 **スタイル・デザイン統一**

### **色彩システム**
```python
COLORS = {
    'primary': 'blue',      # メインアクション
    'positive': 'green',    # 成功・完了
    'warning': 'orange',    # 注意・処理中  
    'negative': 'red',      # エラー・削除
    'info': 'cyan',         # 情報表示
    'grey': 'grey'          # 無効・背景
}
```

### **アイコン統一**
```python
ICONS = {
    'dashboard': 'dashboard',
    'upload': 'upload',
    'chat': 'chat',
    'files': 'folder',
    'search': 'search',
    'user': 'person',
    'settings': 'settings',
    'logout': 'logout'
}
```

### **サイズ・間隔**
- カード間隔: `gap-4` (16px)
- パディング: `p-4` (16px)  
- マージン: `mb-4` (16px)
- ボタンサイズ: `size=lg` (大), デフォルト (中), `size=sm` (小)

---

## 🔄 **データフロー・状態管理**

### **リアクティブ更新**
```python
@ui.refreshable
def dynamic_content():
    # データ変更時自動更新
    data = get_latest_data()
    render_data(data)

# データ更新時
dynamic_content.refresh()
```

### **コンポーネント間通信**
```python
# 親から子へのデータ渡し
component.update(new_data)

# 子から親への通知
component.on_change(callback_function)
```

---

## 📋 **実装済みコンポーネント一覧**

### ✅ **完了**
1. **RAGComponent** - 基底クラス
2. **PageLayout** - 統一レイアウト
3. **NavigationSidebar** - ナビゲーション
4. **RAGForm** - 動的フォーム生成
5. **FileUploadComponent** - ファイルアップロード
6. **RAGTable** - データテーブル
7. **ProcessingStatusComponent** - 処理状況表示

### 🔄 **今後実装予定**
1. **SearchComponent** - 検索フォーム
2. **ChatComponent** - チャット UI
3. **ModalDialog** - モーダル・ダイアログ
4. **NotificationSystem** - 通知システム
5. **ProgressTracker** - 進捗追跡
6. **DataVisualization** - データ可視化

---

## 💡 **使用例**

### **典型的なページ構成**
```python
async def render_data_page(user: User):
    with PageLayout(user=user, title="データ管理"):
        # フォーム部分
        with ui.row():
            upload = FileUploadComponent(user_id=user.id)
            upload.render()
        
        # テーブル部分  
        table = RAGTable(
            data=get_user_files(user.id),
            columns=FILE_COLUMNS,
            actions=FILE_ACTIONS
        )
        table.render()
        
        # ステータス部分
        status = ProcessingStatusComponent(user_id=user.id)
        status.render()
```

---

## 🎯 **今後の拡張方針**

1. **テーマシステム**: ダーク・ライトモード対応
2. **国際化**: 多言語対応基盤
3. **アクセシビリティ**: WAI-ARIA対応
4. **パフォーマンス**: 仮想化・遅延読み込み
5. **テスト**: コンポーネント単体テスト