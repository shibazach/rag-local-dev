# BaseDataGridView 使い方マニュアル

## 概要

BaseDataGridViewは、Visual BasicのDataGridViewに相当する高機能なテーブルコンポーネントです。NiceGUIフレームワーク上で動作し、リアルタイムデータ更新、動的ページネーション、カスタムセルレンダリングなど、エンタープライズアプリケーションに必要な機能を提供します。

## 特徴

- **リアルタイムデータ更新**: データ変更時の自動再描画
- **動的ページネーション**: 画面サイズに応じた行数自動調整
- **カスタムセルレンダリング**: バッジ、ボタン、チェックボックスなど
- **レスポンシブデザイン**: 画面サイズ変更への自動対応
- **高パフォーマンス**: 大量データの効率的な処理
- **継承可能な設計**: カスタマイズと拡張が容易

## 基本的な使い方

### 1. インポート

```python
from app.ui.components.common import BaseDataGridView
```

### 2. 基本的な初期化

```python
# カラム定義
columns = [
    {
        'field': 'id',           # データのフィールド名
        'label': 'ID',           # 表示ラベル
        'width': '60px',         # 列幅（px, fr, %など）
        'align': 'center'        # 配置（left, center, right）
    },
    {
        'field': 'name',
        'label': '名前',
        'width': '1fr',          # 残り幅を自動調整
        'align': 'left'
    },
    {
        'field': 'status',
        'label': 'ステータス',
        'width': '100px',
        'align': 'center',
        'render_type': 'badge',  # カスタムレンダリング
        'badge_colors': {        # バッジの色定義
            'active': '#22c55e',
            'inactive': '#ef4444'
        }
    }
]

# グリッドの作成
grid = BaseDataGridView(
    columns=columns,
    height='400px',              # グリッドの高さ
    auto_rows=True,              # 自動行数調整
    default_rows_per_page=15,    # デフォルト表示行数
    header_color='#2196F3'       # カラムヘッダーの背景色（NiceGUIのprimaryボタンと同じ色）
)
```

### 3. データの設定

```python
# データリストの設定
data = [
    {'id': 1, 'name': '田中太郎', 'status': 'active'},
    {'id': 2, 'name': '佐藤花子', 'status': 'inactive'},
    {'id': 3, 'name': '鈴木一郎', 'status': 'active'},
    # ... 更に多くのデータ
]

grid.set_data(data)
```

### 4. レンダリング

```python
# NiceGUIのコンテキスト内でレンダリング
with ui.column():
    grid.render()
```

## 高度な機能

### カラムヘッダーの色設定

BaseDataGridViewでは `header_color` パラメータでカラムヘッダーの背景色をカスタマイズできます：

```python
# NiceGUIのprimaryボタンと同じ色に統一
grid = BaseDataGridView(
    columns=columns,
    header_color='#2196F3'  # Material Blue 500
)

# その他の色の例
grid = BaseDataGridView(
    columns=columns,
    header_color='#1976d2'  # Material Blue 700（Quasarデフォルト）
)

grid = BaseDataGridView(
    columns=columns,
    header_color='#4caf50'  # Material Green 500
)
```

**色の統一のベストプラクティス:**
- chat.pyの「検索実行」ボタンと同じ色: `#2196F3`
- 共通ボタンAと統一する場合: `#2563eb`（blue-600）
- カスタムブランドカラーと合わせる場合: 各プロジェクトの設計に従う

### NiceGUIコンポーネントとの高さ統一

BaseDataGridViewと同じページでNiceGUIのselect/inputコンポーネントを使用する場合、高さを統一できます：

```python
# ステータスフィルター（ラベルなしで高さ統一）
status_select = ui.select(
    options=['すべてのステータス', '未処理', '処理中', '処理完了'],
    value='すべてのステータス'
).style('width: 200px; height: 32px; min-height: 32px; flex-shrink: 0;').props('outlined dense')

# 検索ボックス（レスポンシブ幅、高さ統一）
search_input = ui.input(
    placeholder='ファイル名で検索...'
).style('flex: 1; min-width: 120px; height: 32px; min-height: 32px;').props('outlined dense')
```

**高さ統一のポイント:**
- `height: 32px; min-height: 32px;` で一貫した高さを設定
- `props('outlined dense')` でコンパクトな表示
- ラベルを削除してヘッダーエリアの高さを節約
- `align-items: center` でパネルヘッダー内での垂直センタリング

### カスタムセルレンダリング

BaseDataGridViewは3種類のカスタムレンダリングをサポート：

#### 1. バッジ（Badge）
```python
{
    'field': 'status',
    'label': 'ステータス',
    'render_type': 'badge',
    'badge_colors': {
        'active': '#22c55e',    # 緑
        'pending': '#f59e0b',   # オレンジ
        'inactive': '#ef4444'   # 赤
    }
}
```

#### 2. ボタン（Button）
```python
{
    'field': 'action',
    'label': 'アクション',
    'render_type': 'button',
    'button_color': 'primary'   # NiceGUIのカラーテーマ
}
```

#### 3. チェックボックス（Checkbox）
```python
{
    'field': 'selected',
    'label': '選択',
    'render_type': 'checkbox'
}
```

### イベントハンドリング

