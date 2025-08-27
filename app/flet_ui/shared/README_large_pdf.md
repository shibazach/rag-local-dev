# 大容量PDF対応システム

本システムは従来の`pdf_preview.py`の制限（大容量PDFでのdata:URL失敗）を解決するため、サイズ適応型の3段階アプローチを実装しています。

## システム構成

### 1. 核心モジュール

- **`pdf_stream_server.py`**: HTTPストリーミングサーバ（Range要求対応）
- **`pdf_large_preview.py`**: メイン統合コンポーネント（サイズ判定+切替）
- **`pdf_image_renderer.py`**: 画像レンダリング（PyMuPDF使用）
- **`pdf_preview_large.py`**: 本番適用用互換ラッパー

### 2. サイズ判定ロジック

```python
# 閾値定義
SMALL_PDF = 1.5MB    # data:URL方式（従来通り）
LARGE_PDF = 20MB     # HTTPストリーミング
HUGE_PDF = 100MB     # 画像レンダリング推奨
```

### 3. 自動切り替えフロー

```
PDFファイル
    │
    ├─ < 1.5MB ──→ data:URL方式（高速・軽量）
    │
    ├─ 1.5-20MB ──→ HTTPストリーミング + PDF.js（部分読み込み）
    │
    ├─ 20-100MB ──→ HTTPストリーミング + PDF.js（大容量対応）
    │
    └─ > 100MB ──→ 画像レンダリング（確実性重視）
```

## 本番適用方法

### Option 1: 段階的置き換え

```python
# 既存コード
from app.flet_ui.shared.pdf_preview import create_pdf_preview

# 新システム（既存インターフェース互換）
from app.flet_ui.shared.pdf_preview_large import create_pdf_preview
```

### Option 2: 直接使用

```python
from app.flet_ui.shared.pdf_large_preview import create_large_pdf_preview

# 大容量対応プレビュー作成
pdf_preview = create_large_pdf_preview()

# ファイル表示（自動サイズ判定）
pdf_preview.show_pdf_preview(file_info)
```

## 動作確認済み環境

### テスト統計
- **対応PDFファイル数**: 31個
- **data:URL方式対象**: 21個（1.5MB未満）
- **HTTPストリーミング対象**: 10個（1.5-4.24MB）
- **画像レンダリング対象**: 0個（テスト環境に100MB超なし）

### 実証テスト結果
- ✅ HTTPストリーミング: Range要求成功（206 Partial Content）
- ✅ 画像レンダリング: PNG生成成功（50KB, 108DPI）
- ✅ エラーハンドリング: 無効データ・ファイル不存在で適切処理
- ✅ arrangement_test統合: 実環境テスト成功

## 依存関係

新規追加：
```
aiohttp>=3.9.0  # HTTPストリーミングサーバ
```

既存利用：
```
PyMuPDF==1.20.2  # 画像レンダリング
flet>=0.21.0     # UIフレームワーク
```

## トラブルシューティング

### よくある問題

1. **`bad type: 'stream'` エラー**
   - PyMuPDFでのメモリビューオブジェクト問題
   - 解決: `io.BytesIO(pdf_data)` 経由でストリーム化

2. **HTTPストリーミング接続失敗**
   - サーバポート競合またはファイアウォール
   - 解決: 動的ポート割り当て使用

3. **画像レンダリング遅延**
   - 大容量PDFでの処理時間
   - 解決: 非同期処理 + プログレス表示

### パフォーマンス最適化

- **キャッシュ**: レンダリング済み画像の10ページキャッシュ
- **Range要求**: 64KB単位の部分配信
- **スレッドプール**: CPU集約的処理の分離
- **リソース管理**: 一時ファイル自動削除

## セキュリティ考慮事項

- **一時ファイル**: `tempfile.mkdtemp()`で安全な場所に作成
- **Range要求**: 範囲チェックで不正アクセス防止
- **ファイルサイズ**: メモリ使用量制限あり
- **エラー情報**: 内部パス情報の非露出

## 今後の拡張予定

- [ ] PDF暗号化対応
- [ ] サムネイル先行表示
- [ ] ページ単位プリフェッチ
- [ ] WebP形式対応（画像レンダリング）
- [ ] OCR統合（テキスト抽出+検索）
