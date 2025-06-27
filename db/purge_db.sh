#!/bin/bash

cd "$(dirname "$0")"

echo "⚠️ ragdbのボリューム/コンテナを完全に削除します。"
echo ""

read -p "本当に初期化しますか？ [yes/NO]: " confirm
if [[ "$confirm" != "yes" ]]; then
  echo "❎ キャンセルされました。変更はありません。"
  exit 0
fi

echo "🛑 コンテナ停止・削除"
docker compose -f docker-compose.db.yml down

echo "🧹 volume 削除（データ全消去）"
docker volume rm ragdb

echo "🧼 ネットワークも削除（必要に応じて）"
docker network rm ragnet 2>/dev/null || echo "⚠️ ネットワークは存在しないか、他のサービスで使用中"

echo "♻️ 完全リセット完了！再構築には ./setup_db.sh を実行してください。"