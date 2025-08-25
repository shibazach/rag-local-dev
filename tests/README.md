# Flet RAGシステム - テストディレクトリ

## 構成

```
tests/
├── README.md                              # このファイル
└── debug/                                # デバッグ用ファイル
    ├── test_tab_d_standalone.py          # TabD単体テスト
    ├── test_ocr_adjustment_standalone.py # OCR調整ページ単体テスト
    ├── main_debug.py                     # デバッグ専用メインアプリ
    └── debug_strategies.md               # デバッグ戦略ドキュメント
```

## 使用方法

### TabD単体テスト
```bash
# WorkspaceRoot で実行
cd /workspace
python tests/debug/test_tab_d_standalone.py
```

### OCR調整ページ単体テスト
```bash
# WorkspaceRoot で実行
cd /workspace
python tests/debug/test_ocr_adjustment_standalone.py
```

### デバッグ専用アプリ
```bash
# メニュー表示
python tests/debug/main_debug.py

# TabD直接起動
python tests/debug/main_debug.py tab_d
```

### URL
- メインアプリ: http://localhost:8500
- デバッグアプリ: http://localhost:8502
- TabD単体テスト: http://localhost:8501
- OCR調整単体テスト: http://localhost:8501

## 注意事項
- 全てのスクリプトはワークスペースルートから実行
- パス解決は各ファイルで自動調整済み
- プロセス終了は `pkill -f ファイル名` で確実に実行
