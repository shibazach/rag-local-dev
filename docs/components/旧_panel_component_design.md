# パネル共通コンポーネント設計書

## 🎯 概要

4ペイン分割レイアウトで使用するパネルを共通コンポーネント化し、再利用性と保守性を向上させる。

## 🏗️ アーキテクチャ

### 基本構成

```
┌─────────────────────────────────┐
│        ヘッダー (48px)           │  ← グラデーション背景、タイトル、ボタン
├─────────────────────────────────┤
│                                 │
│        コンテンツエリア          │  ← flex: 1, 可変高さ
│                                 │
├─────────────────────────────────┤
│        フッター (24px)           │  ← オプション、統計情報
└─────────────────────────────────┘
```

### クラス階層

```python
PanelComponent (基底クラス)
├── DataTablePanel (テーブル専用)
├── ChartPanel (グラフ専用) 
├── LogPanel (ログ専用)
└── CustomPanel (カスタム用途)
```

## 🔧 使用方法

### 1. 基本パネル

```python
from prototypes.ui.components.panel import PanelComponent

# 基本的な使用法
with PanelComponent(
    title="データ分析",
    header_gradient="linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
    header_icon="📊",
    header_buttons=[
        {'icon': '📈', 'action': chart_callback},
        {'icon': '⚙️', 'action': settings_callback}
    ],
    show_footer=True,
    footer_left="📊 データ更新中",
    footer_right="15:30"
) as content:
    # コンテンツを配置
    ui.label("ここにコンテンツ")
    with ui.element('div').style('display: grid; grid-template-columns: repeat(2, 1fr); gap: 8px;'):
        # グリッドレイアウト等
```

### 2. データテーブルパネル

```python
from prototypes.ui.components.panel import DataTablePanel

# テーブル専用パネル
table_panel = DataTablePanel(
    title="ユーザー管理",
    data=users_data,  # 20件のデータ
    columns=table_columns,
    rows_per_page=15,
    header_gradient="linear-gradient(135deg, #f093fb 0%, #f5576c 100%)",
    footer_left="👥 20名のユーザー",
    footer_right="最終同期: 15:30"
)

with table_panel as content:
    table_panel.create_table_content()
```

### 3. ヘルパー関数使用

```python
from prototypes.ui.components.panel import (
    create_data_panel,
    create_user_table_panel,
    create_task_panel,
    create_log_panel
)

# 簡単にパネル作成
with create_data_panel("データ分析", "linear-gradient(135deg, #667eea 0%, #764ba2 100%)") as content:
    # データ表示コンテンツ
    pass

# ユーザーテーブルパネル
with create_user_table_panel(users_data) as content:
    content.create_table_content()
```

## ⚙️ 設定オプション

### PanelComponent パラメータ

| パラメータ | 型 | デフォルト | 説明 |
|-----------|----|-----------|----- |
| `title` | str | 必須 | パネルタイトル |
| `header_gradient` | str | 必須 | ヘッダーグラデーション CSS |
| `header_icon` | str | "" | タイトル前のアイコン |
| `header_buttons` | List[Dict] | [] | ヘッダーボタン定義 |
| `show_footer` | bool | True | フッター表示フラグ |
| `footer_left` | str | "" | 左側フッターテキスト |
| `footer_right` | str | "" | 右側フッターテキスト |
| `footer_background` | str | "#f8f9fa" | フッター背景色 |
| `border_radius` | int | 12 | パネル角丸サイズ |
| `footer_height` | int | 24 | フッター高さ |

### ヘッダーボタン定義

```python
header_buttons = [
    {
        'icon': '📈',           # ボタンアイコン
        'action': callback_func  # クリック時のコールバック関数
    },
    {
        'icon': '⚙️',
        'action': lambda: print('Settings clicked')
    }
]
```

## 🎨 スタイルガイド

### 推奨グラデーション

```python
# データ分析系
GRADIENT_DATA = "linear-gradient(135deg, #667eea 0%, #764ba2 100%)"

# ユーザー管理系  
GRADIENT_USER = "linear-gradient(135deg, #f093fb 0%, #f5576c 100%)"

# タスク管理系
GRADIENT_TASK = "linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)"

# ログ・システム系
GRADIENT_LOG = "linear-gradient(135deg, #fa709a 0%, #fee140 100%)"
```

### フッター色パターン

```python
# 明るい背景（通常）
FOOTER_LIGHT = "#f8f9fa"

# ダーク背景（ログパネル等）
FOOTER_DARK = "#374151"
```

## 🔄 移行手順

### フェーズ1: 基底クラス作成
1. `PanelComponent` 基底クラス実装
2. 既存パネルの1つで動作確認
3. スタイル調整

### フェーズ2: 専用クラス拡張
1. `DataTablePanel` 実装
2. 高密度テーブル + ページネーション組み込み
3. 既存ユーザーテーブルを移植

### フェーズ3: 全パネル移植
1. 残り3パネルの移植
2. ヘルパー関数の活用
3. 統一性チェック

### フェーズ4: 最適化
1. パフォーマンス調整
2. コンポーネント間の連携
3. ドキュメント整備

## 🚀 期待効果

### 開発効率向上
- パネル作成時間 70% 短縮
- 統一されたAPI でコード可読性向上
- バグ修正の一元化

### 保守性向上  
- 設計変更時の影響範囲限定
- テストコードの共通化
- ドキュメント整備

### 拡張性確保
- 新しいパネルタイプの追加が容易
- カスタマイズポイントの明確化
- 将来的な機能追加への対応

## 📊 テーブル仕様

### 高密度設計
- 行高: 28px (従来の60%削減)
- フォントサイズ: 11px
- パディング: 4px 8px
- ページング: 15件/ページ

### カラムヘッダー
- 背景: `#3b82f6` (青)
- 文字色: 白
- フォント: 太字 11px

### スクロール対応
- 横スクロール: 自動表示
- 縦スクロール: テーブルエリア内
- ページネーション: 固定位置

これで本格的な共通コンポーネント化の準備が整いました！