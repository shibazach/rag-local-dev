# 統合PDF表示システム（V5 - 完全版）

本システムは従来の分散したPDFコンポーネント（V1-V4）を統合し、サイズベース自動フォールバック機能を持つ統一ソリューションです。

## 🎯 V5統合アーキテクチャ

### 設計思想
- **単一インターフェース**: 1つのコンポーネントで全サイズのPDF対応
- **自動最適化**: ファイルサイズに応じた最適表示方式の自動選択
- **フォールバック機能**: WebView失敗時の画像方式自動切り替え
- **後方互換**: 既存V1-V4との完全互換性維持

## システム構成

### 1. V5統合モジュール（推奨）

- **`pdf_large_preview_unified.py`**: 🎯 **メイン統合コンポーネント** - 単一API・自動戦略選択
- **`pdf_stream_server_unified.py`**: 統合HTTPサーバー（WebView+画像両対応）

### 2. V3/V4レガシーモジュール（統合済み）

- **V3 (WebView方式)**: `pdf_large_preview_v3.py` + `pdf_stream_server_v3.py`
- **V4 (画像方式)**: `pdf_large_preview_v4.py` + `pdf_stream_server_v4.py` + `pdf_page_renderer.py`

### 3. V1/V2基本モジュール（小容量用）

- **`pdf_preview.py`**: data:URL基本表示（≤1.5MB推奨）

## 🔄 自動戦略選択ロジック

### サイズベース判定

```python
# V5統合版の閾値定義
SIZE_THRESHOLD_WEBVIEW = 20MB    # WebView方式上限
SIZE_THRESHOLD_IMAGE = 100MB     # 画像方式推奨

# 判定フロー
if file_size <= 20MB:
    strategy = "webview"    # PDF.js + WebView表示
else:
    strategy = "image"      # PNG変換 + ft.Image表示
```

### 自動フォールバック

```
PDFファイル読み込み
    │
    ├─ ≤20MB ──→ WebView方式 ──→ ❌失敗 ──→ 画像方式（自動切替）
    │                     │
    │                     └─ ✅成功 ──→ PDF.js表示
    │
    └─ >20MB  ──→ 画像方式 ──→ PNG変換表示
```

## 🚀 V5統合版使用方法

### 推奨: 統合コンポーネント（V5）

```python
from app.flet_ui.shared.pdf_large_preview_unified import create_pdf_preview_unified

# 統合プレビュー作成
pdf_preview = create_pdf_preview_unified(page)

# ファイル読み込み（自動戦略選択）
await pdf_preview.load_pdf("path/to/document.pdf")

# または、バイトデータから
pdf_data = get_pdf_bytes()
await pdf_preview.load_pdf_from_bytes(pdf_data, "document.pdf")

# 戦略強制指定
await pdf_preview.load_pdf("large.pdf", force_strategy="image")
await pdf_preview.load_pdf("small.pdf", force_strategy="webview")
```

### 互換性ラッパー（既存コード）

```python
# 既存V3/V4コード
from app.flet_ui.shared.pdf_large_preview_v4 import create_large_pdf_preview_v4

# 統合版に置き換え（完全互換）
from app.flet_ui.shared.pdf_large_preview_unified import create_large_pdf_preview as create_large_pdf_preview_v4
```

### 戦略手動制御

```python
pdf_preview = create_pdf_preview_unified(page)

# 現在戦略取得
strategy = pdf_preview.get_current_strategy()  # "webview" | "image" | None

# ファイル情報取得
info = pdf_preview.get_file_info()
# {
#   "file_path": "/path/to/file.pdf",
#   "file_size": 25165824,
#   "strategy": "image",
#   "state": "displaying_image",
#   "fallback_attempted": False
# }
```

## ✅ 動作確認・テスト結果

### V5統合版テスト統計
- **基本コンポーネント**: ✅ 初期化・API確認済み
- **戦略判定ロジック**: ✅ サイズベース自動選択確認済み
- **インポート整合性**: ✅ V1-V5全モジュールインポート成功
- **ファクトリ互換性**: ✅ 既存API完全互換確認済み

### 機能比較表

| 機能 | V1基本版 | V3WebView | V4画像 | **V5統合** |
|---|---|---|---|---|
| 小容量PDF (≤1.5MB) | ✅ data:URL | ❌ | ❌ | ✅ WebView自動 |
| 中容量PDF (1.5-20MB) | ❌ 制限 | ✅ PDF.js | ❌ | ✅ WebView自動 |
| 大容量PDF (>20MB) | ❌ 失敗 | ❌ 不安定 | ✅ PNG変換 | ✅ 画像自動 |
| プラットフォーム対応 | 全対応 | 制限あり | 全対応 | **全対応** |
| フォールバック | ❌ | ❌ | ❌ | **✅ 自動** |
| 操作性 | 基本 | 高機能 | 中機能 | **最高** |
| 開発効率 | 低 | 中 | 中 | **最高** |

### 実証テスト結果  
- ✅ **戦略自動選択**: 0.5MB→WebView, 25MB→画像
- ✅ **フォールバック機能**: WebView失敗時の画像切り替え
- ✅ **統合サーバー**: V3/V4統合配信成功
- ✅ **UI統合**: 単一インターフェース動作確認
- ✅ **後方互換性**: 既存V1-V4 API維持確認

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

## 🔮 今後の拡張予定

### V6計画（将来）
- [ ] **マルチページプレビュー**: サムネイル一覧表示
- [ ] **高度検索**: PDF内テキスト検索・ハイライト
- [ ] **注釈機能**: PDF上への注釈・マーキング
- [ ] **暗号化対応**: パスワード保護PDF読み込み
- [ ] **パフォーマンス向上**: WebP形式・先読み最適化

### 既存コンポーネントマイグレーション

```python
# V1-V4 → V5 置き換え推奨パス

# 現在
from app.flet_ui.shared.pdf_preview import create_pdf_preview           # V1
from app.flet_ui.shared.pdf_large_preview_v3 import LargePDFPreviewV3   # V3  
from app.flet_ui.shared.pdf_large_preview_v4 import PDFImagePreviewV4   # V4

# V5統合版（推奨）
from app.flet_ui.shared.pdf_large_preview_unified import create_pdf_preview_unified
```

### レガシー対応状況
- **V1 (`pdf_preview.py`)**: 🟡 小容量専用として保持
- **V2**: 🔴 廃止済み  
- **V3 (`pdf_large_preview_v3.py`)**: 🟡 V5に統合済み・個別使用非推奨
- **V4 (`pdf_large_preview_v4.py`)**: 🟡 V5に統合済み・個別使用非推奨
- **V5 (`pdf_large_preview_unified.py`)**: 🟢 **現在推奨**

## 📋 移行ガイド

### Step 1: 新規開発
```python
# 新規プロジェクトでは直接V5使用
pdf_preview = create_pdf_preview_unified(page)
await pdf_preview.load_pdf("document.pdf")
```

### Step 2: 既存コード移行  
```python
# 段階的移行：インポート変更のみ
# Before
from app.flet_ui.shared.pdf_large_preview_v4 import create_large_pdf_preview_v4

# After（互換性完全保持）
from app.flet_ui.shared.pdf_large_preview_unified import create_large_pdf_preview as create_large_pdf_preview_v4
```

### Step 3: 機能活用
```python
# V5固有機能活用
pdf_preview = create_pdf_preview_unified(page)

# 自動戦略 + フォールバック
await pdf_preview.load_pdf("unknown_size.pdf")  

# 手動戦略指定
await pdf_preview.load_pdf("large.pdf", force_strategy="image")
```
