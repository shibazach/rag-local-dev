# NiceGUI + CSS設計原則

## 1. CSS責任分離の原則

### ❌ 現在の問題
- `main_new.py`と`ui/pages/index.py`で重複CSS定義
- `!important`だらけの強引な解決
- ファイル間でスタイル競合・上書き

### ✅ 正しいアプローチ
```
prototypes/
├── main_new.py                 # ページ定義のみ（CSS記述禁止）
├── ui/
│   ├── styles/
│   │   ├── global.css          # 唯一のグローバルCSS
│   │   └── common.py           # Python定数のみ
│   ├── components/
│   │   └── layout.py           # レイアウトコンポーネント
│   └── pages/
│       └── index.py            # ページ固有ロジック（CSS禁止）
```

## 2. CSS階層構造の原則

### レベル1: ブラウザリセット（最下層）
```css
/* 8px → 0px に統一 */
html, body { margin: 0; padding: 0; }
```

### レベル2: フレームワーク制御
```css
/* Quasar/NiceGUIデフォルト値を正確に上書き */
.q-page { padding: 0; }           /* 16px → 0 */
.nicegui-content { padding: 0; }  /* 1rem → 0 */
.nicegui-row { gap: 0; }         /* 8px → 0 */
```

### レベル3: 共通デザインシステム
```css
/* 再利用可能なユーティリティ */
.flex-center { display: flex; justify-content: center; align-items: center; }
.text-center { text-align: center; }
```

### レベル4: コンポーネント固有（最上層）
```css
/* 具体的なコンポーネントスタイル */
.hero { background: linear-gradient(...); }
```

## 3. `!important`禁止原則

### ❌ 絶対に使わない
```css
margin: 0 !important;  /* 強引な優先度操作 */
```

### ✅ 自然なCSS優先度
```css
/* より具体的なセレクタで自然に優先 */
.q-page .nicegui-content { margin: 0; }
```

## 4. NiceGUI構造理解の原則

### 実際のDOM構造
```html
<body>                           <!-- ブラウザデフォルト: margin: 8px -->
  <div id="q-app">               
    <div class="q-layout">       
      <header class="q-header">  <!-- メニューエリア -->
      <main class="q-page-container">  <!-- Quasarデフォルト: padding: 16px -->
        <div class="q-page">     <!-- Quasarデフォルト: padding: 16px -->
          <div class="nicegui-content">  <!-- NiceGUIデフォルト: padding: 1rem -->
            <!-- 我々のコンテンツ -->
          </div>
        </div>
      </main>
    </div>
  </div>
</body>
```

### 隙間の根本原因
- **3重の余白**: ブラウザ(8px) + Quasar(16px) + NiceGUI(16px) = 40px
- **各レベルを正確に0にする必要**

## 5. センタリング設計原則

### ❌ 間違ったアプローチ
```python
# text-alignはインライン要素のみ有効
ui.label('タイトル').style('text-align: center;')
```

### ✅ 正しいFlexboxアプローチ
```python
# Flexboxコンテナでセンタリング
with ui.column().classes('w-full').style('display: flex; justify-content: center; align-items: center; flex-direction: column;'):
    ui.label('タイトル')  # 自動的に中央配置
```

## 6. ファイル構成原則

### CSS定義場所（1箇所のみ）
```python
# ui/styles/global.css (または ui.add_head_html 1箇所のみ)
ui.add_head_html('''
<style>
/* 全アプリケーション共通スタイル */
html, body { margin: 0; padding: 0; }
.q-page { padding: 0; }
.nicegui-content { padding: 0; }
.flex-center { display: flex; justify-content: center; align-items: center; }
</style>
''')
```

### Python定数管理
```python
# ui/styles/common.py
class CommonStyles:
    FONT_SIZE_XL = "text-xl"
    COLOR_PRIMARY = "#334155"
    PADDING_NONE = "p-0"
```

### ページ実装
```python
# main_new.py または ui/pages/index.py
def create_page():
    with ui.column().classes('w-full flex-center'):  # CSSクラス使用
        ui.label('タイトル').classes(CommonStyles.FONT_SIZE_XL)  # 定数使用
```

## 7. デバッグ原則

### 段階的確認
1. **ブラウザ開発者ツール** → 実際の計算値確認
2. **1つずつ無効化** → 原因特定
3. **最小限のCSS** → 段階的に追加

### 避けるべきパターン
- 「動かない → `!important`追加」
- 「複数箇所でCSS定義」
- 「推測でデフォルト値設定」

## 8. 実装チェックリスト

### ✅ 開始前確認
- [ ] CSS定義は1箇所のみか？
- [ ] NiceGUIの実際のDOM構造を確認したか？
- [ ] ブラウザデフォルト値を調査したか？

### ✅ 実装中確認
- [ ] `!important`を使っていないか？
- [ ] Flexboxとtext-alignを混同していないか？
- [ ] 複数ファイルで同じスタイルを定義していないか？

### ✅ 完成後確認
- [ ] ブラウザ開発者ツールで計算値が正しいか？
- [ ] 画面端の隙間が0pxか？
- [ ] センタリングが期待通りか？

---

**これらの原則に従い、CSS設計の混乱を根本解決します。**