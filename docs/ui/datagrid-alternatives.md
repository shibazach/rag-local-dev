# DataGrid代替案の比較検討

## 現状の課題

現在のBaseDataGridViewでは、カラムヘッダーと値行の境界がずれる問題が発生しています。これはCSSベースのグリッドレイアウトを使用しているため、内容によってセル幅が変動することが原因です。

## 代替案の比較

### 1. NiceGUI標準のui.table（推奨度: ★★★★★）

**実装例:**
```python
columns = [
    {'name': 'filename', 'label': 'ファイル名', 'field': 'filename', 'align': 'left'},
    {'name': 'size', 'label': 'サイズ', 'field': 'size', 'align': 'center'},
    {'name': 'status', 'label': 'ステータス', 'field': 'status', 'align': 'center'},
]

rows = [
    {'filename': 'document.pdf', 'size': '1.2MB', 'status': '処理完了'},
    {'filename': 'report.docx', 'size': '856KB', 'status': '処理中'},
]

ui.table(columns=columns, rows=rows, pagination=10)
```

**利点:**
- NiceGUI公式コンポーネントで安定性が高い
- ページネーション、ソート、フィルター機能が内蔵
- カラム幅の自動調整で境界ずれが発生しない
- Quasarフレームワークベースで高品質なUI

**欠点:**
- カスタマイズの柔軟性がやや低い
- セル内の複雑なレンダリングには制限あり

**移行コスト:** 低（1-2日程度）

### 2. AG-Grid統合（推奨度: ★★★★☆）

**実装例:**
```python
from nicegui import ui

ui.add_head_html('''
<script src="https://unpkg.com/ag-grid-community/dist/ag-grid-community.min.js"></script>
<link rel="stylesheet" href="https://unpkg.com/ag-grid-community/dist/styles/ag-grid.css">
<link rel="stylesheet" href="https://unpkg.com/ag-grid-community/dist/styles/ag-theme-alpine.css">
''')

ui.html('''
<div id="myGrid" style="height: 400px;" class="ag-theme-alpine"></div>
<script>
    const gridOptions = {
        columnDefs: [
            { field: 'filename', headerName: 'ファイル名' },
            { field: 'size', headerName: 'サイズ' },
            { field: 'status', headerName: 'ステータス' }
        ],
        rowData: [
            { filename: 'document.pdf', size: '1.2MB', status: '処理完了' }
        ]
    };
    new agGrid.Grid(document.querySelector('#myGrid'), gridOptions);
</script>
''')
```

**利点:**
- 業界標準の高機能グリッドコンポーネント
- 豊富な機能（仮想スクロール、エクセル風編集、グループ化等）
- 大量データの高速レンダリング
- 境界ずれ問題が発生しない

**欠点:**
- 外部ライブラリ依存で複雑性が増す
- 商用利用にはライセンス必要
- NiceGUIとの統合に工夫が必要

**移行コスト:** 中（3-5日程度）

### 3. HTMLテーブル＋CSS（推奨度: ★★★☆☆）

**実装例:**
```python
with ui.element('table').style('width: 100%; border-collapse: collapse;'):
    with ui.element('thead'):
        with ui.element('tr'):
            ui.element('th').style('border: 1px solid #ddd; padding: 8px;').text('ファイル名')
            ui.element('th').style('border: 1px solid #ddd; padding: 8px;').text('サイズ')
            ui.element('th').style('border: 1px solid #ddd; padding: 8px;').text('ステータス')
    
    with ui.element('tbody'):
        for row in data:
            with ui.element('tr'):
                ui.element('td').style('border: 1px solid #ddd; padding: 8px;').text(row['filename'])
                ui.element('td').style('border: 1px solid #ddd; padding: 8px;').text(row['size'])
                ui.element('td').style('border: 1px solid #ddd; padding: 8px;').text(row['status'])
```

**利点:**
- シンプルで理解しやすい
- 完全な制御が可能
- 境界ずれが発生しにくい

**欠点:**
- ページネーション、ソート等は自前実装必要
- 大量データでパフォーマンス問題
- モダンな見た目にするには工夫必要

**移行コスト:** 低（1-2日程度）

### 4. 現在のBaseDataGridView改良（推奨度: ★★☆☆☆）

**改良案:**
- CSS Gridではなく`display: table`を使用
- 各カラムに固定幅を強制
- JavaScriptで動的な幅調整

**利点:**
- 既存コードの活用が可能
- 学習コストが低い

**欠点:**
- 根本的な問題解決にならない可能性
- メンテナンスコストが高い

**移行コスト:** 低（0.5-1日程度）

## 推奨事項

### 短期的対応（今すぐ）
1. **ui.tableへの移行を推奨**
   - NiceGUI公式コンポーネントで安定性が高い
   - 移行コストが低く、即座に問題解決可能
   - 将来的なメンテナンスも容易

### 長期的対応（将来）
1. **高度な要件が発生した場合**
   - AG-Grid等の専門グリッドライブラリを検討
   - ただし、現状の要件ではオーバースペック

## 移行手順案

### Phase 1: ui.tableへの段階的移行
1. files.pyから開始（最もシンプル）
2. upload.py、data_registration.pyへ展開
3. BaseDataGridViewは非推奨として保持

### Phase 2: 機能調整
1. カスタムレンダリング（HTMLアイコン等）の移植
2. イベントハンドリングの調整
3. スタイリングの統一

### Phase 3: 完全移行
1. BaseDataGridViewの削除
2. ドキュメント更新

## まとめ

カラムヘッダーと値行の境界ずれ問題を根本的に解決するには、**NiceGUI標準のui.tableへの移行が最適**です。公式サポートがあり、安定性・メンテナンス性に優れ、移行コストも低いため、即座に実施可能です。