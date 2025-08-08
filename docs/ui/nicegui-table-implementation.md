# NiceGUI ui.table実装例

## 概要

`app/ui/pages/arrangement_test_tab_e.py`の2つ目のパネルに、files.pyの左ペインテーブルをNiceGUIのui.tableで再実装しました。

## 実装のポイント

### 1. テーブル基本構造

```python
columns = [
    {'name': 'select', 'label': '', 'field': 'select', 'sortable': False, 'align': 'center'},
    {'name': 'filename', 'label': 'ファイル名', 'field': 'filename', 'sortable': True, 'align': 'left'},
    {'name': 'size', 'label': 'サイズ', 'field': 'size', 'sortable': True, 'align': 'center'},
    {'name': 'status', 'label': 'ステータス', 'field': 'status', 'sortable': True, 'align': 'center'},
    {'name': 'created_at', 'label': '作成日時', 'field': 'created_at', 'sortable': True, 'align': 'center'},
    {'name': 'actions', 'label': '操作', 'field': 'actions', 'sortable': False, 'align': 'center'}
]

self.file_table = ui.table(
    columns=columns,
    rows=rows,
    row_key='id',
    pagination={'rowsPerPage': 10, 'sortBy': 'created_at', 'descending': True}
)
```

### 2. チェックボックス列の実装

Vue.jsのスロットを使用してカスタムレンダリング：

```python
self.file_table.add_slot('body-cell-select', '''
    <template v-slot:body-cell-select="props">
        <q-td :props="props">
            <q-checkbox v-model="props.row.selected" 
                        @input="$parent.$emit('selection-change', props.row)"
                        dense />
        </q-td>
    </template>
''')
```

### 3. ステータス列のバッジ表示

Quasarのq-badgeコンポーネントを使用：

```python
self.file_table.add_slot('body-cell-status', '''
    <template v-slot:body-cell-status="props">
        <q-td :props="props">
            <q-badge :color="getStatusColor(props.value)" 
                     :label="props.value" 
                     style="padding: 4px 8px;" />
        </q-td>
    </template>
''')
```

### 4. 操作列のアイコンボタン

Quasarのq-btnコンポーネントでアイコンボタンを実装：

```python
self.file_table.add_slot('body-cell-actions', '''
    <template v-slot:body-cell-actions="props">
        <q-td :props="props">
            <div style="display: flex; gap: 4px; justify-content: center;">
                <q-btn flat round dense icon="visibility" size="sm"
                       @click="$parent.$emit('preview', props.row)">
                    <q-tooltip>プレビュー</q-tooltip>
                </q-btn>
                <q-btn flat round dense icon="info" size="sm"
                       @click="$parent.$emit('info', props.row)">
                    <q-tooltip>詳細情報</q-tooltip>
                </q-btn>
                <q-btn flat round dense icon="delete" size="sm"
                       @click="$parent.$emit('delete', props.row)">
                    <q-tooltip>削除</q-tooltip>
                </q-btn>
            </div>
        </q-td>
    </template>
''')
```

## 実装上の利点

1. **カラム境界の問題解決**: ui.tableはQuasarのテーブルコンポーネントを使用しているため、カラムヘッダーと値行の境界ずれが発生しない

2. **機能の充実**: 
   - ソート機能が標準装備
   - ページネーションが内蔵
   - レスポンシブ対応

3. **カスタマイズ性**:
   - Vue.jsスロットでセルの表示を自由にカスタマイズ
   - Quasarコンポーネントを活用した高品質なUI

4. **イベント処理**:
   - カスタムイベントを通じてPython側でハンドリング
   - チェックボックス、ボタンクリックなどの操作を簡単に処理

## アクセス方法

1. http://localhost:8081/arrangement-test にアクセス
2. 「タブE」を選択
3. 第1パターンレイアウトの右側パネルにui.table実装が表示されます

## 今後の拡張

- 実際のデータとの連携
- 複数選択時のバッチ操作
- フィルタリング機能の追加
- CSVエクスポート機能