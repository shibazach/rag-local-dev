# CSS責任分離

## ファイル構成
```
prototypes/
├── main_new.py                 # ページ定義のみ（CSS記述禁止）
├── ui/
│   ├── styles/
│   │   ├── global.css          # 唯一のグローバルCSS定義場所
│   │   └── common.py           # Python定数・クラス定義
│   ├── components/
│   │   └── layout.py           # レイアウトコンポーネント
│   └── pages/
│       └── *.py                # ページ固有ロジック（CSS記述禁止）
```

## CSS定義規則
- グローバルCSS：`ui.add_head_html()`は1箇所のみで定義
- Python定数：`CommonStyles`クラスで色・サイズ・スペーシング管理
- コンポーネントクラス：再利用可能なTailwind/カスタムクラス定義

## 共通設定の切り出し
```python
# ui/styles/common.py
class CommonStyles:
    # フォントサイズ
    FONT_SIZE_XS = "text-xs"      # 12px
    FONT_SIZE_SM = "text-sm"      # 14px
    FONT_SIZE_BASE = "text-base"  # 16px
    
    # 色設定
    COLOR_PRIMARY = "#334155"     # メイン色
    COLOR_TEXT_PRIMARY = "#1f2937"
    
    # スペーシング
    PADDING_NONE = "p-0"
    MARGIN_NONE = "m-0"
    
    # コンポーネント
    BTN_PRIMARY = "bg-blue-600 hover:bg-blue-700 text-white font-medium px-4 py-2 rounded"
    CARD_BASE = "bg-white rounded-lg shadow-md p-4"
```

## 完全paddingゼロ実現ノウハウ（実証済み）

### 成功パターン
1. **position:fixed + 明示的寸法指定**
   ```css
   position:fixed;top:0;left:0;right:0;width:100%;height:48px;
   background:#334155;padding:0;margin:0;overflow:hidden;
   ```
   → ヘッダー・フッターで100%成功

2. **グローバルCSS階層制御**
   ```css
   html, body { margin:0; padding:0; width:100%; overflow-x:hidden; }
   #q-app { margin:0; padding:0; width:100%; overflow-x:hidden; }
   .q-layout { margin:0; padding:0; width:100%; overflow-x:hidden; }
   .q-page-container { padding:0; margin:0; width:100%; }
   .q-page { padding:0; margin:0; width:100%; }
   .nicegui-content { padding:0; margin:0; width:100%; }
   .nicegui-row, .nicegui-column { margin:0; padding:0; gap:0; }
   ```
   → 全フレームワーク制御で成功

3. **要素別明示的制御**
   ```python
   ui.element('div').style('margin:0;margin-left:0;margin-right:0;padding:0;width:100%;')
   ```
   → 個別要素でも成功

### 失敗パターン
1. **TailwindCSS依存**: `px-4`, `py-2` 等は意図しないpadding挿入
2. **100vw使用**: スクロールバー分はみ出し → `width:100%`が正解
3. **NiceGUI classes()依存**: `w-full`等も内部でpadding付与の可能性

### 確実な手順
1. グローバルCSS設定（main.py）
2. position:fixed要素（ヘッダー・フッター）
3. 個別要素の明示的制御
4. ブラウザ開発者ツールで実測値確認

## デバッグ手順

### 隙間問題の解決手順
1. ブラウザ開発者ツールでDOM構造確認
2. 各レベル（html/body/.q-page/.nicegui-content）の実測値確認
3. 計算値と期待値の差分特定
4. 該当レベルのCSSを正確に上書き

### センタリング問題の解決手順
1. 親コンテナがFlexboxか確認
2. `justify-content`と`align-items`の設定確認
3. 子要素の`flex`プロパティ確認
4. テキストの場合は`text-align`併用