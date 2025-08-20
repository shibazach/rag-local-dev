# 📝 Logs Directory

## フォルダ構造

```
logs/
├── prototypes/        # プロトタイプ開発ログ
│   └── prototypes.log
├── app/              # アプリケーションメインログ
│   └── app.log
├── audit/            # 監査・セキュリティログ
│   ├── audit.log
│   └── security.log
└── README.md         # このファイル
```

## ログファイル説明

### prototypes/
- **prototypes.log**: NiceGUI プロトタイプ開発時のログ

### app/
- **app.log**: メインアプリケーションの実行ログ

### audit/
- **audit.log**: システム監査ログ
- **security.log**: セキュリティ関連ログ

## ログローテーション

必要に応じて logrotate 設定を追加してください：

```bash
/workspace/logs/*/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    copytruncate
}
```
