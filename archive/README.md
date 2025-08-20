# 📦 Archive Directory

このフォルダは、プロジェクトの整理に伴って移動された非推奨・実験ファイルを保管しています。

## フォルダ構造

```
archive/
├── deprecated_files/        # 非推奨バックアップファイル
│   ├── files_backup.py     # 旧ファイル管理ページ
│   └── ocr_adjustment_backup.py  # 旧OCR調整ページ
├── experimental_files/      # 実験用ファイル
│   ├── arrangement_test*.py # UI配置テスト群
│   └── test_minimal.py     # 最小限テストページ
├── deprecated_docs/         # 古いドキュメント
│   ├── 現在の課題と対応方針.md
│   ├── 技術選択比較分析.md
│   └── integration/        # 統合フェーズレポート群
└── README.md               # このファイル
```

## ファイル保管理由

### deprecated_files/ 
- **復旧時の参照用**: 万一現在の実装に問題が発生した場合の参照元
- **履歴保存**: 開発過程の記録として保持

### experimental_files/
- **UI実験記録**: NiceGUI UI実装のテストパターン保存
- **学習資料**: 今後のUI開発時の参考資料

### deprecated_docs/
- **プロジェクト履歴**: システム統合過程の記録
- **意思決定履歴**: 技術選択の判断根拠保存

## 管理方針

- **定期レビュー**: 6ヶ月ごとに内容見直し
- **永続保存**: 重要な技術的判断履歴は永続保存
- **削除基準**: 3年以上参照されない実験ファイルは削除検討

**最終更新**: 2025年1月XX日
