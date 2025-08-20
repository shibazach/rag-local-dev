# 📊 Database Management

## フォルダ構造

```
database/
├── migrations/         # SQLマイグレーションファイル
│   └── 001_create_upload_logs_table.sql
├── scripts/           # Pythonスクリプト
│   └── create_upload_logs_table.py
└── README.md          # このファイル
```

## マイグレーションファイル

### 001_create_upload_logs_table.sql
アップロードログテーブルの作成とインデックス、トリガーの設定

**実行方法:**
```bash
psql -U your_user -d your_database -f database/migrations/001_create_upload_logs_table.sql
```

## スクリプト

### create_upload_logs_table.py
PythonからSQLAlchemyを使用してアップロードログテーブルを作成

**実行方法:**
```bash
python database/scripts/create_upload_logs_table.py
```

## 使用方針

- 新しいマイグレーションファイルは `migrations/` フォルダに連番で配置
- Python実装が必要な複雑な操作は `scripts/` フォルダに配置
- 本番環境では SQLファイル、開発環境では Pythonスクリプトを使用推奨
