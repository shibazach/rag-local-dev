# JavaScript競合防止ガイドライン

## 概要
ファイル選択機能で「一瞬だけデータが表示されて消える」問題の根本原因と防止策をまとめる。

## 問題の経緯
2025年1月30日15時頃、データ登録ページのファイル選択機能で以下の問題が発生：
- PDFデータはDBから正常に取得されている（ターミナルログ確認済み）
- ファイルリストが一瞬表示されて即座に消える現象
- ブラウザコンソールにエラーメッセージなし

## 根本原因
複数のJavaScriptファイルが同じ機能を提供し、初期化処理で競合が発生：

### 競合していたファイル
1. `new/static/js/data_registration.js` - データ登録ページ専用
2. `new/static/js/file_selection.js` - 汎用ファイル選択（独自API使用）

### 競合の仕組み
```html
<!-- data_registration.html -->
<script src="/js/data_registration.js" defer></script>
<script src="/js/file_selection.js" defer></script> <!-- 競合原因 -->
```

1. `data_registration.js`がファイルリストを正常に表示
2. `file_selection.js`が後から読み込まれ、存在しないAPIエンドポイントを呼び出し
3. `file_selection.js`の初期化失敗により、DOMが初期状態に戻される

## 解決策

### 即座の対応
```html
<!-- 修正後: data_registration.html -->
<script src="/js/data_registration.js?v=2" defer></script>
<!-- file_selection.jsを削除 -->
```

### 予防策
1. **単一責任原則**: 1ページ1JavaScript機能
2. **バージョン管理**: `?v=X`でブラウザキャッシュ回避
3. **APIエンドポイント確認**: 使用前に存在確認

## JavaScript設計原則

### ファイル構成ルール
```
新システム用JavaScript:
├── data_registration.js  # データ登録ページ専用
├── chat.js              # チャットページ専用  
├── files.js             # ファイル管理ページ専用
└── common.js            # 共通機能のみ
```

### 命名規則
- `{ページ名}.js` - ページ専用機能
- `common.js` - 全ページ共通機能
- `{機能名}_utils.js` - 特定機能のユーティリティ

### HTMLテンプレートでの読み込み
```html
{% block extra_js %}
<!-- ページ専用JSのみ読み込み -->
<script src="{{ url_for('static', path='/js/{ページ名}.js') }}?v={バージョン}" defer></script>
{% endblock %}
```

## デバッグ手順

### 問題発生時の確認順序
1. **ターミナルログ**: APIが正常にデータを返しているか
2. **ブラウザNetwork**: APIリクエストが成功しているか
3. **ブラウザConsole**: JavaScriptエラーの有無
4. **Elements**: DOMにデータが挿入されているか
5. **Sources**: 複数のJSファイルが競合していないか

### 典型的なエラーパターン
- `Auth.getAuthToken() is not defined` → 認証関数未定義
- `fetch('/api/non-existent') failed` → 存在しないAPIエンドポイント
- `Cannot read property of undefined` → データ構造の不一致

## 今後の開発指針

### JavaScript追加時の注意事項
1. 既存JSファイルとの競合確認
2. APIエンドポイントの事前確認
3. 単一ページでの動作テスト
4. ブラウザキャッシュクリアテスト

### 緊急対応手順
1. 競合しているJSファイルを特定
2. 不要なJSファイルをHTMLから削除
3. バージョン番号を上げてキャッシュクリア
4. 動作確認後、根本原因をドキュメント化

## 関連ファイル
- `new/templates/data_registration.html`
- `new/static/js/data_registration.js`
- `new/static/js/file_selection.js` (使用禁止)
- `new/routes/ui.py`

## 更新履歴
- 2025-01-30: 初版作成（データ登録ページJS競合問題対応）