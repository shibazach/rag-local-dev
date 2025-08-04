# JavaScript初期化とAPIデータ表示の問題解決ガイド

## 概要
データ登録ページでファイルリストが「一瞬表示されて消える」問題の根本原因と解決方法をまとめる。

## 根本原因
1. **JavaScriptオブジェクトの初期化不足**: HTMLテンプレートでJavaScriptオブジェクトの`init()`メソッドが呼ばれていない
2. **APIレスポンス構造の不一致**: JavaScriptが期待するデータ構造とAPIが返すデータ構造が異なる
3. **ファイル競合**: 複数のJavaScriptファイルが同じ機能を実装して競合する

## 解決手順

### 1. JavaScript初期化の確認
HTMLテンプレートの末尾に以下の初期化スクリプトが必要：

```html
<script>
document.addEventListener('DOMContentLoaded', function() {
    DataRegistration.init(); // またはオブジェクト名.init()
});
</script>
```

### 2. APIレスポンス構造の統一
- **API側**: `{ files: [...], pagination: {...} }`形式で返す
- **JavaScript側**: `result.files`でアクセスする
- **注意**: `result.data?.files`ではなく`result.files`

### 3. JavaScriptファイルの競合回避
- 1つのページに対して1つのメインJavaScriptファイルのみ読み込む
- 共通機能は別ファイルに分離し、名前空間を分ける
- `file_selection.js`と`data_registration.js`の同時読み込みは禁止

## 予防策

### JavaScript読み込み時の注意点
```html
<!-- 正しい例: 1つのメインJSのみ -->
{% block extra_js %}
<script src="{{ url_for('static', path='/js/data_registration.js') }}?v=2" defer></script>
{% endblock %}

<!-- 間違い例: 複数のメインJSを読み込み -->
{% block extra_js %}
<script src="{{ url_for('static', path='/js/data_registration.js') }}?v=1" defer></script>
<script src="{{ url_for('static', path='/js/file_selection.js') }}?v=1" defer></script>
{% endblock %}
```

### ブラウザキャッシュ対策
JavaScriptファイルを修正した際は、HTMLテンプレートでバージョン番号を更新：
```html
<script src="...?v=2" defer></script> <!-- v=1 から v=2 に更新 -->
```

## デバッグ手順
1. **開発者ツールのConsoleタブ**: JavaScriptエラーを確認
2. **Networkタブ**: APIリクエスト/レスポンスを確認
3. **Elementsタブ**: DOM要素が正しく生成されているか確認

## 今回の具体例
- **問題**: データ登録ページでファイルが一瞬表示されて消える
- **原因**: `DataRegistration.init()`が呼ばれていない
- **解決**: HTMLテンプレートに初期化スクリプトを追加

## 他のモデルへの注意事項
- **絶対にやってはいけない**: 複数のJavaScriptファイルで同じDOM要素を操作すること
- **必須作業**: 新しいページを作る際は必ず初期化スクリプトを追加すること
- **確認方法**: ブラウザの開発者ツールでエラーを必ず確認すること