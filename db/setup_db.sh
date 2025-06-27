#!/bin/bash
#
# REM: PostgreSQL (ragdb) をビルド→起動し、pgvector拡張を有効化するセットアップスクリプト
# REM: ネットワーク ragnet が無ければ安全に自動生成してから Compose を叩く

set -e                               # REM: 途中エラーで即終了
cd "$(dirname "$0")"

echo "🌐 ネットワーク ragnet を確認..."
if ! docker network inspect ragnet >/dev/null 2>&1; then
  echo "🔧 ragnet が無いので新規作成します"
  docker network create --driver bridge ragnet
else
  echo "✅ ragnet は既に存在。再利用します"
fi

echo "🧱 ビルド（--no-cache）"
docker compose -f docker-compose.db.yml build --no-cache    # ← 必要な compose ファイルを明示

echo "🚀 コンテナ起動"
docker compose -f docker-compose.db.yml up -d

echo "⏳ PostgreSQL の起動待機（5秒）"
sleep 5

echo "コンテナの起動確認"
docker ps | grep ragdb

echo "🔌 EXTENSION: pgvector を有効化"
docker exec ragdb psql -U raguser -d ragdb -c \
  "CREATE EXTENSION IF NOT EXISTS vector;"

echo "🔍 拡張一覧を確認中..."
if docker exec ragdb psql -U raguser -d ragdb -c "\dx" | grep -q vector; then
  echo "✅ pgvector 拡張は正常に有効化されています！"
else
  echo "❌ pgvector 拡張が確認できませんでした。手動で \dx を確認してください。"
  exit 1
fi
