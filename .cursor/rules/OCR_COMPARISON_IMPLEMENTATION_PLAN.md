# OCR比較検証機能 - 新系移植実装計画

## 📋 旧系機能分析結果

### 既存機能概要
**旧系 (`OLD/app/routes/try_ocr.py` + `try_ocr.html`)**
- ✅ 複数OCRエンジン比較 (OCRMyPDF, Tesseract等)
- ✅ ファイルアップロード → 一時処理
- ✅ 単一ページ/全ページ処理対応
- ✅ 誤字修正辞書機能 (CSV辞書使用)
- ✅ 全角→半角変換統合処理
- ✅ リアルタイムPDF表示
- ✅ HTML置換結果ハイライト
- ✅ エンジンパラメータ調整UI

### 主要APIエンドポイント
- `GET /try_ocr` - OCR比較ページ表示
- `POST /api/try_ocr/process` - OCR処理実行
- `GET /api/try_ocr/engines` - 利用可能エンジン一覧
- `GET /api/try_ocr/engine_parameters/{engine_name}` - エンジンパラメータ

## 🎯 新系移植方針

### 要件
1. **DB内ファイル使用**: `files_blob`から直接選択 (アップロード不要)
2. **n=1選択**: データ登録右ペインのファイル選択UIを流用
3. **複数エンジン比較**: 旧系と同等の比較機能
4. **UI統合**: 新系デザインガイドライン準拠

### アーキテクチャ設計

```
new/
├── templates/
│   └── ocr_comparison.html         # 新ページ
├── static/
│   ├── css/
│   │   └── ocr_comparison.css      # 専用CSS
│   └── js/
│       ├── ocr_comparison.js       # メイン機能
│       ├── ocr_file_selector.js    # ファイル選択（データ登録流用）
│       └── ocr_results_display.js  # 結果表示
├── api/
│   └── ocr_comparison.py           # OCR比較API
└── services/
    └── ocr_comparison/
        ├── __init__.py
        ├── comparison_engine.py    # 比較処理エンジン
        └── correction_service.py   # 誤字修正サービス
```

## 🔄 実装フェーズ

### フェーズ1: 基盤実装
- [ ] `ocr_comparison.py` API実装
- [ ] `ocr_comparison.html` ページ作成
- [ ] データ登録右ペインファイル選択機能流用

### フェーズ2: OCR比較エンジン
- [ ] `comparison_engine.py` - 複数エンジン並列処理
- [ ] `correction_service.py` - 誤字修正・正規化処理
- [ ] 結果比較・統計表示機能

### フェーズ3: UI/UX統合
- [ ] `ocr_comparison.css` - 新系デザイン統合
- [ ] `ocr_file_selector.js` - ファイル選択UI (n=1対応)
- [ ] `ocr_results_display.js` - 結果表示・ハイライト

### フェーズ4: 検証・最適化
- [ ] 統合テスト
- [ ] パフォーマンス最適化
- [ ] エラーハンドリング強化

## 🎨 UI設計方針

### レイアウト
```
┌─────────────────────────────────────────┐
│ ナビゲーション                              │
├─────────────────────────────────────────┤
│ 📄 OCR比較検証                            │
├──────────────┬──────────────────────────┤
│ 左ペイン         │ 右ペイン                   │
│                │                        │
│ ファイル選択      │ OCR設定                  │
│ ・DB内ファイル    │ ・エンジン選択             │
│ ・n=1選択       │ ・ページ指定              │
│ ・プレビュー      │ ・誤字修正ON/OFF          │
│                │ ・比較実行ボタン           │
├──────────────┴──────────────────────────┤
│ 下ペイン: 比較結果表示                       │
│ ┌──────┬──────┬──────┬──────┐      │
│ │OCRMyPDF│Tesseract│Custom│統計  │      │
│ │結果     │結果      │結果   │比較  │      │
│ └──────┴──────┴──────┴──────┘      │
└─────────────────────────────────────────┘
```

### データ登録右ペイン流用ポイント
- `FileSelectionManager` クラス活用
- `maxSelection: 1` で単一ファイル選択制限
- 既存のフィルター・検索機能そのまま利用
- `files_blob` テーブル直接アクセス

## 📡 API設計

### `/api/ocr-comparison/process`
```json
{
  "file_id": "uuid-string",
  "engines": ["ocrmypdf", "tesseract", "custom"],
  "page_num": 1,
  "use_correction": true,
  "correction_settings": {
    "enable_typo_fix": true,
    "enable_normalization": true
  }
}
```

### レスポンス
```json
{
  "file_info": {
    "id": "uuid",
    "name": "document.pdf",
    "size": 1024000
  },
  "results": {
    "ocrmypdf": {
      "success": true,
      "text": "処理結果テキスト",
      "processing_time": 2.5,
      "confidence": 0.95,
      "corrections": [...]
    },
    "tesseract": {...},
    "custom": {...}
  },
  "comparison": {
    "similarity_matrix": {...},
    "best_engine": "ocrmypdf",
    "statistics": {...}
  }
}
```

## 🔧 技術詳細

### ファイル選択機能流用
```javascript
// ocr_file_selector.js
class OCRFileSelector extends FileSelectionManager {
    constructor() {
        super();
        this.maxSelection = 1; // n=1制限
        this.allowedTypes = ['.pdf', '.png', '.jpg', '.jpeg'];
    }
    
    onFileSelected(fileId) {
        // OCR比較ページ用の処理
        this.loadFilePreview(fileId);
        this.enableComparisonPanel();
    }
}
```

### OCR比較エンジン統合
```python
# services/ocr_comparison/comparison_engine.py
class OCRComparisonEngine:
    def __init__(self):
        self.ocr_factory = OCREngineFactory()
        self.correction_service = CorrectionService()
    
    async def compare_engines(self, file_path: str, engines: List[str], settings: Dict) -> Dict:
        results = {}
        for engine in engines:
            result = await self.process_with_engine(engine, file_path, settings)
            results[engine] = result
        
        return {
            'results': results,
            'comparison': self.generate_comparison(results)
        }
```

## 📝 実装優先度

1. **High**: API基盤・ファイル選択機能流用
2. **Medium**: OCR比較エンジン・結果表示
3. **Low**: 誤字修正統合・高度な統計機能

この計画に基づいて、段階的にOCR比較検証機能を新系に移植実装します。