```python
# ページ変更イベント
def on_page_change(page_info):
    print(f"ページが{page_info['new_page']}に変更されました")

# セルクリックイベント
def on_cell_click(cell_info):
    print(f"セル clicked: {cell_info['field']} = {cell_info['value']}")

grid = BaseDataGridView(
    columns=columns,
    on_page_change=on_page_change,
    on_cell_click=on_cell_click
)
```

### 動的データ更新

```python
# 行の追加
grid.add_row({'id': 10, 'name': '新規ユーザー', 'status': 'active'})

# データの更新
new_data = [...新しいデータリスト...]
grid.update_data(new_data)

# 特定ページへの移動
grid.go_to_page(3)

# データのクリア
grid.clear_data()
```

### 自動行数調整

```python
grid = BaseDataGridView(
    columns=columns,
    height='100%',           # 親要素の高さに合わせる
    auto_rows=True,          # 自動行数調整を有効化
    min_rows=5,              # 最小表示行数
    max_rows=50,             # 最大表示行数
    enable_resize_observer=True  # ResizeObserver有効化
)
```

## カスタムスタイル

```python
grid = BaseDataGridView(
    columns=columns,
    header_color='#2563eb',      # ヘッダー背景色
    row_hover_color='#f8f9fa'    # 行ホバー色
)
```

## 実装例

### 1. ユーザー管理テーブル

```python
def create_user_management_grid():
    columns = [
        {'field': 'id', 'label': 'ID', 'width': '60px', 'align': 'center'},
        {'field': 'username', 'label': 'ユーザー名', 'width': '150px'},
        {'field': 'email', 'label': 'メールアドレス', 'width': '2fr'},
        {'field': 'role', 'label': '権限', 'width': '100px', 'align': 'center',
         'render_type': 'badge',
         'badge_colors': {
             'admin': '#dc2626',
             'user': '#3b82f6',
             'guest': '#6b7280'
         }},
        {'field': 'active', 'label': '有効', 'width': '60px', 'align': 'center',
         'render_type': 'checkbox'},
        {'field': 'action', 'label': '操作', 'width': '80px', 'align': 'center',
         'render_type': 'button', 'button_color': 'primary'}
    ]
    
    grid = BaseDataGridView(
        columns=columns,
        height='500px',
        default_rows_per_page=20
    )
    
    # サンプルデータ
    users = [
        {'id': 1, 'username': 'admin', 'email': 'admin@example.com', 
         'role': 'admin', 'active': True, 'action': '編集'},
        # ... 更に多くのユーザー
    ]
    
    grid.set_data(users)
    return grid
```

### 2. 検索結果テーブル

```python
def create_search_results_grid():
    columns = [
        {'field': 'filename', 'label': 'ファイル名', 'width': '2fr'},
        {'field': 'relevance', 'label': '関連度', 'width': '100px', 
         'align': 'center', 'render_type': 'badge',
         'badge_colors': {
             '高': '#22c55e',
             '中': '#f59e0b',
             '低': '#6b7280'
         }},
        {'field': 'size', 'label': 'サイズ', 'width': '100px', 'align': 'right'},
        {'field': 'modified', 'label': '更新日時', 'width': '150px'},
        {'field': 'preview', 'label': 'プレビュー', 'width': '80px', 
         'align': 'center', 'render_type': 'button'}
    ]
    
    return BaseDataGridView(
        columns=columns,
        height='calc(100vh - 200px)',  # 動的高さ計算
        auto_rows=True
    )
```

## トラブルシューティング

### 問題: データが表示されない
- `render()`メソッドを呼び出しているか確認
- データ形式が正しいか確認（辞書のリスト）
- カラムの`field`名がデータのキーと一致しているか確認

### 問題: 自動行数調整が機能しない
- 親要素に明確な高さが設定されているか確認
- `auto_rows=True`が設定されているか確認
- `enable_resize_observer=True`を試す

### 問題: カスタムレンダリングが適用されない
- `render_type`が正しく設定されているか確認
- 必要な追加パラメータ（`badge_colors`など）が設定されているか確認

## ベストプラクティス

1. **パフォーマンス最適化**
   - 大量データの場合は、ページネーションを活用
   - 不要な再描画を避けるため、データ更新は一括で実行

2. **アクセシビリティ**
   - 重要な操作にはキーボードショートカットを設定
   - 色だけでなくテキストでも状態を表現

3. **レスポンシブデザイン**
   - `fr`単位を使用して柔軟な列幅を設定
   - モバイルでは列数を減らすことを検討

4. **データ管理**
   - データの一意性を保証するため、各行にIDを設定
   - データ更新時は`update_data()`を使用して一括更新

## 継承とカスタマイズ

BaseDataGridViewは継承可能な設計になっています：

```python
class CustomDataGrid(BaseDataGridView):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # カスタム初期化
    
    def _render_cell(self, row, col):
        # カスタムセルレンダリング
        if col.get('render_type') == 'custom':
            self._render_custom_cell(row, col)
        else:
            super()._render_cell(row, col)
    
    def _render_custom_cell(self, row, col):
        # 独自のレンダリングロジック
        pass
```

## まとめ

BaseDataGridViewは、エンタープライズアプリケーションに必要な高度なテーブル機能を提供します。基本的な使用法から高度なカスタマイズまで、幅広いニーズに対応できる設計となっています。

このマニュアルを参考に、効果的なデータ表示UIを構築してください。