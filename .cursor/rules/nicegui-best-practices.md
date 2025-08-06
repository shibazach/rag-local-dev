# NiceGUI特化ガイドライン

## DOM構造の正確理解
```html
<body>                           <!-- ブラウザデフォルト: margin: 8px -->
  <div id="q-app">               
    <div class="q-layout">       
      <header class="q-header">  <!-- メニューエリア -->
      <main class="q-page-container">  <!-- Quasarデフォルト: padding: 16px -->
        <div class="q-page">     <!-- Quasarデフォルト: padding: 16px -->
          <div class="nicegui-content">  <!-- NiceGUIデフォルト: padding: 1rem -->
            <!-- コンテンツエリア -->
          </div>
        </div>
      </main>
    </div>
  </div>
</body>
```

## 余白除去の正確な実装
- ブラウザリセット：`html, body { margin: 0; padding: 0; }`
- Quasar制御：`.q-page-container, .q-page { padding: 0; }`
- NiceGUI制御：`.nicegui-content { padding: 0; }`
- コンポーネント制御：`.nicegui-row, .nicegui-column { gap: 0; }`

## センタリング設計原則
- Flexboxコンテナ使用：`display: flex; justify-content: center; align-items: center;`
- `text-align: center`はインライン要素のみ使用
- コンテナとアイテムのセンタリングを明確に区別

## NiceGUI公式ドキュメント準拠の基本原則
**参考**: [NiceGUI Documentation](https://nicegui.io/documentation/)

### コンポーネント設計のNiceGUI準拠ルール
1. **ui.element()ベース構築**: 全てのカスタムコンポーネントは`ui.element()`から開始
2. **context manager活用**: `with ui.element():` パターンで階層構造を明確化
3. **style()メソッド統一**: `.style('CSS文字列')` での統一的スタイル制御
4. **props()での属性制御**: HTML属性は`.props('id="xxx" class="yyy"')`で設定
5. **classes()でCSS class**: Tailwind等のクラス指定は`.classes('w-full h-full')`
6. **公式コンポーネント優先**: 可能な限り`ui.button()`, `ui.table()`, `ui.card()`等を活用

### NiceGUIコンポーネント階層構造（公式推奨）
```python
# Level 1: Page Layout（ページ全体）
ui.page('/path')
def page_function():
    with ui.header():         # ヘッダー
        pass
    with ui.column():         # メインコンテンツ
        with ui.row():        # 横並びセクション
            with ui.card():   # カードコンポーネント
                ui.label()    # 個別要素
    with ui.footer():         # フッター
        pass
```

### padding/margin設定の公式準拠アプローチ
```python
# ❌ 旧方式: CSS直書き回避
ui.element('div').style('padding: 16px; margin: 8px;')

# ✅ 推奨: NiceGUIクラス + 必要時CSS補完
ui.element('div').classes('p-4 m-2').style('box-sizing: border-box;')

# ✅ 公式コンポーネント + スタイル調整
ui.card().classes('p-4').style('margin: 0; padding: 16px;')
```

### レスポンシブ設計（公式推奨）
```python
# Tailwindクラス活用
ui.element('div').classes('w-full h-screen md:w-1/2 lg:w-1/3')

# グリッドシステム
with ui.grid(columns='repeat(auto-fit, minmax(300px, 1fr))'):
    for item in items:
        ui.card()
```

## 基本UI要素（公式推奨優先順位）
1. **ui.card()**: パネル・セクション区切り
2. **ui.column() / ui.row()**: レイアウト制御
3. **ui.button()**: 全ボタン操作
4. **ui.table()**: データ表示（ページネーション内蔵）
5. **ui.input() / ui.select()**: フォーム要素
6. **ui.label() / ui.html()**: テキスト表示
7. **ui.icon()**: アイコン表示

## 高度な公式コンポーネント
```python
# ページネーション（公式内蔵機能）
ui.table(columns=columns, rows=rows, pagination=True)

# タブシステム（公式推奨）
with ui.tabs() as tabs:
    ui.tab('tab1', label='タブ1')
    ui.tab('tab2', label='タブ2')
with ui.tab_panels(tabs):
    with ui.tab_panel('tab1'):
        ui.label('タブ1コンテンツ')

# スプリッター（公式コンポーネント）
with ui.splitter() as splitter:
    with splitter.before:
        ui.label('左パネル')
    with splitter.after:
        ui.label('右パネル')
```

## 重要な技術仕様

### NiceGUIデフォルト値（実測）
- `.q-page-container`: `padding: 16px`
- `.q-page`: `padding: 16px`
- `.nicegui-content`: `padding: 1rem` (16px)
- `.nicegui-row`: `gap: 8px`
- `.nicegui-column`: `gap: 8px`

### ブラウザデフォルト値
- `body`: `margin: 8px`
- `h1-h6`: `margin-top`, `margin-bottom`設定あり