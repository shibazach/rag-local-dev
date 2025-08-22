# UI設計ポリシー (Flet対応版)

## UI設計の基本原則

### 情報密度最大化の方針
- **無駄な隙間は完全排除**: `padding=0`, `margin=0`, `spacing=0` で必要最小限の余白
- **1画面内の情報量を最大化**: スクロール不要で全情報を表示
- **Fletコンテナの効率的活用**: `expand=True` と適切な `width`/`height` 設定

### 階層的レイアウト設計 (Flet準拠)
- **Level 1 (最下層)**: Page設定 (`page.padding=0`, `page.spacing=0`)
- **Level 2**: メインコンテナ (`ft.Container` でページ全体制御)  
- **Level 3**: セクションレイアウト (`ft.Column`, `ft.Row` で構造化)
- **Level 4 (最上層)**: 個別コンポーネント (`ft.TextField`, `ft.DataTable` 等)

### 場当たり設計完全排除
- **レイアウト定義は1箇所のみ**: 共通コンポーネントでの統一
- **推測による設定禁止**: [Flet公式ドキュメント](https://flet.dev/docs/controls) で仕様確認必須
- **デバッグ駆動設計**: ブラウザ開発者ツールでFletコンポーネント確認

## Flet固有の設計原則

### 公式コントロール優先使用
```python
# ✅ 推奨: 公式コントロール使用
data_table = ft.DataTable(
    columns=[
        ft.DataColumn(ft.Text("Name")),
        ft.DataColumn(ft.Text("Age")),
    ],
    rows=[
        ft.DataRow(cells=[ft.DataCell(ft.Text("Alice")), ft.DataCell(ft.Text("30"))])
    ]
)

# ❌ 非推奨: カスタムテーブル実装
custom_table = ft.Column([
    ft.Row([ft.Text("Name"), ft.Text("Age")]),  # ヘッダー
    ft.Row([ft.Text("Alice"), ft.Text("30")])   # データ
])
```

### Fletネイティブスタイリング
```python
# ✅ 推奨: Flet公式プロパティ
container = ft.Container(
    bgcolor=ft.Colors.BLUE_100,
    border=ft.border.all(1, ft.Colors.BLUE_400),
    border_radius=ft.border_radius.all(8),
    padding=ft.padding.all(16),
    margin=ft.margin.all(8)
)

# ❌ 非推奨: CSS概念の持ち込み (Fletには存在しない)
# style="background-color: blue; border: 1px solid;" 
```

### レスポンシブレイアウト実装
```python
# ✅ 推奨: Fletのexpandシステム活用
main_layout = ft.Row([
    ft.Container(content=sidebar, width=250),     # 固定幅サイドバー
    ft.Container(content=main_area, expand=True)  # 残り幅を全て使用
])

# ✅ 推奨: 柔軟なflex比率設定
flexible_layout = ft.Row([
    ft.Container(content=area1, expand=1),  # 1/3 幅
    ft.Container(content=area2, expand=2),  # 2/3 幅
])
```

## 実装チェックリスト

### 開始前必須確認
- [ ] [Flet Controls Reference](https://flet.dev/docs/controls) で該当コントロール確認
- [ ] [Flet Gallery](https://flet-controls-gallery.fly.dev/) で実装パターン確認
- [ ] [Flet API Reference](https://docs.flet.dev/controls/) でプロパティ仕様確認

### 実装中必須確認
- [ ] 全てのコントロールが `ft.*` 公式コンポーネントか？
- [ ] プロパティ名がAPI Referenceと一致しているか？
- [ ] レイアウトが `Container`, `Row`, `Column` の適切な組み合わせか？
- [ ] 共通コンポーネントから再利用可能な要素を使用しているか？

### 完成後必須確認
- [ ] 画面サイズ変更時の表示が適切か？
- [ ] 情報密度が最大化されているか？
- [ ] 1画面内にスクロール不要で情報が収まっているか？
- [ ] [公式ギャラリー](https://flet-controls-gallery.fly.dev/) の類似例と一致しているか？

## 禁止事項

### 絶対禁止 (Flet環境では不可能)
- **CSS概念の持ち込み**: `class`, `style`, `stylesheet` 等
- **HTML要素の直接操作**: `<div>`, `<span>` 等の使用
- **JavaScript実装**: イベント処理は全てPythonで

### 強く非推奨
- **カスタムコントロール実装**: 公式コントロールで代替可能な場合
- **ハードコードされた数値**: サイズ・色・スペーシングの直接指定
- **推測による実装**: 公式ドキュメント確認なしの実装

## Fletレイアウトパターン

### 基本レイアウト構造
```python
# 標準的なアプリケーションレイアウト
def create_app_layout():
    return ft.Column([
        # ヘッダー
        ft.Container(
            content=ft.AppBar(title=ft.Text("App Title")),
            bgcolor=ft.Colors.BLUE_600,
            height=56
        ),
        
        # メインコンテンツ
        ft.Container(
            content=ft.Row([
                # サイドバー
                ft.Container(
                    content=create_sidebar(),
                    width=250,
                    bgcolor=ft.Colors.GREY_100
                ),
                
                # メインエリア
                ft.Container(
                    content=create_main_content(),
                    expand=True,
                    padding=ft.padding.all(16)
                )
            ]),
            expand=True
        ),
        
        # フッター
        ft.Container(
            content=ft.Text("Footer", text_align=ft.TextAlign.CENTER),
            bgcolor=ft.Colors.GREY_200,
            height=40
        )
    ])
```

### データ表示最適化
```python
# 情報密度最大化テーブル
def create_dense_table():
    return ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("項目", size=14)),
            ft.DataColumn(ft.Text("値", size=14)),
            ft.DataColumn(ft.Text("状態", size=14)),
        ],
        rows=data_rows,
        column_spacing=20,        # 最小限のカラム間隔
        data_row_min_height=32,   # 行の高さ最小化
        data_row_max_height=36,   # 行の高さ最大化制御
        border=ft.border.all(1, ft.Colors.GREY_300),
        border_radius=ft.border_radius.all(4)
    )
```

## 品質保証ガイドライン

### コンポーネント選択基準
1. **公式コントロール優先**: `ft.DataTable` > カスタムテーブル実装
2. **レイアウト公式パターン**: `ft.Column` + `ft.Row` > 独自レイアウト
3. **スタイリング公式プロパティ**: `ft.Colors.*` > 色コード直指定
4. **イベント公式パターン**: `on_click=handler` > カスタムイベント

### パフォーマンス考慮事項
- **遅延読み込み**: 大量データは `ft.ListView` で仮想化
- **状態管理**: `page.session` または コンポーネントクラスで適切に管理
- **更新最適化**: 必要な部分のみ `control.update()` 実行

### アクセシビリティ対応
- **キーボード操作**: Tab順序の適切な設定
- **視覚的フィードバック**: ホバー・フォーカス状態の明示
- **情報伝達**: `tooltip` プロパティの適切な活用

## 公式リソース活用

### 必須参照ドキュメント
- **[Flet Controls](https://flet.dev/docs/controls)**: 基本コントロール一覧
- **[API Reference](https://docs.flet.dev/controls/)**: 詳細仕様
- **[Gallery](https://flet-controls-gallery.fly.dev/)**: 実装例
- **[Layout Guide](https://qiita.com/Tadataka_Takahashi/items/ab0535d228225d3d7bf1)**: レイアウト基礎

### 実装時の参照手順
1. **要求分析**: 必要なコントロールの特定
2. **公式確認**: Controls Reference での仕様確認  
3. **例示研究**: Gallery での実装パターン確認
4. **API詳細**: API Reference でプロパティ詳細確認
5. **実装**: 公式パターンに準拠した実装
6. **検証**: 公式例との整合性確認

---

*このポリシーは[Flet公式ドキュメント](https://flet.dev/docs/controls)に準拠し、実際の開発経験に基づいて策定されています。*

*最終更新: 2025年8月22日*