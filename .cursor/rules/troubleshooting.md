# トラブルシューティングガイド（2025年1月実証済み）

## 白画面問題の診断手順

### 症状: ページが真っ白で何も表示されない
1. **HTMLレスポンス確認**
   ```bash
   curl -s "http://localhost:8081/ページ名" | grep -c '<div id="app">'
   ```
   - 0の場合: Vue.jsのマウントポイントが生成されていない
   - 1の場合: HTMLは正常、JavaScript側の問題

2. **ブラウザコンソール確認**
   - `F12` → Console タブ
   - 赤色のエラーメッセージを確認
   - 特に`setAttribute`関連のエラーに注意

3. **import経路確認**
   ```python
   # ❌ 循環importの原因
   from prototypes.ui.components.layout import RAGHeader
   
   # ✅ 正しいimport
   from ui.components.layout import RAGHeader
   ```

## JavaScriptエラーの解決方法

### エラー: `Failed to execute 'setAttribute' on 'Element': '0' is not a valid attribute name`

**原因**: NiceGUIの`props()`メソッドで複数行の文字列を不正に連結

```python
# ❌ エラーの原因（スペースなし）
element.props(
    'onfocus="this.style.borderColor=\'#3b82f6\'"'
    'onblur="this.style.borderColor=\'#d1d5db\'"'
)
# → "0":true, "3px":true のような不正な属性が生成される

# ✅ 正しい実装（行末にスペース追加）
element.props(
    'onfocus="this.style.borderColor=\'#3b82f6\'" '  # スペース重要！
    'onblur="this.style.borderColor=\'#d1d5db\'"'
)
```

## ファイル分割時の注意事項

### タブコンテンツの分離
```python
# arrangement_test.py（メインファイル）
from ui.pages.arrangement_test_tab_a import ArrangementTestTabA

# タブAのレンダリング
tab_a = ArrangementTestTabA()
tab_a.render()
```

**重要**: 
- メインファイルとタブファイルのimport経路を統一
- クラス名の重複を避ける
- 各タブファイルは独立して動作可能に設計

## 共通コンポーネント移行時のリスク管理

### 段階的移行プロセス
1. **実験段階**: `arrangement_test.py`で新実装をテスト
2. **バックアップ**: 既存ファイルを`_backup`付きでコピー
3. **小規模テスト**: 1つのコンポーネントから移行
4. **動作確認**: 各段階でサーバー再起動とブラウザ確認
5. **ロールバック準備**: 問題発生時は即座に元に戻す

### ファイル管理のベストプラクティス
```bash
# クリーンアップ前の確認
ls -la prototypes/ui/pages/arrangement_test*

# 不要ファイルの削除（慎重に）
rm prototypes/ui/pages/arrangement_test_old.py
rm prototypes/ui/pages/arrangement_test_new.py
```

## デバッグ効率化テクニック

### サーバー起動の自動化
```bash
# タイムアウト付き起動（推奨）
cd /workspace/prototypes && timeout 15 python3 main.py &
```

### エラーチェックの習慣化
1. コード変更後は必ずサーバー再起動
2. ブラウザのハードリロード（Ctrl+Shift+R）
3. Developer Toolsのコンソール確認
4. ネットワークタブで404エラーチェック

## よくあるエラーと解決法

### TypeError: Button.__init__() got an unexpected keyword argument
**原因**: NiceGUIのAPIが期待と異なる
**解決**: 公式ドキュメントで正しい引数を確認

### 'Element' object has no attribute 'on_click'
**原因**: ui.element()に直接on_clickを設定しようとした
**解決**: ui.button()を使うか、別の方法でクリック処理を実装

### 'Radio' object has no attribute 'on_change'
**原因**: ui.radio()のイベント処理が期待と異なる
**解決**: on_changeはui.radio()の引数として直接渡す

### 高さ制御の問題
**症状**: コンテンツが画面からはみ出る
**診断手順**:
1. ブラウザ開発者ツールで各要素の実測値確認
2. calc()の計算が二重になっていないか確認
3. flex-shrink: 0とflex: 1の使い分けを確認
4. コンテンツ自体の内部spacing確認

## メモリ設定の重要性

作業完了時には必ず[[memory:5216600]]タイムアウト付きサーバー起動を使用し、
不確実な推測ではなく[[memory:5216640]]実際の動作確認を優先すること。