#!/bin/bash

cd "$(dirname "$0")"

echo "🧱 ビルド（--no-cache）"
docker compose build --no-cache

echo "🚀 コンテナ起動"
docker compose up -d

echo "⏳ PostgreSQLの起動待機（5秒）"
sleep 5

echo "🔌 EXTENSION: pgvector を有効化"
docker exec pgvector-db psql -U raguser -d ragdb -c "CREATE EXTENSION IF NOT EXISTS vector;"
if [ $? -ne 0 ]; then
  echo "❌ 拡張作成に失敗しました（PostgreSQLが起動していない可能性）"
  docker logs pgvector-db | tail -n 30
  exit 1
fi

echo "🔍 拡張一覧を確認中..."
docker exec pgvector-db psql -U raguser -d ragdb -c "\dx" | grep vector > /dev/null
if [ $? -eq 0 ]; then
  echo "✅ pgvector 拡張は正常に有効化されています！"
else
  echo "❌ pgvector 拡張が確認できませんでした。手動で \dx を確認してください。"
fi

#echo "🧑‍💻 接続開始（psqlシェル）"
# docker exec -it pgvector-db psql -U raguser -d ragdb
